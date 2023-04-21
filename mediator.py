import asyncio
import websockets
import pickle

#Run/Steps
steps = 25
#Keyframes/Strength
strength_value = 0.65
#Keyframes/CFG
cfg_scale = 6
#Keyframes/3D/Motion
rotation_x = 0.0
rotation_y = 0.0
rotation_z = 0.0
translation_x = 0.0
translation_y = 0.0
translation_z = 0.0
Prompt_Positive = "EMPTY"
Prompt_Negative = "EMPTY"
should_resume = 0
shouldPause = 0
start_frame = 0
frame_outdir = ""
resume_timestring=""
seed_value = -1
did_seed_change = 0
should_use_deforum_prompt_scheduling = 0
#Keyframes/Field Of View/FOV schedule
fov = 70
doVerbose = False
doVerbose2 = False
should_use_deforumation_strength = 1
cadence = 2
async def echo(websocket):
    global Prompt_Positive
    global Prompt_Negative
    global rotation_x
    global rotation_y
    global rotation_z
    global translation_x
    global translation_y
    global translation_z
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
    global cadence
    global should_use_deforum_prompt_scheduling
    async for message in websocket:
        #print("Incomming message:"+str(message))
        arr = pickle.loads(message)
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
                        print("is_paused_rendering:"+str(parameter))
                    await websocket.send(str(shouldPause))
            elif str(parameter) == "should_use_deforum_prompt_scheduling":
                if shouldWrite:
                    should_use_deforum_prompt_scheduling = value
                else:
                    if doVerbose:
                        print("should_use_deforum_prompt_scheduling:" + str(should_use_deforum_prompt_scheduling))
                    await websocket.send(str(should_use_deforum_prompt_scheduling))
            elif str(parameter) == "positive_prompt":
                if shouldWrite:
                    Prompt_Positive = value
                else:
                    if doVerbose:
                        print("negative_prompt:"+str(Prompt_Positive))
                    await websocket.send(str(Prompt_Positive))
            elif str(parameter) == "negative_prompt":
                if shouldWrite:
                    Prompt_Negative = value
                else:
                    if doVerbose:
                        print("sending prompt:"+str(Prompt_Negative))
                    await websocket.send(str(Prompt_Negative))
            #Translation Params
            ###########################################################################
            elif str(parameter) == "translation_x":
                if shouldWrite:
                    translation_x = float(value)
                else:
                    if doVerbose:
                        print("sending translation_x:"+str(translation_x))
                    await websocket.send(str(translation_x))
            elif str(parameter) == "translation_y":
                if shouldWrite:
                    translation_y = float(value)
                else:
                    if doVerbose:
                        print("sending translation_y:"+str(translation_y))
                    await websocket.send(str(translation_y))
            elif str(parameter) == "translation_z":
                if shouldWrite:
                    translation_z = float(value)
                else:
                    if doVerbose:
                        print("sending translation_z:"+str(translation_z))
                    await websocket.send(str(translation_z))
            #Rotation Params
            ###########################################################################
            elif str(parameter) == "rotation_x":
                if shouldWrite:
                    rotation_x = float(value)
                else:
                    if doVerbose:
                        print("sending rotation_x:"+str(rotation_x))
                    await websocket.send(str(rotation_x))
            elif str(parameter) == "rotation_y":
                if shouldWrite:
                    rotation_y = float(value)
                else:
                    if doVerbose:
                        print("sending rotation_y:"+str(rotation_y))
                    await websocket.send(str(rotation_y))
            elif str(parameter) == "rotation_z":
                if shouldWrite:
                    rotation_z = float(value)
                else:
                    if doVerbose:
                        print("sending rotation_z:"+str(rotation_z))
                    await websocket.send(str(rotation_z))
            #FOV Params
            ###########################################################################
            elif str(parameter) == "fov":
                if shouldWrite:
                    fov = float(value)
                else:
                    if doVerbose:
                        print("sending fov:"+str(fov))
                    await websocket.send(str(fov))
            #CFG Params
            ###########################################################################
            elif str(parameter) == "cfg":
                if shouldWrite:
                    cfg_scale = float(value)
                else:
                    if doVerbose:
                        print("sending CFG:"+str(cfg_scale))
                    await websocket.send(str(cfg_scale))
            #Strength Params
            ###########################################################################
            elif str(parameter) == "strength":
                if shouldWrite:
                    strength_value = float(value)
                else:
                    if doVerbose:
                        print("sending STRENGTH:"+str(strength_value))
                    await websocket.send(str(strength_value))
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
                    await websocket.send(str(seed_value))
            elif str(parameter) == "seed_changed":
                if not shouldWrite: #don't support write (it's not nessecary)
                    await websocket.send(str(did_seed_change))

            #Steps Params
            ###########################################################################
            elif str(parameter) == "steps":
                if shouldWrite:
                    steps = int(value)
                else:
                    if doVerbose:
                        print("sending STEPS:"+str(steps))
                    await websocket.send(str(steps))
            #Resume and rewind
            ##########################################################################
            elif str(parameter) == "should_resume":
                if shouldWrite:
                    #print("The value is:"+str(value))
                    should_resume = int(value)
                    if doVerbose2:
                        print("writing should_resume:" + str(should_resume))
                else:
                    await websocket.send(str(should_resume))
            elif str(parameter) == "start_frame":
                if shouldWrite:
                    start_frame = int(value)
                else:
                    if doVerbose2:
                        print("sending start frame:"+str(start_frame))
                    await websocket.send(str(start_frame))
            elif str(parameter) == "frame_outdir":
                if shouldWrite:
                    frame_outdir = str(value)
                else:
                    if doVerbose2:
                        print("sending frame_outdir:"+str(frame_outdir))
                    await websocket.send(str(frame_outdir))
            elif str(parameter) == "resume_timestring":
                if shouldWrite:
                    resume_timestring = str(value)
                else:
                    if doVerbose2:
                        print("sending resume_timestring:"+str(resume_timestring))
                    await websocket.send(str(resume_timestring))
            elif str(parameter) == "should_use_deforumation_strength":
                if shouldWrite:
                    #print("Setting should use deforumation strength to:"+str(int(value)))
                    should_use_deforumation_strength = int(value)
                else:
                    if doVerbose2:
                        print("sending should_use_deforumation_strength:"+str(should_use_deforumation_strength))
                    await websocket.send(str(should_use_deforumation_strength))
            elif str(parameter) == "cadence":
                if shouldWrite:
                    #print("Writing cadence:"+str(value))
                    cadence = str(value)
                else:
                    if doVerbose2:
                        print("sending cadence:"+str(cadence))
                    await websocket.send(str(cadence))


            if shouldWrite: #Return an "OK" if the writes went OK
                await websocket.send("OK")
        else: #Array was not a length of 3 [True/False,<parameter value>,<value>
            if doVerbose:
                await websocket.send("ERROR")


async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())