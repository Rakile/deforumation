import asyncio
import time
import websockets
import pickle
import win32pipe, win32file, pywintypes
import threading
#Server-stuff
stop = None
server = None
serverShutDown = False
#Run/Steps
steps = 25
deforum_steps = 25
#Keyframes/Strength
strength_value = 0.65
deforum_strength = 0.65
#Keyframes/CFG
cfg_scale = 6
deforum_cfg = 6
#Keyframes/3D/Motion
rotation_x = 0.0
rotation_y = 0.0
rotation_z = 0.0
deforum_rotation_x = 0.0
deforum_rotation_y = 0.0
deforum_rotation_z = 0.0
translation_x = 0.0
translation_y = 0.0
translation_z = 0.0
deforum_translation_x = 0.0
deforum_translation_y = 0.0
deforum_translation_z = 0.0
Prompt_Positive = "EMPTY"
Prompt_Negative = "EMPTY"
should_resume = 0
shouldPause = 0
start_frame = 0
frame_outdir = ""
resume_timestring=""
seed_value = -1
did_seed_change = 0
should_use_deforumation_prompt_scheduling = 0
#Keyframes/Field Of View/FOV schedule
fov = 70.0
deforum_fov = 70.0
doVerbose = False
doVerbose2 = False
should_use_deforumation_strength = 1
should_use_deforumation_cfg = 1
should_use_deforumation_cadence = 1
should_use_deforumation_panning = 1
should_use_deforumation_zoomfov = 1
should_use_deforumation_rotation = 1
should_use_deforumation_tilt = 1
cadence = 2
deforum_cadence = 2

cn_weight = []
cn_stepstart = []
cn_stepend = []
cn_lowt = []
cn_hight = []
for i in range(5):
    cn_weight.append(1.0)
    cn_stepstart.append(0.0)
    cn_stepend.append(1.0)
    cn_lowt.append(0)
    cn_hight.append(255)

#cn_weight = 1.00
#cn_stepstart = 0.0
#cn_stepend = 1.0
#cn_lowt = 0
#cn_hight = 255

parseq_keys = 0
use_parseq = 0
parseq_manifest = ""
parseq_strength = 0
parseq_movements = 0
parseq_prompt = 0
should_use_deforumation_noise = 0

noise_multiplier = 1.05
deforum_noise_multiplier = 1.05
perlin_octaves = 4
deforum_perlin_octaves = 4
perlin_persistence = 0.5
deforum_perlin_persistence = 0.5

use_deforumation_cadence_scheduling = 0

deforumation_cadence_scheduling_manifest = "0:(3)"


def find_str(s, char):
    index = 0

    if char in s:
        c = char[0]
        for ch in s:
            if ch == c:
                if s[index:index+len(char)] == char:
                    return index

            index += 1

    return -1

