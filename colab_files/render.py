import os
import pandas as pd
import cv2
import numpy as np
import numexpr
import gc
import random
import PIL
import time
from PIL import Image, ImageOps
from .generate import generate, isJson
from .noise import add_noise
from .animation import anim_frame_warp
from .animation_key_frames import DeformAnimKeys, LooperAnimKeys, ControlNetKeys
#from .video_audio_utilities import get_frame_name, get_next_frame
from .video_audio_utilities import get_frame_name, get_next_frame, render_preview
from .depth import DepthModel
from .colors import maintain_colors
from .parseq_adapter import ParseqAdapter
from modules.processing import StableDiffusionProcessingImg2Img
from .seed import next_seed
from .image_sharpening import unsharp_mask
from .load_images import get_mask, load_img, load_image, get_mask_from_file
from .hybrid_video import (
    hybrid_generation, hybrid_composite, get_matrix_for_hybrid_motion, get_matrix_for_hybrid_motion_prev, get_flow_for_hybrid_motion, get_flow_for_hybrid_motion_prev, image_transform_ransac,
    image_transform_optical_flow, get_flow_from_images, abs_flow_to_rel_flow, rel_flow_to_abs_flow)
from .save_images import save_image
from .composable_masks import compose_mask_with_check
from .settings import save_settings_from_animation_run
from .deforum_controlnet import unpack_controlnet_vids, is_controlnet_enabled
from .subtitle_handler import init_srt_file, write_frame_subtitle, format_animation_params
from .resume import get_resume_vars
from .masks import do_overlay_mask
from .prompt import prepare_prompt
from modules.shared import opts, cmd_opts, state, sd_model
from modules import lowvram, devices, sd_hijack
from .RAFT import RAFT
#Deforumation_mediator imports/settings
import pickle
import json
import types, copy
from .deforum_mediator import mediator_getValue, mediator_setValue, mediator_set_anim_args
#End settings


#Deforumation_stuff
deforumation_cadence_scheduling_manifest=""
#End settings

def get_now_cadence(now_frame):
    relevant_frames_cadence_modulation = json.loads(deforumation_cadence_scheduling_manifest)
    cadence_now = -1
    for frame_number, cadence_value in relevant_frames_cadence_modulation.items():
        if int(now_frame) >= int(frame_number):
            cadence_now = cadence_value
        else:
            return cadence_now

#Planted a "copy" for Deforumation convenience
def get_resume_vars_d(folder, timestring, cadence,startframe=-1):
    DEBUG_MODE = opts.data.get("deforum_debug_mode_enabled", False)
    # count previous frames
    frame_count = 0
    if startframe != -1:
        frame_count = startframe
    else:
        for item in os.listdir(folder):
            # don't count txt files or mp4 files
            if ".txt" in item or ".mp4" in item: 
                pass
            else:
                filename = item.split("_")
                # other image file types may be supported in the future,
                # so we just count files containing timestring
                # that don't contain the depth keyword (depth maps are saved in same folder)
                if timestring in filename and "depth" not in filename:
                    frame_count += 1
                    # add this to debugging var
                    if DEBUG_MODE:
                        print(f"\033[36mResuming:\033[0m File: {filename}")

    print(f"\033[36mResuming:\033[0m Current frame count: {frame_count}")


    # get last frame from frame count corrected for any trailing cadence frames
    #last_frame = frame_count - (frame_count % cadence)

    # calculate previous actual frame
    #prev_frame = last_frame - cadence

    # calculate next actual frame
    #next_frame = last_frame - 1
    if (frame_count <= 1) or ((frame_count-cadence-1) <= 0):
        turbo_prev_image, turbo_prev_frame_idx = None, 0
        turbo_next_image, turbo_next_frame_idx = None, 0
        # initialize vars
        color_match_sample = None
        start_frame = 0
        prev_frame = 0
        next_frame = 0
        prev_img = None
        next_img = None   
    else:
        prev_frame = frame_count - cadence -1
        next_frame = prev_frame + 1

        # get prev_img/next_img from prev/next frame index (files start at 0, so subtract 1 for index var)
        path = os.path.join(folder, f"{timestring}_{prev_frame:09}.png")  
        prev_img = cv2.imread(path)
        path = os.path.join(folder, f"{timestring}_{next_frame:09}.png")  
        next_img = cv2.imread(path)

    # report resume last/next in console
    print(f"\033[36mResuming:\033[0m Last frame: {prev_frame} - Next frame: {next_frame} ")

    # returns:
    #   last frame count, accounting for cadence
    #   next frame count, accounting for cadence
    #   prev frame's image cv2 BGR
    #   next frame's image cv2 BGR
    return prev_frame, next_frame, prev_img, next_img


