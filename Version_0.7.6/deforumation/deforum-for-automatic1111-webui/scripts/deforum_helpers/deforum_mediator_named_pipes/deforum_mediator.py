import asyncio
import websockets
import pickle
import time
import win32pipe, win32file, pywintypes
import ast

needToUpdateMediator = False
anim_args_copy = None
args_copy = None
root_copy = None
exception_in_a_row = 0
#async def sendAsync(value):
#    handle = win32file.CreateFile('\\\\.\\pipe\\Deforum', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
#                                  win32file.OPEN_EXISTING, 0, None)
#    res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
#    bytesToSend = pickle.dumps(value)
#    win32file.WriteFile(handle, bytesToSend)
#    message = win32file.ReadFile(handle, 64 * 1024)
#
#
#    win32file.CloseHandle(handle)
#    return message[1].decode()

async def sendAsync(value):
    bufSize = 64 * 1024
    handle = win32file.CreateFile('\\\\.\\pipe\\Deforum', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,win32file.OPEN_EXISTING, 0, None)
    res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
    bytesToSend = pickle.dumps(value)
    win32file.WriteFile(handle, bytesToSend)
    result, data = win32file.ReadFile(handle, bufSize)
    message = data
    while len(data) == bufSize:
        print("More data has to be read (normal pipe async):"+ str(len(data)))
        result, data = win32file.ReadFile(handle, bufSize)
        message += data

    win32file.CloseHandle(handle)

    message = message.decode()
    if message.startswith("[\'") and message.endswith("\']"):
        message = ast.literal_eval(message)
        if len(message) == 1:
            message = str(message[0])
    return message

def mediator_set_anim_args(anim_args, args, root):
    global anim_args_copy
    global args_copy
    global root_copy
    anim_args_copy = anim_args
    args_copy = args
    root_copy = root

def updateMediator(): #No validation is made that  the websocket server (Mediator.py is actually up and running)
    print("Was ordered to update time_string")
    if anim_args_copy.resume_from_timestring:
        print("Sending Values:" + str(anim_args_copy.resume_timestring))
        return_value = asyncio.run(sendAsync([1, "resume_timestring", anim_args_copy.resume_timestring]))
        #mediator_setValue("resume_timestring", anim_args_copy.resume_timestring)
    else:
        print("Sending Values:" + str(root_copy.timestring))
        return_value = asyncio.run(sendAsync([1, "resume_timestring", root_copy.timestring]))
        #mediator_setValue("resume_timestring", root_copy.timestring) 
    #OUTDIR is the same for either you resume or not.
    mediator_setValue("frame_outdir", args_copy.outdir)


def mediator_getValue(param):
    global needToUpdateMediator
    global exception_in_a_row
    checkerrorConnecting = True
    needToUpdateMediator = False
    exception_in_a_row = 0
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync([0, param, 0]))
            if needToUpdateMediator:
                needToUpdateMediator = False
                updateMediator()
            return return_value
        except Exception as e:
            exception_in_a_row += 1
            if exception_in_a_row > 20:
                print("Deforum Mediator Error:" + str(e))
                print("...while trying to send parameter ("+str(param)+")")
                print("The Deforumation Mediator, is probably not connected (waiting 1.0 seconds, before trying to reconnect...)")
                needToUpdateMediator = True
                exception_in_a_row = 0
            time.sleep(0.05)

def mediator_setValue(param, value):
    global needToUpdateMediator
    global exception_in_a_row
    checkerrorConnecting = True
    needToUpdateMediator = False
    exception_in_a_row = 0
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync([1, param, value]))
            if needToUpdateMediator:
                needToUpdateMediator = False
                updateMediator()
            return return_value
        except Exception as e:
            exception_in_a_row += 1
            if exception_in_a_row > 20:
                print("Deforum Mediator Error:" + str(e))
                print("...while trying to send parameter ("+str(param)+") with value("+str(value)+")")
                print("The Deforumation Mediator, is probably not connected (waiting 1.0 seconds, before trying to reconnect...)")
                needToUpdateMediator = True
                exception_in_a_row = 0
            time.sleep(0.05)