def main(pipeName):
    global serverShutDown
    global Prompt_Positive
    global Prompt_Negative
    global rotation_x
    global rotation_y
    global rotation_z
    global translation_x
    global translation_y
    global translation_z
    global deforum_translation_x
    global deforum_translation_y
    global deforum_translation_z
    global fov
    global cfg_scale
    global strength_value
    global steps
    global should_resume
    global start_frame
    global frame_outdir
    global resume_timestring
    global shouldPause
    global seed_value
    global did_seed_change
    global should_use_deforumation_strength
    global should_use_deforumation_cfg
    global cadence
    global should_use_deforumation_prompt_scheduling
    global cn_weight
    global cn_stepstart
    global cn_stepend
    global cn_lowt
    global cn_hight
    global parseq_keys
    global use_parseq
    global parseq_manifest
    global parseq_strength
    global parseq_movements
    global deforum_rotation_x
    global deforum_rotation_y
    global deforum_rotation_z
    global deforum_fov
    global deforum_strength
    global deforum_cfg
    global deforum_steps
    global parseq_prompt
    global noise_multiplier
    global deforum_perlin_octaves
    global deforum_perlin_persistence
    global deforum_noise_multiplier
    global perlin_octaves
    global perlin_persistence
    global deforum_cadence
    global should_use_deforumation_cadence
    global should_use_deforumation_noise
    global should_use_deforumation_panning
    global should_use_deforumation_zoomfov
    global should_use_deforumation_rotation
    global should_use_deforumation_tilt
    global use_deforumation_cadence_scheduling
    global deforumation_cadence_scheduling_manifest

    print("pipe server:"+str(pipeName))
    count = 0
    pipe = win32pipe.CreateNamedPipe('\\\\.\\pipe\\'+str(pipeName), win32pipe.PIPE_ACCESS_DUPLEX,
                                     win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                     1, 65536, 65536, 0, None)

    while 1==1:
        try:
            #print("Incomming message:"+str(message))
            #print("waiting for client")
            win32pipe.ConnectNamedPipe(pipe, None)
            #print("got client")
            message = win32pipe.SetNamedPipeHandleState(pipe, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            if message == 0:
                print(f"SetNamedPipeHandleState return code: {message}")
                continue
            else:
                message = win32file.ReadFile(pipe, 64 * 1024)
                arr = pickle.loads(message[1])
            if len(arr) == 3:
                shouldWrite = arr[0]
                parameter = arr[1]
                value = arr[2]
                #Prompts Params
                ###########################################################################
    
                if str(parameter) == "is_paused_rendering":
                    if shouldWrite:
                        shouldPause = int(value)
                    else:
                        if doVerbose:
                            print("is_paused_rendering:"+str(shouldPause))
                        win32file.WriteFile(pipe, str.encode(str(shouldPause)))
                elif str(parameter) == "should_use_deforumation_prompt_scheduling":
                    if shouldWrite:
                        should_use_deforumation_prompt_scheduling = value
                    else:
                        if doVerbose:
                            print("should_use_deforumation_prompt_scheduling:" + str(should_use_deforumation_prompt_scheduling))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_prompt_scheduling)))
                elif str(parameter) == "use_deforumation_cadence_scheduling":
                    if shouldWrite:
                        use_deforumation_cadence_scheduling = value
                    else:
                        if doVerbose:
                            print("use_deforumation_cadence_scheduling:" + str(use_deforumation_cadence_scheduling))
                        win32file.WriteFile(pipe, str.encode(str(use_deforumation_cadence_scheduling)))
                elif str(parameter) == "deforumation_cadence_scheduling_manifest":
                    if shouldWrite:
                        deforumation_cadence_scheduling_manifest = value
                    else:
                        if doVerbose:
                            print("deforumation_cadence_scheduling_manifest:" + str(deforumation_cadence_scheduling_manifest))
                        win32file.WriteFile(pipe, str.encode(str(deforumation_cadence_scheduling_manifest)))
                elif str(parameter) == "positive_prompt":
                    if shouldWrite:
                        Prompt_Positive = value
                    else:
                        if doVerbose:
                            print("negative_prompt:"+str(Prompt_Positive))
                        win32file.WriteFile(pipe, str.encode(str(Prompt_Positive)))
                elif str(parameter) == "negative_prompt":
                    if shouldWrite:
                        Prompt_Negative = value
                    else:
                        if doVerbose:
                            print("sending prompt:"+str(Prompt_Negative))
                        win32file.WriteFile(pipe, str.encode(str(Prompt_Negative)))
                #Translation Params
                ###########################################################################
                elif str(parameter) == "translation_x":
                    if shouldWrite:
                        translation_x = float(value)
                    else:
                        if doVerbose:
                            print("sending translation_x:"+str(translation_x))
                        win32file.WriteFile(pipe, str.encode(str(translation_x)))
                elif str(parameter) == "translation_y":
                    if shouldWrite:
                        translation_y = float(value)
                    else:
                        if doVerbose:
                            print("sending translation_y:"+str(translation_y))
                        win32file.WriteFile(pipe, str.encode(str(translation_y)))
                elif str(parameter) == "translation_z":
                    if shouldWrite:
                        translation_z = float(value)
                    else:
                        if doVerbose:
                            print("sending translation_z:"+str(translation_z))
                        win32file.WriteFile(pipe, str.encode(str(translation_z)))
                #What Deforum thinks it has for Translation
                elif str(parameter) == "deforum_translation_x":
                    if shouldWrite:
                        deforum_translation_x = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_translation_x:"+str(deforum_translation_x))
                        win32file.WriteFile(pipe, str.encode(str(deforum_translation_x)))
                elif str(parameter) == "deforum_translation_y":
                    if shouldWrite:
                        deforum_translation_y = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_translation_y:"+str(deforum_translation_y))
                        win32file.WriteFile(pipe, str.encode(str(deforum_translation_y)))
                elif str(parameter) == "deforum_translation_z":
                    if shouldWrite:
                        deforum_translation_z = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_translation_z:"+str(deforum_translation_z))
                        win32file.WriteFile(pipe, str.encode(str(deforum_translation_z)))
                #What Deforum thinks it has for Rotation
                elif str(parameter) == "deforum_rotation_x":
                    if shouldWrite:
                        deforum_rotation_x = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_rotation_x:"+str(deforum_rotation_x))
                        win32file.WriteFile(pipe, str.encode(str(deforum_rotation_x)))
                elif str(parameter) == "deforum_rotation_y":
                    if shouldWrite:
                        deforum_rotation_y = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_translation_y:"+str(deforum_rotation_y))
                        win32file.WriteFile(pipe, str.encode(str(deforum_rotation_y)))
                elif str(parameter) == "deforum_rotation_z":
                    if shouldWrite:
                        deforum_rotation_z = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_rotation_z:"+str(deforum_rotation_z))
                        win32file.WriteFile(pipe, str.encode(str(deforum_rotation_z)))
                #Rotation Params
                ###########################################################################
                elif str(parameter) == "rotation_x":
                    if shouldWrite:
                        rotation_x = float(value)
                        #print("writing rotation_x:" + str(rotation_x))
                        #time.sleep(20)
                    else:
                        if doVerbose:
                            print("sending rotation_x:"+str(rotation_x))
                        win32file.WriteFile(pipe, str.encode(str(rotation_x)))
                elif str(parameter) == "rotation_y":
                    if shouldWrite:
                        rotation_y = float(value)
                    else:
                        if doVerbose:
                            print("sending rotation_y:"+str(rotation_y))
                        win32file.WriteFile(pipe, str.encode(str(rotation_y)))
                elif str(parameter) == "rotation_z":
                    if shouldWrite:
                        rotation_z = float(value)
                    else:
                        if doVerbose:
                            print("sending rotation_z:"+str(rotation_z))
                        win32file.WriteFile(pipe, str.encode(str(rotation_z)))
                #FOV Params
                ###########################################################################
                elif str(parameter) == "fov":
                    if shouldWrite:
                        fov = float(value)
                    else:
                        if doVerbose:
                            print("sending fov:"+str(fov))
                        win32file.WriteFile(pipe, str.encode(str(fov)))
                #what Deforum think it has
                ###########################################################################
                elif str(parameter) == "deforum_fov":
                    if shouldWrite:
                        deforum_fov = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_fov:"+str(deforum_fov))
                        win32file.WriteFile(pipe, str.encode(str(deforum_fov)))
                #CFG Params
                ###########################################################################
                elif str(parameter) == "cfg":
                    if shouldWrite:
                        cfg_scale = int(value)
                    else:
                        if doVerbose:
                            print("sending CFG:"+str(cfg_scale))
                        win32file.WriteFile(pipe, str.encode(str(cfg_scale)))
                #What Deforum think the CFG Value is
                ###########################################################################
                elif str(parameter) == "deforum_cfg":
                    if shouldWrite:
                        deforum_cfg = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_cfg:"+str(deforum_cfg))
                        win32file.WriteFile(pipe, str.encode(str(deforum_cfg)))
                #Strength Params
                ###########################################################################
                elif str(parameter) == "strength":
                    if shouldWrite:
                        strength_value = float(value)
                    else:
                        if doVerbose:
                            print("sending STRENGTH:"+str(strength_value))
                        win32file.WriteFile(pipe, str.encode(str(strength_value)))
                #What Deforum think the Strength Value is
                ###########################################################################
                elif str(parameter) == "deforum_strength":
                    if shouldWrite:
                        deforum_strength = float(value)
                    else:
                        if doVerbose:
                            print("sending deforum_strength:"+str(deforum_strength))
                        win32file.WriteFile(pipe, str.encode(str(deforum_strength)))
                #ControlNet Weight Params
                ###########################################################################
                elif str(parameter).startswith("cn_weight"):
                    cnIndex = int(parameter[len(parameter)-1])
                    if shouldWrite:
                        cn_weight[cnIndex-1] = float(value)
                    else:
                        if doVerbose:
                            print("sending cn_weight:"+str(cn_weight[cnIndex-1]))
                        win32file.WriteFile(pipe, str.encode(str(cn_weight[cnIndex-1])))
                #ControlNet step start Params
                ###########################################################################
                elif str(parameter).startswith("cn_stepstart"):
                    cnIndex = int(parameter[len(parameter)-1])
                    if shouldWrite:
                        cn_stepstart[cnIndex-1] = float(value)
                    else:
                        if doVerbose:
                            print("sending cn_stepstart:"+str(cn_stepstart[cnIndex-1]))
                        win32file.WriteFile(pipe, str.encode(str(cn_stepstart[cnIndex-1])))
                #ControlNet step end Params
                ###########################################################################
                elif str(parameter).startswith("cn_stepend"):
                    cnIndex = int(parameter[len(parameter)-1])
                    if shouldWrite:
                        cn_stepend[cnIndex-1] = float(value)
                    else:
                        if doVerbose:
                            print("sending cn_stepend:"+str(cn_stepend[cnIndex-1]))
                        win32file.WriteFile(pipe, str.encode(str(cn_stepend[cnIndex-1])))
                #ControlNet low threshold Params
                ###########################################################################
                elif str(parameter).startswith("cn_lowt"):
                    cnIndex = int(parameter[len(parameter)-1])
                    if shouldWrite:
                        cn_lowt[cnIndex-1] = int(value)
                    else:
                        if doVerbose:
                            print("sending cn_lowt:"+str(cn_lowt[cnIndex-1]))
                        win32file.WriteFile(pipe, str.encode(str(cn_lowt[cnIndex-1])))
                #ControlNet high threshold Params
                ###########################################################################
                elif str(parameter).startswith("cn_hight"):
                    cnIndex = int(parameter[len(parameter)-1])
                    if shouldWrite:
                        cn_hight[cnIndex-1] = int(value)
                    else:
                        if doVerbose:
                            print("sending cn_hight:"+str(cn_hight[cnIndex-1]))
                        win32file.WriteFile(pipe, str.encode(str(cn_hight[cnIndex-1])))
                #Seed Params
                ###########################################################################
                elif str(parameter) == "seed":
                    if shouldWrite:
                        seed_value = int(value)
                        did_seed_change = 1
                    else:
                        if doVerbose:
                            print("sending SEED:"+str(seed_value))
                        did_seed_change = 0
                        win32file.WriteFile(pipe, str.encode(str(seed_value)))
                elif str(parameter) == "seed_changed":
                    if not shouldWrite: #don't support write (it's not nessecary)
                        win32file.WriteFile(pipe, str.encode(str(did_seed_change)))
                #Perlin persistence Param
                ###########################################################################
                elif str(parameter) == "perlin_persistence":
                    if shouldWrite:
                        perlin_persistence = float(value)
                    else:
                        if doVerbose:
                            print("sending perlin_persistence:" + str(perlin_persistence))
                        win32file.WriteFile(pipe, str.encode(str(perlin_persistence)))
                #Perlin octaves Param
                ###########################################################################
                elif str(parameter) == "perlin_octaves":
                    if shouldWrite:
                        perlin_octaves = int(value)
                    else:
                        if doVerbose:
                            print("sending perlin_octaves:" + str(perlin_octaves))
                        win32file.WriteFile(pipe, str.encode(str(perlin_octaves)))
    
                # Should use Pan params
                ###########################################################################
                elif str(parameter) == "should_use_deforumation_panning":
                    if shouldWrite:
                        should_use_deforumation_panning = int(value)
                    else:
                        if doVerbose:
                            print("sending should_use_deforumation_panning:" + str(should_use_deforumation_panning))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_panning)))
    
                # Should use Tilt params
                ###########################################################################
                elif str(parameter) == "should_use_deforumation_tilt":
                    if shouldWrite:
                        should_use_deforumation_tilt = int(value)
                    else:
                        if doVerbose:
                            print("sending should_use_deforumation_tilt:" + str(should_use_deforumation_tilt))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_tilt)))
                # Should use Rotation params
                ###########################################################################
                elif str(parameter) == "should_use_deforumation_rotation":
                    if shouldWrite:
                        should_use_deforumation_rotation = int(value)
                    else:
                        if doVerbose:
                            print("sending should_use_deforumation_rotation:" + str(should_use_deforumation_rotation))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_rotation)))
                # Should use ZOOM/FOV params
                ###########################################################################
                elif str(parameter) == "should_use_deforumation_zoomfov":
                    if shouldWrite:
                        should_use_deforumation_zoomfov = int(value)
                    else:
                        if doVerbose:
                            print("sending should_use_deforumation_zoomfov:" + str(should_use_deforumation_zoomfov))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_zoomfov)))
                # Should use Noise Params
                ###########################################################################
                elif str(parameter) == "should_use_deforumation_noise":
                    if shouldWrite:
                        should_use_deforumation_noise = int(value)
                    else:
                        if doVerbose:
                            print("sending should_use_deforumation_noise:" + str(should_use_deforumation_noise))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_noise)))
                # Noise Multiplier Param
                ###########################################################################
                elif str(parameter) == "noise_multiplier":
                    if shouldWrite:
                        noise_multiplier = float(value)
                    else:
                        if doVerbose:
                            print("sending noise_multiplier:" + str(noise_multiplier))
                        win32file.WriteFile(pipe, str.encode(str(noise_multiplier)))
                #What Deforum thinks the noise multiplier Value is
                ###########################################################################
                elif str(parameter) == "deforum_noise_multiplier":
                    if shouldWrite:
                        deforum_noise_multiplier = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_noise_multiplier:"+str(deforum_noise_multiplier))
                        win32file.WriteFile(pipe, str.encode(str(deforum_noise_multiplier)))
                #What Deforum thinks the perlin octaves Value is
                ###########################################################################
                elif str(parameter) == "deforum_perlin_octaves":
                    if shouldWrite:
                        deforum_perlin_octaves = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_perlin_octaves:"+str(deforum_perlin_octaves))
                        win32file.WriteFile(pipe, str.encode(str(deforum_perlin_octaves)))
                #What Deforum thinks the perlin octaves Value is
                ###########################################################################
                elif str(parameter) == "deforum_perlin_persistence":
                    if shouldWrite:
                        deforum_perlin_persistence = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_perlin_persistence:"+str(deforum_perlin_persistence))
                        win32file.WriteFile(pipe, str.encode(str(deforum_perlin_persistence)))
                #Steps Params
                ###########################################################################
                elif str(parameter) == "steps":
                    if shouldWrite:
                        steps = int(value)
                    else:
                        if doVerbose:
                            print("sending STEPS:"+str(steps))
                        win32file.WriteFile(pipe, str.encode(str(steps)))
                #What Deforum thinks the Steps Value is
                ###########################################################################
                elif str(parameter) == "deforum_steps":
                    if shouldWrite:
                        deforum_steps = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_steps:"+str(deforum_steps))
                        win32file.WriteFile(pipe, str.encode(str(deforum_steps)))
                #Resume and rewind
                ##########################################################################
                elif str(parameter) == "should_resume":
                    if shouldWrite:
                        #print("The value is:"+str(value))
                        should_resume = int(value)
                        if doVerbose2:
                            print("writing should_resume:" + str(should_resume))
                    else:
                        win32file.WriteFile(pipe, str.encode(str(should_resume)))
                elif str(parameter) == "start_frame":
                    if shouldWrite:
                        start_frame = int(value)
                    else:
                        if doVerbose2:
                            print("sending start frame:"+str(start_frame))
                        win32file.WriteFile(pipe, str.encode(str(start_frame)))
                elif str(parameter) == "frame_outdir":
                    if shouldWrite:
                        frame_outdir = str(value)
                    else:
                        if doVerbose2:
                            print("sending frame_outdir:"+str(frame_outdir))
                        win32file.WriteFile(pipe, str.encode(str(frame_outdir)))
                elif str(parameter) == "resume_timestring":
                    if shouldWrite:
                        resume_timestring = str(value)
                    else:
                        if doVerbose2:
                            print("sending resume_timestring:"+str(resume_timestring))
                        win32file.WriteFile(pipe, str.encode(str(resume_timestring)))
                elif str(parameter) == "should_use_deforumation_strength":
                    if shouldWrite:
                        #print("Setting should use deforumation strength to:"+str(int(value)))
                        should_use_deforumation_strength = int(value)
                    else:
                        if doVerbose2:
                            print("sending should_use_deforumation_strength:"+str(should_use_deforumation_strength))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_strength)))
                elif str(parameter) == "should_use_deforumation_cfg":
                    if shouldWrite:
                        #print("Setting should use deforumation strength to:"+str(int(value)))
                        should_use_deforumation_cfg = int(value)
                    else:
                        if doVerbose2:
                            print("sending should_use_deforumation_cfg:"+str(should_use_deforumation_cfg))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_cfg)))
                elif str(parameter) == "cadence":
                    if shouldWrite:
                        cadence = str(value)
                    else:
                        if doVerbose2:
                            print("sending cadence:"+str(cadence))
                        win32file.WriteFile(pipe, str.encode(str(cadence)))
                elif str(parameter) == "should_use_deforumation_cadence":
                    if shouldWrite:
                        should_use_deforumation_cadence = str(value)
                    else:
                        if doVerbose2:
                            print("sending should_use_deforumation_cadence:"+str(should_use_deforumation_cadence))
                        win32file.WriteFile(pipe, str.encode(str(should_use_deforumation_cadence)))
    
                #What Deforum thinks the cadence Value is
                ###########################################################################
                elif str(parameter) == "deforum_cadence":
                    if shouldWrite:
                        deforum_cadence = int(value)
                    else:
                        if doVerbose:
                            print("sending deforum_cadence:"+str(deforum_cadence))
                        win32file.WriteFile(pipe, str.encode(str(deforum_cadence)))
                elif str(parameter) == "parseq_keys":
                    if shouldWrite:
                        parseq_keys = value
                    else:
                        if doVerbose2:
                            print("sending parseq_keys:")
                        win32file.WriteFile(pipe, pickle.dumps(parseq_keys))
                elif str(parameter) == "use_parseq":
                    if shouldWrite:
                        use_parseq = value
                    else:
                        if doVerbose2:
                            print("sending use_parseq:")
                        win32file.WriteFile(pipe, str.encode(str(use_parseq)))
                elif str(parameter) == "parseq_manifest":
                    if shouldWrite:
                        parseq_manifest = value
                        print("Got parseq_manifest:"+ str(value))
                    else:
                        if doVerbose2:
                            print("sending parseq_manifest:")
                        win32file.WriteFile(pipe, str.encode(str(parseq_manifest)))
                #elif str(parameter) == "parseq_prompt":
                #    if shouldWrite:
                #        parseq_prompt = value
                #    else:
                #        if doVerbose2:
                #            print("sending parseq_prompt:")
                #        win32file.WriteFile(pipe, str.encode(str(parseq_prompt))
                elif str(parameter) == "parseq_strength":
                    if shouldWrite:
                        parseq_strength = value
                    else:
                        if doVerbose2:
                            print("sending parseq_strength:")
                        win32file.WriteFile(pipe, str.encode(str(parseq_strength)))
                elif str(parameter) == "parseq_movements":
                    if shouldWrite:
                        print("parseq_movements:"+str(parseq_movements))
                        parseq_movements = value
                    else:
                        if doVerbose2:
                            print("sending parseq_movements:"+str(parseq_movements))
                        win32file.WriteFile(pipe, str.encode(str(parseq_movements)))
                elif str(parameter) == "shutdown":
                    serverShutDown = True
                else:
                    print("NO SUCH COMMAND:" +parameter+"\nPlease make sure Mediator, Deforumation and the Deforum (render.py, animation.py) are in sync.")
                    if not shouldWrite:
                        win32file.WriteFile(pipe, str.encode(str("NO SUCH COMMAND:" +parameter)))
                if shouldWrite: #Return an "OK" if the writes went OK
                    win32file.WriteFile(pipe, b"OK")
    
            else: #Array was not a length of 3 [True/False,<parameter value>,<value>
                if doVerbose:
                    win32file.WriteFile(pipe, b"ERROR")
        except pywintypes.error as e:
            #print("Error:" + str(e))
            win32file.CloseHandle(pipe)
            pipe = win32pipe.CreateNamedPipe('\\\\.\\pipe\\'+str(pipeName), win32pipe.PIPE_ACCESS_DUPLEX,
                                             win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                             1, 65536, 65536, 0, None)
            #asyncio.get_event_loop().stop()
            #await websocket.close()
            #loop = asyncio.get_event_loop()
            #loop.stop()

async def main2():
    global stop
    global server
    try:
        stop = asyncio.Future()  # run forever
        #server = await websockets.serve(echo, "localhost", 8765)
        #loop = asyncio.get_event_loop()

        while True:
            if serverShutDown:
                print("Shutting down Server")
                #pending = asyncio.Task.all_tasks()
                #group = asyncio.gather(*pending, return_exceptions=True)
                server.close()
                #server. run_until_complete(server)
                #loop.close()
                #server.close()
                break
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        server.close()
        print("Ctrl-c :)")
    #await stop
    #await server.close()
    #async with websockets.serve(echo, "localhost", 8765):
    #    await stop

if __name__ == '__main__':
    try:
        print("Starting mediator_v2 0.5.0 (named pipes)")
        #asyncio.run(main())
        deforumation_thread = threading.Thread(target=main, args=(['Deforumation']))
        deforum_thread = threading.Thread(target=main, args=(['Deforum']))
        deforumation_thread.daemon = True
        deforumation_thread.start()
        deforum_thread.daemon = True
        deforum_thread.start()
        while(True):
            time.sleep(0.1)
    except KeyboardInterrupt:
        serverShutDown = True
        #server.close()
        print("Shutting down Server")


