import asyncio
import websockets
import pickle
import time
needToUpdateMediator = False
anim_args_copy = None
args_copy = None
async def sendAsync(value):
    async with websockets.connect("ws://8.tcp.ngrok.io:16089") as websocket:
        try:
            await asyncio.wait_for(websocket.send(pickle.dumps(value)), timeout=10.0)
            message = 0
            #yield from asyncio.wait_for(message = await websocket.recv(), timeout=1)
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        except TimeoutError:
            print('timeout!')
            return -1
        if message == None:
            message = 0
        return message

def mediator_set_anim_args(anim_args, args):
    global anim_args_copy
    global args_copy
    anim_args_copy = anim_args
    args_copy = args

def updateMediator(): #No validation is made that  the websocket server (Mediator.py is actually up and running)
    print("Was ordered to update time_string")
    if anim_args_copy.resume_from_timestring:
        print("Sending Values:" + str(anim_args_copy.resume_timestring))
        return_value = asyncio.run(sendAsync([1, "resume_timestring", anim_args_copy.resume_timestring]))
        #mediator_setValue("resume_timestring", anim_args_copy.resume_timestring)
    else:
        print("Sending Values:" + str(args_copy.timestring))
        return_value = asyncio.run(sendAsync([1, "resume_timestring", args_copy.timestring]))
        #mediator_setValue("resume_timestring", args_copy.timestring) 
    #OUTDIR is the same for either you resume or not.
    mediator_setValue("frame_outdir", args_copy.outdir)


def mediator_getValue(param):
    global needToUpdateMediator
    checkerrorConnecting = True
    needToUpdateMediator = False
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync([0, param, 0]))
            if needToUpdateMediator:
                needToUpdateMediator = False
                updateMediator()
            return return_value
        except Exception as e:
            print("Deforum Mediator Error:" + str(e))
            print("...while trying to get parameter ("+str(param)+")")
            print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(5)
            needToUpdateMediator = True

def mediator_setValue(param, value):
    global needToUpdateMediator
    checkerrorConnecting = True
    needToUpdateMediator = False
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync([1, param, value]))
            if needToUpdateMediator:
                needToUpdateMediator = False
                updateMediator()
            return return_value
        except Exception as e:
            print("Deforum Mediator Error:" + str(e))
            print("...while trying to send parameter ("+str(param)+") with value("+str(value)+")")
            print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(5)
            needToUpdateMediator = True