def render_animation(args, anim_args, video_args, parseq_args, loop_args, controlnet_args, root):
    cnu = {}
    global deforumation_cadence_scheduling_manifest
    #Deforumation_initialization
    usingDeforumation = True
    cadence_was_one = False
    original_optical_flow_cadence = anim_args.optical_flow_cadence
    original_optical_flow_redo_generation = anim_args.optical_flow_redo_generation
    #End settings
    if not cadence_was_one:
        print("Cadence was not one")
    if opts.data.get("deforum_save_gen_info_as_srt", False):  # create .srt file and set timeframe mechanism using FPS
        srt_filename = os.path.join(args.outdir, f"{root.timestring}.srt")
        srt_frame_duration = init_srt_file(srt_filename, video_args.fps)

    if anim_args.animation_mode in ['2D', '3D']:
        # handle hybrid video generation
        if anim_args.hybrid_composite != 'None' or anim_args.hybrid_motion in ['Affine', 'Perspective', 'Optical Flow']:
            print("Hybrid shit")
            args, anim_args, inputfiles = hybrid_generation(args, anim_args, root)
            # path required by hybrid functions, even if hybrid_comp_save_extra_frames is False
            hybrid_frame_path = os.path.join(args.outdir, 'hybridframes')
            print("animation_mode")
        # initialize prev_flow
        if anim_args.hybrid_motion == 'Optical Flow':
            prev_flow = None

        if loop_args.use_looper:
            print("Using Guided Images mode: seed_behavior will be set to 'schedule' and 'strength_0_no_init' to False")
            if args.strength == 0:
                raise RuntimeError("Strength needs to be greater than 0 in Init tab")
            args.strength_0_no_init = False
            args.seed_behavior = "schedule"
            if not isJson(loop_args.init_images):
                raise RuntimeError("The images set for use with keyframe-guidance are not in a proper JSON format")

    # handle controlnet video input frames generation
    if is_controlnet_enabled(controlnet_args):
        unpack_controlnet_vids(args, anim_args, controlnet_args)
    if usingDeforumation:
        CnSchKeys = ControlNetKeys(anim_args, controlnet_args)
        for cnIndex in range(5): #Save in order to be able to restore later (Deforumation might destroy them)
            keys = [
                "enabled", "module", "model", "weight", "resize_mode", "control_mode", "low_vram", "pixel_perfect",
                "processor_res", "threshold_a", "threshold_b", "guidance_start", "guidance_end"
            ]
            currCnIndex = cnIndex+1
            cnu[f'cn_{currCnIndex}_weight'] = getattr(controlnet_args, f'cn_{currCnIndex}_weight')
            cnu[f'cn_{currCnIndex}_guidance_start'] = getattr(controlnet_args, f'cn_{currCnIndex}_guidance_start')
            cnu[f'cn_{currCnIndex}_guidance_end'] = getattr(controlnet_args, f'cn_{currCnIndex}_guidance_end')
            cnu[f'cn_{currCnIndex}_threshold_a'] = getattr(controlnet_args, f'cn_{currCnIndex}_threshold_a')
            cnu[f'cn_{currCnIndex}_threshold_b'] = getattr(controlnet_args, f'cn_{currCnIndex}_threshold_b')


    #Let the deforum mediator get the anim_args and the args values
    if usingDeforumation:
        mediator_set_anim_args(anim_args, args, root)

    #Deforumation has a chance to overwrite the keys values, if it is using parseq
    if usingDeforumation:
        print("Made for Deforumation version: 0.6.2")
        print("------------------------------------")
        if int(mediator_getValue("use_parseq").strip().strip('\n')) == 1:
            #parseq_adapter.use_parseq = 1

            temp_parseq_manifest = parseq_args.parseq_manifest
            parseq_args.parseq_manifest = str(mediator_getValue("parseq_manifest").strip())

            #keys = ParseqAnimKeys(parseq_args, anim_args, video_args)
            #keys = parseq_adapter.anim_keys
            #parseq_args.parseq_manifest = temp_parseq_manifest

            print("Using Parseq through Deforumation.")
        else:
            print("should_use_deforumation_timestring:" + str(mediator_getValue("should_use_deforumation_timestring").strip().strip('\n')))
            if int(mediator_getValue("should_use_deforumation_timestring").strip().strip('\n')) == 1:
                #Deforum is forced to start from the frame specified by deforum
                frame_idx = int(mediator_getValue("start_frame").strip().strip('\n'))
                mediator_setValue("total_recall_relive", frame_idx)
            args.seed = int(mediator_getValue("seed").strip().strip('\n'))
            if args.seed == -1:
                args.seed = random.randint(0, 2**32 - 1)
    parseq_adapter = ParseqAdapter(parseq_args, anim_args, video_args, controlnet_args, loop_args)
    keys = DeformAnimKeys(anim_args, args.seed) if not parseq_adapter.use_parseq else parseq_adapter.anim_keys
    loopSchedulesAndData = LooperAnimKeys(loop_args, anim_args, args.seed) if not parseq_adapter.use_parseq else parseq_adapter.looper_keys

    # create output folder for the batch
    os.makedirs(args.outdir, exist_ok=True)
    print(f"Saving animation frames to:{args.outdir}")

    # save settings.txt file for the current run
    save_settings_from_animation_run(args, anim_args, parseq_args, loop_args, controlnet_args, video_args, root)

    # resume from timestring
    if anim_args.resume_from_timestring:
        root.timestring = anim_args.resume_timestring

    # Always enable pseudo-3d with parseq. No need for an extra toggle:
    # Whether it's used or not in practice is defined by the schedules
    if parseq_adapter.use_parseq:
        anim_args.flip_2d_perspective = True

        # expand prompts out to per-frame
    #if use_parseq and keys.manages_prompts():
    if parseq_adapter.manages_prompts():
        prompt_series = keys.prompts
    else:
        prompt_series = pd.Series([np.nan for a in range(anim_args.max_frames)])
        for i, prompt in root.animation_prompts.items():
            if str(i).isdigit():
                prompt_series[int(i)] = prompt
            else:
                prompt_series[int(numexpr.evaluate(i))] = prompt
        prompt_series = prompt_series.ffill().bfill()

    # check for video inits
    using_vid_init = anim_args.animation_mode == 'Video Input'

    # load depth model for 3D
    predict_depths = (anim_args.animation_mode == '3D' and anim_args.use_depth_warping) or anim_args.save_depth_maps
    predict_depths = predict_depths or (anim_args.hybrid_composite and anim_args.hybrid_comp_mask_type in ['Depth', 'Video Depth'])
    if predict_depths:
        keep_in_vram = opts.data.get("deforum_keep_3d_models_in_vram")

        device = ('cpu' if cmd_opts.lowvram or cmd_opts.medvram else root.device)
        depth_model = DepthModel(root.models_path, device, root.half_precision, keep_in_vram=keep_in_vram, depth_algorithm=anim_args.depth_algorithm, Width=args.W, Height=args.H,
                                 midas_weight=anim_args.midas_weight)

        # depth-based hybrid composite mask requires saved depth maps
        if anim_args.hybrid_composite != 'None' and anim_args.hybrid_comp_mask_type == 'Depth':
            anim_args.save_depth_maps = True
    else:
        depth_model = None
        anim_args.save_depth_maps = False

    raft_model = None
    load_raft = (anim_args.optical_flow_cadence == "RAFT" and int(anim_args.diffusion_cadence) > 1) or \
                (anim_args.hybrid_motion == "Optical Flow" and anim_args.hybrid_flow_method == "RAFT") or \
                (anim_args.optical_flow_redo_generation == "RAFT")
    if load_raft:
        print("Loading RAFT model...")
        raft_model = RAFT()

    use_deforumation_cadence_scheduling = 0
    # state for interpolating between diffusion steps
    if usingDeforumation: #Should we Connect to the Deforumation websocket server to write the current resume frame properties?
        if int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
            turbo_steps = 1 if using_vid_init else int(mediator_getValue("cadence").strip().strip('\n'))
        else:
            turbo_steps = 1 if using_vid_init else int(anim_args.diffusion_cadence)
        if turbo_steps == 1:
            cadence_was_one = True
        #if int(mediator_getValue("use_deforumation_cadence_scheduling").strip().strip('\n')) == 1:
        #    use_deforumation_cadence_scheduling = 1
        #    deforumation_cadence_scheduling_manifest = str(mediator_getValue("deforumation_cadence_scheduling_manifest").strip().strip('\n'))
        #    print("Deforumation cadence scheduling will be used:\n"
        #          "---------------------------------------------\n"
        #          + str(deforumation_cadence_scheduling_manifest) + "\n")
    else:
        turbo_steps = 1 if using_vid_init else int(anim_args.diffusion_cadence)


    turbo_prev_image, turbo_prev_frame_idx = None, 0
    turbo_next_image, turbo_next_frame_idx = None, 0

    # initialize vars
    prev_img = None
    color_match_sample = None
    start_frame = 0
    frame_idx = start_frame
    # resume animation (requires at least two frames - see function)
    if anim_args.resume_from_timestring:
        # determine last frame and frame to start on
        print("Resume From TimeString!")
        if int(mediator_getValue("should_use_deforumation_timestring").strip().strip('\n')) == 1:
            #Deforum is forced to start from the frame specified by deforum
            frame_idx = int(mediator_getValue("start_frame").strip().strip('\n'))
            ######>>>>>>
            mediator_setValue("total_recall_relive", frame_idx)
            if int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
                print("Cadence value read from Deforumation:"+str(turbo_steps))
            else:
                print("Cadence value read from Deforum:"+str(turbo_steps))
                turbo_steps = int(anim_args.diffusion_cadence)
            
            #frame_idx = frame_idx - (frame_idx%turbo_steps)

            prev_frame, next_frame, prev_img, next_img = get_resume_vars_d(
                folder=args.outdir,
                timestring=root.timestring,
                cadence=turbo_steps,
                startframe=frame_idx
            )
            # set up turbo step vars
            if turbo_steps > 1:
                turbo_prev_image, turbo_prev_frame_idx = prev_img, prev_frame
                turbo_next_image, turbo_next_frame_idx = next_img, next_frame
            # advance start_frame to next frame
            if prev_img is None:
                root.init_sample = None
                root.initial_info = None
                root.first_frame = None
                start_frame = 0
                frame_idx = 0
                print("Trying to close StableDiffusionProcessingImg2Img")
                p = StableDiffusionProcessingImg2Img(sd_model=sd_model,outpath_samples = opts.outdir_samples or opts.outdir_img2img_samples, )
                p.close()
            mediator_setValue("total_recall_relive", frame_idx)
            args.seed = int(mediator_getValue("seed").strip().strip('\n'))
            state.job_count = anim_args.max_frames

        else:        
            prev_frame, next_frame, prev_img, next_img = get_resume_vars(
                folder=args.outdir,
                timestring=root.timestring,
                cadence=turbo_steps
            )

            # set up turbo step vars
            if turbo_steps > 1:
                turbo_prev_image, turbo_prev_frame_idx = prev_img, prev_frame
                turbo_next_image, turbo_next_frame_idx = next_img, next_frame

        # advance start_frame to next frame
        #start_frame = next_frame + 1

    if usingDeforumation: #Should we Connect to the Deforumation websocket server to write the current resume frame properties?
        mediator_setValue("total_recall_relive", frame_idx)
        mediator_setValue("should_resume", 0)        
        print("DEFORUM, SETTING OUTDIR:"+args.outdir)
        mediator_setValue("frame_outdir", args.outdir)
        print("DEFORUM, SETTING RESUME OR TIME-STRING:"+str(root.timestring))
        mediator_setValue("resume_timestring", root.timestring)  

        #Should we use parseq? (use_deforumation_cadence_scheduling = parseq should be used)
        if int(mediator_getValue("use_deforumation_cadence_scheduling").strip().strip('\n')) == 1:
            use_deforumation_cadence_scheduling = 1
            deforumation_cadence_scheduling_manifest = str(mediator_getValue("deforumation_cadence_scheduling_manifest").strip().strip('\n'))
            print("Deforumation cadence scheduling will be used:\n"
                  "---------------------------------------------\n"
                  + str(deforumation_cadence_scheduling_manifest) + "\n")
            turbo_steps = get_now_cadence(frame_idx)
            print("Starting on frame:"+str(frame_idx)+", cadence:"+str(turbo_steps)+", should be used.")

    previous_turbo_steps = turbo_steps #usingDeforumation

    # reset the mask vals as they are overwritten in the compose_mask algorithm
    mask_vals = {}
    noise_mask_vals = {}

    mask_vals['everywhere'] = Image.new('1', (args.W, args.H), 1)
    noise_mask_vals['everywhere'] = Image.new('1', (args.W, args.H), 1)

    mask_image = None

    if args.use_init and args.init_image != None and args.init_image != '':
        _, mask_image = load_img(args.init_image,
                                 shape=(args.W, args.H),
                                 use_alpha_as_mask=args.use_alpha_as_mask)
        mask_vals['video_mask'] = mask_image
        noise_mask_vals['video_mask'] = mask_image

    # Grab the first frame masks since they wont be provided until next frame
    # Video mask overrides the init image mask, also, won't be searching for init_mask if use_mask_video is set
    # Made to solve https://github.com/deforum-art/deforum-for-automatic1111-webui/issues/386
    if anim_args.use_mask_video:
        args.mask_file = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)
        root.noise_mask = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)

        mask_vals['video_mask'] = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)
        noise_mask_vals['video_mask'] = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)
    elif mask_image is None and args.use_mask:
        mask_vals['video_mask'] = get_mask(args)
        noise_mask_vals['video_mask'] = get_mask(args)  # TODO?: add a different default noisc mask

    # get color match for 'Image' color coherence only once, before loop
    if anim_args.color_coherence == 'Image':
        color_match_sample = load_image(anim_args.color_coherence_image_path)
        color_match_sample = color_match_sample.resize((args.W, args.H), PIL.Image.LANCZOS)
        color_match_sample = cv2.cvtColor(np.array(color_match_sample), cv2.COLOR_RGB2BGR)

    # Webui
    state.job_count = anim_args.max_frames
    last_preview_frame = 0

    while frame_idx < anim_args.max_frames:
        state.job = f"frame {frame_idx + 1}/{anim_args.max_frames}"
        state.job_no = frame_idx + 1

        if state.skipped:
            print("\n** PAUSED **")
            state.skipped = False
            while not state.skipped:
                time.sleep(0.1)
            print("** RESUMING **")
        if usingDeforumation: #Should we Connect to the Deforumation websocket server and get is_paused_rendering?
            ispaused = 0
            while int(mediator_getValue("is_paused_rendering").strip().strip('\n')) == 1:
                if ispaused == 0:
                    print("\n** PAUSED **")
                    ispaused = 1
                time.sleep(0.5)
            if ispaused:
                print("** RESUMING **")
                start_frame = int(mediator_getValue("start_frame").strip().strip('\n'))
                if int(mediator_getValue("should_use_total_recall").strip().strip('\n')):
                    mediator_setValue("total_recall_relive", start_frame)


            if int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
            # resume animation (requires at least two frames - see function)
            # determine last frame and frame to start on
            # get last frame from frame count corrected for any trailing cadence frames
            should_use_deforumation_cadence_schedule = int(mediator_getValue("use_deforumation_cadence_scheduling").strip().strip('\n'))
            if using_vid_init:
                turbo_steps = 1

            elif should_use_deforumation_cadence_schedule and use_deforumation_cadence_scheduling == 0:
                use_deforumation_cadence_scheduling = 1
                deforumation_cadence_scheduling_manifest = str(mediator_getValue("deforumation_cadence_scheduling_manifest").strip().strip('\n'))
                print("Deforumation cadence scheduling was not used but will now be used!\n"
                      "------------------------------------------------------------------")
                turbo_steps = get_now_cadence(frame_idx)
                print("get_now_cadence() returned" + str(turbo_steps))
                if int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                    turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
            elif should_use_deforumation_cadence_schedule and use_deforumation_cadence_scheduling == 1:
                turbo_steps = get_now_cadence(frame_idx)
                print("Deforumation cadence scheduling conntineously used, cadence:" + str(turbo_steps))
            elif int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
                #print("Cadence value read from Deforumation:"+str(turbo_steps))
                mediator_setValue("deforum_cadence", turbo_steps)
            else:
                print("Cadence value read from Deforum:"+str(turbo_steps))
                turbo_steps = int(anim_args.diffusion_cadence)
                mediator_setValue("deforum_cadence", turbo_steps)
                mediator_setValue("cadence", turbo_steps)

            shouldResume = int(mediator_getValue("should_resume").strip().strip('\n'))  #should_resume should be set when third party chooses another frame (rewinding forward, etc), it doesn't need to happen in paused mode       
            if (previous_turbo_steps != turbo_steps) or (shouldResume == 1):
                #print("frame_idx is:"+str(frame_idx))
                #print("previous_turbo_steps is:"+str(previous_turbo_steps))
                #print("turbo_steps is:"+str(turbo_steps))
                #print("That would oldly have taken us to:"+str(frame_idx - previous_turbo_steps - (frame_idx%turbo_steps)))
                #print("But staying on:"+str(frame_idx))

                if shouldResume == 1: #If shouldResume == 1, then third party has choosen to jump to a non continues frame
                    #print("Gott the start_frame:"+str(start_frame))
                    #print("Was at frame:"+str(frame_idx))
                    mediator_setValue("should_resume", 0)

                start_frame = int(mediator_getValue("start_frame").strip().strip('\n'))

                if frame_idx != start_frame or previous_turbo_steps != turbo_steps:
                    frame_idx = start_frame  #- (start_frame%turbo_steps)
                    previous_turbo_steps = turbo_steps

                    #if (previous_turbo_steps != turbo_steps)
                    #    frame_idx = turbo_next_frame_idx - previous_turbo_steps + turbo_steps

                    #frame_idx = frame_idx - previous_turbo_steps #Undo the last render         
                    #frame_idx = frame_idx - previous_turbo_steps - (frame_idx%turbo_steps)
                    #frame_idx = frame_idx - (frame_idx%turbo_steps)
                    #print("frame_idx is:"+str(frame_idx))
                    #print("previous_turbo_steps is:"+str(previous_turbo_steps))
                    #print("turbo_steps is:"+str(turbo_steps))
                    #print("That would oldly have taken us to:"+str(frame_idx - previous_turbo_steps - (frame_idx%turbo_steps)))
                    #frame_idx = turbo_next_frame_idx - previous_turbo_steps + turbo_steps
                    #print("But staying on:"+str(frame_idx))


                    prev_frame, next_frame, prev_img, next_img = get_resume_vars_d(
                        folder=args.outdir,
                        timestring=root.timestring,
                        cadence=turbo_steps,
                        startframe=frame_idx
                    )
                    # set up turbo step vars
                    if turbo_steps > 1:
                        turbo_prev_image, turbo_prev_frame_idx = prev_img, prev_frame
                        turbo_next_image, turbo_next_frame_idx = next_img, next_frame
                    # advance start_frame to next frame
                    if prev_img is None:
                        root.init_sample = None
                        root.initial_info = None
                        root.first_frame = None
                        start_frame = 0
                        frame_idx = 0
                        print("Trying to close StableDiffusionProcessingImg2Img")
                        p = StableDiffusionProcessingImg2Img(sd_model=sd_model,outpath_samples = opts.outdir_samples or opts.outdir_img2img_samples, )
                        p.close()

                    mediator_setValue("total_recall_relive", frame_idx)
                    args.seed = int(mediator_getValue("seed").strip().strip('\n'))

                    state.job_count = anim_args.max_frames
                    last_preview_frame = frame_idx                
                    state.job = f"frame {frame_idx + 1}/{anim_args.max_frames}"
                    state.job_no = frame_idx + 1

            mediator_setValue("deforum_cadence", turbo_steps)
            previous_turbo_steps = turbo_steps #usingDeforumation
            #print("previous_turbo_steps:"+str(previous_turbo_steps))
            #print("turbo_steps:" + str(turbo_steps))
            #print("turbo_prev_frame_idx:" + str(turbo_prev_frame_idx))
            #print("turbo_next_frame_idx:" + str(turbo_next_frame_idx))
            #print("start_frame:" + str(start_frame))
            #print("frame_idx:" + str(frame_idx))

            #else:
            #    donothing = 0

        print(f"\033[36mAnimation frame: \033[0m{frame_idx}/{anim_args.max_frames}  ")

        noise = keys.noise_schedule_series[frame_idx]
        if usingDeforumation: #Should we Connect to the Deforumation websocket server and get seed_changed == new seed?
            if int(mediator_getValue("seed_changed").strip().strip('\n')):
                print("Seed has been changed!")
                args.seed = int(mediator_getValue("seed").strip().strip('\n'))
                mediator_setValue("seed_changed", 0)
                if args.seed == -1:
                    args.seed = random.randint(0, 2**32 - 1)
                print("To:"+str(args.seed))
        if usingDeforumation:
            if (int(mediator_getValue("should_use_deforumation_strength").strip().strip('\n')) == 1):
                strength = float(mediator_getValue("strength").strip().strip('\n'))
                mediator_setValue("deforum_strength", strength)
            else:
                strength = keys.strength_schedule_series[frame_idx]    
                mediator_setValue("deforum_strength", strength)
                mediator_setValue("strength", strength)
        else:
            strength = keys.strength_schedule_series[frame_idx]
        if usingDeforumation:
            if (int(mediator_getValue("should_use_deforumation_cfg").strip().strip('\n')) == 1):
                scale = float(mediator_getValue("cfg").strip().strip('\n'))
                mediator_setValue("deforum_cfg", scale)
            else:
                scale = keys.cfg_scale_schedule_series[frame_idx]
                mediator_setValue("deforum_cfg", scale)
                mediator_setValue("cfg", scale)
        else: #if usingDeforumation == False or connectedToServer == False: #If we are not using Deforumation, go with the values in Deforum GUI (or if we can't connect to the Deforumation server).
            scale = keys.cfg_scale_schedule_series[frame_idx]

        contrast = keys.contrast_schedule_series[frame_idx]
        kernel = int(keys.kernel_schedule_series[frame_idx])
        sigma = keys.sigma_schedule_series[frame_idx]
        amount = keys.amount_schedule_series[frame_idx]
        threshold = keys.threshold_schedule_series[frame_idx]
        cadence_flow_factor = keys.cadence_flow_factor_schedule_series[frame_idx]
        redo_flow_factor = keys.redo_flow_factor_schedule_series[frame_idx]
        hybrid_comp_schedules = {
            "alpha": keys.hybrid_comp_alpha_schedule_series[frame_idx],
            "mask_blend_alpha": keys.hybrid_comp_mask_blend_alpha_schedule_series[frame_idx],
            "mask_contrast": keys.hybrid_comp_mask_contrast_schedule_series[frame_idx],
            "mask_auto_contrast_cutoff_low": int(keys.hybrid_comp_mask_auto_contrast_cutoff_low_schedule_series[frame_idx]),
            "mask_auto_contrast_cutoff_high": int(keys.hybrid_comp_mask_auto_contrast_cutoff_high_schedule_series[frame_idx]),
            "flow_factor": keys.hybrid_flow_factor_schedule_series[frame_idx]
        }
        scheduled_sampler_name = None
        scheduled_clipskip = None
        scheduled_noise_multiplier = None
        scheduled_ddim_eta = None
        scheduled_ancestral_eta = None

        mask_seq = None
        noise_mask_seq = None

        if usingDeforumation: #Should we Connect to the Deforumation websocket server to get CFG values?
            args.steps = int(mediator_getValue("steps").strip().strip('\n'))
            mediator_setValue("deforum_steps", args.steps)      
        else: #If we are not using Deforumation, go with the values in Deforum GUI (or if we can't connect to the Deforumation server).
            if anim_args.enable_steps_scheduling and keys.steps_schedule_series[frame_idx] is not None:
                args.steps = int(keys.steps_schedule_series[frame_idx])
                mediator_setValue("deforum_steps", args.steps)      
                mediator_setValue("steps", args.steps)      
        if anim_args.enable_sampler_scheduling and keys.sampler_schedule_series[frame_idx] is not None:
            scheduled_sampler_name = keys.sampler_schedule_series[frame_idx].casefold()
        if anim_args.enable_clipskip_scheduling and keys.clipskip_schedule_series[frame_idx] is not None:
            scheduled_clipskip = int(keys.clipskip_schedule_series[frame_idx])

        if usingDeforumation:
            if int(mediator_getValue("should_use_deforumation_noise").strip().strip('\n')) == 1:
                scheduled_noise_multiplier = float(mediator_getValue("noise_multiplier").strip().strip('\n'))
                mediator_setValue("deforum_noise_multiplier", scheduled_noise_multiplier)
            else:
                if anim_args.enable_noise_multiplier_scheduling and keys.noise_multiplier_schedule_series[frame_idx] is not None:
                    scheduled_noise_multiplier = float(keys.noise_multiplier_schedule_series[frame_idx])
                    mediator_setValue("deforum_noise_multiplier", scheduled_noise_multiplier)
                    mediator_setValue("noise_multiplier", scheduled_noise_multiplier)
        elif anim_args.enable_noise_multiplier_scheduling and keys.noise_multiplier_schedule_series[frame_idx] is not None:
                scheduled_noise_multiplier = float(keys.noise_multiplier_schedule_series[frame_idx])



        if anim_args.enable_ddim_eta_scheduling and keys.ddim_eta_schedule_series[frame_idx] is not None:
            scheduled_ddim_eta = float(keys.ddim_eta_schedule_series[frame_idx])
        if anim_args.enable_ancestral_eta_scheduling and keys.ancestral_eta_schedule_series[frame_idx] is not None:
            scheduled_ancestral_eta = float(keys.ancestral_eta_schedule_series[frame_idx])
        if args.use_mask and keys.mask_schedule_series[frame_idx] is not None:
            mask_seq = keys.mask_schedule_series[frame_idx]
        if anim_args.use_noise_mask and keys.noise_mask_schedule_series[frame_idx] is not None:
            noise_mask_seq = keys.noise_mask_schedule_series[frame_idx]

        if args.use_mask and not anim_args.use_noise_mask:
            noise_mask_seq = mask_seq

        depth = None

        if anim_args.animation_mode == '3D' and (cmd_opts.lowvram or cmd_opts.medvram):
            # Unload the main checkpoint and load the depth model
            lowvram.send_everything_to_cpu()
            sd_hijack.model_hijack.undo_hijack(sd_model)
            devices.torch_gc()
            if predict_depths: depth_model.to(root.device)

        if turbo_steps == 1 and opts.data.get("deforum_save_gen_info_as_srt"):
            params_string = format_animation_params(keys, prompt_series, frame_idx)
            write_frame_subtitle(srt_filename, frame_idx, srt_frame_duration, f"F#: {frame_idx}; Cadence: false; Seed: {args.seed}; {params_string}")
            params_string = None



        if usingDeforumation: #Should we Connect to the Deforumation websocket server to get CFG values?
            should_use_deforumation_cadence_schedule = int(mediator_getValue("use_deforumation_cadence_scheduling").strip().strip('\n'))
            if using_vid_init:
                turbo_steps = 1

            elif should_use_deforumation_cadence_schedule and use_deforumation_cadence_scheduling == 0:
                use_deforumation_cadence_scheduling = 1
                deforumation_cadence_scheduling_manifest = str(mediator_getValue("deforumation_cadence_scheduling_manifest").strip().strip('\n'))
                print("Deforumation cadence scheduling was not used but will now be used!\n"
                      "------------------------------------------------------------------")
                turbo_steps = get_now_cadence(frame_idx)
                print("get_now_cadence() returned" + str(turbo_steps))
                if int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                    turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
            elif should_use_deforumation_cadence_schedule and use_deforumation_cadence_scheduling == 1:
                turbo_steps = get_now_cadence(frame_idx)
                print("Deforumation cadence scheduling conntineously used, cadence:" + str(turbo_steps))
            elif int(mediator_getValue("should_use_deforumation_cadence").strip().strip('\n')) == 1:
                turbo_steps = int(mediator_getValue("cadence").strip().strip('\n'))
                #print("Cadence value read from Deforumation:"+str(turbo_steps))
                mediator_setValue("deforum_cadence", turbo_steps)
            else:
                #print("Cadence value read from Deforum:"+str(turbo_steps))
                turbo_steps = int(anim_args.diffusion_cadence)
                mediator_setValue("deforum_cadence", turbo_steps)
                mediator_setValue("cadence", turbo_steps)


            if previous_turbo_steps != turbo_steps:
                #print("frame_idX is:"+str(frame_idx))
                #print("previous_turbo_steps is:"+str(previous_turbo_steps))
                #print("turbo_steps is:"+str(turbo_steps))
                #print("That would oldly have taken us to:"+str(frame_idx - previous_turbo_steps - (frame_idx%turbo_steps)))
                frame_idx = turbo_next_frame_idx - previous_turbo_steps + turbo_steps
                #print("But staying on:"+str(frame_idx))

                prev_frame, next_frame, prev_img, next_img = get_resume_vars_d(
                    folder=args.outdir,
                    timestring=root.timestring,
                    cadence=turbo_steps,
                    startframe=frame_idx
                )
                # set up turbo step vars
                if turbo_steps > 1:
                    turbo_prev_image, turbo_prev_frame_idx = prev_img, prev_frame
                    turbo_next_image, turbo_next_frame_idx = next_img, next_frame
                # advance start_frame to next frame
                if prev_img is None:
                    root.init_sample = None
                    root.initial_info = None
                    root.first_frame = None
                start_frame = 0

                mediator_setValue("total_recall_relive", frame_idx)
                args.seed = int(mediator_getValue("seed").strip().strip('\n'))
                state.job_count = anim_args.max_frames

                state.job_count = anim_args.max_frames
                last_preview_frame = frame_idx                
                state.job = f"frame {frame_idx + 1}/{anim_args.max_frames}"
                state.job_no = frame_idx + 1
            #else:
            #    print("****************** Warning: You are using total recall, and therefore no forced Rewind to match Cadence will be done! ******************")
            #    print("previous_turbo_steps was:"+str(previous_turbo_steps))
            #    print("and now turbo_steps:"+str(turbo_steps))


            mediator_setValue("deforum_cadence", turbo_steps)
            previous_turbo_steps = turbo_steps #usingDeforumation
            #print("previous_turbo_steps:"+str(previous_turbo_steps))


        if turbo_steps > 1:
            tween_frame_start_idx = max(start_frame, frame_idx - turbo_steps) #Maybe need to fix .png image #usingDeforumation
            cadence_flow = None
            if frame_idx < 0:
                print("frame_idx pushed into negative, so adjusting frame_idx to 0.")
                frame_idx = 0
                tween_frame_start_idx = 0

            if usingDeforumation:
                should_use_optical_flow = int(mediator_getValue("should_use_optical_flow").strip().strip('\n'))
                if should_use_optical_flow != 1:
                    anim_args.optical_flow_cadence = "None"
                    anim_args.optical_flow_redo_generation = "None"
                    print("Disabling optical flow")
                else:
                    anim_args.optical_flow_cadence = original_optical_flow_cadence
                    anim_args.optical_flow_redo_generation = original_optical_flow_redo_generation

                    cadence_flow_factor = int(mediator_getValue("cadence_flow_factor").strip().strip('\n'))
                    redo_flow_factor = int(mediator_getValue("generation_flow_factor").strip().strip('\n'))
                    print("Enabling optical flow")

            for tween_frame_idx in range(tween_frame_start_idx, frame_idx):
                #If controlnet is being used, get the values from Deforumation
                if usingDeforumation:
                    mediator_setValue("total_recall_relive", frame_idx)
                    if is_controlnet_enabled(controlnet_args):
                        for cnIndex in range(5):
                            currCnIndex = cnIndex+1
                            cn_udcn = int(mediator_getValue("cn_udcn"+str(cnIndex+1)).strip().strip('\n'))
                            if cn_udcn == 1:
                                setattr(controlnet_args, f'cn_{currCnIndex}_weight', "0:(" + str(mediator_getValue("cn_weight"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                                #print(str(getattr(controlnet_args, f'cn_{currCnIndex}_weight')))
                                setattr(controlnet_args, f'cn_{currCnIndex}_guidance_start', "0:(" + str(mediator_getValue("cn_stepstart"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                                #print(str(getattr(controlnet_args, f'cn_{currCnIndex}_guidance_start')))
                                setattr(controlnet_args, f'cn_{currCnIndex}_guidance_end', "0:(" + str(mediator_getValue("cn_stepend"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                                #print(str(getattr(controlnet_args, f'cn_{currCnIndex}_guidance_end')))
                                setattr(controlnet_args, f'cn_{currCnIndex}_threshold_a', int(mediator_getValue("cn_lowt"+str(cnIndex+1)).strip().strip('\n')))
                                #print(str(getattr(controlnet_args, f'cn_{currCnIndex}_threshold_a')))
                                setattr(controlnet_args, f'cn_{currCnIndex}_threshold_b', int(mediator_getValue("cn_hight"+str(cnIndex+1)).strip().strip('\n')))
                                #print(str(getattr(controlnet_args, f'cn_{currCnIndex}_threshold_b')))
                            else:
                                setattr(controlnet_args, f'cn_{currCnIndex}_weight', cnu[f'cn_{currCnIndex}_weight'])
                                setattr(controlnet_args, f'cn_{currCnIndex}_guidance_start', cnu[f'cn_{currCnIndex}_guidance_start'])
                                setattr(controlnet_args, f'cn_{currCnIndex}_guidance_end', cnu[f'cn_{currCnIndex}_guidance_end'])
                                setattr(controlnet_args, f'cn_{currCnIndex}_threshold_a', cnu[f'cn_{currCnIndex}_threshold_a'])
                                setattr(controlnet_args, f'cn_{currCnIndex}_threshold_b', cnu[f'cn_{currCnIndex}_threshold_b'])
                                mediator_setValue("cn_weight"+str(cnIndex+1), getattr(CnSchKeys, f"cn_{currCnIndex}_weight_schedule_series")[frame_idx])
                                mediator_setValue("cn_stepstart"+str(cnIndex+1),getattr(CnSchKeys, f"cn_{currCnIndex}_guidance_start_schedule_series")[frame_idx])
                                mediator_setValue("cn_stepend"+str(cnIndex+1), getattr(CnSchKeys, f"cn_{currCnIndex}_guidance_end_schedule_series")[frame_idx])
                                mediator_setValue("cn_lowt"+str(cnIndex+1), getattr(controlnet_args, f"cn_{currCnIndex}_threshold_a"))
                                mediator_setValue("cn_hight"+str(cnIndex+1), getattr(controlnet_args, f"cn_{currCnIndex}_threshold_b"))



                #print("!Inside tween for loop!")
                # update progress during cadence
                state.job = f"frame {tween_frame_idx + 1}/{anim_args.max_frames}"
                state.job_no = tween_frame_idx + 1
                # cadence vars
                tween = float(tween_frame_idx - tween_frame_start_idx + 1) / float(frame_idx - tween_frame_start_idx)
                advance_prev = turbo_prev_image is not None and tween_frame_idx > turbo_prev_frame_idx
                advance_next = tween_frame_idx > turbo_next_frame_idx

                # optical flow cadence setup before animation warping
                if anim_args.animation_mode in ['2D', '3D'] and anim_args.optical_flow_cadence != 'None':
                    if keys.strength_schedule_series[tween_frame_start_idx] > 0:
                        if cadence_flow is None and turbo_prev_image is not None and turbo_next_image is not None:
                            cadence_flow = get_flow_from_images(turbo_prev_image, turbo_next_image, anim_args.optical_flow_cadence, raft_model) / 2
                            print("Creating: turbo_next_image")
                            turbo_next_image = image_transform_optical_flow(turbo_next_image, -cadence_flow, 1)

                if opts.data.get("deforum_save_gen_info_as_srt"):
                    params_string = format_animation_params(keys, prompt_series, tween_frame_idx)
                    write_frame_subtitle(srt_filename, tween_frame_idx, srt_frame_duration, f"F#: {tween_frame_idx}; Cadence: {tween < 1.0}; Seed: {args.seed}; {params_string}")
                    params_string = None

                print(f"Creating in-between {'' if cadence_flow is None else anim_args.optical_flow_cadence + ' optical flow '}cadence frame: {tween_frame_idx}; tween:{tween:0.2f};")

                if depth_model is not None:
                    assert (turbo_next_image is not None)
                    depth = depth_model.predict(turbo_next_image, anim_args.midas_weight, root.half_precision)

                if advance_prev:
                    turbo_prev_image, _ = anim_frame_warp(turbo_prev_image, args, anim_args, keys, tween_frame_idx, depth_model, depth=depth, device=root.device, half_precision=root.half_precision)
                if advance_next:
                    turbo_next_image, _ = anim_frame_warp(turbo_next_image, args, anim_args, keys, tween_frame_idx, depth_model, depth=depth, device=root.device, half_precision=root.half_precision)

                # hybrid video motion - warps turbo_prev_image or turbo_next_image to match motion
                if tween_frame_idx > 0:
                    if anim_args.hybrid_motion in ['Affine', 'Perspective']:
                        if anim_args.hybrid_motion_use_prev_img:
                            matrix = get_matrix_for_hybrid_motion_prev(tween_frame_idx - 1, (args.W, args.H), inputfiles, prev_img, anim_args.hybrid_motion)
                            if advance_prev:
                                turbo_prev_image = image_transform_ransac(turbo_prev_image, matrix, anim_args.hybrid_motion)
                            if advance_next:
                                turbo_next_image = image_transform_ransac(turbo_next_image, matrix, anim_args.hybrid_motion)
                        else:
                            matrix = get_matrix_for_hybrid_motion(tween_frame_idx - 1, (args.W, args.H), inputfiles, anim_args.hybrid_motion)
                            if advance_prev:
                                turbo_prev_image = image_transform_ransac(turbo_prev_image, matrix, anim_args.hybrid_motion)
                            if advance_next:
                                turbo_next_image = image_transform_ransac(turbo_next_image, matrix, anim_args.hybrid_motion)
                    if anim_args.hybrid_motion in ['Optical Flow']:
                        if anim_args.hybrid_motion_use_prev_img:
                            flow = get_flow_for_hybrid_motion_prev(tween_frame_idx - 1, (args.W, args.H), inputfiles, hybrid_frame_path, prev_flow, prev_img, anim_args.hybrid_flow_method, raft_model,
                                                                   anim_args.hybrid_flow_consistency, anim_args.hybrid_consistency_blur, anim_args.hybrid_comp_save_extra_frames)
                            if advance_prev:
                                turbo_prev_image = image_transform_optical_flow(turbo_prev_image, flow, hybrid_comp_schedules['flow_factor'])
                            if advance_next:
                                turbo_next_image = image_transform_optical_flow(turbo_next_image, flow, hybrid_comp_schedules['flow_factor'])
                            prev_flow = flow
                        else:
                            flow = get_flow_for_hybrid_motion(tween_frame_idx - 1, (args.W, args.H), inputfiles, hybrid_frame_path, prev_flow, anim_args.hybrid_flow_method, raft_model,
                                                              anim_args.hybrid_flow_consistency, anim_args.hybrid_consistency_blur, anim_args.hybrid_comp_save_extra_frames)
                            if advance_prev:
                                turbo_prev_image = image_transform_optical_flow(turbo_prev_image, flow, hybrid_comp_schedules['flow_factor'])
                            if advance_next:
                                turbo_next_image = image_transform_optical_flow(turbo_next_image, flow, hybrid_comp_schedules['flow_factor'])
                            prev_flow = flow

                # do optical flow cadence after animation warping
                if cadence_flow is not None:
                    print("Cadence flow exists")
                    cadence_flow = abs_flow_to_rel_flow(cadence_flow, args.W, args.H)
                    cadence_flow, _ = anim_frame_warp(cadence_flow, args, anim_args, keys, tween_frame_idx, depth_model, depth=depth, device=root.device, half_precision=root.half_precision)
                    cadence_flow_inc = rel_flow_to_abs_flow(cadence_flow, args.W, args.H) * tween
                    if advance_prev:
                        turbo_prev_image = image_transform_optical_flow(turbo_prev_image, cadence_flow_inc, cadence_flow_factor)
                    if advance_next:
                        turbo_next_image = image_transform_optical_flow(turbo_next_image, cadence_flow_inc, cadence_flow_factor)

                turbo_prev_frame_idx = turbo_next_frame_idx = tween_frame_idx
                if turbo_prev_image is not None and tween < 1.0:
                    img = turbo_prev_image * (1.0 - tween) + turbo_next_image * tween
                else:
                    img = turbo_next_image

                # intercept and override to grayscale
                if anim_args.color_force_grayscale:
                    img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY)
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                    # overlay mask
                if args.overlay_mask and (anim_args.use_mask_video or args.use_mask):
                    img = do_overlay_mask(args, anim_args, img, tween_frame_idx, True)

                # get prev_img during cadence
                prev_img = img

                # current image update for cadence frames (left commented because it doesn't currently update the preview)
                # state.current_image = Image.fromarray(cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2RGB))

                # saving cadence frames
                filename = f"{root.timestring}_{tween_frame_idx:09}.png"
                cv2.imwrite(os.path.join(args.outdir, filename), img)
                if usingDeforumation: #Should we Connect to the Deforumation websocket server to tell 3:d parties what frame we are on currently?
                    shouldResume = int(mediator_getValue("should_resume").strip().strip('\n'))  #If the user pushed "Set current image" in Deforumation, we can't just overwrite the new start_frame  
                    if not shouldResume:
                        mediator_setValue("start_frame", tween_frame_idx)
                    mediator_setValue("saved_frame_params", tween_frame_idx)                     

                if anim_args.save_depth_maps:
                    depth_model.save(os.path.join(args.outdir, f"{root.timestring}_depth_{tween_frame_idx:09}.png"), depth)

        # get color match for video outside of prev_img conditional
        hybrid_available = anim_args.hybrid_composite != 'None' or anim_args.hybrid_motion in ['Optical Flow', 'Affine', 'Perspective']
        if anim_args.color_coherence == 'Video Input' and hybrid_available:
            if int(frame_idx) % int(anim_args.color_coherence_video_every_N_frames) == 0:
                prev_vid_img = Image.open(os.path.join(args.outdir, 'inputframes', get_frame_name(anim_args.video_init_path) + f"{frame_idx:09}.jpg"))
                prev_vid_img = prev_vid_img.resize((args.W, args.H), PIL.Image.LANCZOS)
                color_match_sample = np.asarray(prev_vid_img)
                color_match_sample = cv2.cvtColor(color_match_sample, cv2.COLOR_RGB2BGR)

        # after 1st frame, prev_img exists
        if prev_img is not None:
            # apply transforms to previous frame
            prev_img, depth = anim_frame_warp(prev_img, args, anim_args, keys, frame_idx, depth_model, depth=None, device=root.device, half_precision=root.half_precision)

            # do hybrid compositing before motion
            if anim_args.hybrid_composite == 'Before Motion':
                args, prev_img = hybrid_composite(args, anim_args, frame_idx, prev_img, depth_model, hybrid_comp_schedules, root)

            # hybrid video motion - warps prev_img to match motion, usually to prepare for compositing
            if anim_args.hybrid_motion in ['Affine', 'Perspective']:
                if anim_args.hybrid_motion_use_prev_img:
                    matrix = get_matrix_for_hybrid_motion_prev(frame_idx - 1, (args.W, args.H), inputfiles, prev_img, anim_args.hybrid_motion)
                else:
                    matrix = get_matrix_for_hybrid_motion(frame_idx - 1, (args.W, args.H), inputfiles, anim_args.hybrid_motion)
                prev_img = image_transform_ransac(prev_img, matrix, anim_args.hybrid_motion)
            if anim_args.hybrid_motion in ['Optical Flow']:
                if anim_args.hybrid_motion_use_prev_img:
                    flow = get_flow_for_hybrid_motion_prev(frame_idx - 1, (args.W, args.H), inputfiles, hybrid_frame_path, prev_flow, prev_img, anim_args.hybrid_flow_method, raft_model,
                                                           anim_args.hybrid_flow_consistency, anim_args.hybrid_consistency_blur, anim_args.hybrid_comp_save_extra_frames)
                else:
                    flow = get_flow_for_hybrid_motion(frame_idx - 1, (args.W, args.H), inputfiles, hybrid_frame_path, prev_flow, anim_args.hybrid_flow_method, raft_model,
                                                      anim_args.hybrid_flow_consistency, anim_args.hybrid_consistency_blur, anim_args.hybrid_comp_save_extra_frames)
                prev_img = image_transform_optical_flow(prev_img, flow, hybrid_comp_schedules['flow_factor'])
                prev_flow = flow

            # do hybrid compositing after motion (normal)
            if anim_args.hybrid_composite == 'Normal':
                args, prev_img = hybrid_composite(args, anim_args, frame_idx, prev_img, depth_model, hybrid_comp_schedules, root)

            # apply color matching
            if anim_args.color_coherence != 'None':
                if color_match_sample is None:
                    color_match_sample = prev_img.copy()
                else:
                    prev_img = maintain_colors(prev_img, color_match_sample, anim_args.color_coherence)

            # intercept and override to grayscale
            if anim_args.color_force_grayscale:
                prev_img = cv2.cvtColor(prev_img, cv2.COLOR_BGR2GRAY)
                prev_img = cv2.cvtColor(prev_img, cv2.COLOR_GRAY2BGR)

            # apply scaling
            contrast_image = (prev_img * contrast).round().astype(np.uint8)
            # anti-blur
            if amount > 0:
                contrast_image = unsharp_mask(contrast_image, (kernel, kernel), sigma, amount, threshold, mask_image if args.use_mask else None)
            # apply frame noising
            if args.use_mask or anim_args.use_noise_mask:
                root.noise_mask = compose_mask_with_check(root, args, noise_mask_seq, noise_mask_vals, Image.fromarray(cv2.cvtColor(contrast_image, cv2.COLOR_BGR2RGB)))

            if usingDeforumation: #Should we Connect to the Deforumation websocket server to get CFG values?
                if int(mediator_getValue("should_use_deforumation_noise").strip().strip('\n')) == 1:
                    deforumation_perlin_octaves = int(mediator_getValue("perlin_octaves").strip().strip('\n'))
                    deforumation_perlin_persistence = float(mediator_getValue("perlin_persistence").strip().strip('\n'))
                    noised_image = add_noise(contrast_image, noise, args.seed, anim_args.noise_type,
                                             (anim_args.perlin_w, anim_args.perlin_h, deforumation_perlin_octaves, deforumation_perlin_persistence),
                                             root.noise_mask, args.invert_mask)
                    mediator_setValue("deforum_perlin_octaves", deforumation_perlin_octaves)
                    mediator_setValue("deforum_perlin_persistence", deforumation_perlin_persistence)

                else:
                    noised_image = add_noise(contrast_image, noise, args.seed, anim_args.noise_type,
                                             (anim_args.perlin_w, anim_args.perlin_h, anim_args.perlin_octaves, anim_args.perlin_persistence),
                                             root.noise_mask, args.invert_mask)
                    mediator_setValue("deforum_perlin_octaves", anim_args.perlin_octaves)
                    mediator_setValue("deforum_perlin_persistence", anim_args.perlin_persistence)
                    mediator_setValue("perlin_octaves", anim_args.perlin_octaves)
                    mediator_setValue("perlin_persistence", anim_args.perlin_persistence)
            else:
                noised_image = add_noise(contrast_image, noise, args.seed, anim_args.noise_type,
                                         (anim_args.perlin_w, anim_args.perlin_h, anim_args.perlin_octaves, anim_args.perlin_persistence),
                                         root.noise_mask, args.invert_mask)


            # use transformed previous frame as init for current
            args.use_init = True
            root.init_sample = Image.fromarray(cv2.cvtColor(noised_image, cv2.COLOR_BGR2RGB))
            args.strength = max(0.0, min(1.0, strength))

        args.scale = scale

        # Pix2Pix Image CFG Scale - does *nothing* with non pix2pix checkpoints
        args.pix2pix_img_cfg_scale = float(keys.pix2pix_img_cfg_scale_series[frame_idx])

        # grab prompt for current frame
        if usingDeforumation: #Should we Connect to the Deforumation websocket server to get CFG values?
            if (int(mediator_getValue("should_use_deforumation_prompt_scheduling").strip().strip('\n')) == 1): #Should we use manual or deforum's strength scheduling?
                deforumation_positive_prompt = str(mediator_getValue("positive_prompt"))
                deforumation_negative_prompt = str(mediator_getValue("negative_prompt"))
                args.prompt = deforumation_positive_prompt + "--neg "+ deforumation_negative_prompt
            else:
                args.prompt = prompt_series[frame_idx]
                pos_prompt, neg_prompt = args.prompt.strip().split("--neg")
                mediator_setValue("positive_prompt", pos_prompt)
                mediator_setValue("negative_prompt", neg_prompt)

        else: #If we are not using Deforumation, go with the values in Deforum GUI (or if we can't connect to the Deforumation server).
            args.prompt = prompt_series[frame_idx]

        #if args.seed_behavior == 'schedule' or use_parseq:
        if args.seed_behavior == 'schedule' or parseq_adapter.manages_seed():            
            args.seed = int(keys.seed_schedule_series[frame_idx])

        if anim_args.enable_checkpoint_scheduling:
            args.checkpoint = keys.checkpoint_schedule_series[frame_idx]
        else:
            args.checkpoint = None

        # SubSeed scheduling
        if anim_args.enable_subseed_scheduling:
            root.subseed = int(keys.subseed_schedule_series[frame_idx])
            root.subseed_strength = float(keys.subseed_strength_schedule_series[frame_idx])

        #if use_parseq:
        if parseq_adapter.manages_seed():
            anim_args.enable_subseed_scheduling = True
            root.subseed = int(keys.subseed_schedule_series[frame_idx])
            root.subseed_strength = keys.subseed_strength_schedule_series[frame_idx]

        # set value back into the prompt - prepare and report prompt and seed
        args.prompt = prepare_prompt(args.prompt, anim_args.max_frames, args.seed, frame_idx)

        # grab init image for current frame
        if using_vid_init:
            init_frame = get_next_frame(args.outdir, anim_args.video_init_path, frame_idx, False)
            print(f"Using video init frame {init_frame}")
            args.init_image = init_frame
            args.strength = max(0.0, min(1.0, strength))
        if anim_args.use_mask_video:
            args.mask_file = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)
            root.noise_mask = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)

            mask_vals['video_mask'] = get_mask_from_file(get_next_frame(args.outdir, anim_args.video_mask_path, frame_idx, True), args)

        if args.use_mask:
            args.mask_image = compose_mask_with_check(root, args, mask_seq, mask_vals, root.init_sample) if root.init_sample is not None else None  # we need it only after the first frame anyway

        # setting up some arguments for the looper
        loop_args.imageStrength = loopSchedulesAndData.image_strength_schedule_series[frame_idx]
        loop_args.blendFactorMax = loopSchedulesAndData.blendFactorMax_series[frame_idx]
        loop_args.blendFactorSlope = loopSchedulesAndData.blendFactorSlope_series[frame_idx]
        loop_args.tweeningFrameSchedule = loopSchedulesAndData.tweening_frames_schedule_series[frame_idx]
        loop_args.colorCorrectionFactor = loopSchedulesAndData.color_correction_factor_series[frame_idx]
        loop_args.use_looper = loopSchedulesAndData.use_looper
        loop_args.imagesToKeyframe = loopSchedulesAndData.imagesToKeyframe

        if 'img2img_fix_steps' in opts.data and opts.data["img2img_fix_steps"]:  # disable "with img2img do exactly x steps" from general setting, as it *ruins* deforum animations
            opts.data["img2img_fix_steps"] = False
        if scheduled_clipskip is not None:
            opts.data["CLIP_stop_at_last_layers"] = scheduled_clipskip
        if scheduled_noise_multiplier is not None:
            opts.data["initial_noise_multiplier"] = scheduled_noise_multiplier
        if scheduled_ddim_eta is not None:
            opts.data["eta_ddim"] = scheduled_ddim_eta
        if scheduled_ancestral_eta is not None:
            opts.data["eta_ancestral"] = scheduled_ancestral_eta

        if anim_args.animation_mode == '3D' and (cmd_opts.lowvram or cmd_opts.medvram):
            if predict_depths: depth_model.to('cpu')
            devices.torch_gc()
            lowvram.setup_for_low_vram(sd_model, cmd_opts.medvram)
            sd_hijack.model_hijack.hijack(sd_model)


        if usingDeforumation:
            mediator_setValue("total_recall_relive", frame_idx)
            if is_controlnet_enabled(controlnet_args):
                for cnIndex in range(5):
                    currCnIndex = cnIndex+1
                    cn_udcn = int(mediator_getValue("cn_udcn"+str(cnIndex+1)).strip().strip('\n'))
                    if cn_udcn == 1:
                        #print("ControlNet " + str(currCnIndex) + " should use Deforumation values.")
                        #print("Got weight from mediator:" + str(float(mediator_getValue("cn_weight"+str(cnIndex+1)))))
                        setattr(controlnet_args, f'cn_{currCnIndex}_weight', "0:(" + str(mediator_getValue("cn_weight"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_start', "0:(" + str(mediator_getValue("cn_stepstart"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_end', "0:(" + str(mediator_getValue("cn_stepend"+str(cnIndex+1)).strip().strip('\n')) + ")" )
                        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_a', int(mediator_getValue("cn_lowt"+str(cnIndex+1)).strip().strip('\n')))
                        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_b', int(mediator_getValue("cn_hight"+str(cnIndex+1)).strip().strip('\n')))
                    else:
                        setattr(controlnet_args, f'cn_{currCnIndex}_weight', cnu[f'cn_{currCnIndex}_weight'])
                        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_start', cnu[f'cn_{currCnIndex}_guidance_start'])
                        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_end', cnu[f'cn_{currCnIndex}_guidance_end'])
                        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_a', cnu[f'cn_{currCnIndex}_threshold_a'])
                        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_b', cnu[f'cn_{currCnIndex}_threshold_b'])
                        #print("ControlNet " + str(currCnIndex) + " should use Deforum values.")
                        #print("Got weight:" + str(getattr(CnSchKeys, f"cn_{currCnIndex}_weight_schedule_series")[frame_idx]))
                        mediator_setValue("cn_weight"+str(cnIndex+1), getattr(CnSchKeys, f"cn_{currCnIndex}_weight_schedule_series")[frame_idx])
                        mediator_setValue("cn_stepstart"+str(cnIndex+1),getattr(CnSchKeys, f"cn_{currCnIndex}_guidance_start_schedule_series")[frame_idx])
                        mediator_setValue("cn_stepend"+str(cnIndex+1), getattr(CnSchKeys, f"cn_{currCnIndex}_guidance_end_schedule_series")[frame_idx])
                        mediator_setValue("cn_lowt"+str(cnIndex+1), getattr(controlnet_args, f"cn_{currCnIndex}_threshold_a"))
                        mediator_setValue("cn_hight"+str(cnIndex+1), getattr(controlnet_args, f"cn_{currCnIndex}_threshold_b"))


        # optical flow redo before generation
        if anim_args.optical_flow_redo_generation != 'None' and prev_img is not None and strength > 0:
            print(f"Optical flow redo is diffusing and warping using {anim_args.optical_flow_redo_generation} optical flow before generation.")
            stored_seed = args.seed
            args.seed = random.randint(0, 2 ** 32 - 1)
            #disposable_image = generate(args, keys, anim_args, loop_args, controlnet_args, root, frame_idx, sampler_name=scheduled_sampler_name)
            disposable_image = generate(args, keys, anim_args, loop_args, controlnet_args, root, parseq_adapter, frame_idx, sampler_name=scheduled_sampler_name)
            if disposable_image != None:
                disposable_image = cv2.cvtColor(np.array(disposable_image), cv2.COLOR_RGB2BGR)
                disposable_flow = get_flow_from_images(prev_img, disposable_image, anim_args.optical_flow_redo_generation, raft_model)
                disposable_image = cv2.cvtColor(disposable_image, cv2.COLOR_BGR2RGB)
                disposable_image = image_transform_optical_flow(disposable_image, disposable_flow, redo_flow_factor)
                args.seed = stored_seed
                root.init_sample = Image.fromarray(disposable_image)
                del (disposable_image, disposable_flow, stored_seed)
                gc.collect()

        # diffusion redo
        if int(anim_args.diffusion_redo) > 0 and prev_img is not None and strength > 0:
            stored_seed = args.seed
            for n in range(0, int(anim_args.diffusion_redo)):
                print(f"Redo generation {n + 1} of {int(anim_args.diffusion_redo)} before final generation")
                args.seed = random.randint(0, 2 ** 32 - 1)
                #disposable_image = generate(args, keys, anim_args, loop_args, controlnet_args, root, frame_idx, sampler_name=scheduled_sampler_name)
                disposable_image = generate(args, keys, anim_args, loop_args, controlnet_args, root, parseq_adapter, frame_idx, sampler_name=scheduled_sampler_name)
                disposable_image = cv2.cvtColor(np.array(disposable_image), cv2.COLOR_RGB2BGR)
                # color match on last one only
                if n == int(anim_args.diffusion_redo):
                    disposable_image = maintain_colors(prev_img, color_match_sample, anim_args.color_coherence)
                args.seed = stored_seed
                root.init_sample = Image.fromarray(cv2.cvtColor(disposable_image, cv2.COLOR_BGR2RGB))
            del (disposable_image, stored_seed)
            gc.collect()

        # generation
        #image = generate(args, keys, anim_args, loop_args, controlnet_args, root, frame_idx, sampler_name=scheduled_sampler_name)
        
        image = generate(args, keys, anim_args, loop_args, controlnet_args, root, parseq_adapter, frame_idx, sampler_name=scheduled_sampler_name)
        #mediator_setValue("saved_frame_params", frame_idx)
        if image is None:
            break

        # do hybrid video after generation
        if frame_idx > 0 and anim_args.hybrid_composite == 'After Generation':
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            args, image = hybrid_composite(args, anim_args, frame_idx, image, depth_model, hybrid_comp_schedules, root)
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # color matching on first frame is after generation, color match was collected earlier, so we do an extra generation to avoid the corruption introduced by the color match of first output
        if frame_idx == 0 and (anim_args.color_coherence == 'Image' or (anim_args.color_coherence == 'Video Input' and hybrid_available)):
            image = maintain_colors(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), color_match_sample, anim_args.color_coherence)
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        elif color_match_sample is not None and anim_args.color_coherence != 'None' and not anim_args.legacy_colormatch:
            image = maintain_colors(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), color_match_sample, anim_args.color_coherence)
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # intercept and override to grayscale
        if anim_args.color_force_grayscale:
            image = ImageOps.grayscale(image)
            image = ImageOps.colorize(image, black="black", white="white")

        # overlay mask
        if args.overlay_mask and (anim_args.use_mask_video or args.use_mask):
            image = do_overlay_mask(args, anim_args, image, frame_idx)

        # on strength 0, set color match to generation
        if ((not anim_args.legacy_colormatch and not args.use_init) or (anim_args.legacy_colormatch and strength == 0)) and not anim_args.color_coherence in ['Image', 'Video Input']:
            color_match_sample = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        if not using_vid_init:
            prev_img = opencv_image

        if turbo_steps > 1:
            turbo_prev_image, turbo_prev_frame_idx = turbo_next_image, turbo_next_frame_idx
            turbo_next_image, turbo_next_frame_idx = opencv_image, frame_idx
            frame_idx += turbo_steps
        else:
            filename = f"{root.timestring}_{frame_idx:09}.png"
            save_image(image, 'PIL', filename, args, video_args, root)
            if usingDeforumation: #Should we Connect to the Deforumation websocket server to tell 3:d parties what frame_idx we are on currently?
                shouldResume = int(mediator_getValue("should_resume").strip().strip('\n'))  #If the user pushed "Set current image" in Deforumation, we can't just overwrite the new start_frame  

                if not shouldResume:
                    mediator_setValue("start_frame", frame_idx)
                mediator_setValue("saved_frame_params", frame_idx)

            if anim_args.save_depth_maps:
                if cmd_opts.lowvram or cmd_opts.medvram:
                    lowvram.send_everything_to_cpu()
                    sd_hijack.model_hijack.undo_hijack(sd_model)
                    devices.torch_gc()
                    depth_model.to(root.device)
                depth = depth_model.predict(opencv_image, anim_args.midas_weight, root.half_precision)
                depth_model.save(os.path.join(args.outdir, f"{root.timestring}_depth_{frame_idx:09}.png"), depth)
                if cmd_opts.lowvram or cmd_opts.medvram:
                    depth_model.to('cpu')
                    devices.torch_gc()
                    lowvram.setup_for_low_vram(sd_model, cmd_opts.medvram)
                    sd_hijack.model_hijack.hijack(sd_model)
            frame_idx += 1

        state.current_image = image
        if not int(mediator_getValue("seed_changed").strip().strip('\n')):
            mediator_setValue("seed", args.seed)
        args.seed = next_seed(args, root)
        last_preview_frame = render_preview(args, anim_args, video_args, root, frame_idx, last_preview_frame)

    #Restore Deforum CN Properties
    for cnIndex in range(5):
        currCnIndex = cnIndex+1
        setattr(controlnet_args, f'cn_{currCnIndex}_weight', cnu[f'cn_{currCnIndex}_weight'] )
        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_start', cnu[f'cn_{currCnIndex}_guidance_start'])
        setattr(controlnet_args, f'cn_{currCnIndex}_guidance_end', cnu[f'cn_{currCnIndex}_guidance_end'])
        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_a', cnu[f'cn_{currCnIndex}_threshold_a'])
        setattr(controlnet_args, f'cn_{currCnIndex}_threshold_b', cnu[f'cn_{currCnIndex}_threshold_b'])


    if predict_depths and not keep_in_vram:
        depth_model.delete_model()  # handles adabins too

    if load_raft:
        raft_model.delete_model()
