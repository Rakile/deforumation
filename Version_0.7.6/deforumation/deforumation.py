import inspect
import wx
import wx.media
from wx.adv import Animation, AnimationCtrl
import wx.lib.scrolledpanel
import asyncio
import websockets
import os
import time
import pickle
import json
import wx.lib.newevent
import threading
import requests
import collections
import pyeaze
import win32pipe, win32file, pywintypes
import sys
import subprocess
import shutil
import ast
import speech_recognition as sp
import pyaudio
import wave
import queue
from array import array

#import subprocess
cadenceArray = {}
totalRecallFilePath = "./totalrecall.txt"
deforumationSettingsPath = "./deforumation_settings.txt"
deforumationPredefinedMotionPathSettings = "./deforumation_settings_motions.txt"
deforumationSettingsPath_Keys = "./deforum_settings_keys.txt"
deforumationPromptsPath = "./prompts/"
deforumation_image_backup_folder = "./image_backup/"
gif_animation_output_path = "./motion_images/"
screenWidth = 1500
screenHeight = 1060
USE_BUFFERED_DC = True
should_stay_on_top = False
frame_path = "gibberish"
Prompt_Positive = ""
Prompt_Negative = ""
Strength_Scheduler = 0.65
CFG_Scale = 7
FOV_Scale = 70
Translation_X = 0.0
Translation_Y = 0.0
Translation_Z = 0.0
Rotation_3D_X = 0.0
Rotation_3D_Y = 0.0
Rotation_3D_Z = 0.0
Translation_X_ARMED = 0.0
Translation_Y_ARMED = 0.0
Translation_Z_ARMED = 0.0
Rotation_3D_X_ARMED = 0.0
Rotation_3D_Y_ARMED = 0.0
Rotation_3D_Z_ARMED = 0.0
Translation_X_SIRUP = 0.0
Translation_Y_SIRUP = 0.0
tbrY = 500+190
trbX = 50
is_fov_locked = False
is_reverse_fov_locked = False
is_paused_rendering = False
STEP_Schedule = 25
seedValue = -1
render_frame_window_is_open = False
should_render_live = False
current_render_frame = -1
current_frame = 0
should_use_deforumation_strength = 1
should_use_deforumation_prompt_scheduling = 1
should_use_deforumation_cfg = 1
should_use_deforumation_cadence = 1
should_use_deforumation_noise = 0
should_use_deforumation_panning = 1
should_use_deforumation_zoomfov = 1
should_use_deforumation_rotation = 1
should_use_deforumation_tilt = 1
should_use_before_deforum_prompt = 0
should_use_after_deforum_prompt = 0
renderWindowX = 100
renderWindowY = 100
#ControlNet
CN_Weight = []
CN_StepStart = []
CN_StepEnd = []
CN_LowT = []
CN_HighT = []
CN_UDCn = []
for i in range(5):
    CN_Weight.append(1.0)
    CN_StepStart.append(0.0)
    CN_StepEnd.append(1.0)
    CN_LowT.append(0)
    CN_HighT.append(255)
    CN_UDCn.append(0)
#KEYBOARD KEYS
pan_left_key = 0
pan_right_key = 0
pan_up_key = 0
pan_down_key = 0
zoom_down_key = 0
zoom_up_key = 0
Cadence_Schedule = 2
noise_multiplier = 1.05
Perlin_Octave_Value = 4
Perlin_Persistence_Value = 0.5
zero_pan_active = False
zero_rotate_active = False
zero_zoom_active = False
zero_tilt_active = False
stepit_pan = 0
stepit_rotate = 0
stepit_zoom = 0
isReplaying = 0
replayFrom = 0
replayTo = 0
replayFPS = 30
armed_rotation = False
armed_pan = False
armed_zoom = False
armed_tilt = False
#pstb = False
#pmob = False
is_Parseq_Active = False
showLiveValues = False
pan_step_input_box_value = "1.0"
rotate_step_input_box_value = "1.0"
tilt_step_input_box_value = "1.0"
zero_pan_step_input_box_value = "0"
zero_rotate_step_input_box_value = "0"
zero_zoom_step_input_box_value = "0"
current_active_cn_index = 1
should_use_optical_flow = 1
cadence_flow_factor = 1
generation_flow_factor = 1
#Bezier curve stuff
bezierArray = []
parameter_container = {}
should_use_total_recall = 0
should_use_total_recall_in_deforumation = 0
should_use_deforumation_timestring = 0
number_of_recalled_frames = 0
should_use_total_recall_prompt = 0
should_use_total_recall_movements = 0
should_use_total_recall_others = 0
windowlabel = ""
create_gif_animation_on_preview = 0
frame_has_changed = False
zero_frame_pan_progress_string = "None"
zero_frame_zoom_progress_string = "None"
zero_frame_rotate_progress_string = "None"
zero_pan_current_settings = "<\"0-P: None\">"
zero_zoom_current_settings = "<\"0-Z: None\">"
zero_rotation_current_settings = "<\"0-R: None\">"
zero_tilt_current_settings = "<\"0-T: None\">"
currently_active_motion = -1
is_static_motion = True
should_hide_parseq_box = False
should_hide_totalrecall_box = False
# Use a stream with a callback in non-blocking mode
CHUNK_SIZE = 1024
MIN_VOLUME = 500
# if the recording thread can't consume fast enough, the listener will start discarding
BUF_MAX_SIZE = CHUNK_SIZE * 10
current_live_view_pipe = None

async def sendAsync_special(value):
    if shouldUseNamedPipes:
        bufSize = 64 * 1024
        handle = win32file.CreateFile('\\\\.\\pipe\\Deforumation', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
                                      win32file.OPEN_EXISTING, 0, None)
        res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        bytesToSend = pickle.dumps(value)
        win32file.WriteFile(handle, bytesToSend)
        result, data = win32file.ReadFile(handle, bufSize)
        message = data
        while len(data) == bufSize:
            print("More data has to be read (special pipe async):"+ str(len(data)))
            result, data = win32file.ReadFile(handle, bufSize)
            message += data
        win32file.CloseHandle(handle)
        return message
    else:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # await websocket.send(pickle.dumps(value))
            try:
                await asyncio.wait_for(websocket.send(pickle.dumps(value)), timeout=10.0)
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            except TimeoutError:
                print('timeout!')
            if message == None:
                message = "-NO CONNECTION-"
            # asyncio.ensure_future(message=websocket.recv())
            # print(str(message))
            return message


async def sendAsync(value):
    if shouldUseNamedPipes:
        bufSize = 64 * 1024
        handle = win32file.CreateFile('\\\\.\\pipe\\Deforumation', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
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
    else:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # await websocket.send(pickle.dumps(value))
            try:
                await asyncio.wait_for(websocket.send(pickle.dumps(value)), timeout=10.0)
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            except TimeoutError:
                print('timeout!')
            if message.startswith("[\'") and message.endswith("\']"):
                message = ast.literal_eval(message)
                if len(message) == 1:
                    message = str(message[0])

            return message

def scale_bitmap(bitmap, width, height):
    if bitmap.IsOk():
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
    else:
        result = None
    return result

def get_current_image_path():
    outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
    resume_timestring = str(readValue("resume_timestring"))
    imagePath = outdir + "/" + resume_timestring + "_" + str(current_frame).zfill(9) + ".png"
    return imagePath

def create_ffmpeg_image_string():
    outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
    resume_timestring = str(readValue("resume_timestring"))
    imagePath = outdir + "/" + resume_timestring + "_%09d.png"
    return imagePath

def get_current_image_path_paused():
    outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
    resume_timestring = str(readValue("resume_timestring"))
    imagePath = outdir + "/" + resume_timestring + "_" + str(current_render_frame).zfill(9) + ".png"
    return imagePath

def get_current_image_path_f(frame_num):
    outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
    resume_timestring = str(readValue("resume_timestring"))
    imagePath = outdir + "/" + resume_timestring + "_" + str(frame_num).zfill(9) + ".png"
    return imagePath

def writeValue(param, value):
    checkerrorConnecting = True
    while checkerrorConnecting:
        try:
            asyncio.run(sendAsync([1, param, value]))
            checkerrorConnecting = False
        except Exception as e:
            #print("Deforumation Mediator Error:" + str(e))
            #print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(0.05)


def readValue_special(param, value = -1):
    checkerrorConnecting = True
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync_special([0, param, value]))
            if return_value != None:
            #    if str(return_value) == "-NO CONNECTION-":
            #        print("Mediator.py is running? Were getting a time out, when trying to read a value. Waiting 5 seconds before trying to connect again.")
            #        time.sleep(5)
            #        continue
                return return_value
        except Exception as e:
            #print("Exception number:" + str(e.args[0]))
            if e.args[0] != 231 and e.args[0] !=2:
                print("Deforumation Mediator ErrorX:" + str(e))
            #print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(0.05)

def readValue(param):
    checkerrorConnecting = True
    while checkerrorConnecting:
        try:
            return_value = asyncio.run(sendAsync([0, param, 0]))
            if return_value != None:
            #    if str(return_value) == "-NO CONNECTION-":
            #        print("Mediator.py is running? Were getting a time out, when trying to read a value. Waiting 5 seconds before trying to connect again.")
            #        time.sleep(5)
            #        continue
                return return_value
        except Exception as e:
            #print("Exception number:" + str(e.args[0]))
            if e.args[0] != 231 and e.args[0] !=2:
                print("Deforumation Mediator Error2:" + str(e))
            #print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(0.05)

def askRange(parent=None, message=''):

    dlg = wx.Dialog(parent, title = message, size = (190,200))
    panel = wx.Panel(dlg)
    lblList = ['Not Applicable', 'Far Range', 'Medium Range', 'Close Range', 'Special Range']
    rbox = wx.RadioBox(panel, label='Motion Range Type', pos=(25, 5), choices=lblList, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
    #rbox.Bind(wx.EVT_RADIOBOX, OnRadioBoxCN)
    wx.Button(panel, wx.ID_OK, label="ok", size=(50, 20), pos=(55, 140), style=wx.RA_SPECIFY_COLS)

    okORcancel = dlg.ShowModal()
    result = rbox.GetString(rbox.GetSelection())
    dlg.Destroy()
    return result

def ask(parent=None, message='', default_value='', caption="Important message"):
    dlg = wx.TextEntryDialog(parent, message, value=default_value, caption=caption)
    okORcancel = dlg.ShowModal()
    result = dlg.GetValue()
    if okORcancel == wx.ID_CANCEL:
        result = ""
    dlg.Destroy()
    return result

def waitForNewImageFromDeforum():
    global current_live_view_pipe
    bufSize = 64 * 1024
    value = -1
    try:
        current_live_view_pipe = win32pipe.CreateNamedPipe('\\\\.\\pipe\\deforumation_pipe_in', win32pipe.PIPE_ACCESS_DUPLEX, win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT, 1, 65536, 65536, 0, None)

        win32pipe.ConnectNamedPipe(current_live_view_pipe, None)
        message = win32pipe.SetNamedPipeHandleState(current_live_view_pipe, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        if message == 0:
            print(f"SetNamedPipeHandleState return code: {message}")
            value = 0
            return value
        else:
            totalToSend = []
            result, data = win32file.ReadFile(current_live_view_pipe, bufSize)
            message = data
            while len(data) == bufSize:
                print("More data has to be read (special pipe async):" + str(len(data)))
                result, data = win32file.ReadFile(current_live_view_pipe, bufSize)
                message += data

            arr = pickle.loads(message)
        if len(arr) == 3:
            shouldWrite = arr[0]
            parameter = arr[1]
            value = arr[2]
            if str(parameter) == "new_image_created":
                #print(f"New image received, image number:{value}")
                value = value
            elif str(parameter) == "close_thread":
                value = -666
        #Wether right or wrong, returns have to be made, and handles need to be closed ;)
        win32file.WriteFile(current_live_view_pipe, b"OK")
        win32file.CloseHandle(current_live_view_pipe)
        #print("Receive loop done!")
    except Exception as e:
        print("Error:" + str(e))
        win32file.CloseHandle(current_live_view_pipe)
    return value

def changeBitmapWorker_piped(parent):
    #global current_render_frame
    global should_render_live
    global isReplaying
    #global current_frame
    global current_render_frame
    imageFound = True
    last_rendered = -1
    shouldrunthis = True
    if shouldrunthis == True:
        while parent.shouldRun:
            if (should_render_live == True) and (isReplaying == 0):
                #Create a pipe server, that awaits new images
                #print("Now waiting for the next image")
                value = 0
                current_frame = waitForNewImageFromDeforum()
                #print("Got Image!")
                #print("Got back image number:" + str(value))
                if current_frame == -666:
                    break
                #current_frame = int(readValue("start_frame"))
                #print("current_frame says it got image:" + str(current_frame))
                #current_frame = value

                #current_frame = int(asyncio.get_event_loop().run_until_complete(sendAsync([0, "start_frame", 0])))
                #loop = asyncio.get_event_loop()
                #task = loop.create_task(sendAsync([0, "start_frame", 0]))

                #finally:
                #    lock.release()
                if current_frame == last_rendered:
                    continue
                last_rendered = current_frame
                is_paused = readValue("is_paused_rendering")
                #if current_render_frame < current_frame or int(is_paused) == 0:
                if int(is_paused) == 0:
                    imagePath = get_current_image_path_f(current_frame)
                    maxBackTrack = 100
                    while not os.path.isfile(imagePath):
                        if (current_frame <= 0):
                            imageFound = False
                            break
                        current_frame = int(current_frame) - 1
                        imagePath = get_current_image_path_f(current_frame)
                        maxBackTrack = maxBackTrack - 1
                        if maxBackTrack == 0:
                            imageFound = False
                    if(imageFound):
                        if bool(parent):
                            parent.bitmap = wx.Bitmap(imagePath)
                            if bool(parent.parent):
                                bitmap_width, bitmap_height = parent.parent.GetSize()
                                parent.bitmap = scale_bitmap(parent.bitmap, bitmap_width-18, bitmap_height-40)
                                parent.Refresh()
                            else:
                                isReplaying = 0
                                #print("Thread destroyed")
                                return
                        #print("Image_Nr:"+str(current_frame).zfill(9))
                    else:
                        imageFound = True
                time.sleep(0.25)
            elif isReplaying == 1:
                imagePath = get_current_image_path_f(replayFrom)
                #print("Looking for:"+imagePath)
                for index in range(replayFrom, replayTo, 1):
                    if isReplaying == 0 or not parent.shouldRun:
                        break
                    imagePath = get_current_image_path_f(index)
                    if os.path.isfile(imagePath):
                        parent.bitmap = wx.Bitmap(imagePath)
                        if isReplaying == 0 or not parent.shouldRun:
                            break
                        bitmap_width, bitmap_height = parent.parent.GetSize()
                        if isReplaying == 0 or not parent.shouldRun:
                            break
                        parent.bitmap = scale_bitmap(parent.bitmap, bitmap_width, bitmap_height)
                        parent.Refresh()
                        current_frame = str(index)
                        current_frame = current_frame.zfill(9)
                        current_render_frame = int(current_frame)
                        time.sleep(float(1/replayFPS))
                isReplaying = 0
                bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 18, 18)
                parent.parent.parent.replay_button.SetBitmap(bmp)
                #print("Done Replaying")
    bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
    bmp = scale_bitmap(bmp, 18, 18)
    if bool(parent.parent.parent):
        parent.parent.parent.replay_button.SetBitmap(bmp)
    isReplaying = 0
    #print("Thread destroyed")

def changeBitmapWorker(parent):
    #global current_render_frame
    global should_render_live
    global isReplaying
    #global current_frame
    global current_render_frame
    imageFound = True
    last_rendered = -1
    shouldrunthis = True
    if shouldrunthis == True:
        while parent.shouldRun:
            if (should_render_live == True) and (isReplaying == 0):
                #lock = asyncio.Lock()
                #try:
                current_frame = int(readValue("start_frame"))
                #current_frame = int(asyncio.get_event_loop().run_until_complete(sendAsync([0, "start_frame", 0])))
                #loop = asyncio.get_event_loop()
                #task = loop.create_task(sendAsync([0, "start_frame", 0]))

                #finally:
                #    lock.release()
                if current_frame == last_rendered:
                    continue
                last_rendered = current_frame
                is_paused = readValue("is_paused_rendering")
                #if current_render_frame < current_frame or int(is_paused) == 0:
                if int(is_paused) == 0:
                    imagePath = get_current_image_path_f(current_frame)
                    maxBackTrack = 100
                    while not os.path.isfile(imagePath):
                        if (current_frame <= 0):
                            imageFound = False
                            break
                        current_frame = int(current_frame) - 1
                        imagePath = get_current_image_path_f(current_frame)
                        maxBackTrack = maxBackTrack - 1
                        if maxBackTrack == 0:
                            imageFound = False
                    if(imageFound):
                        if bool(parent):
                            parent.bitmap = wx.Bitmap(imagePath)
                            if bool(parent.parent):
                                bitmap_width, bitmap_height = parent.parent.GetSize()
                                parent.bitmap = scale_bitmap(parent.bitmap, bitmap_width-18, bitmap_height-40)
                                parent.Refresh()
                            else:
                                isReplaying = 0
                                #print("Thread destroyed")
                                return
                        #print("Image_Nr:"+str(current_frame).zfill(9))
                    else:
                        imageFound = True
                time.sleep(0.25)
            elif isReplaying == 1:
                imagePath = get_current_image_path_f(replayFrom)
                #print("Looking for:"+imagePath)
                for index in range(replayFrom, replayTo, 1):
                    if isReplaying == 0 or not parent.shouldRun:
                        break
                    imagePath = get_current_image_path_f(index)
                    if os.path.isfile(imagePath):
                        parent.bitmap = wx.Bitmap(imagePath)
                        if isReplaying == 0 or not parent.shouldRun:
                            break
                        bitmap_width, bitmap_height = parent.parent.GetSize()
                        if isReplaying == 0 or not parent.shouldRun:
                            break
                        parent.bitmap = scale_bitmap(parent.bitmap, bitmap_width, bitmap_height)
                        parent.Refresh()
                        current_frame = str(index)
                        current_frame = current_frame.zfill(9)
                        current_render_frame = int(current_frame)
                        time.sleep(float(1/replayFPS))
                isReplaying = 0
                bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 18, 18)
                parent.parent.parent.replay_button.SetBitmap(bmp)
                #print("Done Replaying")
    bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
    bmp = scale_bitmap(bmp, 18, 18)
    if bool(parent.parent.parent):
        parent.parent.parent.replay_button.SetBitmap(bmp)
    isReplaying = 0
    #print("Thread destroyed")
class MyPanel(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self,parent,id=-1)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.parent = parent
        self.shouldRun = True
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.bitmap = None

        if shouldUseNamedPipes:
            self.t = threading.Thread(target=changeBitmapWorker_piped, args=(self,))
            self.t.daemon = True
            self.t.start()
        else:
            self.t = threading.Thread(target=changeBitmapWorker, args=(self,))
            self.t.daemon = True
            self.t.start()

        # Variables for rectangle drawing
        self.start_pos = None
        self.current_pos = None
        self.rectangle = wx.Rect()

        # Bind mouse events to the bitmap
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right_down)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)

        #self.Bind(wx.EVT_PAINT, self.on_paint)

    def setXYRotation(self, event):
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Y_ARMED
        global Rotation_3D_X_ARMED

        pos = event.GetPosition()
        clicked_bitmap = event.GetEventObject()

        # Get the underlying image of the clicked bitmap
        image = self.bitmap #clicked_bitmap.GetBitmap().ConvertToImage()

        # Get the image size
        image_width = image.GetWidth()
        image_height = image.GetHeight()

        print("x:", pos.x, " y:", pos.y, " width:", image_width, " height:", image_height)
        # Normalize the click position to a range of -7 to 7 on both axes
        # Old calculation below
        # normalized_x = (pos.x / image_width) * 14 - 7
        # normalized_y = (pos.y / image_height) * 14 - 7
        # New calculation reflects the zoom granularity
        zoom_granularity_value = float(self.parent.parent.zoom_step_input_box.GetValue())
        normalized_x = ((pos.x / image_width) * zoom_granularity_value * 2) - zoom_granularity_value
        normalized_y = ((pos.y / image_height) * zoom_granularity_value * 2) - zoom_granularity_value

        # Print the normalized click position
        print("Normalized Click Position:", normalized_x, normalized_y)
        Rotation_3D_Y_ARMED = 0.0
        Rotation_3D_X_ARMED = 0.0
        Rotation_3D_Y = normalized_x
        Rotation_3D_X = -normalized_y

        print("Normalized Click Position:", Rotation_3D_Y_ARMED, Rotation_3D_X_ARMED, Rotation_3D_Y, Rotation_3D_X)

    def on_mouse_right_down(self, event):
        self.setXYRotation(event)

        event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
        event.SetEventObject(self.parent.parent.rotate_zero_button)
        event.SetId(self.parent.parent.rotate_zero_button.GetId())
        self.parent.parent.rotate_zero_button.GetEventHandler().ProcessEvent(event)

    def on_mouse_left_down(self, event):
        self.start_pos = event.GetPosition()

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.current_pos = event.GetPosition()
            self.rectangle = self.calculate_rectangle()
            self.Refresh()  # Redraw the bitmap with the rectangle

    def calculate_rectangle(self):
        x = min(self.start_pos.x, self.current_pos.x)
        y = min(self.start_pos.y, self.current_pos.y)
        width = abs(self.current_pos.x - self.start_pos.x)
        height = abs(self.current_pos.y - self.start_pos.y)

        return wx.Rect(x, y, width, height)

    def on_paint(self, event):
        if self.bitmap != None:
            dc = wx.BufferedPaintDC(self.bitmap)
            dc.Clear()
            dc.DrawBitmap(self.bitmap.GetBitmap(), 0, 0)

            #if self.start_pos and self.current_pos:
            #    self.draw_rectangle(dc)
        else:
            pass

    def draw_rectangle(self, dc):
        pen = wx.Pen(wx.Colour(255, 0, 0), width=2)
        dc.SetPen(pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(self.rectangle)

    def calculate_midpoint(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2

        midpoint_x = (x1 + x2) / 2
        midpoint_y = (y1 + y2) / 2

        midpoint = (midpoint_x, midpoint_y)

        return midpoint

    def on_mouse_left_up(self, event):
        if self.start_pos and self.current_pos:
            # Print rectangle position and size
            print("Rectangle Position:", self.rectangle.GetPosition())
            print("Rectangle Size:", self.rectangle.GetSize())
            # normalise
            image_size = self.bitmap.GetSize()
            rectangle_width = self.rectangle.GetSize()[0]
            rectangle_height = self.rectangle.GetSize()[1]

            #Below, is OLD zoom_factor
            #zoom_factor = min(image_size[0] / rectangle_width, image_size[1] / rectangle_height)*3
            #Here is the new calculated zoom_factor
            zoom_granularity_value = float(self.parent.parent.zoom_step_input_box.GetValue())
            if rectangle_width <= rectangle_height:
                zoom_delta = zoom_granularity_value / (image_size[0] / rectangle_width)
                zoom_factor = zoom_granularity_value - zoom_delta
            else:
                zoom_delta = zoom_granularity_value / (image_size[1] / rectangle_height)
                zoom_factor = zoom_granularity_value - zoom_delta

            print("zoom_factor:", zoom_factor)
            self.Translation_Z_ARMED = 0.0
            self.Translation_Z = zoom_factor
            print("Translation_Z:" + str(self.Translation_Z))

            # fire slider event
            evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
            evt.SetEventObject(self.parent.parent.zoom_slider)
            evt.SetId(self.parent.parent.zoom_slider.GetId())
            self.parent.parent.zoom_slider.SetValue(int(self.Translation_Z * 100))
            self.parent.parent.zoom_slider.GetEventHandler().ProcessEvent(evt)

            # fire zero zoom button pressed
            event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            event.SetEventObject(self.parent.parent.zoom_zero_button)
            event.SetId(self.parent.parent.zoom_zero_button.GetId())
            self.parent.parent.zoom_zero_button.GetEventHandler().ProcessEvent(event)

            # fire right mouse button on image
            midpoint = self.calculate_midpoint(self.start_pos, self.current_pos)
            print("midpoint", midpoint)
            # event = wx.PyCommandEvent(wx.EVT_RIGHT_DOWN.typeId)
            # event.SetEventObject(self.bitmap)
            # event.SetId(self.bitmap.GetId())
            # event.SetPosition(midpoint)
            # self.bitmap.GetEventHandler().ProcessEvent(event)

            event = wx.MouseEvent(wx.EVT_RIGHT_DOWN.typeId)
            event.SetEventObject(self)#.bitmap)
            event.SetId(self.GetId()) #self.bitmap.GetId())
            point = wx.Point(int(midpoint[0]), int(midpoint[1]))
            event.SetPosition(point)
            self.ProcessEvent(event)

            self.start_pos = None
            self.current_pos = None
            self.Refresh()  # Redraw the bitmap without the rectangle

    def OnExit(self, event):
        self.shouldRun = False
    def OnPaint(self, evt):
        if self.bitmap == None:
            self.current_width, self.current_height = self.GetSize()
            self.resize(self.current_width, self.current_height)
        #    self.bitmap = self.parent.bitmap
        if self.bitmap != None:
            dc = wx.BufferedPaintDC(self)
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0,0)
            if self.start_pos and self.current_pos:
                self.draw_rectangle(dc)
        else:
            pass
    def DeInitialize(self):
        self.shouldRun = False
    def resize(self,width,height):
        self.SetSize(width, height)
        #if is_paused_rendering:
        #    imagePath = get_current_image_path_paused()
        #else:
        #    imagePath = get_current_image_path()
        if is_paused_rendering:
            imagePath = get_current_image_path_f(current_render_frame)
        else:
            current_frame = int(readValue("start_frame"))
            imagePath = get_current_image_path_f(current_frame)

        self.bitmap = wx.Bitmap(imagePath)
        bitmap_width, bitmap_height = self.parent.GetSize()
        tempBitmap = scale_bitmap(self.bitmap, bitmap_width-18, bitmap_height-40)
        if tempBitmap != None and tempBitmap.IsOk():
            self.bitmap = tempBitmap
        self.Refresh()

class render_window(wx.Frame):
    def __init__(self, parent, title):
        global render_frame_window_is_open
        render_frame_window_is_open = True
        self.parent = parent
        super(render_window, self).__init__(parent, title=title, size=(100, 100))
        if should_stay_on_top:
            self.ToggleWindowStyle(wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.Bind(wx.EVT_SIZING, self.OnResize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        #panel = wx.Panel(self)
        self.panel = MyPanel(self)
        self.panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.panel.SetDoubleBuffered(True)
        self.bitmap = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)

    def OnMove(self, evt):
        global renderWindowX, renderWindowY
        x, y = self.GetPosition()
        renderWindowX = x
        renderWindowY = y
        #print("X:"+str(x)+" Y:"+str(y))
    def OnResize(self, evt):
        self.current_width, self.current_height = self.GetSize()
        #aspectRatio = (self.BestSize.Height-18)/(self.BestSize.Width-40)
        #self.current_height = int(aspectRatio*self.current_width)
        self.panel.resize(self.current_width, self.current_height)
        #self.Refresh()
        #print("width=" + str(self.current_width))
        #print("height=" + str(self.current_height))
    def OnErase(self, evt):
        evt.Skip()
    def DrawImage(self):
        self.current_width, self.current_height = self.GetSize()
        self.panel.resize(self.current_width, self.current_height)
        #print("width=" + str(self.current_width))
        #print("height=" + str(self.current_height))
    def CloseNamedPipeThread(self):
        try:
            bufSize = 64 * 1024
            handle = win32file.CreateFile('\\\\.\\pipe\\deforumation_pipe_in', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
            value = [1, "close_thread", 0]
            bytesToSend = pickle.dumps(value)
            win32file.WriteFile(handle, bytesToSend)
            # Need to receive back data to close the write call (but totally discards this)
            #print("AWaiting reply")
            result, data = win32file.ReadFile(handle, bufSize)
            message = data
            while len(data) == bufSize:
                print("More data has to be read (normal pipe async):" + str(len(data)))
                result, data = win32file.ReadFile(handle, bufSize)
                message += data
            #print("Got reply:" + str(message))
        except pywintypes.error as e:
            print("Something went wrong when trying to end the named pipe live view thread")

    def OnExit(self, event):
        global should_render_live
        global render_frame_window_is_open
        #win32file.CloseHandle(current_live_view_pipe)
        #Sending a close to anu live named-pipe thread running
        if shouldUseNamedPipes:
            self.CloseNamedPipeThread()
        self.panel.DeInitialize()
        self.panel.Hide()
        self.panel.Close()
        self.panel.Destroy()
        self.panel = None
        self.parent.framer = None
        self.parent.live_render_checkbox.SetValue(0)
        #print("Closing render window!")
        self.Destroy()
        render_frame_window_is_open = False
        should_render_live = False
        if self.bitmap != None:
            self.bitmap.Destroy()
            self.bitmap = None
        should_render_live = False
        #print("CLOSING, framer.bitmap is:"+ str(self.bitmap))


def record(self, stopped, q):
    # the file name output you want to record into
    filename = "Recording.wav"
    # set the chunk size of 1024 samples
    framesperbuffer = 1024
    # sample format
    FORMAT = pyaudio.paInt16
    # mono, change to 2 if you want stereo
    channels = 1
    # 44100 samples per second
    sample_rate = 44100
    record_seconds = 0.5
    # initialize PyAudio object
    #p = pyaudio.PyAudio()
    frames = []

    voice_detected = 0
    should_begin_recording = False
    showRecordingOnce = False
    while self.is_recording:
        if stopped.wait(timeout=0):
            break
        chunk = q.get()
        vol = max(chunk)
        if vol >= MIN_VOLUME:
            if voice_detected == 0:
                frames = []
                should_begin_recording = True
            voice_detected = 50

        if voice_detected > 0 and should_begin_recording and not showRecordingOnce:
            bmp = wx.Bitmap("./images/record_recording.bmp", wx.BITMAP_TYPE_BMP)
            self.record_button.SetBitmap(bmp)
            showRecordingOnce = True
        if voice_detected > 0 and should_begin_recording:
            data = chunk
            # if you want to hear your voice while recording
            # stream.write(data)
            frames.append(data)
            # TODO: write to file
            #print("O")
            voice_detected = voice_detected -1
        else:
            if should_begin_recording:
                should_begin_recording = False
                showRecordingOnce = False
                wf = wave.open(filename, "wb")
                # set the channels
                wf.setnchannels(channels)
                # set the sample format
                wf.setsampwidth(self.p.get_sample_size(FORMAT))
                # set the sample rate
                wf.setframerate(sample_rate)
                # write the frames as bytes
                wf.writeframes(b"".join(frames))
                # close the file
                wf.close()
                recognizer = sp.Recognizer()
                filename = "./Recording.wav"
                with sp.AudioFile(filename) as source:
                    try:
                        # listen for the data (load audio to memory)
                        audio_data = recognizer.record(source)
                        # recognize (convert from speech to text)
                        text = recognizer.recognize_google(audio_data)
                        zoom_in_word = ['zoom in', 'resume in', 'turn in']
                        zoom_out_word = ['zoom out', 'resume out', 'turn out', 'resume Route', 'turn Route']
                        pan_left_word = ['go left', 'pan left', 'call left', 'turn left', 'time left', 'pin left', 'pin lift', 'pin left', 'pem left', 'pen left', 'pam left']
                        pan_right_word = ['go right', 'pan right', 'go Wright', 'call right', 'call Wright', 'turn right', 'turn brigh', 'pin right', 'time right', 'pin right', 'pin right', 'pem right', 'pen right', 'pam right']
                        pan_up_word = ['go up', 'turn up', 'call up', 'open up', 'pan up', 'pin up', 'pem up', 'pen up', 'pam up']
                        pan_down_word = ['go down', 'turn down', 'call down', 'pan down', 'pin down', 'pin down', 'pem down', 'pen down', 'pam down']
                        rotate_left_word = ['rotate left', 'rotate lift', 'rooted left', 'rooted lift']
                        rotate_right_word = ['rotate right', 'rotate Wright', 'rotate bright', 'rooted right']
                        rotate_up_word = ['rotate up', 'rooted up']
                        rotate_down_word = ['rotate down', 'rooted down']
                        tilt_left_word = ['tilt left', 'tilt lift']
                        tilt_right_word = ['tilt right', 'tilt Wright', 'tilt bright']
                        add_to_sentence = 'add'
                        cancel_voice_sentence = 'cancel'
                        reset_panning = ['reset pan', 'reset plan']
                        reset_zoom = ['reset zoom', 'reset resume', 'reset turn']
                        reset_rotation = ['reset rotation']
                        reset_tilt = ['reset tilt']
                        print("Got the sentence:\"" + str(text) + "\"")
                        #self.rotation_3d_x_right_button
                        #self.rotation_3d_y_up_button

                        if cancel_voice_sentence in text:
                            print("Canceling the spoken sentence!")
                            pass
                        elif text.startswith(tuple(reset_tilt)):
                            print("Resetting tilt")
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.rotation_3d_z_left_button)
                            evt.SetId(self.rotation_3d_z_left_button.GetId())
                            self.rotation_3d_z_left_button.GetEventHandler().ProcessEvent(evt)

                        elif text.startswith(tuple(reset_rotation)):
                            print("Resetting rotation")
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.rotation_3d_x_left_button)
                            evt.SetId(self.rotation_3d_x_left_button.GetId())
                            self.rotation_3d_x_left_button.GetEventHandler().ProcessEvent(evt)
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.rotation_3d_y_up_button)
                            evt.SetId(self.rotation_3d_y_up_button.GetId())
                            self.rotation_3d_y_up_button.GetEventHandler().ProcessEvent(evt)

                        elif text.startswith(tuple(reset_panning)):
                            print("Resetting panning")
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.transform_y_down_button)
                            evt.SetId(self.transform_y_down_button.GetId())
                            self.transform_y_down_button.GetEventHandler().ProcessEvent(evt)
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.transform_x_left_button)
                            evt.SetId(self.transform_x_left_button.GetId())
                            self.transform_x_left_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(reset_zoom)):
                            print("Resetting zoom")
                            evt = wx.PyCommandEvent(wx.EVT_RIGHT_UP.typeId)
                            evt.SetEventObject(self.zoom_slider)
                            evt.SetId(self.zoom_slider.GetId())
                            self.zoom_slider.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(tilt_left_word)):
                            print("Tilting left")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_z_left_button)
                            evt.SetId(self.rotation_3d_z_left_button.GetId())
                            self.rotation_3d_z_left_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(tilt_right_word)):
                            print("Tilting right")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_z_right_button)
                            evt.SetId(self.rotation_3d_z_right_button.GetId())
                            self.rotation_3d_z_right_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(rotate_left_word)):
                            print("Rotate left")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_x_left_button)
                            evt.SetId(self.rotation_3d_x_left_button.GetId())
                            self.rotation_3d_x_left_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(rotate_right_word)):
                            print("Rotate right")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_x_right_button)
                            evt.SetId(self.rotation_3d_x_right_button.GetId())
                            self.rotation_3d_x_right_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(rotate_up_word)):
                            print("Rotate up")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_y_up_button)
                            evt.SetId(self.rotation_3d_y_up_button.GetId())
                            self.rotation_3d_y_up_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(rotate_down_word)):
                            print("Rotate down")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.rotation_3d_y_down_button)
                            evt.SetId(self.rotation_3d_y_down_button.GetId())
                            self.rotation_3d_y_down_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(pan_left_word)):
                            print("Panning left")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.transform_x_left_button)
                            evt.SetId(self.transform_x_left_button.GetId())
                            self.transform_x_left_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(pan_right_word)):
                            print("Panning right")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.transform_x_right_button)
                            evt.SetId(self.transform_x_right_button.GetId())
                            self.transform_x_right_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(pan_up_word)):
                            print("Panning up")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.transform_y_upp_button)
                            evt.SetId(self.transform_y_upp_button.GetId())
                            self.transform_y_upp_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(pan_down_word)):
                            print("Panning down")
                            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
                            evt.SetEventObject(self.transform_y_down_button)
                            evt.SetId(self.transform_y_down_button.GetId())
                            self.transform_y_down_button.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(zoom_in_word)):
                            #self.zoom_slider.SetValue(self.zoom_slider.GetValue() + 20)
                            words = text.split(' ')
                            print("Zooming In")
                            index=0
                            if len(words) >= index+2:
                                #print(words[index+2])
                                evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
                                evt.SetEventObject(self.zoom_slider)
                                evt.SetId(self.zoom_slider.GetId())
                                self.zoom_slider.SetValue(self.zoom_slider.GetValue() + int(words[index+2]))
                                #print(str(self.zoom_slider.GetValue()))
                                self.zoom_slider.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(tuple(zoom_out_word)):
                            #self.zoom_slider.SetValue(self.zoom_slider.GetValue() + 20)
                            words = text.split(' ')
                            print("Zooming Out")
                            index=0
                            if len(words) >= index+2:
                                #print(words[index+2])
                                evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
                                evt.SetEventObject(self.zoom_slider)
                                evt.SetId(self.zoom_slider.GetId())
                                self.zoom_slider.SetValue(self.zoom_slider.GetValue() - int(words[index+2]))
                                #print(str(self.zoom_slider.GetValue()))
                                self.zoom_slider.GetEventHandler().ProcessEvent(evt)
                        elif text.startswith(add_to_sentence):
                            self.positive_prompt_input_ctrl_2.SetValue(self.positive_prompt_input_ctrl_2.GetValue() + ", " + text[len(add_to_sentence):])
                            self.saveCurrentPrompt("P")
                            self.saveCurrentPrompt("N")
                            # Arrange the possitive prompts according to priority (now for some lazy programing):
                            positive_prio = {
                                int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                                int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                                int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                                int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                            sortedDict = sorted(positive_prio.items())
                            # totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
                            totalPossitivePromptString = sortedDict[0][1]
                            if sortedDict[1][1] != "":
                                totalPossitivePromptString += "," + sortedDict[1][1]
                            if sortedDict[2][1] != "":
                                totalPossitivePromptString += "," + sortedDict[2][1]
                            if sortedDict[3][1] != "":
                                totalPossitivePromptString += "," + sortedDict[3][1]

                            self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
                            self.writeValue("negative_prompt",
                                            self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
                            self.writeValue("prompts_touched", 1)
                            self.SetLabel(windowlabel + " -- Prompts saved to mediator, specifically to frame " + str(
                            self.readValue("start_frame")))
                        else:
                            self.positive_prompt_input_ctrl_2.SetValue(text)
                            self.saveCurrentPrompt("P")
                            self.saveCurrentPrompt("N")
                            # Arrange the possitive prompts according to priority (now for some lazy programing):
                            positive_prio = {
                                int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                                int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                                int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                                int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                            sortedDict = sorted(positive_prio.items())
                            # totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
                            totalPossitivePromptString = sortedDict[0][1]
                            if sortedDict[1][1] != "":
                                totalPossitivePromptString += "," + sortedDict[1][1]
                            if sortedDict[2][1] != "":
                                totalPossitivePromptString += "," + sortedDict[2][1]
                            if sortedDict[3][1] != "":
                                totalPossitivePromptString += "," + sortedDict[3][1]

                            self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
                            self.writeValue("negative_prompt",
                                            self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
                            self.writeValue("prompts_touched", 1)
                            self.SetLabel(windowlabel + " -- Prompts saved to mediator, specifically to frame " + str(
                            self.readValue("start_frame")))
                    except Exception as e:
                        #Normally lands here if no valid words could be recognized
                        print(str(e))
                bmp = wx.Bitmap("./images/record_on.bmp", wx.BITMAP_TYPE_BMP)
                self.record_button.SetBitmap(bmp)
    #print("Done recording")
def listen(self, stopped, q):
    #FORMAT = pyaudio.paInt16
    stream = self.p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
    )

    while self.is_recording:
        if stopped.wait(timeout=0):
            break
        try:
            q.put(array('h', stream.read(CHUNK_SIZE)))
        except queue.Full:
            pass  # discard
    #print("Exiting Recorder listen")

"""def startRecording(self):
    # the file name output you want to record into
    filename = "Recording.wav"
    # set the chunk size of 1024 samples
    chunk = 1024
    # sample format
    FORMAT = pyaudio.paInt16
    # mono, change to 2 if you want stereo
    channels = 1
    # 44100 samples per second
    sample_rate = 44100
    record_seconds = 0.5
    # initialize PyAudio object
    p = pyaudio.PyAudio()
    # open stream object as input & output
    stream = p.open(format=FORMAT,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=True,
                    frames_per_buffer=chunk)
    frames = []
    print("Recording...")
    while(self.is_recording):
        for i in range(int(sample_rate / chunk * record_seconds)):
            data = stream.read(chunk)
            # if you want to hear your voice while recording
            # stream.write(data)
            frames.append(data)
    print("Finished recording.")
    # stop and close stream
    stream.stop_stream()
    stream.close()
    # terminate pyaudio object
    p.terminate()
    # save audio file
    # open the file in 'write bytes' mode
    wf = wave.open(filename, "wb")
    # set the channels
    wf.setnchannels(channels)
    # set the sample format
    wf.setsampwidth(p.get_sample_size(FORMAT))
    # set the sample rate
    wf.setframerate(sample_rate)
    # write the frames as bytes
    wf.writeframes(b"".join(frames))
    # close the file
    wf.close()
    recognizer = sp.Recognizer()
    filename = "./Recording.wav"
    with sp.AudioFile(filename) as source:
        # listen for the data (load audio to memory)
        audio_data = recognizer.record(source)
        # recognize (convert from speech to text)
        text = recognizer.recognize_google(audio_data)
        self.positive_prompt_input_ctrl.SetValue(text)

        self.saveCurrentPrompt("P")
        self.saveCurrentPrompt("N")
        # Arrange the possitive prompts according to priority (now for some lazy programing):
        positive_prio = {int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                         int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                         int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                         int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
        sortedDict = sorted(positive_prio.items())
        # totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
        totalPossitivePromptString = sortedDict[0][1]
        if sortedDict[1][1] != "":
            totalPossitivePromptString += "," + sortedDict[1][1]
        if sortedDict[2][1] != "":
            totalPossitivePromptString += "," + sortedDict[2][1]
        if sortedDict[3][1] != "":
            totalPossitivePromptString += "," + sortedDict[3][1]

        self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
        self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
        self.writeValue("prompts_touched", 1)
        self.SetLabel(windowlabel + " -- Prompts saved to mediator, specifically to frame " + str(self.readValue("start_frame")))"""

class Mywin(wx.Frame):
    def loadPredefinedMotions(self, filterFPS = None, filterRange = None):
        #ANIMATED MOTION "BUTTONS"
        if self.p2 != None:
            self.p2.Destroy()

        self.p2 = wx.lib.scrolledpanel.ScrolledPanel(self.panel, -1, size=(602, 110), pos=(int(screenWidth / 2) + 54, 304),style=wx.SIMPLE_BORDER)
        self.p2.SetupScrolling()
        self.p2.SetBackgroundColour('#FFFFFF')
        self.bSizer = wx.BoxSizer(wx.HORIZONTAL)

        #PRE DEFINED MOTIONS
        self.predefined_motions_name = []
        predefined_motions_gif = []
        self.predefined_motions_line = []
        self.predefined_motions_fps_line = []
        #self.predefined_motions_range_line = []
        self.ctrl = []
        self.anim = []

        self.fps_filters = []
        self.fps_filters.append("ALL AND ANY FPS")

        self.range_filters = []
        self.range_filters.append("Any Range")

        self.predefined_motions_fps_line.append(-2)
        self.is_recording = False

        if os.path.isfile(deforumationPredefinedMotionPathSettings):
            deforumFile = open(deforumationPredefinedMotionPathSettings, 'r')
            lines = deforumFile.readlines()
            deforumFile.close()
            motion_index = 0
            for motion in lines:
                if motion.startswith("#") or len(motion) < 5:
                    continue
                motionNameStart = 0
                motionNameEnd = motion.find(",")
                motionName = motion[motionNameStart:motionNameEnd]

                countParantheses = motionName.count('(')
                motionRangeName = "Not Applicable"
                if countParantheses == 2:
                    motionNameRangeIndexStart = motionName.rfind('(')
                    motionNameRangeIndexEnd = motionName.rfind(')')
                    motionRangeName = motionName[motionNameRangeIndexStart+1:motionNameRangeIndexEnd]
                    if not (str(motionRangeName)) in self.range_filters:
                        self.range_filters.append(motionRangeName)

                motionGifEnd = motion[motionNameEnd+1:].find(",")
                motionGif = motion[motionNameEnd+1:motionGifEnd+motionNameEnd+1].lstrip().rstrip()
                predefined_motions_gif.append(motionGif)

                FPS_end = motion[motionGifEnd+motionNameEnd+1+1:].find(',')
                FPS = int(motion[motionGifEnd+motionNameEnd+1+1:motionGifEnd+motionNameEnd+1+1+FPS_end].strip(' '))
                if FPS == -1:
                    if countParantheses == 1:
                        motionNameRangeIndexStart = motionName.rfind('(')
                        motionNameRangeIndexEnd = motionName.rfind(')')
                        motionRangeName = motionName[motionNameRangeIndexStart + 1:motionNameRangeIndexEnd]
                        if not (str(motionRangeName)) in self.range_filters:
                            self.range_filters.append(motionRangeName)
                    if not "FPS INDEPENDENT" in self.fps_filters:
                        self.fps_filters.append("FPS INDEPENDENT")
                        self.predefined_motions_fps_line.append(-1)
                else:
                    if not (str(FPS)+" FPS") in self.fps_filters:
                        self.fps_filters.append(str(FPS)+" FPS")
                        self.predefined_motions_fps_line.append(FPS)
                if ((filterFPS == FPS) or (filterFPS == -2) or (filterFPS == None)) and ((filterRange == "Any Range") or (filterRange == motionRangeName) or (filterFPS == None)):
                    self.predefined_motions_line.append(motion[motionGifEnd+1+motionNameEnd+1:].strip("\n").strip(" "))
                    self.predefined_motions_name.append(motionName)
                    if os.path.isfile(motionGif):
                        #self.anim.append(Animation(motionGif))  # , type=wx.adv.ANIMATION_TYPE_GIF)
                        animation = Animation(motionGif)
                        #self.ctrl.append(AnimationCtrl(self.p2, -1, self.anim[motion_index], pos=(motion_index * self.anim[motion_index].GetSize()[0] + motion_index * 20, 10)))
                        self.ctrl.append(AnimationCtrl(self.p2, -1, animation, pos=(motion_index * animation.GetSize()[0] + motion_index * 20, 10)))
                        self.ctrl[motion_index].SetLabel("IMAGE_MOTION_"+str(motion_index))
                        self.ctrl[motion_index].Bind(wx.EVT_LEFT_UP, self.OnClicked)
                        self.ctrl[motion_index].Bind(wx.EVT_RIGHT_UP, self.OnClicked)
                        self.ctrl[motion_index].SetToolTip(motionName)
                        self.ctrl[motion_index].Play()
                        #anImage = self.anim[motion_index].GetFrame(0)
                        #x = int(self.anim[motion_index].GetSize()[0])
                        #y = int(self.anim[motion_index].GetSize()[1])
                        anImage = animation.GetFrame(0)
                        x = int(animation.GetSize()[0])
                        y = int(animation.GetSize()[1])
                        anImage.SetRGB(wx.Rect(0, 0, x, 5), 255, 0, 0)
                        anImage.SetRGB(wx.Rect(0, y-5, x, 5), 255, 0, 0)
                        anImage.SetRGB(wx.Rect(0, 0, 5, y), 255, 0, 0)
                        anImage.SetRGB(wx.Rect(x-5, 0, 5, y), 255, 0, 0)
                        self.ctrl[motion_index].SetInactiveBitmap(anImage.ConvertToBitmap())
                        #wx.Image.ConvertToBitmap()
                        #anImage = aBitmap.ConvertToImage()
                        #imgColors = anImage.GetRGB()
                        #wx.Image.SetRGB(imgColors)
                        #self.ctrl[motion_index].GetAnimation()
                        self.bSizer.Add(self.ctrl[motion_index], 0, wx.ALL, 5)
                    else:
                        #self.anim.append(Animation(wx.Animation))
                        self.ctrl.append(AnimationCtrl(self.p2))
                    motion_index += 1
        self.p2.SetSizer(self.bSizer)

        if self.predefined_motion_choice == None:
            self.predefined_motion_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(int(screenWidth / 2) + 422, 59),size=(240,40), choices=self.predefined_motions_name, style=0, name="predefinedmotion")
        else:
            self.predefined_motion_choice.SetItems(self.predefined_motions_name)
        self.predefined_motion_choice.Bind(wx.EVT_CHOICE, self.OnMotionChoice)
        self.predefined_motion_choice.SetToolTip("Here you can choose a pre-defined motion, which then can be triggered by pushing the \"Use predefined motion\"-button. You can also choose to use the same motions below, by clicking the animated GIFs.")

        #Create a dropdown box with different FPS filtering values that was taken from available names
        if self.predefined_motion_fps_choice == None:
            self.predefined_motion_fps_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(int(screenWidth / 2) + 13, 280), size=(140,40), choices=self.fps_filters, style=0, name="FPS Filter")
        else:
            self.predefined_motion_fps_choice.SetItems(self.fps_filters)
        self.predefined_motion_fps_choice.Bind(wx.EVT_CHOICE, self.OnFPSChoice)

        #Create a dropdown box with different Range filtering values that was taken from available range names in pre-defined motion file
        if self.predefined_motion_range_choice == None:
            self.predefined_motion_range_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(int(screenWidth / 2) + 160, 280), size=(140,40), choices=self.range_filters, style=0, name="RANGE Filter")
        else:
            self.predefined_motion_range_choice.SetItems(self.range_filters)
        self.predefined_motion_range_choice.Bind(wx.EVT_CHOICE, self.OnRangeChoice)


    def __init__(self, parent, title):
        #global pmob
        #global pstb
        global ppb
        global parameter_container
        super(Mywin, self).__init__(parent, title=title, size=(screenWidth, screenHeight))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.framer = None

        #Event dictionary helper
        self.eventDict = {}
        for evtname in dir(wx):
            if evtname.startswith('EVT_'):
                evt = getattr(wx, evtname)
                if isinstance(evt, wx.PyEventBinder):
                    self.eventDict[evt.typeId] = evtname

        self.p = pyaudio.PyAudio()
        #print(str(pyo.pa_list_devices()))

        # expand key frame strings to values
        #component_names = deforum_args.get_component_names()
        #args_dict = {component_names[i]:i for i in range(0, len(component_names))}
        #args, anim_args, parseq_args = deforum_args.process_args(args_dict)
        #keys = animation_key_frames.DeformAnimKeys(anim_args, -1)
        #self.parseq_keys = parseq_adapter.ParseqAnimKeys(parseq_args, anim_args)
        #data1 = pickle.dumps(self.parseq_keys)
        #print(str(self.parseq_keys.translation_x_series))
        #writeValue("parseq_keys", self.parseq_keys)
        #writeValue("use_parseq", 0)
        #self.StartMediaPlayback("out.mp4", "wxWMP10MediaBackend")
        #Positive Prompt
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0, 0))
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer7 = wx.BoxSizer(wx.VERTICAL)
        sizer8 = wx.BoxSizer(wx.VERTICAL)
        sizer2_bd = wx.BoxSizer(wx.HORIZONTAL)
        self.positivePromtText = wx.StaticText(self.panel, label="Positive prompt:", size=(200, 25))
        font = self.positivePromtText.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.positivePromtText.SetFont(font)
        sizer.Add(self.positivePromtText, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_prio = wx.TextCtrl(self.panel, size=(20,20))
        self.positive_prompt_input_ctrl_prio.SetValue("1")
        self.positive_prompt_input_ctrl_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")
        sizer2.Add(self.positive_prompt_input_ctrl_prio, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_hide_box = wx.CheckBox(self.panel, id=101, label="Hide")
        self.positive_prompt_input_ctrl_hide_box.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer2.Add(self.positive_prompt_input_ctrl_hide_box, 0, wx.ALL, 0)
        #sizer.Add(sizer2, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_before_deforumation_box = wx.CheckBox(self.panel, id=5675, label="Add before Deforum prompt.")
        self.positive_prompt_input_ctrl_before_deforumation_box.SetToolTip("If \"Use Deforumation prompt scheduling\" is un-checked, Deforum's prompt schedule will be used. If this box is checked, the prompt written here will be added in front of Deforum's prompt.")
        self.positive_prompt_input_ctrl_before_deforumation_box.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        sizer2.Add(self.positive_prompt_input_ctrl_before_deforumation_box, 0, wx.LEFT, 20)
        #sizer.Add(sizer2, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_after_deforumation_box = wx.CheckBox(self.panel, id=657, label="Add after Deforum prompt.")
        self.positive_prompt_input_ctrl_after_deforumation_box.SetToolTip("If \"Use Deforumation prompt scheduling\" is un-checked, Deforum's prompt schedule will be used. If this box is checked, the prompt written here will be added after Deforum's prompt.")
        self.positive_prompt_input_ctrl_after_deforumation_box.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        sizer2.Add(self.positive_prompt_input_ctrl_after_deforumation_box, 0, wx.LEFT, 20)
        sizer.Add(sizer2, 0, wx.ALL|wx.EXPAND, 0)


        self.positive_prompt_input_ctrl = wx.TextCtrl(self.panel, id=9999, style=wx.TE_MULTILINE, size=(int(screenWidth/2),100))
        self.positive_prompt_input_ctrl.SetToolTip("This is the main positive prompt window. When \"Save Prompts\" is pushed, this prompt will belong to the current image frame.")
        sizer.Add(self.positive_prompt_input_ctrl, 0, wx.ALL , 0)
        #self.positive_prompt_input_ctrl.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)
        self.positive_prompt_input_ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
        self.positive_prompt_input_ctrl.Bind(wx.EVT_KEY_UP, self.OnKeyEvent_Empty)

        self.positive_prompt_input_ctrl_2_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer3.Add(self.positive_prompt_input_ctrl_2_prio, 0, wx.ALL|wx.EXPAND, 0)
        self.positive_prompt_input_ctrl_2_prio.SetValue("2")
        self.positive_prompt_input_ctrl_2_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_2 = wx.CheckBox(self.panel, id=102, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_2.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_2.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer3.Add(self.positive_prompt_input_ctrl_hide_box_2, 0, wx.ALL, 0)
        sizer.Add(sizer3, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_2 = wx.TextCtrl(self.panel, id=9999, style=wx.TE_MULTILINE, size=(int(screenWidth/2),50))
        self.positive_prompt_input_ctrl_2.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_2, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_2.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
        self.positive_prompt_input_ctrl_2.Bind(wx.EVT_KEY_UP, self.OnKeyEvent_Empty)
        #self.positive_prompt_input_ctrl_2.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)

        self.positive_prompt_input_ctrl_3_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer4.Add(self.positive_prompt_input_ctrl_3_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_3_prio.SetValue("3")
        self.positive_prompt_input_ctrl_3_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_3 = wx.CheckBox(self.panel, id=103, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_3.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_3.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer4.Add(self.positive_prompt_input_ctrl_hide_box_3, 0, wx.ALL, 0)
        sizer.Add(sizer4, 0, wx.ALL, 0)


        self.positive_prompt_input_ctrl_3 = wx.TextCtrl(self.panel, id=9999, style=wx.TE_MULTILINE, size=(int(screenWidth/2),50))
        self.positive_prompt_input_ctrl_3.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_3, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_3.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
        self.positive_prompt_input_ctrl_3.Bind(wx.EVT_KEY_UP, self.OnKeyEvent_Empty)
        #self.positive_prompt_input_ctrl_3.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)

        self.positive_prompt_input_ctrl_4_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer5.Add(self.positive_prompt_input_ctrl_4_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_4_prio.SetValue("4")
        self.positive_prompt_input_ctrl_4_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_4 = wx.CheckBox(self.panel, id=104, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_4.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_4.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer5.Add(self.positive_prompt_input_ctrl_hide_box_4, 0, wx.ALL, 0)
        sizer.Add(sizer5, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_4 = wx.TextCtrl(self.panel, id=9999, style=wx.TE_MULTILINE, size=(int(screenWidth/2),50))
        self.positive_prompt_input_ctrl_4.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_4, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_4.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
        self.positive_prompt_input_ctrl_4.Bind(wx.EVT_KEY_UP, self.OnKeyEvent_Empty)
        #self.positive_prompt_input_ctrl_4.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)

        #TURN OFF TOOLTIP
        self.turn_off_tooltip_button = wx.Button(self.panel, label="Turn off tooltips", pos=(int(screenWidth / 2) + 140+120, 10), size=(100,16))
        self.turn_off_tooltip_button.SetToolTip("This will turn off tooltip of all components.")
        self.turn_off_tooltip_button.Bind(wx.EVT_BUTTON, self.OnClicked)


        #Should show/hide Total Recall box?
        self.hide_totalrecall_box_Checkbox = wx.CheckBox(self.panel, label="Hide Total Recall box", pos=(trbX+300+120, 10))
        self.hide_totalrecall_box_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #Should show/hide PARSEQ bnox?
        self.hide_parseq_box_Checkbox = wx.CheckBox(self.panel, label="Hide PARSEQ box", pos=(trbX+460+120, 10))
        self.hide_parseq_box_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #Should use Deforum prompt scheduling?
        self.shouldUseDeforumPromptScheduling_Checkbox = wx.CheckBox(self.panel, label="Use Deforumation prompt scheduling", pos=(trbX+600+120, 10))
        self.shouldUseDeforumPromptScheduling_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #Stay On Top
        self.stayOnTop_Checkbox = wx.CheckBox(self.panel, label="Stay on top", pos=(trbX+1130+80, 10))
        self.stayOnTop_Checkbox.SetToolTip("This will keep Deforumation and the Live Render window on top, if checked.")
        self.stayOnTop_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #Negative Prompt
        self.negativePromtText = wx.StaticText(self.panel, label="Negative prompt:")
        font = self.negativePromtText.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.negativePromtText.SetFont(font)
        sizer6.Add(self.negativePromtText, 5, wx.ALL | wx.EXPAND, 0)
        sizer6.AddSpacer(5)
        sizer7.AddSpacer(5)
        self.negative_prompt_input_ctrl_hide_box = wx.CheckBox(self.panel, id=105, label="Hide")
        self.negative_prompt_input_ctrl_hide_box.SetToolTip("Minimize or maximize this prompt window.")
        self.negative_prompt_input_ctrl_hide_box.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer7.Add(self.negative_prompt_input_ctrl_hide_box, 0, wx.ALL, 0)
        sizer6.Add(sizer7, 0, wx.ALL, 0)
        sizer.Add(sizer6, 0, wx.ALL, 0)


        self.negative_prompt_input_ctrl = wx.TextCtrl(self.panel, id=9999, style=wx.TE_MULTILINE, size=(int(screenWidth/2),100))
        self.negative_prompt_input_ctrl.SetToolTip("This is the negative prompt window. When \"Save Prompts\" is pushed, this prompt will belong to the current image frame.")
        sizer.Add(self.negative_prompt_input_ctrl, 0, wx.ALL, 0)
        self.negative_prompt_input_ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyEvent)
        self.negative_prompt_input_ctrl.Bind(wx.EVT_KEY_UP, self.OnKeyEvent_Empty)
        #self.negative_prompt_input_ctrl.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)

        #if os.path.isfile(deforumationSettingsPath):
        #    self.negative_prompt_input_ctrl.SetValue(promptfileRead.readline())
        #    promptfileRead.close()

        self.panel.SetSizer(sizer)
        #SHOW LIVE RENDER CHECK-BOX
        self.live_render_checkbox = wx.CheckBox(self.panel, label="LIVE RENDER", pos=(trbX+1130-340, tbrY-110))
        self.live_render_checkbox.SetToolTip("Shows another window, that displays the current frame that is being generated, or if in paused mode, the frame choosen with the \"frame picker input box\".")
        self.live_render_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #TURN ON/OFF OPTICAL FLOW
        self.opticalflow_checkbox = wx.CheckBox(self.panel, label="Optical flow on/off", pos=(trbX+1130-320, tbrY-74))
        self.opticalflow_checkbox.SetToolTip("When checked, uses the \"Coherence\\Optical flow cadence & Optical flow generation\", else None is used")
        self.opticalflow_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        self.opticalflow_checkbox.SetValue(True)
        #SET CADENCE FLOW FACTOR INPUT BOX
        self.cadence_flow_factor_box = wx.TextCtrl(self.panel, 1241, size=(28,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1130-320, tbrY-54))
        self.cadence_flow_factor_box.SetToolTip("This is the cadence flow factor that will be used if Optical flow is turned on. Press ENTER to save.")
        self.cadence_flow_factor_box.SetLabel("1")
        self.cadence_flow_factor_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1241)
        #SET GENERATION FLOW FACTOR INPUT BOX
        self.generation_flow_factor_box = wx.TextCtrl(self.panel, 1242, size=(28,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1130-290, tbrY-54))
        self.generation_flow_factor_box.SetToolTip("This is the generation flow factor that will be used if Optical flow is turned on. Press ENTER to save.")
        self.generation_flow_factor_box.SetLabel("1")
        self.generation_flow_factor_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1242)

        #OFF GRID BUTTON FOR KEYBOARD INPUT
        #self.off_grid_input_box = wx.Button(panel, label="", pos=(-1000, -1000))
        self.off_grid_input_box = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(1, 1), pos=(-100,-100))
        #self.off_grid_button.Bind(wx.EVT_BUTTON, self.OnClicked)

        #SHOW CURRENT IMAGE, BUTTON
        self.show_current_image = wx.Button(self.panel, label="Show current image", pos=(trbX+992-340, tbrY-110))
        self.show_current_image.SetToolTip("This will display the current (or the latest) image that Deforum is rendering. This can change during a render or by using the \"Set current image\"-button.")
        self.show_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)
        #REWIND BUTTTON
        bmp = wx.Bitmap("./images/left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1000-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_button.SetToolTip("Steps one image backwards dependent on the frame number currently set in the \"frame picker input box\".")
        self.rewind_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_button.SetLabel("REWIND")
        #REWIND CLOSEST BUTTTON
        bmp = wx.Bitmap("./images/rewind_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_closest_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+970-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_closest_button.SetToolTip("Tries to find the last saved prompt starting from the frame number set in the \"frame picker input box\".")
        self.rewind_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_closest_button.SetLabel("REWIND_CLOSEST")
        #SET CURRENT FRAME INPUT BOX
        self.frame_step_input_box = wx.TextCtrl(self.panel, 2, size=(48,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1032-340, tbrY-74))
        self.frame_step_input_box.SetToolTip("This is the \"frame picker input box\", which is used to navigate to a certain frame, or to show the current frame that is being generated (when pushing \"Show current frame\"). You can enter a frame number and then press Return in order to jump to a frame.")
        self.frame_step_input_box.SetLabel("0")
        self.frame_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=2)
        #FORWARD BUTTTON
        bmp = wx.Bitmap("./images/right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1080-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_button.SetToolTip("Steps one image forwards dependent on the frame number currently set in the \"frame picker input box\".")
        self.forward_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_button.SetLabel("FORWARD")
        #FORWARD CLOSEST BUTTTON
        bmp = wx.Bitmap("./images/forward_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_closest_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1110-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_closest_button.SetToolTip("Tries to find the next saved prompt starting from the frame number set in the \"frame picker input box\".")
        self.forward_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_closest_button.SetLabel("FORWARD_CLOSEST")
        #SET CURRENT IMAGE, BUTTON
        self.set_current_image = wx.Button(self.panel, label="Set current image", pos=(trbX+998-340, tbrY-40))
        self.set_current_image.SetToolTip("This will force the current image to be the number given in the \"frame picker input box\". This will also instruct Deforum to use this as it's current frame. After rewinding or forwarding, it is neccessary to push \"Set current image\" if you want Deforum to know that this the new starting position. All prompts that have been saved on a time frame later than this, will be deleted.")
        self.set_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)

        img = wx.Image(256, 256)
        self.bitmap = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(img), pos=(trbX + 650 +340, tbrY - 100))
        self.bitmap.SetToolTip("This is a preview window, that will only update to the current image through using the \"Show current frame\"-button, or by using the controls for rewinding or forwarding.")


        # Variables for rectangle drawing
        self.start_pos = None
        self.current_pos = None
        self.rectangle = wx.Rect()

        # Bind mouse events to the bitmap
        self.bitmap.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right_down)
        self.bitmap.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.bitmap.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
        self.bitmap.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.bitmap.Bind(wx.EVT_PAINT, self.on_paint)

        #CREATE AND LOAD PRE-DEFINED MOTIONS
        self.p2 = None
        self.predefinedMotions = wx.StaticBox(self.panel, id=wx.ID_ANY, label='Predefined Motions', size=(300, 103), pos=(int(screenWidth / 2) + 416, 38))  # orient=wx.HORIZONTAL)
        self.predefined_motion_fps_choice = None
        self.predefined_motion_range_choice = None
        self.predefined_motion_choice = None
        self.loadPredefinedMotions()
        self.predefined_motion_choice.SetSelection(0)
        self.predefined_motion_fps_choice.SetSelection(0)
        self.predefined_motion_range_choice.SetSelection(0)

        #USE PRE-DEFINED MOTION BUTTON
        self.use_predefined_motion_button = wx.Button(self.panel, label="Use predefined motion", pos=(int(screenWidth / 2) + 422, 88))
        self.use_predefined_motion_button.SetToolTip("This will use the predefined motion specified in the \"Predefined Motions\" drop down box.")
        self.use_predefined_motion_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.use_predefined_motion_button.SetToolTip("Pushing this button, will apply the predefined motion (if not TotalRecall is being used and is active)")

        #SHOULD USE TOTAL RECALL
        self.create_gif_animation_checkbox = wx.CheckBox(self.panel, label="Create pre-defined motion", pos=(int(screenWidth / 2) + 422, 116))
        self.create_gif_animation_checkbox.SetToolTip("When activated, right-clicking the replay-button create a pre-defined motion using every frame's motion status. If left clicking the replay-button when this checkbox is checked, it will create a pre-defined motion with your currently set motion values. The GIF animation will be created in the folder: " + str(deforumationPredefinedMotionPathSettings))
        self.create_gif_animation_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)


        #####################################################
        self.audioSettingsField = wx.StaticBox(self.panel, id=wx.ID_ANY, label='Audio Playback Settings', size=(400, 90), pos=(int(screenWidth / 2) + 14, 38))  # orient=wx.HORIZONTAL)
        #FFMPEG PATH
        self.ffmpeg_path_input_box = wx.TextCtrl(self.panel, size=(200,20), pos=(int(screenWidth/2)+20, 60))
        self.ffmpeg_path_input_box.SetToolTip("Select path to ffmpeg. If you have ffmpeg as part of the environment, no path needs to be set.")
        self.ffmpeg_path_input_box.SetHint("<Path to ffmpeg executable>")
        #AUDIO PATH
        #self.audio_path_input_box = wx.TextCtrl(self.panel, size=(180,20), pos=(int(screenWidth/2)+20, 61))
        #self.audio_path_input_box.SetToolTip("Path to audio file.")
        #self.audio_path_input_box.SetHint("<Path to audio file>")
        #AUDIO PATH 2
        self.audio_path2_input_box =wx.FilePickerCtrl(self.panel, size=(280,50), pos=(int(screenWidth/2)+20, 76), message="Select audio file")
        self.audio_path2_input_box.SetPath("<Path to audio file>")
        self.audio_path2_input_box.SetToolTip("Select an audio file that will be used when Replaying.")
        #COMBOBOX FOR CHOOSING A Backend for media playing
        backends = ['wxAMMediaBackend', 'wxMCIMediaBackend', 'wxQTMediaBackend', 'wxGStreamerMediaBackend', 'wxRealPlayerMediaBackend', 'wxWMP10MediaBackend']
        self.backend_chooser_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(int(screenWidth/2)+224, 59),size=(180,40), choices=backends, style=0, name="backends")
        self.backend_chooser_choice.SetToolTip("wxQTMediaBackend is for MAC\nwxGStreamerMediaBackend is for UNIX\nwxWMP10MediaBackend is for Windows")
        #self.backend_chooser_choice.Bind(wx.EVT_CHOICE, self.OnComponentChoice)
        self.backend_chooser_choice.SetSelection(5)


        #REPLAY BUTTON
        self.replay_input_box_text = wx.StaticText(self.panel, label="Replay", pos=(trbX+990, tbrY-130))
        self.replay_from_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1030, tbrY-131))
        self.replay_from_input_box.SetToolTip("Replay from this frame.")
        self.replay_from_input_box.SetValue("0")
        self.replay_to_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1090, tbrY-131))
        self.replay_to_input_box.SetToolTip("Replay to this frame.")
        self.replay_to_input_box.SetValue("0")
        self.replay_input_divider_box_text = wx.StaticText(self.panel, label="-", pos=(trbX+1077, tbrY-130))
        bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 18, 18)
        self.replay_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX + 1145, tbrY -135), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.replay_button.SetToolTip("This will replay the range given in the input boxes to the left. Left-clicking this button will replay the range in the Live Render window. Right-clicking this button will use ffmpeg and any audio file to replay the choosen range. If you have activated the \"Create pre-defined motion\"-checkbox, right clicking this button will create a pre-defined motion using every frame's motion status. If you have activated the \"Create pre-defined motion\"-checkbox, left clicking this button will create a pre-defined motion with your currently set motion values.")
        self.replay_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.replay_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.replay_button.SetLabel("REPLAY")

        #REPLAY FPS BOX
        self.fps_input_box_text = wx.StaticText(self.panel, label="fps", pos=(trbX+1180, tbrY-130))
        self.replay_fps_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1200, tbrY-131))
        self.replay_fps_input_box.SetToolTip("When doing a replay, this is the fps that should be used to replay the images. It is mostly used when right-clicking the replay button (using ffmpeg to render a video file).")
        self.replay_fps_input_box.SetValue("30")

        #FIX ASPECT RATIO
        self.fix_aspect_ratio_liverender_button = wx.Button(self.panel, label="Fix Aspect Ratio", pos=(trbX+1244, tbrY-132))
        self.fix_aspect_ratio_liverender_button.SetToolTip("This will adjust the Live Render Windows aspect ratio (using width as the leading value).")
        self.fix_aspect_ratio_liverender_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        #####################################################

        #####################################################
        self.totalRecallSettingsField = wx.StaticBox(self.panel, id=wx.ID_ANY, label='Total Recall', size=(702, 140), pos=(int(screenWidth / 2) + 14, 140))  # orient=wx.HORIZONTAL)
        self.totalRecallSettingsLine = wx.StaticLine(self.panel, size=(702, 2), id=wx.ID_ANY, style = wx.LI_HORIZONTAL, pos=(int(screenWidth / 2) + 14, 196))
        #SHOULD USE TOTAL RECALL
        self.should_use_total_recall_checkbox = wx.CheckBox(self.panel, label="Use total recall...", pos=(int(screenWidth / 2) + 20, 160))
        self.should_use_total_recall_checkbox.SetToolTip("When activated, total recall is used on the chosen range.")
        self.should_use_total_recall_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #TOTAL RECALL FROM INPUT BOX
        self.total_recall_from_input_box_text = wx.StaticText(self.panel, label="From:", pos=(int(screenWidth / 2) + 140, 160))
        self.total_recall_from_input_box = wx.TextCtrl(self.panel, id=1240, size=(40,20), pos=(int(screenWidth / 2) + 180, 159))
        self.total_recall_from_input_box.SetToolTip("Total recall from this frame.")
        self.total_recall_from_input_box.SetValue("0")
        self.total_recall_from_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)

        #TOTAL RECALL TO INPUT BOX
        self.total_recall_to_input_box_text = wx.StaticText(self.panel, label="To:", pos=(int(screenWidth / 2) + 240, 160))
        self.total_recall_to_input_box = wx.TextCtrl(self.panel, id=1239, size=(40,20), pos=(int(screenWidth / 2) + 260, 159))
        self.total_recall_to_input_box.SetToolTip("Total recall to this frame.")
        self.total_recall_to_input_box.SetValue("0")
        self.total_recall_to_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)
        #SHOULD USE TOTAL RECALL
        self.should_use_total_recall_in_deforumation_checkbox = wx.CheckBox(self.panel, label="View orig. values in Deforumation", pos=(int(screenWidth / 2) + 20, 200))
        self.should_use_total_recall_in_deforumation_checkbox.SetToolTip("When activated, original values used, will be shown in Deforumation.")
        self.should_use_total_recall_in_deforumation_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #Original values -> Manual values
        self.copy_original_to_manual_button = wx.Button(self.panel, label="Orig. val -> Manual val", size=(160,17), pos=(int(screenWidth / 2) + 250, 200))
        self.copy_original_to_manual_button.SetToolTip("Will copy all the original value settings to be used as the current manual settings.")
        self.copy_original_to_manual_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.copy_original_to_manual_button.Disable()

        #BYPASS PROMPTS
        self.should_use_total_recall_prompt_checkbox = wx.CheckBox(self.panel, label="Recall prompts", pos=(int(screenWidth / 2) + 260, 180))
        self.should_use_total_recall_prompt_checkbox.SetToolTip("When activated, total recall will allow manual prompt changing.")
        self.should_use_total_recall_prompt_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #TOTAL RECALL MOVEMENT
        self.should_use_total_recall_movement_checkbox = wx.CheckBox(self.panel, label="Recall movements", pos=(int(screenWidth / 2) + 20, 180))
        self.should_use_total_recall_movement_checkbox.SetToolTip("When activated, total recall will include all movements (PAN, ZOOM, TILT), else if not checked, movements are not recalled.")
        self.should_use_total_recall_movement_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #TOTAL RECALL OTHER
        self.should_use_total_recall_others_checkbox = wx.CheckBox(self.panel, label="Recall \"others\"", pos=(int(screenWidth / 2) + 150, 180))
        self.should_use_total_recall_others_checkbox.SetToolTip("When activated, total recall will include all parameters but Movements and Prompt, else if not checked, \"others\" are not recalled.")
        self.should_use_total_recall_others_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD FORCE DEFORUM To USE DEFORUMATION'S START FRAME ON RESUME FROM TIMESTRING
        self.should_use_deforumation_start_string_checkbox = wx.CheckBox(self.panel, label="Use Deforumation timestamp when resuming", pos=(int(screenWidth / 2) + 260, 253))
        self.should_use_deforumation_start_string_checkbox.SetToolTip("When activated, and you have choosen to \"Resume from timestring\" in Deforum, Deforum is forced to start at the frame chosen by you through \"Set current image\".")
        self.should_use_deforumation_start_string_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #ERASE TOTAL RECALL MEMORY
        self.should_erase_total_recall_memory = wx.Button(self.panel, label="Erase total recall memory", pos=(int(screenWidth / 2) + 20, 220))
        self.should_erase_total_recall_memory.SetToolTip("This will erase all the data that total recall has collected in this session.")
        self.should_erase_total_recall_memory.Bind(wx.EVT_BUTTON, self.OnClicked)

        #DOWNLOAD RECORDED DATA
        self.download_recorded_data = wx.Button(self.panel, label="Save Recall Data", pos=(int(screenWidth / 2) + 20, 250))
        self.download_recorded_data.SetToolTip("Download your recorded data.")
        self.download_recorded_data.Bind(wx.EVT_BUTTON, self.OnClicked)

        #UPLOAD RECORDED DATA
        self.upload_recorded_data = wx.Button(self.panel, label="Load Recall Data", pos=(int(screenWidth / 2) + 140, 250))
        self.upload_recorded_data.SetToolTip("Upload your recorded data.")
        self.upload_recorded_data.Bind(wx.EVT_BUTTON, self.OnClicked)

        #TOTAL CURRENT RECALL FRAMES
        self.total_current_recall_frames_text = wx.StaticText(self.panel, label="Number of recall points: 0", pos=(int(screenWidth / 2) + 180, 223))

        #SAVE PROJEKT
        #self.save_project_as_zip = wx.Button(self.panel, label="Total save", pos=(int(screenWidth / 2) + 520, 220))
        #self.save_project_as_zip.SetToolTip("This will save everything that has to do with Deforum and Deforumation (Deforum folder, Deforumation folder, Total recall data and current Deforum timestring folder.")
        #self.save_project_as_zip.Bind(wx.EVT_BUTTON, self.OnClicked)


        #####################################################
        #BACKUP ALL CURRENT FRAMES
        self.backup_all_images = wx.Button(self.panel, label="Backup All Images", pos=(int(screenWidth / 2) + 370+100, 150))
        self.backup_all_images.SetToolTip("Make a quick backup of all your currently generated images.")
        self.backup_all_images.Bind(wx.EVT_BUTTON, self.OnClicked)

        #RESTORE ALL CURRENT FRAMES
        self.restore_all_images = wx.Button(self.panel, label="Restore All Images", pos=(int(screenWidth / 2) + 490+100, 150))
        self.restore_all_images.SetToolTip("Restores images to current Deforum timestring directory, from the latest backup made.")
        self.restore_all_images.Bind(wx.EVT_BUTTON, self.OnClicked)
        ###############
        #SAVE PROMPTS BUTTON
        self.update_prompts = wx.Button(self.panel, label="SAVE PROMPTS",size=(int(screenWidth/2-6),20))
        self.update_prompts.SetToolTip("When pushing this, the current Positive Prompt, and the current Negative Prompt will be saved on the currently set frame. While generating, the current frame will be increasing, and your prompts will be saved along with it.")
        sizer.Add(self.update_prompts, 0, wx.ALL, 5)
        self.update_prompts.Bind(wx.EVT_BUTTON, self.OnClicked)

        ################################################
        #ARM PAN VALUE BUTTON
        bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 10, 10)
        self.arm_pan_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX-15, tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.arm_pan_button.SetToolTip("When activated, you enter arming mode for panning. In arming mode, these panning values are separate from the actual panning values. These values are the end point when doing a transitioning of the current panning values. Such a transition is started by pushing the \"0\"-button.")
        self.arm_pan_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.arm_pan_button.SetLabel("ARM_PAN")

        #PAN STEPS INPUT
        self.pan_step_input_box = wx.TextCtrl(self.panel, id=1334, size=(40,20), style = wx.TE_PROCESS_ENTER, pos=(trbX-15, 30+tbrY+15))
        self.pan_step_input_box.SetToolTip("Sets the granularity of how much the panning value should change, when using the panning buttons.")
        self.pan_step_input_box.SetLabel("1.0")
        self.pan_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1334)
        self.pan_step_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus, id=1334)

        #LEFT PAN BUTTTON
        bmp = wx.Bitmap("./images/left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(5+trbX, 55+tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_left_button.SetToolTip("Left click: Decreases the X-axel panning value | Right click: Zeroes the X-axel value | Middle-mouse click: Decreases the X-axel panning value, but uses the syrup motion to get from the current value to the increased value in the number of steps choosen in the 0-Step box.")
        self.transform_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_left_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_x_left_button.Bind(wx.EVT_MIDDLE_UP, self.OnClicked)
        self.transform_x_left_button.Bind(wx.EVT_MIDDLE_DCLICK, self.OnClicked)
        self.transform_x_left_button.SetLabel("PAN_LEFT")

        #SET PAN VALUE X
        self.pan_X_Value_Text = wx.StaticText(self.panel, label=str(Translation_X), pos=(trbX-26, 55+tbrY+5+15))
        self.pan_X_Value_Text.SetToolTip("Current X-panning value.")
        font = self.pan_X_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_X_Value_Text.SetFont(font)

        #SET PAN VALUE X SIRUP
        self.pan_X_Sirup_Value_Text = wx.StaticText(self.panel, label=str("%.2f" % Translation_X_SIRUP), pos=(trbX-26, 55+tbrY+20+15))
        self.pan_X_Sirup_Value_Text.SetToolTip("Current X-panning SIRUP value.")
        font = self.pan_X_Sirup_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_X_Sirup_Value_Text.SetFont(font)
        self.pan_X_Sirup_Value_Text.SetForegroundColour((255,255,255))


        #SET PAN VALUE Y
        self.pan_Y_Value_Text = wx.StaticText(self.panel, label=str(Translation_Y), pos=(40+trbX, 5+tbrY))
        self.pan_Y_Value_Text.SetToolTip("Current Y-panning value.")
        font = self.pan_Y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_Y_Value_Text.SetFont(font)

        #SET PAN VALUE X SIRUP
        self.pan_Y_Sirup_Value_Text = wx.StaticText(self.panel, label=str("%.2f" % Translation_Y_SIRUP), pos=(40+trbX, 5+tbrY+15))
        self.pan_Y_Sirup_Value_Text.SetToolTip("Current Y-panning SIRUP value.")
        font = self.pan_Y_Sirup_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_Y_Sirup_Value_Text.SetFont(font)
        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))


        #UPP PAN BUTTTON
        bmp = wx.Bitmap("./images/upp_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_upp_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 25+tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_upp_button.SetToolTip("Left click: Increases the Y-axel panning value | Right click: Zeroes the Y-axel value | Middle-mouse click: Increases the Y-axel panning value, but uses the syrup motion to get from the current value to the increased value in the number of steps choosen in the 0-Step box.")
        self.transform_y_upp_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_upp_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_y_upp_button.Bind(wx.EVT_MIDDLE_UP, self.OnClicked)
        self.transform_y_upp_button.SetLabel("PAN_UP")

        #RIGHT PAN BUTTTON
        bmp = wx.Bitmap("./images/right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(65+trbX, 55+tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_right_button.SetToolTip("Left click: Increases the X-axel panning value | Right click: Zeroes the X-axel value | Middle-mouse click: Increases the X-axel panning value, but uses the syrup motion to get from the current value to the increased value in the number of steps choosen in the 0-Step box.")
        self.transform_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_right_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_x_right_button.Bind(wx.EVT_MIDDLE_UP, self.OnClicked)
        self.transform_x_right_button.SetLabel("PAN_RIGHT")
        #DOWN PAN BUTTTON
        bmp = wx.Bitmap("./images/down_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 85+tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_down_button.SetToolTip("Left click: Decreases the Y-axel panning value | Right click: Zeroes the Y-axel value | Middle-mouse click: Decreases the Y-axel panning value, but uses the syrup motion to get from the current value to the increased value in the number of steps choosen in the 0-Step box.")
        self.transform_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_down_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_y_down_button.Bind(wx.EVT_MIDDLE_UP, self.OnClicked)
        self.transform_y_down_button.SetLabel("PAN_DOWN")

        #ZERO PAN BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 22, 22)
        self.transform_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 56+tbrY+15), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_zero_button.SetToolTip("Will start a transition from the current panning values, to the armed panning values.")
        self.transform_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_zero_button.Bind(wx.EVT_MIDDLE_UP, self.OnClicked)
        self.transform_zero_button.SetLabel("ZERO PAN")

        #ZERO PAN STEP INPUT BOX STRING
        self.zero_pan_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(trbX+74, tbrY+14+15))
        #ZERO PAN STEP INPUT BOX
        self.zero_pan_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+70, tbrY+30+15))
        self.zero_pan_step_input_box.SetToolTip("The number of frames that it will take for a panning transition to go from the current panning value to the armed panning value.")
        self.zero_pan_step_input_box.SetLabel("0")


        ########################################################

        #ZOOM SLIDER
        self.zoom_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=0, minValue=-1000, maxValue=1000, pos = (142+trbX, tbrY+5), size = (20, 135), style = wx.SL_VERTICAL  | wx.SL_LEFT | wx.SL_AUTOTICKS | wx.SL_INVERSE) # | wx.SL_LABELS)
        self.zoom_slider.SetToolTip("Zooming value (Z-axis).")
        self.zoom_slider.SetTickFreq(int(float(10) * 100 / 10))
        self.zoom_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.zoom_slider.Bind(wx.EVT_RIGHT_UP, self.OnClicked)

        self.zoom_slider.SetLabel("ZOOM")
        self.ZOOM_X_Text = wx.StaticText(self.panel, label="Z", pos=(170+trbX, tbrY+40))
        self.ZOOM_X_Text2 = wx.StaticText(self.panel, label="O", pos=(170+trbX, tbrY+60))
        self.ZOOM_X_Text3 = wx.StaticText(self.panel, label="O", pos=(170+trbX, tbrY+80))
        self.ZOOM_X_Text4 = wx.StaticText(self.panel, label="M", pos=(169+trbX, tbrY+100))
        self.zoom_value_text = wx.StaticText(self.panel, label="0.01", pos=(116+trbX, tbrY+65))
        self.zoom_value_high_text = wx.StaticText(self.panel, label="10", pos=(140+trbX, tbrY-7))
        font = self.zoom_value_high_text.GetFont()
        font = font.Bold()
        self.zoom_value_high_text.SetFont(font)
        self.zoom_value_low_text = wx.StaticText(self.panel, label="-10", pos=(136+trbX, tbrY+138))
        font = self.zoom_value_low_text.GetFont()
        font = font.Bold()
        self.zoom_value_low_text.SetFont(font)

        #ZOOM STEPS INPUT
        self.zoom_step_input_box = wx.TextCtrl(self.panel, id = 1335, size=(30,20), style=wx.TE_PROCESS_ENTER, pos=(105+trbX, tbrY+115))
        self.zoom_step_input_box.SetToolTip("The granularity of the Zoom slider.")
        self.zoom_step_input_box.SetLabel("10")
        #self.zoom_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=151)
        self.zoom_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1335)
        self.zoom_step_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus, id=1335)

        #self.seed_input_box =      wx.TextCtrl(self.panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+340, tbrY-50-60))

        #FOV SLIDER
        self.fov_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=70, minValue=20, maxValue=120, pos = (190+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.fov_slider.SetToolTip("Sets the current Field Of View (70 is default).")
        self.fov_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.fov_slider.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.fov_slider.SetTickFreq(1)
        self.fov_slider.SetLabel("FOV")
        self.FOV_Text = wx.StaticText(self.panel, label="F", pos=(250+trbX, tbrY+40))
        self.FOV_Text2 = wx.StaticText(self.panel, label="O", pos=(249+trbX, tbrY+60))
        self.FOV_Text3 = wx.StaticText(self.panel, label="V", pos=(250+trbX, tbrY+80))

        #LOCK FOV TO ZOOM BUTTON
        bmp = wx.Bitmap("./images/lock_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_lock_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY+6), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_lock_button.SetToolTip("Locks the FOV slider to the Zoom slider (bi-directional).")
        self.fov_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_lock_button.SetLabel("LOCK FOV")

        #REVERSE FOV TO ZOOM BUTTON
        bmp = wx.Bitmap("./images/reverse_fov_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_reverse_lock_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY+120), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_reverse_lock_button.SetToolTip("Changes the direction of the lock between the Zoom and Fov slider (when using the \"Lock Zoom and Fov\"-button).")
        self.fov_reverse_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_reverse_lock_button.SetLabel("REVERSE FOV")

        #ARM ZOOM VALUE BUTTON
        bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 10, 10)
        self.arm_zoom_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+230, tbrY-10), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.arm_zoom_button.SetToolTip("When activated, you enter arming mode for zooming. In arming mode, these zoom values are separate from the actual zoom values. These values are the end point when doing a transitioning of the current zoom values. Such a transition is started by pushing the \"0\"-button.")
        self.arm_zoom_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.arm_zoom_button.SetLabel("ARM_ZOOM")

        #ZERO ARM STEP INPUT BOX STRING
        self.zero_zoom_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(trbX+256, tbrY-15))
        #ZERO PAN STEP INPUT BOX
        self.zero_zoom_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+254, tbrY))
        self.zero_zoom_step_input_box.SetToolTip("The number of frames that it will take for a zooming transition to go from the current zoom value to the armed zoom value.")
        self.zero_zoom_step_input_box.SetLabel("0")

        #ZERO ZOOM BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 18, 18)
        self.zoom_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+258, tbrY+20), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.zoom_zero_button.SetToolTip("Will start a transition from the current zoom values, to the armed zoom values.")
        self.zoom_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.zoom_zero_button.SetLabel("ZERO ZOOM")

        #STRENGTH SCHEDULE SLIDER
        self.strength_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=65, minValue=0, maxValue=100, pos = (trbX-25, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.strength_schedule_slider.SetToolTip("Sets the Strength value. The scale shown is 100 times larger than the actual value (so when using strength==100 it's actually 1.0)")
        self.strength_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.strength_schedule_slider.SetTickFreq(1)
        self.strength_schedule_slider.SetLabel("STRENGTH SCHEDULE")
        self.step_schedule_Text = wx.StaticText(self.panel, label="Strength Value", pos=(trbX-25, tbrY-70))

        #SHOULD USE DEFORUMATION STRENGTH VALUES? CHECK-BOX
        self.should_use_deforumation_strength_checkbox = wx.CheckBox(self.panel, label="USE DEFORUMATION STRENGTH", pos=(trbX+60, tbrY-66))
        self.should_use_deforumation_strength_checkbox.SetToolTip("When activated, Deforumations Strength value will be used.")
        self.should_use_deforumation_strength_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION CFG VALUES? CHECK-BOX
        self.should_use_deforumation_cfg_checkbox = wx.CheckBox(self.panel, label="USE DEFORUMATION CFG", pos=(trbX+460, tbrY-66))
        self.should_use_deforumation_cfg_checkbox.SetToolTip("When activated, Deforumations CFG value will be used.")
        self.should_use_deforumation_cfg_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION CADENCE VALUES? CHECK-BOX
        self.should_use_deforumation_cadence_checkbox = wx.CheckBox(self.panel, label="U.D.Ca", pos=(trbX+780, tbrY))
        self.should_use_deforumation_cadence_checkbox.SetToolTip("When activated, Deforumations Cadence value will be used.")
        self.should_use_deforumation_cadence_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION NOISE VALUES? CHECK-BOX
        self.should_use_deforumation_noise_checkbox = wx.CheckBox(self.panel, label="U.D.No", pos=(trbX+720, tbrY+74))
        self.should_use_deforumation_noise_checkbox.SetToolTip("When activated, Deforumations Noise values will be used.")
        self.should_use_deforumation_noise_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION PANNING VALUES? CHECK-BOX
        self.should_use_deforumation_panning_checkbox = wx.CheckBox(self.panel, label="U.D.Pa", pos=(trbX+40, tbrY-8))
        self.should_use_deforumation_panning_checkbox.SetToolTip("When activated, Deforumations Panning values will be used.")
        self.should_use_deforumation_panning_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION ZOOM/FOV VALUES? CHECK-BOX
        self.should_use_deforumation_zoomfov_checkbox = wx.CheckBox(self.panel, label="U.D.Zo", pos=(trbX+172, tbrY-6))
        self.should_use_deforumation_zoomfov_checkbox.SetToolTip("When activated, Deforumations ZOOM and FOV values will be used.")
        self.should_use_deforumation_zoomfov_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION ROTATION VALUES? CHECK-BOX
        self.should_use_deforumation_rotation_checkbox = wx.CheckBox(self.panel, label="U.D.Ro", pos=(trbX+354, tbrY-8))
        self.should_use_deforumation_rotation_checkbox.SetToolTip("When activated, Deforumations Rotation values will be used.")
        self.should_use_deforumation_rotation_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION TILT VALUES? CHECK-BOX
        self.should_use_deforumation_tilt_checkbox = wx.CheckBox(self.panel, label="U.D.Ti", pos=(trbX+480, tbrY-2))
        self.should_use_deforumation_tilt_checkbox.SetToolTip("When activated, Deforumations Tilt values will be used.")
        self.should_use_deforumation_tilt_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #ZERO MOTION STATUS LABELS

        self.zero_pan_current_settings_Text = wx.StaticText(self.panel, label=zero_pan_current_settings, pos=(trbX - 40 , tbrY - 150))
        self.zero_zoom_current_settings_Text = wx.StaticText(self.panel, label=zero_zoom_current_settings, pos=(trbX +250 - 10 , tbrY - 150))
        self.zero_rotate_current_settings_Text = wx.StaticText(self.panel, label=zero_rotation_current_settings, pos=(trbX + 440 - 20, tbrY - 150))
        self.zero_tilt_current_settings_Text = wx.StaticText(self.panel, label=zero_tilt_current_settings, pos=(trbX + 720 - 4, tbrY - 150))

        #SAMPLE STEP SLIDER
        self.sample_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=25, minValue=1, maxValue=200, pos = (trbX-25, tbrY-50-70), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.sample_schedule_slider.SetToolTip("Tells Deforum how many steps it should use during image generation.")
        self.sample_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.sample_schedule_slider.SetTickFreq(1)
        self.sample_schedule_slider.SetLabel("STEPS")
        self.strength_schedule_Text = wx.StaticText(self.panel, label="Steps", pos=(trbX-25, tbrY-70-64))

        #SEED INPUT BOX
        self.seed_schedule_Text = wx.StaticText(self.panel, label="Seed", pos=(trbX+340, tbrY-50-80))
        self.seed_input_box = wx.TextCtrl(self.panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+340, tbrY-50-60))
        self.seed_input_box.SetToolTip("Tells Deforum what the seed should be (-1 == random). The method used (iter, fixed, etc), is decided by Deforum's Seed behaviour option.")
        self.seed_input_box.SetLabel("-1")
        self.seed_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus, id=3)
        self.seed_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=3)



        #CFG SCHEDULE SLIDER
        self.cfg_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=7, minValue=1, maxValue=30, pos = (trbX+340, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cfg_schedule_slider.SetToolTip("Tells Deforum what CFG value to use.")
        self.cfg_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cfg_schedule_slider.SetTickFreq(1)
        self.cfg_schedule_slider.SetLabel("CFG SCALE")
        self.CFG_scale_Text = wx.StaticText(self.panel, label="CFG Scale", pos=(trbX+340, tbrY-70))


        #LOOK LEFT BUTTTON
        bmp = wx.Bitmap("./images/look_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_left_button.SetToolTip("How many degrees it should continuously rotate left.")
        self.rotation_3d_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_left_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_x_left_button.SetLabel("LOOK_LEFT")

        #SET ROTATION VALUE X
        self.rotation_3d_x_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_X), pos=(240+trbX-30+80, 55+tbrY+5))
        self.rotation_3d_x_Value_Text.SetToolTip("Current X-Rotation value.")
        font = self.rotation_3d_x_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_x_Value_Text.SetFont(font)

        #ROTATE STEPS INPUT
        self.rotate_step_input_box = wx.TextCtrl(self.panel, id=1333, size=(40,20), style = wx.TE_PROCESS_ENTER, pos=(240+trbX-15+80, 30+tbrY))
        self.rotate_step_input_box.SetToolTip("The Rotation granularity.")
        self.rotate_step_input_box.SetLabel("1.0")
        self.rotate_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1333)
        self.rotate_step_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus, id=1333)
        #LOOK UPP BUTTTON
        bmp = wx.Bitmap("./images/look_upp.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_up_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY-30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_up_button.SetToolTip("How many degrees it should continuously rotate upwards.")
        self.rotation_3d_y_up_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_up_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_y_up_button.SetLabel("LOOK_UP")

        #ZERO ROTATE STEP INPUT BOX STRING
        self.zero_rotate_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(240+trbX+43+100, 55+tbrY-40))
        #ZERO ROTATE STEP INPUT BOX
        self.zero_rotate_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(240+trbX+40+100, 55+tbrY-25))
        self.zero_rotate_step_input_box.SetToolTip("The number of frames that it will take for a rotation transition to go from the current rotation values to the armed rotation values.")
        self.zero_rotate_step_input_box.SetLabel("0")

        #SET ROTATION VALUE Y
        self.rotation_3d_y_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_Y), pos=(240+trbX+35+80, 55+tbrY-48))
        self.rotation_3d_y_Value_Text.SetToolTip("Current Y-Rotation value.")
        font = self.rotation_3d_y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_y_Value_Text.SetFont(font)
        #ARM ROTATION VALUE BUTTON
        bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 10, 10)
        self.arm_rotation_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+80, tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.arm_rotation_button.SetToolTip("When activated, you enter arming mode for rotation. In arming mode, these rotation values are separate from the actual rotation values. These values are the end point when doing a transitioning of the current panning values. Such a transition is started by pushing the \"0\"-button.")
        self.arm_rotation_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.arm_rotation_button.SetLabel("ARM_ROTATION")

        #LOOK RIGHT BUTTTON
        bmp = wx.Bitmap("./images/look_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+57+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_right_button.SetToolTip("How many degrees it should continuously rotate right.")
        self.rotation_3d_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_right_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_x_right_button.SetLabel("LOOK_RIGHT")

        #LOOK DOWN BUTTTON
        bmp = wx.Bitmap("./images/look_down.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY+30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_down_button.SetToolTip("How many degrees it should continuously rotate downwards.")
        self.rotation_3d_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_down_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_y_down_button.SetLabel("LOOK_DOWN")

        #SPIN BUTTTON
        bmp = wx.Bitmap("./images/rotate_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(300+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_left_button.SetToolTip("How many degrees it should continuously spin anti-clock-wise.")
        self.rotation_3d_z_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_left_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_z_left_button.SetLabel("ROTATE_LEFT")

        #ZERO ROTATE BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 20, 20)
        self.rotate_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotate_zero_button.SetToolTip("Will start a transition from the current rotation values, to the armed panning values.")
        self.rotate_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotate_zero_button.SetLabel("ZERO ROTATE")

        #ROTATE RIGHT BUTTTON
        bmp = wx.Bitmap("./images/rotate_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(380+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_right_button.SetToolTip("How many degrees it should continuously spin clock-wise.")
        self.rotation_3d_z_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_right_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.rotation_3d_z_right_button.SetLabel("ROTATE_RIGHT")

        #SET ROTATION VALUE Z
        self.rotation_Z_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_Z), pos=(360+trbX+46+80, 60+tbrY))
        self.rotation_Z_Value_Text.SetToolTip("The current Z-Rotation value (negative == clockwise, positive == anti-clockwise).")
        font = self.rotation_Z_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_Z_Value_Text.SetFont(font)

        #ZERO TILT BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 32, 32)
        self.tilt_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(360+trbX+36+80, 88+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.tilt_zero_button.SetToolTip("Immediately Zeroes the Tilt value.")
        self.tilt_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.tilt_zero_button.SetLabel("ZERO TILT")

        #TILT STEPS INPUT
        self.tilt_step_input_box = wx.TextCtrl(self.panel, id=1336, size=(40,20), style=wx.TE_PROCESS_ENTER, pos=(360+trbX+10+80, 30+tbrY))
        self.tilt_step_input_box.SetToolTip("Sets the granularity of how many degrees it should tilt, when using the Tilt buttons.")
        self.tilt_step_input_box.SetLabel("1.0")
        self.tilt_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=1336)
        self.tilt_step_input_box.Bind(wx.EVT_KILL_FOCUS, self.OnFocus, id=1336)

        #ZERO TILT STEP INPUT BOX
        self.zero_tilt_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(360+trbX+36+110, 14+tbrY))
        self.zero_tilt_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(360+trbX+34+110, 30+tbrY))
        self.zero_tilt_step_input_box.SetToolTip("The number of frames that it will take for a tilt transition to go from the current tilt values to the armed tilt values.")
        self.zero_tilt_step_input_box.SetLabel("0")

        #ARM TILT VALUE BUTTON
        bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 10, 10)
        self.arm_tilt_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(360+trbX+10+80, tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.arm_tilt_button.SetToolTip("When activated, you enter arming mode for tilt. In arming mode, these tilt values are separate from the actual tilt values. These values are the end point when doing a transitioning of the current panning values. Such a transition is started by pushing the \"0\"-button.")
        self.arm_tilt_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.arm_tilt_button.SetLabel("ARM_TILT")


        #PAUSE VIDEO RENDERING
        if is_paused_rendering:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO RESUME RENDERING", size=(int(screenWidth/2-6),20))
            self.pause_rendering.SetToolTip("Push this button to resume the paused image generation.")
        else:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO PAUSE RENDERING", size=(int(screenWidth/2-6),20))
            self.pause_rendering.SetToolTip("Push this button to pause the ongoing image generation.")
        sizer.Add(self.pause_rendering, 0, wx.ALL, 5)
        self.pause_rendering.Bind(wx.EVT_BUTTON, self.OnClicked)

        #CADENCE SLIDER
        self.cadence_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(Cadence_Schedule), minValue=1, maxValue=20, pos = (trbX+1000-340, tbrY+20), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cadence_slider.SetToolTip("Tells Deforum what cadence value it should use. A higher cadence will create so called in-between(tweens) images that are not diffused.")
        self.cadence_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cadence_slider.SetTickFreq(1)
        self.cadence_slider.SetLabel("CADENCE")
        self.cadence_slider_Text = wx.StaticText(self.panel, label="Cadence Scale", pos=(trbX+1000-340, tbrY))
        #CADENCE SUGGESTION
        self.cadence_suggestion = wx.StaticText(self.panel, label="(hist cad: ??)", pos=(trbX+1000-140, tbrY))
        self.cadence_suggestion.SetToolTip("This tries to remember what cadence you had at the current frame. It is always good to start with the same cadence after you have rewinded as it for a better transition.")

        #CADENCE SCHEDULE INPUT BOX
        self.cadence_schedule_input_box = wx.TextCtrl(self.panel, id=1233, size=(150,20), pos=(trbX+1000-220, tbrY-22))
        self.cadence_schedule_input_box.SetToolTip("Used for scheduling the cadence.")
        self.cadence_schedule_input_box.SetHint("<Cadence Schedule Here>")
        self.cadence_schedule_Checkbox = wx.CheckBox(self.panel, label = "Use C.", id=73, pos=(trbX+1000-66, tbrY-20))
        self.cadence_schedule_Checkbox.SetToolTip("When checked, tells Deforum to use this Cadence Schedule.")
        self.cadence_schedule_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #self.cadence_schedule_input_box.Bind(wx.EVT_TEXT_PASTE, self.OnPaste)
        self.cadence_schedule_input_box.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        #COMBOBOX FOR CHOOSING A COMPONENT
        languages = ['Noise Multiplier', 'Perlin Octaves', 'Perlin Persistence']
        self.component_chooser_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(trbX+950-150, tbrY+70),size=(140,40), choices=languages, style=0, name="Arne")
        self.component_chooser_choice.Bind(wx.EVT_CHOICE, self.OnComponentChoice)
        self.component_chooser_choice.SetSelection(0)
        #NOISE SLIDER
        self.noise_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=105, minValue=0, maxValue=200, pos = (trbX+950-340, tbrY+110), size = (360, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.noise_slider.SetToolTip("How much uniformed noise should Deforum use. Lower values will loose detail (smoothing things out), and higher values will add more detail making it sharper (too much will result in a scrambled image).")
        self.noise_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.noise_slider.SetTickFreq(1)
        self.noise_slider.SetLabel("Noise")
        self.noise_slider_Text = wx.StaticText(self.panel, label="Noise", pos=(trbX+1000-340, tbrY+95))

        #PERLIN PERSISTENCE SLIDER
        self.perlin_persistence_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=4, minValue=0, maxValue=100, pos = (trbX+950-340, tbrY+110), size = (360, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.perlin_persistence_slider.SetToolTip("How much perlin persistence should Deforum use. Note that if you choose Noise type \"perlin\", your image seems to must have the dimensions 512x512 (else it will complain).")
        self.perlin_persistence_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.perlin_persistence_slider.SetTickFreq(1)
        self.perlin_persistence_slider.SetLabel("Perlin Persistence")
        self.perlin_persistence_slider_Text = wx.StaticText(self.panel, label="Perlin persistence", pos=(trbX+1000-340, tbrY+95))
        self.perlin_persistence_slider.Hide()
        self.perlin_persistence_slider_Text.Hide()

        #PERLIN OCTAVE SLIDER
        self.perlin_octave_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=4, minValue=1, maxValue=7, pos = (trbX+950-340, tbrY+110), size = (360, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.perlin_octave_slider.SetToolTip("How much perlin octave noise should Deforum use. Note that if you choose Noise type \"perlin\", your image seems to must have the dimensions 512x512 (else it will complain).")
        self.perlin_octave_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.perlin_octave_slider.SetTickFreq(1)
        self.perlin_octave_slider.SetLabel("Perlin Octaves")
        self.perlin_octave_slider_Text = wx.StaticText(self.panel, label="Perlin octaves", pos=(trbX+1000-340, tbrY+95))
        self.perlin_octave_slider.Hide()
        self.perlin_octave_slider_Text.Hide()

        #CONTROLNET RADIO BUTTON CHOICE
        ##############################################################
        lblList = ['CN 1', 'CN 2', 'CN 3', 'CN 4', 'CN 5']
        self.rbox = wx.RadioBox(self.panel, label='ControlNet', pos = (trbX+320, tbrY+124), choices=lblList, majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        self.rbox.Bind(wx.EVT_RADIOBOX, self.OnRadioBoxCN)
        #self.control_net_choice_radiobox = wx.RadioButton(self.panel, id=300, label = "CN 1", pos = (trbX+140, tbrY+180), style = wx.RB_GROUP)

        #ControlNet Sliders
        ###############################################################
        #CONTROLNET WEIGHT
        self.control_net_weight_slider = []
        self.control_net_weight_slider_Text = []
        self.control_net_stepstart_slider = []
        self.control_net_stepstart_slider_Text = []
        self.control_net_stepend_slider = []
        self.control_net_stepend_slider_Text = []
        self.control_net_lowt_slider = []
        self.control_net_lowt_slider_Text = []
        self.control_net_hight_slider = []
        self.control_net_hight_slider_Text = []
        self.control_net_active_checkbox = []
        for cnIndex in range(5):
            self.control_net_weight_slider.append(wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_Weight[cnIndex]*100), minValue=0, maxValue=200, pos = (trbX-40, tbrY+190), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS ))
            self.control_net_weight_slider[cnIndex].SetToolTip("Tells, if activated, the ControlNet, what weight it should use. The slider value is scaled by 100 (actual value 100 times smaller)")
            self.control_net_weight_slider[cnIndex].Bind(wx.EVT_SCROLL, self.OnClicked)
            self.control_net_weight_slider[cnIndex].SetTickFreq(1)
            self.control_net_weight_slider[cnIndex].SetLabel("CN WEIGHT"+str(cnIndex))
            self.control_net_weight_slider_Text.append(wx.StaticText(self.panel, label="ControlNet("+str(cnIndex+1)+") - Weight", pos=(trbX-40, tbrY+175)))
            self.control_net_weight_slider_Text[cnIndex].Hide()
            self.control_net_weight_slider[cnIndex].Hide()

            #CONTROLNET ENDING CONTROL STEP
            self.control_net_stepend_slider.append(wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepEnd[cnIndex]*100), minValue=0, maxValue=100, pos = (trbX+640, tbrY+190), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS ))
            self.control_net_stepend_slider[cnIndex].SetToolTip("Tells, if activated, the ControlNet, what step it should end on. The slider value is scaled by 100 (actual value 100 times smaller)")
            self.control_net_stepend_slider[cnIndex].Bind(wx.EVT_SCROLL, self.OnClicked)
            self.control_net_stepend_slider[cnIndex].SetTickFreq(1)
            self.control_net_stepend_slider[cnIndex].SetLabel("CN STEPEND"+str(cnIndex))
            self.control_net_stepend_slider_Text.append(wx.StaticText(self.panel, label="ControlNet("+str(cnIndex+1)+") - Ending Control Step", pos=(trbX+640, tbrY+175)))
            self.control_net_stepend_slider[cnIndex].Hide()
            self.control_net_stepend_slider_Text[cnIndex].Hide()
            #CONTROLNET STARTING CONTROL STEP
            self.control_net_stepstart_slider.append(wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepStart[cnIndex]*100), minValue=0, maxValue=100, pos = (trbX+300, tbrY+190), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS ))
            self.control_net_stepstart_slider[cnIndex].SetToolTip("Tells, if activated, the ControlNet, what step it should start on. The slider value is scaled by 100 (actual value 100 times smaller)")
            self.control_net_stepstart_slider[cnIndex].Bind(wx.EVT_SCROLL, self.OnClicked)
            self.control_net_stepstart_slider[cnIndex].SetTickFreq(1)
            self.control_net_stepstart_slider[cnIndex].SetLabel("CN STEPSTART"+str(cnIndex))
            self.control_net_stepstart_slider_Text.append(wx.StaticText(self.panel, label="ControlNet("+str(cnIndex+1)+") - Starting Control Step", pos=(trbX+300, tbrY+175)))
            self.control_net_stepstart_slider[cnIndex].Hide()
            self.control_net_stepstart_slider_Text[cnIndex].Hide()
            #CONTROLNET LOW THRESHOLD
            self.control_net_lowt_slider.append(wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_LowT[cnIndex]), minValue=0, maxValue=255, pos = (trbX-40, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS ))
            self.control_net_lowt_slider[cnIndex].SetToolTip("Tells, if activated, the ControlNet, what the lower threshold should be. Values below the low threshold always get discarded. Values in between the the two thresholds may get kept or may get discarded depending on various rules and maths.")
            self.control_net_lowt_slider[cnIndex].Bind(wx.EVT_SCROLL, self.OnClicked)
            self.control_net_lowt_slider[cnIndex].SetTickFreq(1)
            self.control_net_lowt_slider[cnIndex].SetLabel("CN LOWT"+str(cnIndex))
            self.control_net_lowt_slider_Text.append(wx.StaticText(self.panel, label="ControlNet("+str(cnIndex+1)+") - Low Threshold", pos=(trbX-40, tbrY+240)))
            self.control_net_lowt_slider[cnIndex].Hide()
            self.control_net_lowt_slider_Text[cnIndex].Hide()
            #CONTROLNET HIGH THRESHOLD
            self.control_net_hight_slider.append(wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_HighT[cnIndex]), minValue=0, maxValue=255, pos = (trbX+300, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS ))
            self.control_net_hight_slider[cnIndex].SetToolTip("Tells, if activated, the ControlNet, what the higher threshold should be. Values below the low threshold always get discarded. Values above the high threshold always get kept. Values in between the the two thresholds may get kept or may get discarded depending on various rules and maths.")
            self.control_net_hight_slider[cnIndex].Bind(wx.EVT_SCROLL, self.OnClicked)
            self.control_net_hight_slider[cnIndex].SetTickFreq(1)
            self.control_net_hight_slider[cnIndex].SetLabel("CN HIGHT"+str(cnIndex))
            self.control_net_hight_slider_Text.append(wx.StaticText(self.panel, label="ControlNet("+str(cnIndex+1)+") - High Threshold", pos=(trbX+300, tbrY+240)))
            self.control_net_hight_slider[cnIndex].Hide()
            self.control_net_hight_slider_Text[cnIndex].Hide()
            # SHOULD USE CURRENT CONTROL NET?
            self.control_net_active_checkbox.append(wx.CheckBox(self.panel, label="U.D.Cn"+str(cnIndex), pos=(trbX+250, tbrY+148)))
            self.control_net_active_checkbox[cnIndex].SetToolTip("When activated, Deforumations Cadence value will be used.")
            self.control_net_active_checkbox[cnIndex].Bind(wx.EVT_CHECKBOX, self.OnClicked)
            self.control_net_active_checkbox[cnIndex].Hide()

        #UN-HIDE CN 0
        self.SetCurrentActiveCN(1)


        ########## PARSEQ FIELD###############
        self.parseqSettingsField = wx.StaticBox(self.panel, id=wx.ID_ANY, label='PARSEQ', size=(450, 66), pos=(int(screenWidth / 2) + 14, 420))  # orient=wx.HORIZONTAL)

        #PARSEQ URL INPUT BOX
        self.Parseq_URL_input_box_text = wx.StaticText(self.panel, label="Use PARSEQ as Guide", pos=(int(screenWidth / 2) + 40, 440))

        self.Parseq_activation_Checkbox = wx.CheckBox(self.panel, id=73, pos=(int(screenWidth / 2) + 20, 440))
        self.Parseq_activation_Checkbox.SetToolTip("Tells, Deforum and Deforumation that Parseq is to be used as scheduler.")
        self.Parseq_activation_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        self.Parseq_URL_input_box = wx.TextCtrl(self.panel, 28, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(int(screenWidth / 2) + 20, 460))
        self.Parseq_URL_input_box.SetToolTip("This should point to a URL that contains a JSON file, as generated by the online Parseq application (https://sd-parseq.web.app).")
        self.Parseq_URL_input_box.SetHint("<URL to Parseq JSON File here>")
        #PARSEQ SEND TO DEFORUM BUTTON
        self.Send_URL_to_Deforum = wx.Button(self.panel, id=wx.ID_ANY, label="Send URL to Deforum", pos=(int(screenWidth / 2) + 326, 460), size=(120, 20))
        self.Send_URL_to_Deforum.SetToolTip("This sends the actual URL to Deforum, so that it knows what Parseq file it should use during scheduling.")
        self.Send_URL_to_Deforum.Bind(wx.EVT_BUTTON, self.OnClicked)

        #Add recording button
        bmp = wx.Bitmap("./images/record_off.bmp", wx.BITMAP_TYPE_BMP)
        self.record_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(int(screenWidth / 2) + 10, 334), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.record_button.SetToolTip("Push to record. When recording use the following commands to control Deforumation:\n"
                                      "\"<Any sentence>\": Your spoken sentence will be added to the second prompt window.\n"
                                      "\"add + <Any sentence>\": Using \"add\" and then speaking a sentence will add to the current sentence.\n"
                                      "\"cancel\": Using the word \"cancel\" anywhere in the spoken sentence, will cancel the output to the prompt window completely.\n"
                                      "\"Pan lef, pan right, pan up, pan down\": Controls the panning\n"
                                      "\"Zoom in, zoom out\": Controls the Zoom\n"
                                      "\"Rotate left, rotate right, rotate up, rotate down\": Controls the rotation\n"
                                      "\"Tilt left, Tilt right\": Controls the tilt\n"
                                      "\"Reset panning\": Resets the paning values\n"
                                      "\"Reset zoom\": Resets the zoom value\n"
                                      "\"Reset rotation\": Resets the rotation values\n"
                                      "\"Reset tilt \": Resets the tilt value\n")
        self.record_button.ToolTip.SetAutoPop(1000*30)
        self.record_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.record_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.record_button.SetLabel("RECORD")

        #LIVE VALUE BUTTON
        self.Live_Values_Checkbox = wx.CheckBox(self.panel, id=wx.ID_ANY, label="Live Values", pos=(trbX-40, tbrY + 130))
        self.Live_Values_Checkbox.SetToolTip("Activating \"Live Values\", will get motion and other setting values as how Deforum sees them (those can differ from the values that are displayed in Deforumation because of what override choices you have made.). The values will also be visually reflected in Deforums GUI (sliders and values will show Deforum's values). Some values are also displyed at the bottom of Deforumation's screen. NOTE, that your current Deforumation values will revert, when you uncheck this box.")
        self.Live_Values_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        self.deforum_strength_value_info_text = wx.StaticText(self.panel, label="Strength:", pos=(trbX-40, tbrY+310))
        self.deforum_trx_value_info_text = wx.StaticText(self.panel, label="Tr X:", pos=(trbX+40, tbrY+310))
        self.deforum_try_value_info_text = wx.StaticText(self.panel, label="Tr Y:", pos=(trbX+100, tbrY+310))
        self.deforum_trz_value_info_text = wx.StaticText(self.panel, label="Tr Z:", pos=(trbX+160, tbrY+310))
        self.deforum_rox_value_info_text = wx.StaticText(self.panel, label="Ro X:", pos=(trbX+220, tbrY+310))
        self.deforum_roy_value_info_text = wx.StaticText(self.panel, label="Ro Y:", pos=(trbX+280, tbrY+310))
        self.deforum_roz_value_info_text = wx.StaticText(self.panel, label="Ro Z:", pos=(trbX+340, tbrY+310))
        self.deforum_steps_value_info_text = wx.StaticText(self.panel, label="Steps:", pos=(trbX+400, tbrY+310))
        self.deforum_cfg_value_info_text = wx.StaticText(self.panel, label="CFG:", pos=(trbX+460, tbrY+310))
        self.deforum_cadence_value_info_text = wx.StaticText(self.panel, label="Cadence:", pos=(trbX+520, tbrY+310))
        self.deforum_pdmotion_value_info_text = wx.StaticText(self.panel, label="P-D Motion:", pos=(trbX+600, tbrY+310))
        self.deforum_zero_pan_value_info_text = wx.StaticText(self.panel, label="0-Pan:", pos=(trbX+720, tbrY+310))
        self.deforum_zero_zoom_value_info_text = wx.StaticText(self.panel, label="0-Zoom:", pos=(trbX+800, tbrY+310))
        self.deforum_zero_rotation_value_info_text = wx.StaticText(self.panel, label="0-Rotate:", pos=(trbX+890, tbrY+310))
        self.deforum_zero_tilt_value_info_text = wx.StaticText(self.panel, label="0-Tilt:", pos=(trbX + 1000, tbrY + 310))

        self.deforum_zero_pan_x_value_info_text = wx.StaticText(self.panel, label="0-Pan_X:", pos=(trbX+660, tbrY+250))
        self.deforum_zero_pan_y_value_info_text = wx.StaticText(self.panel, label="0-Pan_Y:", pos=(trbX+660, tbrY+250+15))


        #CADENCE RE-SCHEDULER
        self.cadence_rescheduler_text = wx.StaticText(self.panel, label="CADENCE RE-SCHEDULER", pos=(trbX-40, tbrY+340))
        font = wx.Font(14, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
        self.cadence_rescheduler_text.SetFont(font)
        #INPUTBOX URL or FILE
        self.cadence_rescheduler_url_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(240,20), pos=(trbX-40, tbrY+380))
        self.cadence_rescheduler_url_input_box.SetToolTip("Insert a URL or a FILE-path to your JSON parseq file here.")
        self.cadence_rescheduler_url_input_box.SetHint("<URL or FILE path to parseq file, here>")
        #CHECKBOX USE DISCO STYLE FROM POSITIVE PROMPT
        self.cadence_rescheduler_disco_checkbox = wx.CheckBox(self.panel, id=wx.ID_ANY, label="Use the values from \"Positive prompt\" (Deforum/Disco)-style", pos=(trbX+220, tbrY+380))
        self.cadence_rescheduler_disco_checkbox.SetToolTip("If you check this box, values (Disco style) will be used instead of from a parseq JSON. Values will be taken from the Positive prompt.")
        self.cadence_rescheduler_disco_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #INPUTBOX CADENCE TO BE USED
        self.cadence_rescheduler_cadence_text = wx.StaticText(self.panel, label="Cadence value:", pos=(trbX-40, tbrY+402))
        self.cadence_rescheduler_cadence_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(20,20), pos=(trbX+46, tbrY+400))
        self.cadence_rescheduler_cadence_input_box.SetValue("3")
        self.cadence_rescheduler_cadence_input_box.SetToolTip("The cadence value to use for the re-schedule.")
        #INPUTBOX TRIGGER PARAMETER
        self.cadence_rescheduler_trigger_parameter_text = wx.StaticText(self.panel, label="Trigger parameter:", pos=(trbX-40, tbrY+422))
        self.cadence_rescheduler_trigger_parameter_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(120,20), pos=(trbX+62, tbrY+420))
        self.cadence_rescheduler_trigger_parameter_input_box.SetValue("strength")
        self.cadence_rescheduler_trigger_parameter_input_box.SetToolTip("The parameter (like \"strength\" or \"translation_z\") that you use as trigger.")
        #INPUTBOX MIN AND MAX TRIGGER VALUES
        self.cadence_rescheduler_trigger_min_text = wx.StaticText(self.panel, label="Min:", pos=(trbX-40, tbrY+442))
        self.cadence_rescheduler_trigger_min_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(40,20), pos=(trbX-10, tbrY+440))
        self.cadence_rescheduler_trigger_min_input_box.SetValue("0.1")
        self.cadence_rescheduler_trigger_min_input_box.SetToolTip("The minimum value that your chosen parameter value should trigger on.")
        self.cadence_rescheduler_trigger_max_text = wx.StaticText(self.panel, label="Max:", pos=(trbX+40, tbrY+442))
        self.cadence_rescheduler_trigger_max_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(40,20), pos=(trbX+70, tbrY+440))
        self.cadence_rescheduler_trigger_max_input_box.SetValue("0.1")
        self.cadence_rescheduler_trigger_max_input_box.SetToolTip("The maximum value that your chosen parameter value should trigger on.")
        #CALCULATE RE-SCHEDULING BUTTON
        self.cadence_rescheduler_calculate_button = wx.Button(self.panel, id=wx.ID_ANY, label="Re-schedule", pos=(trbX-40, tbrY+470), size=(75, 20))
        self.cadence_rescheduler_calculate_button.SetToolTip("This will try to re-schedule the cadence in order to meet your set criterias. The result will be outputed in the box to your right, and also be put into the clip-board.")
        self.cadence_rescheduler_calculate_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        #RESULT OF RE-SCHEDULING BOX
        self.cadence_rescheduler_result_text = wx.StaticText(self.panel, label="Result:", pos=(trbX+40, tbrY+472))
        self.cadence_rescheduler_result_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(360,20), pos=(trbX+80, tbrY+470))
        self.cadence_rescheduler_result_input_box.SetHint("<The result, and proposed cadence schedule will be showed here>")
        self.cadence_rescheduler_result_input_box.SetToolTip("The result, and proposed cadence schedule will be showed here.")
        #INFORMATIVE MESSAGES OF THE RESULTING CALCULATION
        self.cadence_rescheduler_result_informational_text = wx.StaticText(self.panel, label="Informational:", pos=(trbX-40, tbrY+492))
        self.cadence_rescheduler_result_informational_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(420,20), pos=(trbX+40, tbrY+490))
        self.cadence_rescheduler_result_informational_input_box.SetHint("<Informational messages after running a \"Re-schedule\" will be shown here>")
        self.cadence_rescheduler_result_informational_input_box.SetToolTip("Informational messages after running a \"Re-schedule\" will be shown here.")


        #COMBOBOX TEXT FOR CHOOSING A BEZIER CURVE
        self.bezier_points_input_box_text = wx.StaticText(self.panel, label="Curve type", pos=(trbX+560, tbrY+26))

        #COMBOBOX FOR CHOOSING A BEZIER CURVE
        beziers = ['ease', 'linear', 'ease-in', 'ease-out', 'ease-in-out']
        self.bezier_chooser_choice = wx.Choice(self.panel, id=wx.ID_ANY,  pos=(trbX+560, tbrY+46),size=(100,40), choices=beziers, style=0, name="Arne")
        self.bezier_chooser_choice.SetToolTip("Choose the curve that should be used when using the \"arm\"-functionality on a motion")
        self.bezier_chooser_choice.Bind(wx.EVT_CHOICE, self.OnBezierChoice)
        self.bezier_chooser_choice.SetSelection(1)

        #INPUT BOX FOR BEZIER POINTS
        self.bezier_points_input_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(100, 20), pos=(trbX + 560, tbrY+70))
        self.bezier_points_input_box.SetToolTip("The cubic bezier point, which can be changed or will be populated accoring to what pre-defined curve you chose above.")
        self.bezier_points_input_box.SetValue("(0, 0), (1, 1)")

        #self.cadence_rescheduler_url_input_box.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        #Checkbox stuff
        #self.cadence_schedule_Checkbox = wx.CheckBox(self.panel, label = "Use C.", id=73, pos=(trbX+1000-66, tbrY-20))
        #self.cadence_schedule_Checkbox.SetToolTip("When checked, tells Deforum to use this Cadence Schedule.")
        #self.cadence_schedule_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)


        self.Centre()
        self.Show()
        self.Fit()

        self.loadAllValues()
        if not should_use_total_recall:
            self.setAllComponentValues()
        #KEYBOARD INPUT EVNTG HANDLER
        self.off_grid_input_box.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.off_grid_input_box.SetFocus()

        self.Layout()
        self.Bind(wx.EVT_SIZING, self.OnResize)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.PanelClicked)


    def OnKeyEvent_Empty(self, e): #Dummy Event handler to not get BEEP sound when Ctrl+S
        e.Skip()

    def rasgnar(selfself, e):
        print("hej")
    def OnKeyEvent(self, e):
        keycode = e.GetKeyCode()
        controlDown = e.CmdDown()
        altDown = e.AltDown()
        shiftDown = e.ShiftDown()
        if keycode == 83 and controlDown:
            event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            event.SetEventObject(self.update_prompts)
            event.SetId(self.update_prompts.GetId())
            self.update_prompts.GetEventHandler().ProcessEvent(event)
        else:
            e.Skip()
    def OnBezierChoice(self, event):
        global bezierArray
        selectionString = self.bezier_chooser_choice.GetString(self.bezier_chooser_choice.GetSelection())
        print("You choose:" + self.bezier_chooser_choice.GetString(self.bezier_chooser_choice.GetSelection()))

        if selectionString == 'ease':
            self.bezier_points_input_box.SetValue("(0.25, 0.1), (0.25, 1)")
        elif selectionString == 'linear':
            self.bezier_points_input_box.SetValue("(0, 0), (1, 1)")
        elif selectionString == 'ease-in':
            self.bezier_points_input_box.SetValue("(.42, 0), (1, 1)")
        elif selectionString == 'ease-out':
            self.bezier_points_input_box.SetValue("(0, 0), (.58, 1)")
        elif selectionString == 'ease-in-out':
            self.bezier_points_input_box.SetValue("(.42, 0), (.58, 1)")

    def OnMotionChoice(self, event):
        #print("Selection index:" + str(self.predefined_motion_choice.GetSelection()))
        index = self.predefined_motion_choice.GetSelection()
        #print("Values:" + str(self.predefined_motions_line[index]))
    def OnFPSChoice(self, event):
        #print("Selection index:" + str(self.predefined_motion_fps_choice.GetSelection()))
        indexFPS = self.predefined_motion_fps_choice.GetSelection()
        #print("Values:" + str(self.predefined_motions_fps_line[indexFPS]))

        indexRange = self.predefined_motion_range_choice.GetSelection()

        self.loadPredefinedMotions(filterFPS=self.predefined_motions_fps_line[indexFPS], filterRange=self.range_filters[indexRange])
        self.predefined_motion_choice.SetSelection(0)
        self.predefined_motion_fps_choice.SetSelection(indexFPS)
        self.predefined_motion_range_choice.SetSelection(indexRange)

    def OnRangeChoice(self, event):
        #print("Selection index:" + str(self.predefined_motion_range_choice.GetSelection()))
        indexRange = self.predefined_motion_range_choice.GetSelection()
        #print("Values:" + str(self.range_filters[indexRange]))

        indexFPS = self.predefined_motion_fps_choice.GetSelection()

        self.loadPredefinedMotions(filterRange=self.range_filters[indexRange], filterFPS=self.predefined_motions_fps_line[indexFPS])
        self.predefined_motion_choice.SetSelection(0)
        self.predefined_motion_range_choice.SetSelection(indexRange)
        self.predefined_motion_fps_choice.SetSelection(indexFPS)

    def OnComponentChoice(self, event):
        print("You choose:"+ self.component_chooser_choice.GetString(self.component_chooser_choice.GetSelection()))
        selectionString = self.component_chooser_choice.GetString(self.component_chooser_choice.GetSelection())
        if selectionString == "Noise Multiplier":
            self.noise_slider.Show()
            self.noise_slider_Text.Show()
            self.perlin_octave_slider.Hide()
            self.perlin_octave_slider_Text.Hide()
            self.perlin_persistence_slider.Hide()
            self.perlin_persistence_slider_Text.Hide()
        elif selectionString == "Perlin Octaves":
            self.noise_slider.Hide()
            self.noise_slider_Text.Hide()
            self.perlin_octave_slider.Show()
            self.perlin_octave_slider_Text.Show()
            self.perlin_persistence_slider.Hide()
            self.perlin_persistence_slider_Text.Hide()
        elif selectionString == "Perlin Persistence":
            self.noise_slider.Hide()
            self.noise_slider_Text.Hide()
            self.perlin_octave_slider.Hide()
            self.perlin_octave_slider_Text.Hide()
            self.perlin_persistence_slider.Show()
            self.perlin_persistence_slider_Text.Show()

    def OnRadioBoxCN(self, event):
        btn = self.rbox.GetStringSelection()
        #print(btn)
        currentActive = int(btn[int(len(btn)-1)])
        #print("IT IS CN:"+str(currentActive))
        self.SetCurrentActiveCN(currentActive)

    def OnShouldHide(self, event):
        global tbrY
        global screenWidth
        global screenHeight
        eventID = event.GetId()
        if eventID == 101:
            if self.positive_prompt_input_ctrl.IsShown():
                self.positive_prompt_input_ctrl.Hide()
                self.positive_prompt_input_ctrl_hide_box.SetLabel("Show")
                tbrY = tbrY - 100
                screenHeight = screenHeight - 100
            else:
                self.positive_prompt_input_ctrl.Show()
                self.positive_prompt_input_ctrl_hide_box.SetLabel("Hide")
                tbrY = tbrY + 100
                screenHeight = screenHeight + 100
        elif eventID == 102:
            if self.positive_prompt_input_ctrl_2.IsShown():
                self.positive_prompt_input_ctrl_2.Hide()
                self.positive_prompt_input_ctrl_hide_box_2.SetLabel("Show")
                tbrY = tbrY - 50
                screenHeight = screenHeight - 50
            else:
                self.positive_prompt_input_ctrl_2.Show()
                self.positive_prompt_input_ctrl_hide_box_2.SetLabel("Hide")
                tbrY = tbrY + 50
                screenHeight = screenHeight + 50
        elif eventID == 103:
            if self.positive_prompt_input_ctrl_3.IsShown():
                self.positive_prompt_input_ctrl_3.Hide()
                self.positive_prompt_input_ctrl_hide_box_3.SetLabel("Show")
                tbrY = tbrY - 50
                screenHeight = screenHeight - 50
            else:
                self.positive_prompt_input_ctrl_3.Show()
                self.positive_prompt_input_ctrl_hide_box_3.SetLabel("Hide")
                tbrY = tbrY + 50
                screenHeight = screenHeight + 50
        elif eventID == 104:
            if self.positive_prompt_input_ctrl_4.IsShown():
                self.positive_prompt_input_ctrl_4.Hide()
                self.positive_prompt_input_ctrl_hide_box_4.SetLabel("Show")
                tbrY = tbrY - 50
                screenHeight = screenHeight - 50
            else:
                self.positive_prompt_input_ctrl_4.Show()
                self.positive_prompt_input_ctrl_hide_box_4.SetLabel("Hide")
                tbrY = tbrY + 50
                screenHeight = screenHeight + 50
        elif eventID == 105:
            if self.negative_prompt_input_ctrl.IsShown():
                self.negative_prompt_input_ctrl.Hide()
                self.negative_prompt_input_ctrl_hide_box.SetLabel("Show")
                tbrY = tbrY - 100
                screenHeight = screenHeight - 100
            else:
                self.negative_prompt_input_ctrl.Show()
                self.negative_prompt_input_ctrl_hide_box.SetLabel("Hide")
                tbrY = tbrY + 100
                screenHeight = screenHeight + 100

        self.SetSize(screenWidth, screenHeight)
        self.updateComponents()
        self.panel.Refresh()
        self.panel.Layout()

    def updateComponents(self):
        #self.shouldUseDeforumPromptScheduling_Checkbox.SetPosition((trbX + 600, 10))
        self.stayOnTop_Checkbox.SetPosition((trbX + 1130, 10))
        self.live_render_checkbox.SetPosition((trbX + 1130-340, tbrY - 110))
        self.show_current_image.SetPosition((trbX + 992-340, tbrY - 110))
        self.rewind_button.SetPosition((trbX + 1000-340, tbrY - 80))
        self.rewind_closest_button.SetPosition((trbX + 970-340, tbrY - 80))
        self.frame_step_input_box.SetPosition((trbX + 1032-340, tbrY - 74))
        self.forward_button.SetPosition((trbX + 1080-340, tbrY - 80))
        self.forward_closest_button.SetPosition((trbX + 1110-340, tbrY - 80))
        self.set_current_image.SetPosition((trbX + 998-340, tbrY - 40))
        self.bitmap.SetPosition((trbX + 650 +340, tbrY - 100))
        self.pan_step_input_box.SetPosition((trbX - 15, 30 + tbrY))
        self.pan_X_Value_Text.SetPosition((trbX-26, 55+tbrY+5+15))
        self.pan_Y_Value_Text.SetPosition((40 + trbX, 5 + tbrY))

        self.pan_X_Sirup_Value_Text.SetPosition((trbX-26, 55+tbrY+20+15))
        self.pan_Y_Sirup_Value_Text.SetPosition((40+trbX, 5+tbrY+15))


        self.transform_x_left_button.SetPosition((5 + trbX, 55 + tbrY+15))
        self.transform_y_upp_button.SetPosition((35 + trbX, 25 + tbrY+15))
        self.transform_x_right_button.SetPosition((65 + trbX, 55 + tbrY+15))
        self.transform_y_down_button.SetPosition((35 + trbX, 85 + tbrY+15))
        self.transform_zero_button.SetPosition((35 + trbX, 56 + tbrY+15))
        self.zero_pan_step_input_box_text.SetPosition((trbX + 74, tbrY + 14))
        self.zero_pan_step_input_box.SetPosition((trbX + 70, tbrY + 30))
        self.zero_rotate_step_input_box_text.SetPosition((240 + trbX + 43 + 100, 55 + tbrY - 40))
        self.zero_rotate_step_input_box.SetPosition((240 + trbX + 40 + 100, 55 + tbrY - 25))
        self.zoom_slider.SetPosition((142+trbX, tbrY+5))
        self.ZOOM_X_Text.SetPosition((170 + trbX, tbrY + 40))
        self.ZOOM_X_Text2.SetPosition((170 + trbX, tbrY + 60))
        self.ZOOM_X_Text3.SetPosition((170 + trbX, tbrY + 80))
        self.ZOOM_X_Text4.SetPosition((169 + trbX, tbrY + 100))
        self.zoom_value_text.SetPosition((116+trbX, tbrY+65))
        self.zoom_value_high_text.SetPosition((140+trbX, tbrY-7))
        self.zoom_value_low_text.SetPosition((136+trbX, tbrY+138))
        self.zoom_step_input_box.SetPosition((105+trbX, tbrY+115))

        self.fov_slider.SetPosition((190 + trbX, tbrY - 5))
        self.FOV_Text.SetPosition((250 + trbX, tbrY + 40))
        self.FOV_Text2.SetPosition((249 + trbX, tbrY + 60))
        self.FOV_Text3.SetPosition((250 + trbX, tbrY + 80))
        self.fov_lock_button.SetPosition((172+trbX, tbrY+6))
        self.fov_reverse_lock_button.SetPosition((172 + trbX, tbrY + 120))

        self.arm_zoom_button.SetPosition((trbX+230, tbrY-10))
        self.zero_zoom_step_input_box_text.SetPosition((trbX+256, tbrY-15))
        self.zero_zoom_step_input_box.SetPosition((trbX+254, tbrY))
        self.zoom_zero_button.SetPosition((trbX+258, tbrY+20))

        self.strength_schedule_slider.SetPosition((trbX - 25, tbrY - 50))
        #self.parseq_strength_button.SetPosition((trbX-45, tbrY-46))
        #self.parseq_movements_button.SetPosition((trbX+280, tbrY+100))
        self.step_schedule_Text.SetPosition((trbX - 25, tbrY - 70))
        self.should_use_deforumation_strength_checkbox.SetPosition((trbX+60, tbrY-66))
        self.should_use_deforumation_cfg_checkbox.SetPosition((trbX+460, tbrY-66))
        self.should_use_deforumation_cadence_checkbox.SetPosition((trbX+780, tbrY))
        self.should_use_deforumation_noise_checkbox.SetPosition((trbX+720, tbrY+74))
        self.should_use_deforumation_panning_checkbox.SetPosition((trbX+40, tbrY-8))
        self.should_use_deforumation_zoomfov_checkbox.SetPosition((trbX + 172, tbrY - 8))
        self.should_use_deforumation_rotation_checkbox.SetPosition((trbX+354, tbrY-8))
        self.should_use_deforumation_tilt_checkbox.SetPosition((trbX+480, tbrY-2))

        self.zero_pan_current_settings_Text.SetPosition((trbX - 40 , tbrY - 150))
        self.zero_zoom_current_settings_Text.SetPosition((trbX + 250 - 10, tbrY - 150))
        self.zero_rotate_current_settings_Text.SetPosition((trbX + 440 - 20, tbrY - 150))
        self.zero_tilt_current_settings_Text.SetPosition((trbX + 720 - 4, tbrY - 150))

        self.sample_schedule_slider.SetPosition((trbX - 25, tbrY - 50 - 70))
        self.strength_schedule_Text.SetPosition((trbX - 25, tbrY - 70 - 64))
        self.seed_schedule_Text.SetPosition((trbX + 340, tbrY - 50 - 80))
        self.seed_input_box.SetPosition((trbX + 340, tbrY - 50 - 60))
        self.cfg_schedule_slider.SetPosition((trbX + 340, tbrY - 50))
        self.CFG_scale_Text.SetPosition((trbX + 340, tbrY - 70))
        self.rotation_3d_x_left_button.SetPosition((240 + trbX + 80, 55 + tbrY))
        self.rotation_3d_x_Value_Text.SetPosition((240 + trbX - 30 + 80, 55 + tbrY + 5))
        self.rotate_step_input_box.SetPosition((240 + trbX - 15 + 80, 30 + tbrY))
        self.rotation_3d_y_up_button.SetPosition((240 + trbX + 30 + 80, 55 + tbrY - 30))
        self.rotation_3d_y_Value_Text.SetPosition((240 + trbX + 35 + 80, 55 + tbrY - 48))
        self.rotation_3d_x_right_button.SetPosition((240 + trbX + 57 + 80, 55 + tbrY))
        self.rotation_3d_y_down_button.SetPosition((240 + trbX + 30 + 80, 55 + tbrY + 30))
        self.rotation_3d_z_left_button.SetPosition((300 + trbX + 57 + 80, 50 + tbrY))
        self.rotate_zero_button.SetPosition((240 + trbX + 30 + 80, 55 + tbrY))
        self.rotation_3d_z_right_button.SetPosition((380 + trbX + 57 + 80, 50 + tbrY))
        self.rotation_Z_Value_Text.SetPosition((360 + trbX + 46 + 80, 60 + tbrY))
        self.tilt_zero_button.SetPosition((360 + trbX + 36 + 80, 88 + tbrY))
        self.tilt_step_input_box.SetPosition((360 + trbX + 10 + 80, 30 + tbrY))
        self.zero_tilt_step_input_box.SetPosition((360 + trbX + 34 + 110, 30 + tbrY))
        self.zero_tilt_step_input_box_text.SetPosition((360 + trbX + 36 + 110, 14 + tbrY))
        self.arm_tilt_button.SetPosition((360 + trbX + 10 + 80, tbrY))
        self.cadence_slider.SetPosition((trbX + 1000-340, tbrY + 20))
        self.cadence_slider_Text.SetPosition((trbX + 1000-340, tbrY))
        self.cadence_schedule_input_box.SetPosition((trbX+1000-220, tbrY-22))
        self.cadence_schedule_Checkbox.SetPosition((trbX+1000-66, tbrY-20))
        self.cadence_suggestion.SetPosition((trbX+1000-140, tbrY))
        #CN
        self.rbox.SetPosition((trbX+320, tbrY+124))
        for cnIndex in range(5):
            self.control_net_weight_slider[cnIndex].SetPosition((trbX-40, tbrY+190))
            self.control_net_weight_slider_Text[cnIndex].SetPosition((trbX-40, tbrY+175))
            self.control_net_stepstart_slider[cnIndex].SetPosition((trbX+300, tbrY+190))
            self.control_net_stepstart_slider_Text[cnIndex].SetPosition((trbX+300, tbrY+175))
            self.control_net_stepend_slider[cnIndex].SetPosition((trbX+640, tbrY+190))
            self.control_net_stepend_slider_Text[cnIndex].SetPosition((trbX+640, tbrY+175))
            self.control_net_lowt_slider[cnIndex].SetPosition((trbX-40, tbrY+260))
            self.control_net_lowt_slider_Text[cnIndex].SetPosition((trbX-40, tbrY+240))
            self.control_net_hight_slider[cnIndex].SetPosition((trbX+300, tbrY+260))
            self.control_net_hight_slider_Text[cnIndex].SetPosition((trbX+300, tbrY+240))
            self.control_net_active_checkbox[cnIndex].SetPosition((trbX + 250, tbrY + 148))

        #END CN
        #self.Send_URL_to_Deforum.SetPosition((trbX + 820, tbrY + 242))
        #self.Parseq_URL_input_box.SetPosition((trbX + 640, tbrY + 265))
        #self.Parseq_URL_input_box_text.SetPosition((trbX + 640, tbrY + 245))
        #self.Parseq_activation_Checkbox.SetPosition((trbX+780, tbrY + 245))
        self.replay_input_box_text.SetPosition((trbX+990, tbrY-130))
        self.replay_from_input_box.SetPosition((trbX+1030, tbrY-131))
        self.replay_to_input_box.SetPosition((trbX+1090, tbrY-131))
        self.replay_input_divider_box_text.SetPosition((trbX+1077, tbrY-130))
        self.replay_button.SetPosition((trbX + 1145, tbrY -135))
        self.fps_input_box_text.SetPosition((trbX+1180, tbrY-130))
        self.fix_aspect_ratio_liverender_button.SetPosition((trbX+1244, tbrY-132))
        self.replay_fps_input_box.SetPosition((trbX+1200, tbrY-131))
        self.arm_pan_button.SetPosition((trbX-15, tbrY))
        self.arm_rotation_button.SetPosition((240+trbX+80, tbrY))
        self.deforum_strength_value_info_text.SetPosition((trbX-40, tbrY+310))
        self.deforum_trx_value_info_text.SetPosition((trbX+40, tbrY+310))
        self.deforum_try_value_info_text.SetPosition((trbX+100, tbrY+310))
        self.deforum_trz_value_info_text.SetPosition((trbX+160, tbrY+310))
        self.deforum_rox_value_info_text.SetPosition((trbX+220, tbrY+310))
        self.deforum_roy_value_info_text.SetPosition((trbX+280, tbrY+310))
        self.deforum_roz_value_info_text.SetPosition((trbX+340, tbrY+310))
        self.deforum_steps_value_info_text.SetPosition((trbX+400, tbrY+310))
        self.deforum_cfg_value_info_text.SetPosition((trbX+460, tbrY+310))
        self.deforum_cadence_value_info_text.SetPosition((trbX+520, tbrY+310))
        self.deforum_pdmotion_value_info_text.SetPosition((trbX + 600, tbrY + 310))
        self.deforum_zero_pan_value_info_text.SetPosition((trbX+720, tbrY+310))
        self.deforum_zero_zoom_value_info_text.SetPosition((trbX+800, tbrY+310))
        self.deforum_zero_rotation_value_info_text.SetPosition((trbX+890, tbrY+310))
        self.deforum_zero_tilt_value_info_text.SetPosition((trbX + 980, tbrY + 310))
        self.deforum_zero_pan_x_value_info_text.SetPosition((trbX + 660, tbrY + 250))
        self.deforum_zero_pan_y_value_info_text.SetPosition((trbX + 660, tbrY + 250+15))
        self.component_chooser_choice.SetPosition((trbX+950-150, tbrY+70))
        self.Live_Values_Checkbox.SetPosition((trbX-40, tbrY + 130))
        self.noise_slider.SetPosition((trbX+950-340, tbrY+110))
        self.perlin_persistence_slider.SetPosition((trbX+950-340, tbrY+110))
        self.perlin_octave_slider.SetPosition((trbX+950-340, tbrY+110))
        self.noise_slider_Text.SetPosition((trbX+1000-340, tbrY+95))
        self.perlin_octave_slider_Text.SetPosition((trbX+1000-340, tbrY+95))
        self.perlin_octave_slider_Text.SetPosition((trbX+1000-340, tbrY+95))

        self.cadence_rescheduler_text.SetPosition((trbX-40, tbrY+340))
        self.cadence_rescheduler_url_input_box.SetPosition((trbX-40, tbrY+380))
        self.cadence_rescheduler_disco_checkbox.SetPosition((trbX+220, tbrY+380))
        self.cadence_rescheduler_cadence_text.SetPosition((trbX-40, tbrY+402))
        self.cadence_rescheduler_cadence_input_box.SetPosition((trbX+46, tbrY+400))
        self.cadence_rescheduler_trigger_parameter_text.SetPosition((trbX-40, tbrY+422))
        self.cadence_rescheduler_trigger_parameter_input_box.SetPosition((trbX+62, tbrY+420))
        self.cadence_rescheduler_trigger_min_text.SetPosition((trbX-40, tbrY+442))
        self.cadence_rescheduler_trigger_min_input_box.SetPosition((trbX-10, tbrY+440))
        self.cadence_rescheduler_trigger_max_text.SetPosition((trbX+40, tbrY+442))
        self.cadence_rescheduler_trigger_max_input_box.SetPosition((trbX+70, tbrY+440))
        self.cadence_rescheduler_calculate_button.SetPosition((trbX-40, tbrY+470))
        self.cadence_rescheduler_result_text.SetPosition((trbX+40, tbrY+472))
        self.cadence_rescheduler_result_input_box.SetPosition((trbX+80, tbrY+470))
        self.cadence_rescheduler_result_informational_text.SetPosition((trbX-40, tbrY+492))
        self.cadence_rescheduler_result_informational_input_box.SetPosition((trbX+40, tbrY+490))
        self.bezier_chooser_choice.SetPosition((trbX+560, tbrY+46))
        self.bezier_points_input_box_text.SetPosition((trbX + 560, tbrY + 26))
        self.bezier_points_input_box.SetPosition((trbX + 560, tbrY+70))
        self.opticalflow_checkbox.SetPosition((trbX+1130-320, tbrY-74))
        self.cadence_flow_factor_box.SetPosition((trbX+1130-320, tbrY-54))
        self.generation_flow_factor_box.SetPosition((trbX+1130-290, tbrY-54))


    def SetCurrentActiveCN(self, cnSelectIndex):
        global current_active_cn_index
        current_active_cn_index = cnSelectIndex
        #UN-HIDE A CN (LAZY WAY OF HIDE UNHIDE)
        for cnIndex in range(5):
            if (cnSelectIndex-1) == cnIndex:
                self.control_net_weight_slider_Text[cnIndex].Show()
                self.control_net_weight_slider[cnIndex].Show()
                self.control_net_stepstart_slider[cnIndex].Show()
                self.control_net_stepstart_slider_Text[cnIndex].Show()
                self.control_net_stepend_slider[cnIndex].Show()
                self.control_net_stepend_slider_Text[cnIndex].Show()
                self.control_net_lowt_slider[cnIndex].Show()
                self.control_net_lowt_slider_Text[cnIndex].Show()
                self.control_net_hight_slider[cnIndex].Show()
                self.control_net_hight_slider_Text[cnIndex].Show()
                self.control_net_active_checkbox[cnIndex].Show()
            else:
                self.control_net_weight_slider_Text[cnIndex].Hide()
                self.control_net_weight_slider[cnIndex].Hide()
                self.control_net_stepstart_slider[cnIndex].Hide()
                self.control_net_stepstart_slider_Text[cnIndex].Hide()
                self.control_net_stepend_slider[cnIndex].Hide()
                self.control_net_stepend_slider_Text[cnIndex].Hide()
                self.control_net_lowt_slider[cnIndex].Hide()
                self.control_net_lowt_slider_Text[cnIndex].Hide()
                self.control_net_hight_slider[cnIndex].Hide()
                self.control_net_hight_slider_Text[cnIndex].Hide()
                self.control_net_active_checkbox[cnIndex].Hide()


    def OnResize(self, evt):
        global screenHeight
        global screenWidth
        self.current_width, self.current_height = self.GetSize()
        screenWidth, screenHeight = self.GetSize()
        #self.positive_prompt_input_ctrl.SetSize(-1, 40)
        #self.positive_prompt_input_ctrl.SetMinSize(size=(-1,20))
        #self.positive_prompt_input_ctrl.Hide()
        #self.positive_prompt_input_ctrl.Redo()
        #self.panel.Layout()
        #self.panel.resize(self.current_width, self.current_height)
        #print("width=" + str(self.current_width))
        #print("height=" + str(self.current_height))

    def PanelClicked(self, event):
        #print("Pushed pannel %s" % (event))
        evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
        evt.SetEventObject(self.show_current_image)
        evt.SetId(self.show_current_image.GetId())
        self.show_current_image.GetEventHandler().ProcessEvent(evt)

        self.off_grid_input_box.SetFocus()
    def KeyDown(self, event):
        keycode = event.GetKeyCode()
        #if keycode !=wx.WXK_NONE:
            #print("Pushed:" + str(keycode))
        if event.GetKeyCode() == pan_up_key:
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self.transform_y_upp_button)
            evt.SetId(self.transform_y_upp_button.GetId())
            self.transform_y_upp_button.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == pan_down_key:
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self.transform_y_down_button)
            evt.SetId(self.transform_y_down_button.GetId())
            self.transform_y_down_button.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == pan_left_key:
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self.transform_x_left_button)
            evt.SetId(self.transform_x_left_button.GetId())
            self.transform_x_left_button.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == pan_right_key:
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self.transform_x_right_button)
            evt.SetId(self.transform_x_right_button.GetId())
            self.transform_x_right_button.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == zoom_up_key:
            evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
            evt.SetEventObject(self.zoom_slider)
            evt.SetId(self.zoom_slider.GetId())
            self.zoom_slider.SetValue(self.zoom_slider.GetValue()+1*100)
            self.zoom_slider.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == zoom_down_key:
            evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
            evt.SetEventObject(self.zoom_slider)
            evt.SetId(self.zoom_slider.GetId())
            self.zoom_slider.SetValue(self.zoom_slider.GetValue()-1*100)
            self.zoom_slider.GetEventHandler().ProcessEvent(evt)


    def startMotion(self, motionIndex):
        self.ctrl[motionIndex].Play()

    def setTextColor(self, textObject, color, value):
        textObject.SetForegroundColour(color)
        textObject.SetLabel(value)
        textObject.Hide()
        textObject.Show()

    def setValuesFromSavedFrame(self, frameNumber):
        global Translation_X
        global Translation_Y
        global Translation_Z
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Z
        global Strength_Scheduler
        global CFG_Scale
        global FOV_Scale
        global is_fov_locked
        global is_reverse_fov_locked
        global STEP_Schedule
        global Cadence_Schedule
        global noise_multiplier
        global Perlin_Octave_Value
        global Perlin_Persistence_Value
        global is_paused_rendering
        global should_use_deforumation_strength
        global pan_left_key,pan_right_key,pan_up_key,pan_down_key,zoom_up_key,zoom_down_key
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT
        global CN_UDCn
        global should_use_deforumation_prompt_scheduling
        global should_use_deforumation_cfg
        global should_use_deforumation_cadence
        global should_use_deforumation_noise
        global should_use_deforumation_panning
        global should_use_deforumation_zoomfov
        global should_use_deforumation_rotation
        global should_use_deforumation_tilt
        global pan_step_input_box_value
        global rotate_step_input_box_value
        global tilt_step_input_box_value
        global zero_pan_step_input_box_value
        global zero_rotate_step_input_box_value
        global zero_zoom_step_input_box_value
        global shouldUseDeforumPromptScheduling
        global should_use_optical_flow
        global cadence_flow_factor
        global generation_flow_factor
        global parameter_container
        parameter_container = pickle.loads(readValue_special("saved_frame_params", frameNumber))
        if parameter_container != 0x0:
            if parameter_container and parameter_container != None:
                self.positive_prompt_input_ctrl.SetValue(parameter_container.Prompt_Positive)
                self.positive_prompt_input_ctrl_2.SetValue("")
                self.positive_prompt_input_ctrl_3.SetValue("")
                self.positive_prompt_input_ctrl_4.SetValue("")
                self.negative_prompt_input_ctrl.SetValue(parameter_container.Prompt_Negative)
                #Strength_Scheduler = float(parameter_container.strength_value)
                self.strength_schedule_slider.SetValue(int(float(parameter_container.strength_value)*100))
                #CFG_Scale = float(parameter_container.cfg_scale)
                self.cfg_schedule_slider.SetValue(int(float(parameter_container.cfg_scale)))
                #STEP_Schedule = int(parameter_container.steps)
                self.sample_schedule_slider.SetValue(int(parameter_container.steps))
                #FOV_Scale = float(parameter_container.fov)
                self.fov_slider.SetValue(int(float(parameter_container.fov)))
                #Translation_X = float(parameter_container.translation_x)
                if not armed_pan:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(parameter_container.translation_x)))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(parameter_container.translation_y)))
                else:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(Translation_X_ARMED)))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(Translation_Y_ARMED)))

                #Translation_Z = float(parameter_container.translation_z)
                #elif armed_pan:
                #    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(Translation_X_ARMED)))
                #    #Translation_Y = float(parameter_container.translation_y)
                #    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(Translation_Y_ARMED)))
                #    #Translation_Z = float(parameter_container.translation_z)

                #self.zoom_slider.SetValue(int(float(parameter_container.translation_z))*100)
                #self.zoom_value_text.SetLabel('%.2f' % (float(parameter_container.translation_z)))
                #Rotation_3D_X = float(parameter_container.rotation_x)
                #Rotation_3D_Y = float(parameter_container.rotation_y)
                #Rotation_3D_Z = float(parameter_container.rotation_z)
                if not armed_rotation:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_y)))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_x)))
                else:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Y_ARMED)))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_X_ARMED)))

                if not armed_zoom:
                    self.zoom_value_text.SetLabel(str('%.2f' % float(parameter_container.translation_z)))
                    self.zoom_slider.SetValue(int(float(parameter_container.translation_z) * 100))
                else:
                    self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z_ARMED)))
                    self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))

                if not armed_tilt:
                    self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_z)))
                else:
                    self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Z_ARMED)))


                #Cadence_Schedule = int(parameter_container.cadence)
                self.cadence_slider.SetValue(int(parameter_container.cadence))
                ###CN
                for cnIndex in range(5):
                    #CN_Weight[cnIndex] = float(parameter_container.cn_weight[cnIndex])
                    self.control_net_weight_slider[cnIndex].SetValue(int(float(parameter_container.cn_weight[cnIndex])*100))
                    #CN_StepStart[cnIndex] = float(parameter_container.cn_stepstart[cnIndex])
                    self.control_net_stepstart_slider[cnIndex].SetValue(int(float(parameter_container.cn_stepstart[cnIndex])*100))
                    #CN_StepEnd[cnIndex] = float(parameter_container.cn_stepend[cnIndex])
                    self.control_net_stepend_slider[cnIndex].SetValue(int(float(parameter_container.cn_stepend[cnIndex])*100))
                    #CN_LowT[cnIndex] = int(parameter_container.cn_lowt[cnIndex])
                    self.control_net_lowt_slider[cnIndex].SetValue(int(parameter_container.cn_lowt[cnIndex]))
                    #CN_HighT[cnIndex] = int(parameter_container.cn_hight[cnIndex])
                    self.control_net_hight_slider[cnIndex].SetValue(int(parameter_container.cn_hight[cnIndex]))
                    #CN_UDCn[cnIndex] = int(parameter_container.cn_udcn[cnIndex])
                    self.control_net_active_checkbox[cnIndex].SetValue(int(parameter_container.cn_udcn[cnIndex]))
                ##CN END
                #noise_multiplier = float(parameter_container.noise_multiplier)
                self.noise_slider.SetValue(int(float(parameter_container.noise_multiplier)*100))
                #Perlin_Octave_Value = int(parameter_container.perlin_octaves)
                self.perlin_octave_slider.SetValue(int(parameter_container.perlin_octaves))
                #Perlin_Persistence_Value = float(parameter_container.perlin_persistence)
                self.perlin_persistence_slider.SetValue(int(float(parameter_container.perlin_persistence)*100))

                #self.opticalflow_checkbox
                #cadence_flow_factor = int(parameter_container.cadence_flow_factor)
                #generation_flow_factor = int(parameter_container.generation_flow_factor)
                self.opticalflow_checkbox.SetValue(int(parameter_container.should_use_optical_flow))
                self.cadence_flow_factor_box.SetValue(str(int(parameter_container.cadence_flow_factor)))
                self.generation_flow_factor_box.SetValue(str(int(parameter_container.generation_flow_factor)))

                #seed
                #seedValue = int(parameter_container.seed_value)
                self.seed_input_box.SetValue(str(int(parameter_container.seed_value)))
        else:
            #print("Frame " + str(frameNumber)+ " has no stored recall values.")
            empty = 0
    def loadAllValues(self):
        global Translation_X
        global Translation_Y
        global Translation_Z
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Z
        global Strength_Scheduler
        global CFG_Scale
        global FOV_Scale
        global is_fov_locked
        global is_reverse_fov_locked
        global STEP_Schedule
        global Cadence_Schedule
        global noise_multiplier
        global Perlin_Octave_Value
        global Perlin_Persistence_Value
        global is_paused_rendering
        global should_use_deforumation_strength
        global pan_left_key,pan_right_key,pan_up_key,pan_down_key,zoom_up_key,zoom_down_key
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT
        global CN_UDCn
        global should_use_deforumation_prompt_scheduling
        global should_use_deforumation_cfg
        global should_use_deforumation_cadence
        global should_use_deforumation_noise
        global should_use_deforumation_panning
        global should_use_deforumation_zoomfov
        global should_use_deforumation_rotation
        global should_use_deforumation_tilt
        global pan_step_input_box_value
        global rotate_step_input_box_value
        global tilt_step_input_box_value
        global zero_pan_step_input_box_value
        global zero_rotate_step_input_box_value
        global zero_zoom_step_input_box_value
        global shouldUseDeforumPromptScheduling
        global should_use_optical_flow
        global cadence_flow_factor
        global generation_flow_factor
        global should_use_total_recall
        global should_use_total_recall_prompt
        global should_use_total_recall_movements
        global should_use_total_recall_others
        global should_use_deforumation_timestring
        global current_render_frame
        global current_frame
        global Translation_X_ARMED
        global Translation_Y_ARMED
        global Translation_Z_ARMED
        global Rotation_3D_X_ARMED
        global Rotation_3D_Y_ARMED
        global Rotation_3D_Z_ARMED
        if os.path.isfile(deforumationSettingsPath_Keys):
            deforumFile = open(deforumationSettingsPath_Keys, 'r')
            lines = deforumFile.readlines()
            for shortcut in lines:
                param = shortcut.strip('\n').replace(" ","").split('=')
                param_name = param[0]
                value = param[1]
                if param_name.lower() == 'pan_left_key':
                    pan_left_key = int(value)
                elif param_name.lower() == 'pan_right_key':
                    pan_right_key = int(value)
                elif param_name.lower() == 'pan_up_key':
                    pan_up_key = int(value)
                elif param_name.lower() == 'pan_down_key':
                    pan_down_key = int(value)
                elif param_name.lower() == 'zoom_up_key':
                    zoom_up_key = int(value)
                elif param_name.lower() == 'zoom_down_key':
                    zoom_down_key = int(value)

            deforumFile.close()

        if os.path.isfile(deforumationSettingsPath):
            try:
                deforumFile = open(deforumationSettingsPath, 'r')
                is_paused_rendering = int(deforumFile.readline().strip().strip('\n'))
                if is_paused_rendering:
                    self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
                else:
                    self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
                aLine = deforumFile.readline()
                aLine = aLine[:len(aLine)-1].replace('`^','\n')
                self.positive_prompt_input_ctrl.SetValue(aLine)
                aLine = deforumFile.readline()
                aLine = aLine[:len(aLine)-1].replace('`^','\n')
                self.positive_prompt_input_ctrl_2.SetValue(aLine)
                aLine = deforumFile.readline()
                aLine = aLine[:len(aLine)-1].replace('`^','\n')
                self.positive_prompt_input_ctrl_3.SetValue(aLine)
                aLine = deforumFile.readline()
                aLine = aLine[:len(aLine)-1].replace('`^','\n')
                self.positive_prompt_input_ctrl_4.SetValue(aLine)
                aLine = deforumFile.readline()
                aLine = aLine[:len(aLine)-1].replace('`^','\n')
                self.negative_prompt_input_ctrl.SetValue(aLine)
                Strength_Scheduler = float(deforumFile.readline().strip().strip('\n'))
                self.strength_schedule_slider.SetValue(int(Strength_Scheduler*100))
                CFG_Scale = float(deforumFile.readline().strip().strip('\n'))
                self.cfg_schedule_slider.SetValue(int(CFG_Scale))
                STEP_Schedule = int(deforumFile.readline().strip().strip('\n'))
                self.sample_schedule_slider.SetValue(STEP_Schedule)
                FOV_Scale = float(deforumFile.readline().strip().strip('\n'))
                self.fov_slider.SetValue(int(FOV_Scale))
                Translation_X = float(deforumFile.readline().strip().strip('\n'))
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                Translation_Y = float(deforumFile.readline().strip().strip('\n'))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                Translation_Z = float(deforumFile.readline().strip().strip('\n'))
                self.zoom_slider.SetValue(int(Translation_Z)*100)
                self.zoom_value_text.SetLabel('%.2f' % (Translation_Z))
                Rotation_3D_X = float(deforumFile.readline().strip().strip('\n'))
                Rotation_3D_Y = float(deforumFile.readline().strip().strip('\n'))
                Rotation_3D_Z = float(deforumFile.readline().strip().strip('\n'))
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))
                should_use_deforumation_prompt_scheduling = int(deforumFile.readline().strip().strip('\n'))
                if should_use_deforumation_prompt_scheduling:
                    #bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
                    #bmp = scale_bitmap(bmp, 15, 15)
                    #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                    self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
                    self.writeValue("should_use_deforumation_prompt_scheduling", 1)
                    shouldUseDeforumPromptScheduling = 1
                else:
                    #bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
                    #bmp = scale_bitmap(bmp, 15, 15)
                    #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                    self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
                    self.writeValue("should_use_deforumation_prompt_scheduling", 0)
                    shouldUseDeforumPromptScheduling = 0
                should_use_deforumation_strength = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_strength_checkbox.SetValue(int(should_use_deforumation_strength))
                should_use_deforumation_cfg = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_cfg_checkbox.SetValue(int(should_use_deforumation_cfg))
                should_use_deforumation_cadence = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_cadence_checkbox.SetValue(int(should_use_deforumation_cadence))
                should_use_deforumation_noise = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_noise_checkbox.SetValue(int(should_use_deforumation_noise))
                should_use_deforumation_panning = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_panning_checkbox.SetValue(int(should_use_deforumation_panning))
                should_use_deforumation_zoomfov = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_zoomfov_checkbox.SetValue(int(should_use_deforumation_zoomfov))
                should_use_deforumation_rotation = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_rotation_checkbox.SetValue(int(should_use_deforumation_rotation))
                should_use_deforumation_tilt = int(deforumFile.readline().strip().strip('\n'))
                self.should_use_deforumation_tilt_checkbox.SetValue(int(should_use_deforumation_tilt))

                pan_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.pan_step_input_box.SetValue(pan_step_input_box_value)
                rotate_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.rotate_step_input_box.SetValue(rotate_step_input_box_value)
                tilt_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.tilt_step_input_box.SetValue(tilt_step_input_box_value)
                Cadence_Schedule = int(deforumFile.readline().strip().strip('\n'))
                #print("CS:"+ str(Cadence_Schedule))
                self.cadence_slider.SetValue(Cadence_Schedule)
                zero_pan_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.zero_pan_step_input_box.SetValue(zero_pan_step_input_box_value)
                zero_rotate_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.zero_rotate_step_input_box.SetValue(zero_rotate_step_input_box_value)
                zero_zoom_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.zero_zoom_step_input_box.SetValue(zero_zoom_step_input_box_value)

                ###CN
                for cnIndex in range(5):
                    CN_Weight[cnIndex] = float(deforumFile.readline().strip().strip('\n'))
                    self.control_net_weight_slider[cnIndex].SetValue(int(CN_Weight[cnIndex]*100))
                    CN_StepStart[cnIndex] = float(deforumFile.readline().strip().strip('\n'))
                    self.control_net_stepstart_slider[cnIndex].SetValue(int(CN_StepStart[cnIndex]*100))
                    CN_StepEnd[cnIndex] = float(deforumFile.readline().strip().strip('\n'))
                    self.control_net_stepend_slider[cnIndex].SetValue(int(CN_StepEnd[cnIndex]*100))
                    CN_LowT[cnIndex] = int(deforumFile.readline().strip().strip('\n'))
                    self.control_net_lowt_slider[cnIndex].SetValue(CN_LowT[cnIndex])
                    CN_HighT[cnIndex] = int(deforumFile.readline().strip().strip('\n'))
                    self.control_net_hight_slider[cnIndex].SetValue(CN_HighT[cnIndex])
                    CN_UDCn[cnIndex] = int(deforumFile.readline().strip().strip('\n'))
                    self.control_net_hight_slider[cnIndex].SetValue(CN_UDCn[cnIndex])

                ##CN END
                noise_multiplier = float(deforumFile.readline().strip().strip('\n'))
                self.noise_slider.SetValue(int(float(noise_multiplier)*100))
                Perlin_Octave_Value = int(deforumFile.readline().strip().strip('\n'))
                self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
                Perlin_Persistence_Value = float(deforumFile.readline().strip().strip('\n'))
                self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value)*100))

                #Optical Flow values

                should_use_optical_flow = int(deforumFile.readline().strip().strip('\n'))
                self.opticalflow_checkbox.SetValue(int(should_use_optical_flow))

                #self.opticalflow_checkbox
                cadence_flow_factor = int(deforumFile.readline().strip().strip('\n'))
                generation_flow_factor = int(deforumFile.readline().strip().strip('\n'))
                self.cadence_flow_factor_box.SetValue(str(cadence_flow_factor))
                self.generation_flow_factor_box.SetValue(str(generation_flow_factor))

                self.ffmpeg_path_input_box.SetValue(deforumFile.readline().strip().strip('\n'))
                #self.audio_path_input_box.SetValue(deforumFile.readline().strip().strip('\n'))
                self.audio_path2_input_box.SetPath(deforumFile.readline().strip().strip('\n'))
                self.backend_chooser_choice.SetSelection(int(deforumFile.readline().strip('\n')))

                zero_tilt_step_input_box_value = deforumFile.readline().strip().strip('\n')
                self.zero_tilt_step_input_box.SetValue(zero_tilt_step_input_box_value)


            except Exception as e:
                print(e)
            self.writeValue("is_paused_rendering", is_paused_rendering)
            positive_prio = {
                int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
            sortedDict = sorted(positive_prio.items())
            totalPossitivePromptString = sortedDict[0][1]
            if sortedDict[1][1] !="":
                totalPossitivePromptString += "," + sortedDict[1][1]
            if sortedDict[2][1] !="":
                totalPossitivePromptString += "," + sortedDict[2][1]
            if sortedDict[3][1] !="":
                totalPossitivePromptString += "," + sortedDict[3][1]

            should_use_total_recall = int(self.readValue("should_use_total_recall"))
            if should_use_total_recall == 1:
                Translation_X_ARMED = 0
                Translation_Y_ARMED = 0
                Translation_Z_ARMED = 0
                Rotation_3D_X_ARMED = 0
                Rotation_3D_Y_ARMED = 0
                Rotation_3D_Z_ARMED = 0

            if not should_use_total_recall:
                self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ' ') + "\n")
                self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ' ') + "\n")
                self.writeValue("strength", Strength_Scheduler)
                self.writeValue("cfg", CFG_Scale)
                self.writeValue("steps", STEP_Schedule)
                self.writeValue("fov", FOV_Scale)
                self.writeValue("translation_x", Translation_X)
                self.writeValue("translation_y", Translation_Y)
                self.writeValue("translation_z", Translation_Z)
                self.writeValue("rotation_x", Rotation_3D_X)
                self.writeValue("rotation_y", Rotation_3D_Y)
                self.writeValue("rotation_z", Rotation_3D_Z)
                self.writeValue("should_use_deforumation_prompt_scheduling", int(should_use_deforumation_prompt_scheduling))
                self.writeValue("should_use_deforumation_strength", int(should_use_deforumation_strength))
                self.writeValue("should_use_deforumation_cfg", int(should_use_deforumation_cfg))
                self.writeValue("should_use_deforumation_cadence", int(should_use_deforumation_cadence))
                self.writeValue("should_use_deforumation_noise", int(should_use_deforumation_noise))
                self.writeValue("should_use_deforumation_panning", int(should_use_deforumation_panning))
                self.writeValue("should_use_deforumation_zoomfov", int(should_use_deforumation_zoomfov))
                self.writeValue("should_use_deforumation_rotation", int(should_use_deforumation_rotation))
                self.writeValue("should_use_deforumation_tilt", int(should_use_deforumation_tilt))
                self.writeValue("cadence", int(Cadence_Schedule))
                for cnIndex in range(5):
                    self.writeValue("cn_weight"+str(cnIndex+1), float(CN_Weight[cnIndex]))
                    self.writeValue("cn_stepstart"+str(cnIndex+1), float(CN_StepStart[cnIndex]))
                    self.writeValue("cn_stepend"+str(cnIndex+1), float(CN_StepEnd[cnIndex]))
                    self.writeValue("cn_lowt"+str(cnIndex+1), float(CN_LowT[cnIndex]))
                    self.writeValue("cn_hight"+str(cnIndex+1), float(CN_HighT[cnIndex]))
                    self.writeValue("cn_udcn" + str(cnIndex + 1), int(CN_UDCn[cnIndex]))

                self.writeValue("noise_multiplier", float(noise_multiplier))
                self.writeValue("perlin_octaves", int(Perlin_Octave_Value))
                self.writeValue("perlin_persistence", float(Perlin_Persistence_Value))
                self.writeValue("use_deforumation_cadence_scheduling", 0)

                self.writeValue("should_use_optical_flow", int(should_use_optical_flow))
                self.writeValue("cadence_flow_factor", int(cadence_flow_factor))
                self.writeValue("generation_flow_factor", int(generation_flow_factor))

            #Total recall values

            self.should_use_total_recall_checkbox.SetValue(should_use_total_recall)
            should_use_total_recall_movements = int(self.readValue("should_use_total_recall_movements"))
            self.should_use_total_recall_movement_checkbox.SetValue(should_use_total_recall_movements)
            should_use_total_recall_others = int(self.readValue("should_use_total_recall_others"))
            self.should_use_total_recall_others_checkbox.SetValue(should_use_total_recall_others)
            should_use_total_recall_prompt = int(self.readValue("should_use_total_recall_prompt"))
            self.should_use_total_recall_prompt_checkbox.SetValue(should_use_total_recall_prompt)
            tr_fromValue = int(self.readValue("total_recall_from"))
            tr_toValue = int(self.readValue("total_recall_to"))
            self.total_recall_from_input_box.SetValue(str(tr_fromValue))
            self.total_recall_to_input_box.SetValue(str(tr_toValue))

            should_use_deforumation_timestring = int(self.readValue("should_use_deforumation_timestring"))
            self.should_use_deforumation_start_string_checkbox.SetValue(should_use_deforumation_timestring)

            #Get Number of recall points
            number_of_recalled_frames = int(self.readValue("get_number_of_recalled_frames"))
            self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))

            #Fix to current image
            current_frame = self.readValue("start_frame")
            self.frame_step_input_box.SetValue(str(current_frame))
            current_render_frame = int(current_frame)
            self.loadCurrentPrompt("P", current_frame, 1)
            self.loadCurrentPrompt("N", current_frame, 1)
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self.show_current_image)
            evt.SetId(self.show_current_image.GetId())
            self.show_current_image.GetEventHandler().ProcessEvent(evt)

        else:
            self.writeAllValues()
    def writeValue(self, param, value):
        checkerrorConnecting = True
        while checkerrorConnecting:
            try:
                asyncio.run(sendAsync([1, param, value]))
                checkerrorConnecting = False
            except Exception as e:
                #print("Deforumation Mediator Error:" + str(e))
                #print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...writing:"+str(param))
                time.sleep(0.05)

    def readValue(self, param, value = 0):
        checkerrorConnecting = True
        while checkerrorConnecting:
            try:
                return_value = asyncio.run(sendAsync([0, param, value]))
                #print("All good reading:" + str(param))
                return return_value
            except Exception as e:
                #print("Deforumation Mediator Error:" + str(e))
                #print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...ererror:reading:"+str(param))
                time.sleep(0.05)

    def setAllPromptCopmponentValues(self):
        if should_use_deforumation_prompt_scheduling:
            self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
            self.writeValue("should_use_deforumation_prompt_scheduling", 1)
        else:
            self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
            self.writeValue("should_use_deforumation_prompt_scheduling", 0)
        self.loadCurrentPrompt("P", current_render_frame, 0)
        self.loadCurrentPrompt("N", current_render_frame, 0)

    def setAllMotionComponentValues(self):
        self.fov_slider.SetValue(int(FOV_Scale))
        self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
        self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
        self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
        self.zoom_slider.SetValue(int(Translation_Z) * 100)
        self.zoom_value_text.SetLabel('%.2f' % (Translation_Z))
        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
        self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))
        self.should_use_deforumation_zoomfov_checkbox.SetValue(int(should_use_deforumation_zoomfov))
        self.should_use_deforumation_rotation_checkbox.SetValue(int(should_use_deforumation_rotation))
        self.should_use_deforumation_tilt_checkbox.SetValue(int(should_use_deforumation_tilt))
        self.should_use_deforumation_panning_checkbox.SetValue(int(should_use_deforumation_panning))
        #self.zero_pan_step_input_box.SetValue(zero_pan_step_input_box_value)
        #self.zero_rotate_step_input_box.SetValue(zero_rotate_step_input_box_value)
        #self.zero_zoom_step_input_box.SetValue(zero_zoom_step_input_box_value)
        self.pan_step_input_box.SetValue(pan_step_input_box_value)
        self.rotate_step_input_box.SetValue(rotate_step_input_box_value)
        self.tilt_step_input_box.SetValue(tilt_step_input_box_value)

    def setAllOtherComponentValues(self):
        # OTHER COMPONENTS
        self.strength_schedule_slider.SetValue(int(Strength_Scheduler * 100))
        self.cfg_schedule_slider.SetValue(int(CFG_Scale))
        self.sample_schedule_slider.SetValue(STEP_Schedule)
        self.seed_input_box.SetValue(str(seedValue))
        self.should_use_deforumation_strength_checkbox.SetValue(int(should_use_deforumation_strength))
        self.should_use_deforumation_cfg_checkbox.SetValue(int(should_use_deforumation_cfg))
        self.should_use_deforumation_cadence_checkbox.SetValue(int(should_use_deforumation_cadence))
        self.should_use_deforumation_noise_checkbox.SetValue(int(should_use_deforumation_noise))
        self.cadence_slider.SetValue(Cadence_Schedule)
        for cnIndex in range(5):
            self.control_net_weight_slider[cnIndex].SetValue(int(CN_Weight[cnIndex] * 100))
            self.control_net_stepstart_slider[cnIndex].SetValue(int(CN_StepStart[cnIndex] * 100))
            self.control_net_stepend_slider[cnIndex].SetValue(int(CN_StepEnd[cnIndex] * 100))
            self.control_net_lowt_slider[cnIndex].SetValue(CN_LowT[cnIndex])
            self.control_net_hight_slider[cnIndex].SetValue(CN_HighT[cnIndex])
            self.control_net_active_checkbox[cnIndex].SetValue(CN_UDCn[cnIndex])

        self.noise_slider.SetValue(int(float(noise_multiplier) * 100))
        self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
        self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value) * 100))

        self.opticalflow_checkbox.SetValue(int(should_use_optical_flow))
        self.cadence_flow_factor_box.SetValue(str(cadence_flow_factor))
        self.generation_flow_factor_box.SetValue(str(generation_flow_factor))

    def setAllComponentValues(self):
        try:
            if is_paused_rendering:
                self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            else:
                self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            #PROMPT COMPONENTS
            if should_use_deforumation_prompt_scheduling == 1:
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
                self.writeValue("should_use_deforumation_prompt_scheduling", 1)
            else:
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
                self.writeValue("should_use_deforumation_prompt_scheduling", 0)
            self.loadCurrentPrompt("P", current_render_frame, 0)
            self.loadCurrentPrompt("N", current_render_frame, 0)

            #MOTION COMPONENTS
            self.fov_slider.SetValue(int(FOV_Scale))
            self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
            self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
            self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            self.zoom_slider.SetValue(int(Translation_Z) * 100)
            self.zoom_value_text.SetLabel('%.2f' % (Translation_Z))
            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
            self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))
            self.should_use_deforumation_zoomfov_checkbox.SetValue(int(should_use_deforumation_zoomfov))
            self.should_use_deforumation_rotation_checkbox.SetValue(int(should_use_deforumation_rotation))
            self.should_use_deforumation_tilt_checkbox.SetValue(int(should_use_deforumation_tilt))
            self.should_use_deforumation_panning_checkbox.SetValue(int(should_use_deforumation_panning))
            #self.zero_pan_step_input_box.SetValue(zero_pan_step_input_box_value)
            #self.zero_rotate_step_input_box.SetValue(zero_rotate_step_input_box_value)
            #self.zero_zoom_step_input_box.SetValue(zero_zoom_step_input_box_value)
            self.pan_step_input_box.SetValue(pan_step_input_box_value)
            self.rotate_step_input_box.SetValue(rotate_step_input_box_value)
            self.tilt_step_input_box.SetValue(tilt_step_input_box_value)

            #OTHER COMPONENTS
            self.strength_schedule_slider.SetValue(int(Strength_Scheduler * 100))
            self.cfg_schedule_slider.SetValue(int(CFG_Scale))
            self.sample_schedule_slider.SetValue(STEP_Schedule)
            self.seed_input_box.SetValue(str(seedValue))
            self.should_use_deforumation_strength_checkbox.SetValue(int(should_use_deforumation_strength))
            self.should_use_deforumation_cfg_checkbox.SetValue(int(should_use_deforumation_cfg))
            self.should_use_deforumation_cadence_checkbox.SetValue(int(should_use_deforumation_cadence))
            self.should_use_deforumation_noise_checkbox.SetValue(int(should_use_deforumation_noise))
            self.cadence_slider.SetValue(Cadence_Schedule)
            for cnIndex in range(5):
                self.control_net_weight_slider[cnIndex].SetValue(int(CN_Weight[cnIndex] * 100))
                self.control_net_stepstart_slider[cnIndex].SetValue(int(CN_StepStart[cnIndex] * 100))
                self.control_net_stepend_slider[cnIndex].SetValue(int(CN_StepEnd[cnIndex] * 100))
                self.control_net_lowt_slider[cnIndex].SetValue(CN_LowT[cnIndex])
                self.control_net_hight_slider[cnIndex].SetValue(CN_HighT[cnIndex])
                self.control_net_active_checkbox[cnIndex].SetValue(CN_UDCn[cnIndex])

            self.noise_slider.SetValue(int(float(noise_multiplier) * 100))
            self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
            self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value) * 100))

            self.opticalflow_checkbox.SetValue(int(should_use_optical_flow))
            self.cadence_flow_factor_box.SetValue(str(cadence_flow_factor))
            self.generation_flow_factor_box.SetValue(str(generation_flow_factor))


        except Exception as e:
            print(e)

    def sendAllMotionValues(self):
        SendBlock = []
        SendBlock.append(pickle.dumps([1, "translation_x", Translation_X]))
        SendBlock.append(pickle.dumps([1, "translation_y", Translation_Y]))
        SendBlock.append(pickle.dumps([1, "translation_z", Translation_Z]))
        SendBlock.append(pickle.dumps([1, "rotation_x", Rotation_3D_X]))
        SendBlock.append(pickle.dumps([1, "rotation_y", Rotation_3D_Y]))
        SendBlock.append(pickle.dumps([1, "rotation_z", Rotation_3D_Z]))
        SendBlock.append(pickle.dumps([1, "fov", FOV_Scale]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_panning", int(should_use_deforumation_panning)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_zoomfov", int(should_use_deforumation_zoomfov)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_rotation", int(should_use_deforumation_rotation)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_tilt", int(should_use_deforumation_tilt)]))
        self.writeValue("<BLOCK>", SendBlock)


    def sendAllOtherValues(self):
        SendBlock = []
        SendBlock.append(pickle.dumps([1, "strength", Strength_Scheduler]))
        SendBlock.append(pickle.dumps([1, "cfg", CFG_Scale]))
        SendBlock.append(pickle.dumps([1, "steps", STEP_Schedule]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_strength", int(should_use_deforumation_strength)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_cfg", int(should_use_deforumation_cfg)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_cadence", int(should_use_deforumation_cadence)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_noise", int(should_use_deforumation_noise)]))
        SendBlock.append(pickle.dumps([1, "cadence", int(Cadence_Schedule)]))
        for cnIndex in range(5):
            SendBlock.append(pickle.dumps([1, "cn_weight" + str(cnIndex + 1), float(CN_Weight[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_stepstart" + str(cnIndex + 1), float(CN_StepStart[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_stepend" + str(cnIndex + 1), float(CN_StepEnd[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_lowt" + str(cnIndex + 1), float(CN_LowT[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_hight" + str(cnIndex + 1), float(CN_HighT[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_udcn" + str(cnIndex + 1), int(CN_UDCn[cnIndex])]))

        SendBlock.append(pickle.dumps([1, "noise_multiplier", float(noise_multiplier)]))
        SendBlock.append(pickle.dumps([1, "perlin_octaves", int(Perlin_Octave_Value)]))
        SendBlock.append(pickle.dumps([1, "perlin_persistence", float(Perlin_Persistence_Value)]))
        SendBlock.append(pickle.dumps([1, "use_deforumation_cadence_scheduling", 0]))

        SendBlock.append(pickle.dumps([1, "should_use_optical_flow", int(should_use_optical_flow)]))
        SendBlock.append(pickle.dumps([1, "cadence_flow_factor", int(cadence_flow_factor)]))
        SendBlock.append(pickle.dumps([1, "generation_flow_factor", int(generation_flow_factor)]))

        self.writeValue("<BLOCK>", SendBlock)

    def sendAllPropmptValues(self):
        positive_prio = {
            int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
            int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
            int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
            int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
        sortedDict = sorted(positive_prio.items())
        totalPossitivePromptString = sortedDict[0][1]
        if sortedDict[1][1] != "":
            totalPossitivePromptString += "," + sortedDict[1][1]
        if sortedDict[2][1] != "":
            totalPossitivePromptString += "," + sortedDict[2][1]
        if sortedDict[3][1] != "":
            totalPossitivePromptString += "," + sortedDict[3][1]
        self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ' ') + "\n")
        self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ' ') + "\n")
        self.writeValue("should_use_deforumation_prompt_scheduling", int(should_use_deforumation_prompt_scheduling))

    def sendAllValues(self):
        #Prompt Values
        positive_prio = {
            int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
            int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
            int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
            int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
        sortedDict = sorted(positive_prio.items())
        totalPossitivePromptString = sortedDict[0][1]
        if sortedDict[1][1] != "":
            totalPossitivePromptString += "," + sortedDict[1][1]
        if sortedDict[2][1] != "":
            totalPossitivePromptString += "," + sortedDict[2][1]
        if sortedDict[3][1] != "":
            totalPossitivePromptString += "," + sortedDict[3][1]
        self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ' ') + "\n")
        self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ' ') + "\n")
        self.writeValue("should_use_deforumation_prompt_scheduling", int(should_use_deforumation_prompt_scheduling))

        #Motion Values
        SendBlock = []
        SendBlock.append(pickle.dumps([1, "translation_x", Translation_X]))
        SendBlock.append(pickle.dumps([1, "translation_y", Translation_Y]))
        SendBlock.append(pickle.dumps([1, "translation_z", Translation_Z]))

        SendBlock.append(pickle.dumps([1, "rotation_x", Rotation_3D_X]))
        SendBlock.append(pickle.dumps([1, "rotation_y", Rotation_3D_Y]))
        SendBlock.append(pickle.dumps([1, "rotation_z", Rotation_3D_Z]))
        SendBlock.append(pickle.dumps([1, "fov", FOV_Scale]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_panning", int(should_use_deforumation_panning)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_zoomfov", int(should_use_deforumation_zoomfov)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_rotation", int(should_use_deforumation_rotation)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_tilt", int(should_use_deforumation_tilt)]))

        #Other Values
        SendBlock.append(pickle.dumps([1, "strength", Strength_Scheduler]))
        SendBlock.append(pickle.dumps([1, "cfg", CFG_Scale]))
        SendBlock.append(pickle.dumps([1, "steps", STEP_Schedule]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_strength", int(should_use_deforumation_strength)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_cfg", int(should_use_deforumation_cfg)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_cadence", int(should_use_deforumation_cadence)]))
        SendBlock.append(pickle.dumps([1, "should_use_deforumation_noise", int(should_use_deforumation_noise)]))
        SendBlock.append(pickle.dumps([1, "cadence", int(Cadence_Schedule)]))
        for cnIndex in range(5):
            SendBlock.append(pickle.dumps([1, "cn_weight" + str(cnIndex + 1), float(CN_Weight[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_stepstart" + str(cnIndex + 1), float(CN_StepStart[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_stepend" + str(cnIndex + 1), float(CN_StepEnd[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_lowt" + str(cnIndex + 1), float(CN_LowT[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_hight" + str(cnIndex + 1), float(CN_HighT[cnIndex])]))
            SendBlock.append(pickle.dumps([1, "cn_udcn" + str(cnIndex + 1), int(CN_UDCn[cnIndex])]))

        SendBlock.append(pickle.dumps([1, "noise_multiplier", float(noise_multiplier)]))
        SendBlock.append(pickle.dumps([1, "perlin_octaves", int(Perlin_Octave_Value)]))
        SendBlock.append(pickle.dumps([1, "perlin_persistence", float(Perlin_Persistence_Value)]))
        SendBlock.append(pickle.dumps([1, "use_deforumation_cadence_scheduling", 0]))

        SendBlock.append(pickle.dumps([1, "should_use_optical_flow", int(should_use_optical_flow)]))
        SendBlock.append(pickle.dumps([1, "cadence_flow_factor", int(cadence_flow_factor)]))
        SendBlock.append(pickle.dumps([1, "generation_flow_factor", int(generation_flow_factor)]))

        self.writeValue("<BLOCK>", SendBlock)

    def copyAllOriginalValuesToManual(self, frameNumber):
        global Translation_X
        global Translation_Y
        global Translation_Z
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Z
        global Strength_Scheduler
        global CFG_Scale
        global FOV_Scale
        global is_fov_locked
        global is_reverse_fov_locked
        global STEP_Schedule
        global Cadence_Schedule
        global noise_multiplier
        global Perlin_Octave_Value
        global Perlin_Persistence_Value
        global is_paused_rendering
        global should_use_deforumation_strength
        global pan_left_key,pan_right_key,pan_up_key,pan_down_key,zoom_up_key,zoom_down_key
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT
        global CN_UDCn
        global should_use_deforumation_prompt_scheduling
        global should_use_deforumation_cfg
        global should_use_deforumation_cadence
        global should_use_deforumation_noise
        global should_use_deforumation_panning
        global should_use_deforumation_zoomfov
        global should_use_deforumation_rotation
        global should_use_deforumation_tilt
        global pan_step_input_box_value
        global rotate_step_input_box_value
        global tilt_step_input_box_value
        global zero_pan_step_input_box_value
        global zero_rotate_step_input_box_value
        global zero_zoom_step_input_box_value
        global shouldUseDeforumPromptScheduling
        global should_use_optical_flow
        global cadence_flow_factor
        global generation_flow_factor
        global parameter_container
        global seedValue
        parameter_container = pickle.loads(readValue_special("saved_frame_params", frameNumber))
        if parameter_container != 0x0:
            if parameter_container and parameter_container != None:
                #self.positive_prompt_input_ctrl.SetValue(parameter_container.Prompt_Positive)
                #self.positive_prompt_input_ctrl_2.SetValue("")
                #self.positive_prompt_input_ctrl_3.SetValue("")
                #self.positive_prompt_input_ctrl_4.SetValue("")
                #self.negative_prompt_input_ctrl.SetValue(parameter_container.Prompt_Negative)
                Strength_Scheduler = float(parameter_container.strength_value)
                #self.strength_schedule_slider.SetValue(int(float(parameter_container.strength_value)*100))
                CFG_Scale = float(parameter_container.cfg_scale)
                #self.cfg_schedule_slider.SetValue(int(float(parameter_container.cfg_scale)))
                STEP_Schedule = int(parameter_container.steps)
                #self.sample_schedule_slider.SetValue(int(parameter_container.steps))
                FOV_Scale = float(parameter_container.fov)
                #self.fov_slider.SetValue(int(float(parameter_container.fov)))
                Translation_X = float(parameter_container.translation_x)
                Translation_Y = float(parameter_container.translation_y)
                Translation_Z = float(parameter_container.translation_z)
                #if not armed_pan:
                #    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(parameter_container.translation_x)))
                #    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(parameter_container.translation_y)))
                #else:
                #    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(Translation_X_ARMED)))
                #    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(Translation_Y_ARMED)))

                #elif armed_pan:
                #    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(Translation_X_ARMED)))
                #    #Translation_Y = float(parameter_container.translation_y)
                #    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(Translation_Y_ARMED)))
                #    #Translation_Z = float(parameter_container.translation_z)

                #self.zoom_slider.SetValue(int(float(parameter_container.translation_z))*100)
                #self.zoom_value_text.SetLabel('%.2f' % (float(parameter_container.translation_z)))
                Rotation_3D_X = float(parameter_container.rotation_x)
                Rotation_3D_Y = float(parameter_container.rotation_y)
                Rotation_3D_Z = float(parameter_container.rotation_z)
                #if not armed_rotation:
                #    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_y)))
                #    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_x)))
                #else:
                #    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Y_ARMED)))
                #    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_X_ARMED)))

                #if not armed_zoom:
                #    self.zoom_value_text.SetLabel(str('%.2f' % float(parameter_container.translation_z)))
                #    self.zoom_slider.SetValue(int(float(parameter_container.translation_z) * 100))
                #else:
                #    self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z_ARMED)))
                #    self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))

                #self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(parameter_container.rotation_z)))

                Cadence_Schedule = int(parameter_container.cadence)
                #self.cadence_slider.SetValue(int(parameter_container.cadence))
                ###CN
                for cnIndex in range(5):
                    CN_Weight[cnIndex] = float(parameter_container.cn_weight[cnIndex])
                    #self.control_net_weight_slider[cnIndex].SetValue(int(float(parameter_container.cn_weight[cnIndex])*100))
                    CN_StepStart[cnIndex] = float(parameter_container.cn_stepstart[cnIndex])
                    #self.control_net_stepstart_slider[cnIndex].SetValue(int(float(parameter_container.cn_stepstart[cnIndex])*100))
                    CN_StepEnd[cnIndex] = float(parameter_container.cn_stepend[cnIndex])
                    #self.control_net_stepend_slider[cnIndex].SetValue(int(float(parameter_container.cn_stepend[cnIndex])*100))
                    CN_LowT[cnIndex] = int(parameter_container.cn_lowt[cnIndex])
                    #self.control_net_lowt_slider[cnIndex].SetValue(int(parameter_container.cn_lowt[cnIndex]))
                    CN_HighT[cnIndex] = int(parameter_container.cn_hight[cnIndex])
                    #self.control_net_hight_slider[cnIndex].SetValue(int(parameter_container.cn_hight[cnIndex]))
                    CN_UDCn[cnIndex] = int(parameter_container.cn_udcn[cnIndex])
                    #self.control_net_active_checkbox[cnIndex].SetValue(int(parameter_container.cn_udcn[cnIndex]))
                ##CN END
                noise_multiplier = float(parameter_container.noise_multiplier)
                #self.noise_slider.SetValue(int(float(parameter_container.noise_multiplier)*100))
                Perlin_Octave_Value = int(parameter_container.perlin_octaves)
                #self.perlin_octave_slider.SetValue(int(parameter_container.perlin_octaves))
                Perlin_Persistence_Value = float(parameter_container.perlin_persistence)
                #self.perlin_persistence_slider.SetValue(int(float(parameter_container.perlin_persistence)*100))

                #self.opticalflow_checkbox
                #self.opticalflow_checkbox
                should_use_optical_flow = int(parameter_container.should_use_optical_flow)
                cadence_flow_factor = int(parameter_container.cadence_flow_factor)
                generation_flow_factor = int(parameter_container.generation_flow_factor)
                #self.cadence_flow_factor_box.SetValue(str(int(parameter_container.cadence_flow_factor)))
                #self.generation_flow_factor_box.SetValue(str(int(parameter_container.generation_flow_factor)))

                #seed
                seedValue = int(parameter_container.seed_value)
                #self.seed_input_box.SetValue(str(int(parameter_container.seed_value)))
        else:
            #print("Frame " + str(frameNumber)+ " has no stored recall values.")
            temp = 0

    def writeAllValues(self):

        #OLD STUFF
        #try:
        #    if is_paused_rendering:
        #        # Arrange the possitive prompts according to priority (now for some lazy programing):
        #        positive_prio = {
        #            int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
        #            int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
        #            int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
        #            int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
        #        sortedDict = sorted(positive_prio.items())
        #        totalPossitivePromptString = sortedDict[0][1]
        #        if sortedDict[1][1] != "":
        #            totalPossitivePromptString += "," + sortedDict[1][1]
        #        if sortedDict[2][1] != "":
        #            totalPossitivePromptString += "," + sortedDict[2][1]
        #        if sortedDict[3][1] != "":
        #            totalPossitivePromptString += "," + sortedDict[3][1]

        #       self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', '') + "\n")
        #        self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
        #except Exception as e:
        #    print(e)
        deforumFile = open(deforumationSettingsPath, 'w')
        deforumFile.write(str(int(is_paused_rendering))+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_2.GetValue().strip().replace('\n', '`^')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_3.GetValue().strip().replace('\n', '`^')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_4.GetValue().strip().replace('\n', '`^')+"\n")
        deforumFile.write(self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')+"\n")
        deforumFile.write(str('%.2f' % Strength_Scheduler)+"\n")
        deforumFile.write(str('%.2f' % CFG_Scale)+"\n")
        deforumFile.write(str(STEP_Schedule)+"\n")
        deforumFile.write(str('%.2f' % FOV_Scale)+"\n")
        deforumFile.write(str('%.2f' % Translation_X)+"\n")
        deforumFile.write(str('%.2f' % Translation_Y)+"\n")
        deforumFile.write(str('%.2f' % Translation_Z)+"\n")
        deforumFile.write(str('%.2f' % Rotation_3D_X)+"\n")
        deforumFile.write(str('%.2f' % Rotation_3D_Y)+"\n")
        deforumFile.write(str('%.2f' % Rotation_3D_Z)+"\n")
        deforumFile.write(str(int(should_use_deforumation_prompt_scheduling)) + "\n")
        deforumFile.write(str(int(should_use_deforumation_strength))+"\n")
        deforumFile.write(str(int(should_use_deforumation_cfg))+"\n")
        deforumFile.write(str(int(should_use_deforumation_cadence))+"\n")
        deforumFile.write(str(int(should_use_deforumation_noise))+"\n")
        deforumFile.write(str(int(should_use_deforumation_panning))+"\n")
        deforumFile.write(str(int(should_use_deforumation_zoomfov))+"\n")
        deforumFile.write(str(int(should_use_deforumation_rotation))+"\n")
        deforumFile.write(str(int(should_use_deforumation_tilt))+"\n")
        deforumFile.write(self.pan_step_input_box.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.rotate_step_input_box.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.tilt_step_input_box.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(str(self.cadence_slider.GetValue())+"\n")
        deforumFile.write(str(self.zero_pan_step_input_box.GetValue().strip().replace('\n', '')+"\n"))
        deforumFile.write(str(self.zero_rotate_step_input_box.GetValue().strip().replace('\n', ''))+"\n")
        deforumFile.write(str(self.zero_zoom_step_input_box.GetValue().strip().replace('\n', '')+"\n"))
        for cnIndex in range(5):
            deforumFile.write(str('%.2f' % CN_Weight[cnIndex])+"\n")
            deforumFile.write(str('%.2f' % CN_StepStart[cnIndex])+"\n")
            deforumFile.write(str('%.2f' % CN_StepEnd[cnIndex])+"\n")
            deforumFile.write(str(CN_LowT[cnIndex])+"\n")
            deforumFile.write(str(CN_HighT[cnIndex])+"\n")
            deforumFile.write(str(CN_UDCn[cnIndex]) + "\n")

        deforumFile.write(str('%.2f' % noise_multiplier)+"\n")
        deforumFile.write(str(Perlin_Octave_Value)+"\n")
        deforumFile.write(str('%.2f' % Perlin_Persistence_Value)+"\n")

        deforumFile.write(str(should_use_optical_flow)+"\n")
        deforumFile.write(str(cadence_flow_factor)+"\n")
        deforumFile.write(str(generation_flow_factor)+"\n")

        deforumFile.write(str(self.ffmpeg_path_input_box.GetValue())+"\n")
        deforumFile.write(str(self.audio_path2_input_box.GetPath())+"\n")
        deforumFile.write(str(self.backend_chooser_choice.GetSelection()) +"\n")
        deforumFile.write(str(self.zero_tilt_step_input_box.GetValue().strip().replace('\n', '')))

        deforumFile.close()

    def getClosestPrompt(self, forwardrewindType, p_current_frame):
        resume_timestring = str(readValue("resume_timestring"))
        returnFrame = str(p_current_frame)
        if os.path.isfile(deforumationPromptsPath + resume_timestring + "_P" + ".txt") and os.path.isfile(deforumationPromptsPath + resume_timestring + "_N" + ".txt"):
            promptFile_positive = open(deforumationPromptsPath + resume_timestring + "_P" + ".txt", 'r')
            promptFile_negative = open(deforumationPromptsPath + resume_timestring + "_N" + ".txt", 'r')
            positive_lines = promptFile_positive.readlines()
            negative_lines = promptFile_negative.readlines()
            promptFile_positive.close()
            promptFile_negative.close()
            positive_promptToShow = self.positive_prompt_input_ctrl.GetValue()
            negative_promptToShow = self.negative_prompt_input_ctrl.GetValue()
            len_pos = len(positive_lines)
            len_neg = len(negative_lines)
            for index in range(0, len(positive_lines), 2):
                param = positive_lines[index].strip('\n').replace(" ", "").split(',')
                frame_index = param[0]
                type = param[1]
                if forwardrewindType == "R" and int(p_current_frame-1) >= int(frame_index):
                    if len_pos > index:
                        positive_promptToShow = positive_lines[index + 1]
                    if len_neg > index:
                        negative_promptToShow = negative_lines[index + 1]
                    returnFrame = frame_index
                elif forwardrewindType == "F" and int(p_current_frame+1) <= int(frame_index):
                    if len_pos > index:
                        positive_promptToShow = positive_lines[index + 1]
                    if len_neg > index:
                        negative_promptToShow = negative_lines[index + 1]
                    returnFrame = frame_index
                    break
            self.positive_prompt_input_ctrl.SetValue(str(positive_promptToShow))
            self.negative_prompt_input_ctrl.SetValue(str(negative_promptToShow))
        return str(returnFrame)

    def loadCurrentPrompt(self, promptType, frame_start,showType):
        resume_timestring = str(readValue("resume_timestring"))
        if os.path.isfile(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt"):
            promptFile = open(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt", 'r')
            old_lines = promptFile.readlines()
            promptFile.close()
            if promptType == "P":
                promptToShow =  self.positive_prompt_input_ctrl.GetValue()
            else:
                promptToShow = self.negative_prompt_input_ctrl.GetValue()
            loadedFromFile = False
            for index in range(0, len(old_lines), 2):
                param = old_lines[index].strip('\n').replace(" ", "").split(',')
                frame_index = param[0]
                type = param[1]
                if int(frame_start) >= int(frame_index):
                    promptToShow = old_lines[index+1]
                    loadedFromFile = True
                else:
                    break
            if showType == 0:
                if promptType == "P" and loadedFromFile:
                    aPromptStart = 0
                    aPromptEnd = promptToShow.find("`~")
                    if aPromptEnd == -1:
                        self.positive_prompt_input_ctrl.SetValue(str(promptToShow).replace('`^', '\n'))
                    else:
                        aPrompt = promptToShow[aPromptStart:aPromptEnd]
                        self.positive_prompt_input_ctrl.SetValue(str(aPrompt).replace('`^','\n'))
                        aPromptStart = aPromptEnd + 2
                        aPromptEnd = promptToShow[aPromptStart:].find("`~")
                        aPrompt = promptToShow[aPromptStart:aPromptEnd+aPromptStart]
                        self.positive_prompt_input_ctrl_2.SetValue(str(aPrompt).replace('`^','\n'))
                        aPromptStart = aPromptStart + aPromptEnd + 2
                        aPromptEnd = promptToShow[aPromptStart:].find("`~")
                        aPrompt = promptToShow[aPromptStart:aPromptEnd+aPromptStart]
                        self.positive_prompt_input_ctrl_3.SetValue(str(aPrompt).replace('`^','\n'))
                        aPromptStart = aPromptStart + aPromptEnd + 2
                        aPromptEnd = promptToShow[aPromptStart:].find("`~")
                        aPrompt = promptToShow[aPromptStart:aPromptEnd+aPromptStart]
                        self.positive_prompt_input_ctrl_4.SetValue(str(aPrompt).replace('`^','\n'))
                elif promptType == "P" and not loadedFromFile:
                    self.positive_prompt_input_ctrl.SetValue(str(promptToShow).replace('`^', '\n'))
                else:
                    self.negative_prompt_input_ctrl.SetValue(str(promptToShow).replace('`^','\n'))
            elif showType == 1:
                if promptType == "P":
                    # Arrange the possitive prompts according to priority (now for some lazy programing):
                    positive_prio = {
                        int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                        int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                        int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                        int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                    sortedDict = sorted(positive_prio.items())
                    #totalPossitivePromptString = sortedDict[0][1] + "," + sortedDict[1][1] + "," + sortedDict[2][1] + "," + sortedDict[3][1]
                    totalPossitivePromptString = sortedDict[0][1]
                    if sortedDict[1][1] != "":
                        totalPossitivePromptString += "," + sortedDict[1][1]
                    if sortedDict[2][1] != "":
                        totalPossitivePromptString += "," + sortedDict[2][1]
                    if sortedDict[3][1] != "":
                        totalPossitivePromptString += "," + sortedDict[3][1]
                    self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ' ') + "\n")
                else:
                    self.writeValue("negative_prompt", promptToShow.strip().replace('\n', ' ')+"\n")


    def saveCurrentPrompt(self, promptType):
        resume_timestring = str(readValue("resume_timestring"))
        fileAlreadyExists = True
        if not os.path.exists(deforumationPromptsPath):
            print("Folder doesn't exist.... creating.")
            os.mkdir(deforumationPromptsPath)
        if not os.path.isfile(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt"):
            print("File Doesn't Exist, creteating file:" + resume_timestring + "_" + promptType + ".txt")
            promptFile = open(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt", 'w')
            promptFile.close()
            fileAlreadyExists = False
        if not os.path.isfile(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt"):
            print("File Still Doesn't Exist, aborting:" + resume_timestring + "_" + promptType + ".txt")
            return
        else:
            promptFile = open(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt", 'r')
            old_lines = promptFile.readlines()
            promptFile.close()
            promptFile = open(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt", 'w')
            new_lines = [None] * 2
            didWriteNewPrompt = False
            copy_of_current = current_frame = str(self.readValue("start_frame"))
            if promptType == "P":
                print("Writing positive prompt at frame:" + str(copy_of_current))
            else:
                print("Writing negative prompt at frame:" + str(copy_of_current))
            for index in range(0, len(old_lines), 2):
                if not didWriteNewPrompt:
                    param = old_lines[index].strip('\n').replace(" ", "").split(',')
                    frame_index = param[0]
                    type = param[1]
                    if int(copy_of_current) == int(frame_index):
                        new_lines[0] = frame_index + "," + type
                        if promptType == "P":
                            new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_2.GetValue().strip().replace('\n', '`^')
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_3.GetValue().strip().replace('\n', '`^')
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_4.GetValue().strip().replace('\n', '`^') + "`~"
                        else:
                            new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        promptFile.write(str(new_lines[0]) + "\n")
                        promptFile.write(str(new_lines[1]))
                        #if index+2 != len(old_lines):
                        #    promptFile.write("\n")
                        didWriteNewPrompt = True
                    elif int(copy_of_current) < int(frame_index):
                        new_lines[0] = str(copy_of_current) + "," + type
                        if promptType == "P":
                            new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_2.GetValue().strip().replace('\n', '`^')
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_3.GetValue().strip().replace('\n', '`^')
                            new_lines[1] += "`~" + self.positive_prompt_input_ctrl_4.GetValue().strip().replace('\n', '`^') + "`~"
                        else:
                            new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        promptFile.write(str(new_lines[0]) + "\n")
                        promptFile.write(str(new_lines[1]))
                        #promptFile.write(frame_index + "," + type + "\n")
                        #promptFile.write(old_lines[index + 1])
                        didWriteNewPrompt = True
                        break
                    else:
                        promptFile.write(old_lines[index])
                        promptFile.write(old_lines[index + 1])

                #else:
                #    promptFile.write(old_lines[index])
                #    promptFile.write(old_lines[index + 1])
            if not didWriteNewPrompt:
                new_lines[0] = str(copy_of_current) + "," + promptType
                if promptType == "P":
                    new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                    if new_lines[1] == "":
                        new_lines[1] = " "
                    new_lines[1] += "`~" + self.positive_prompt_input_ctrl_2.GetValue().strip().replace('\n', '`^')
                    new_lines[1] += "`~" + self.positive_prompt_input_ctrl_3.GetValue().strip().replace('\n', '`^')
                    new_lines[1] += "`~" + self.positive_prompt_input_ctrl_4.GetValue().strip().replace('\n','`^') + "`~"
                else:
                    new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '`^')
                    if new_lines[1] == "":
                        new_lines[1] = " "
                if fileAlreadyExists:
                    promptFile.write("\n")
                promptFile.write(str(new_lines[0]) + "\n")
                promptFile.write(str(new_lines[1]))
            promptFile.close()

    def OnFocus(self, event):
        global seedValue
        global rotate_step_input_box_value
        global pan_step_input_box_value
        global zoom_step_input_box_value
        global tilt_step_input_box_value

        if event.GetId() == 1233:
            self.cadence_schedule_Checkbox.SetValue(False)
            self.writeValue("use_deforumation_cadence_scheduling", 0)
            #self.cadence_schedule_Checkbox.SetCursor(0)
        if event.GetId() == 1239 or event.GetId() == 1240:
            self.writeValue("total_recall_from", int(self.total_recall_from_input_box.GetValue()))
            self.writeValue("total_recall_to", int(self.total_recall_to_input_box.GetValue()))
            if should_use_total_recall:
                self.SetLabel(windowlabel + " -- Using total recall from frame " + str(self.total_recall_from_input_box.GetValue()) + " to frame " + self.total_recall_to_input_box.GetValue())
            else:
                self.SetLabel(windowlabel + " -- \"From\" or \"To\" has changed... (From = " + str(self.total_recall_from_input_box.GetValue()) + " To = " + self.total_recall_to_input_box.GetValue()+")")
        if event.GetId() == 1333:
            rotate_step_input_box_value = self.rotate_step_input_box.GetValue()
        if event.GetId() == 1334:
            pan_step_input_box_value = self.pan_step_input_box.GetValue()
        if event.GetId() == 1335:
            minmaxval = self.zoom_step_input_box.GetValue()
            self.zoom_slider.SetMin(int(-float(minmaxval)*100))
            self.zoom_slider.SetMax(int(float(minmaxval)*100))
            self.zoom_value_high_text.SetLabel(minmaxval)
            self.zoom_value_low_text.SetLabel("-"+minmaxval)
            self.zoom_slider.SetTickFreq(int(float(minmaxval)*100/10))
            zoom_step_input_box_value = minmaxval
        if event.GetId() == 1336:
            tilt_step_input_box_value = self.tilt_step_input_box.GetValue()
        if event.GetId() == 3:
            oldSeedValue = seedValue
            seedValue = int(self.seed_input_box.GetValue())
            if oldSeedValue != seedValue:
                print("New seed:"+str(seedValue))
                self.writeValue("seed", seedValue)
                self.writeValue("seed_changed", 1)
        if event.GetId() == 9999:
            newevent = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            newevent.SetEventObject(self.update_prompts)
            newevent.SetId(self.update_prompts.GetId())
            self.update_prompts.GetEventHandler().ProcessEvent(newevent)

        if should_use_total_recall_in_deforumation:
            if current_render_frame != -1:
                self.setValuesFromSavedFrame(int(current_render_frame))
        elif should_use_total_recall and (int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue())) and (int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue())):
            if current_render_frame != -1:
                self.setValuesFromSavedFrame(int(current_render_frame))
        else:
            if armed_pan:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
            else:
                if not showLiveValues:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
            self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
            if armed_rotation:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X_ARMED))
            else:
                if not showLiveValues:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))

            if armed_zoom:
                self.zoom_value_text.SetLabel(str('%.2f' % Translation_Z_ARMED))
                self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))
            else:
                if not showLiveValues:
                    self.zoom_value_text.SetLabel(str('%.2f' % Translation_Z))
                    self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
                    # self.fov_slider.SetValue(int(FOV_Scale))

            if armed_tilt:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z_ARMED))
            else:
                if not showLiveValues:
                    self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))


        # obj.SetToolTip(obj_tooltip)
        self.writeAllValues()
        event.Skip()


    def OnClicked(self, event):
        global Translation_X
        global Translation_Y
        global Translation_Z
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Z
        global Strength_Scheduler
        global CFG_Scale
        global FOV_Scale
        global is_fov_locked
        global is_reverse_fov_locked
        global is_paused_rendering
        global STEP_Schedule
        global current_frame
        global seedValue
        global should_render_live
        global current_render_frame
        global should_use_deforumation_strength
        global Cadence_Schedule
        global noise_multiplier
        global Perlin_Octave_Value
        global Perlin_Persistence_Value
        global should_stay_on_top
        global should_use_deforumation_prompt_scheduling
        global zero_pan_active
        global zero_rotate_active
        global zero_zoom_active
        global zero_tilt_active
        global stepit_pan
        global stepit_rotate
        global stepit_zoom
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT
        global CN_UDCa
        global CN_UDCn
        global isReplaying
        global replayFrom
        global replayTo
        global replayFPS
        global cadenceArray
        global armed_rotation
        global armed_pan
        global armed_zoom
        global armed_tilt
        global Translation_X_ARMED
        global Translation_Y_ARMED
        global Translation_Z_ARMED
        global Rotation_3D_X_ARMED
        global Rotation_3D_Y_ARMED
        global Rotation_3D_Z_ARMED
        #global pstb
        #global pmob
        global is_Parseq_Active
        global showLiveValues
        global ppb
        global should_use_deforumation_cfg
        global should_use_deforumation_cadence
        global should_use_deforumation_noise
        global should_use_deforumation_panning
        global should_use_deforumation_zoomfov
        global should_use_deforumation_rotation
        global should_use_deforumation_tilt
        global should_use_optical_flow
        global cadence_flow_factor
        global generation_flow_factor
        global should_use_total_recall
        global should_use_total_recall_in_deforumation
        global should_use_deforumation_timestring
        global number_of_recalled_frames
        global should_use_total_recall_prompt
        global should_use_total_recall_movements
        global should_use_total_recall_others
        global create_gif_animation_on_preview
        global frame_has_changed
        global zero_pan_current_settings
        global zero_zoom_current_settings
        global zero_rotation_current_settings
        global zero_tilt_current_settings
        global currently_active_motion
        global is_static_motion
        global should_hide_parseq_box
        global should_hide_totalrecall_box
        global Translation_X_SIRUP
        global Translation_Y_SIRUP
        global should_use_before_deforum_prompt
        global should_use_after_deforum_prompt
        global rotate_step_input_box_value
        global pan_step_input_box_value
        global zoom_step_input_box_value
        global tilt_step_input_box_value
        btn = event.GetEventObject().GetLabel()

        #Initial values
        #########################
        total_recall_movements_inside_range_and_active = False
        total_recall_others_inside_range_and_active = False
        total_recall_prompt_inside_range_and_active = False
        if (should_use_total_recall and int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue()) and int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue())):
            if should_use_total_recall_movements:
                total_recall_movements_inside_range_and_active = True
            if should_use_total_recall_others:
                total_recall_others_inside_range_and_active = True
            if should_use_total_recall_prompt:
                total_recall_prompt_inside_range_and_active = True
        #End of initial values

        #print("Label of pressed button = ", str(event.GetId()))
        if btn == "PUSH TO PAUSE RENDERING":
            self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            is_paused_rendering = True
            self.writeValue("is_paused_rendering", is_paused_rendering)
            #print(dict(sorted(cadenceArray.items())))
        elif btn == "PUSH TO RESUME RENDERING":
            self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            if should_use_deforumation_prompt_scheduling == 1:
                self.loadCurrentPrompt("P", current_frame, 1)
                self.loadCurrentPrompt("N", current_frame, 1)
            is_paused_rendering = False
            self.writeValue("is_paused_rendering", is_paused_rendering)

        elif btn == "RECORD":

            if self.is_recording == False:
                self.is_recording = True
                bmp = wx.Bitmap("./images/record_on.bmp", wx.BITMAP_TYPE_BMP)
                self.record_button.SetBitmap(bmp)

                stopped = threading.Event()
                q = queue.Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK_SIZE)))

                listen_t = threading.Thread(target=listen, args=(self, stopped, q))
                listen_t.start()
                record_t = threading.Thread(target=record, args=(self, stopped, q))
                record_t.start()

            else:
                self.is_recording = False
                bmp = wx.Bitmap("./images/record_off.bmp", wx.BITMAP_TYPE_BMP)
                #bmp = scale_bitmap(bmp, 22, 22)
                self.record_button.SetBitmap(bmp)

        elif btn == "Re-schedule":
            should_use_disco = False
            if self.cadence_rescheduler_disco_checkbox.GetValue():
                should_use_disco = True

            if not should_use_disco:
                manifestOrUrl = self.cadence_rescheduler_url_input_box.GetValue()
                try:
                    if (manifestOrUrl.startswith('http')):
                        # Using URL
                        body = requests.get(manifestOrUrl).text
                        parseq_json = json.loads(body)
                    else:
                        f = open(manifestOrUrl)
                        parseq_json = json.load(f)
                        f.close()
                except Exception as e:
                    wx.MessageBox(str(e), "URL/FILE input error")
                    return
                # Get all frames
                rendered_frames = parseq_json['rendered_frames']
                # Number of frames to interprete
                numberOfParseqFrames = len(rendered_frames)
            else:
                disco_string = self.positive_prompt_input_ctrl.GetValue().replace('\n', '').replace('\r', '').replace(' ', '').replace('(', '').replace(')', '')
                my_list = disco_string.split(",")
                parseq_json = {}
                for entity in my_list:
                    two_time = entity.split(":")
                    parseq_json[f"{two_time[0]}"] = float(two_time[1])
                # Number of frames to interprete
                numberOfParseqFrames = len(parseq_json)
            # Relevant Frames
            relevant_frames = {}
            # What is the trigger
            trigger_param = str(self.cadence_rescheduler_trigger_parameter_input_box.GetValue()).lower()
            # Value trigger
            trigger_min = float(self.cadence_rescheduler_trigger_min_input_box.GetValue())
            trigger_max = float(self.cadence_rescheduler_trigger_max_input_box.GetValue())


            # Get all frames
            if not should_use_disco:
                for i in range(numberOfParseqFrames):
                    parseq_frame = -1
                    for key, value in rendered_frames[i].items():
                        if key == "frame":
                            parseq_frame = int(value)
                        if key == trigger_param:
                            parseq_value = round(float(value), 3)
                            if (parseq_value >= float(trigger_min)) and (parseq_value <= float(trigger_max)):
                                # print("Frame("+str(parseq_frame)+"):"+trigger_param+"("+str(parseq_value)+")")
                                relevant_frames[parseq_frame] = parseq_value
            else:
                #for i in range(numberOfParseqFrames):
                #    parseq_frame = -1
                for key, value in parseq_json.items():
                    parseq_frame = int(key)
                    parseq_value = round(float(value), 3)
                    if (parseq_value >= float(trigger_min)) and (parseq_value <= float(trigger_max)):
                        # print("Frame("+str(parseq_frame)+"):"+trigger_param+"("+str(parseq_value)+")")
                        relevant_frames[parseq_frame] = parseq_value

            print("Frames that are in scope, from your current settings:")
            print(str(relevant_frames))
            number_relevant_frames = len(relevant_frames)
            relevant_frames = collections.OrderedDict(sorted(relevant_frames.items()))

            # What cadence should be used in the calculation
            now_cadence = int(self.cadence_rescheduler_cadence_input_box.GetValue())
            if now_cadence <= 0 or now_cadence >20:
                wx.MessageBox("Cadence value must be 1 to 20", "Cadence value error")
                return

            # Relevant Frames
            relevant_frames_cadence_modulation = {}
            relevant_frames_cadence_modulation[0] = now_cadence

            number_of_cadence_warning = 0
            previous_frame_number = 0
            cadence_rescheduler_result_informational_input_box_message = ""
            for frame_number, value in relevant_frames.items():
                frame_modulus = int(frame_number) % now_cadence
                if frame_modulus != 0:
                    # print("WARNING! Frame(" + str(frame_number) + "):" + trigger_param + "(" + str(value) + "), might not trigger with start cadence:("+str(now_cadence)+")")
                    number_of_cadence_warning += 1
                    if previous_frame_number >= (frame_number - frame_modulus):
                        print("WARNING!!!, frame number:" + str(
                            previous_frame_number) + ", will be overriden or \"discarded\" (because they lie too close), by frame:" + str(
                            frame_number))
                        cadence_rescheduler_result_informational_input_box_message += "WARNING!!!, frame number:" + str(previous_frame_number) + ", will be overriden or \"discarded\" (because they lie too close), by frame:" + str(frame_number) + "\n"
                    relevant_frames_cadence_modulation[frame_number - frame_modulus] = frame_modulus
                    relevant_frames_cadence_modulation[frame_number] = now_cadence
                previous_frame_number = frame_number
            if cadence_rescheduler_result_informational_input_box_message != "":
                self.cadence_rescheduler_result_informational_input_box.SetValue(cadence_rescheduler_result_informational_input_box_message)
            else:
                if number_of_cadence_warning == 0:
                    self.cadence_rescheduler_result_informational_input_box.SetValue("No Schedule Problems Detected")
                else:
                    self.cadence_rescheduler_result_informational_input_box.SetValue("No Schedule Problems Detected, but re-scheduling has been done on "+ str(number_of_cadence_warning) +" places where triggering would have been prevented.")

            print("\nOut of " + str(number_relevant_frames) + " trigger points (" + trigger_param + "), " + str(
                number_of_cadence_warning) + " might not trigger.")

            print("\nSuggested cadence schedule to trigger on all important " + trigger_param + " values\n"
                                                                                            "------------------------------------------------------------------------\n"
                                                                                            "Deforumation type schedule:\n")
            if number_of_cadence_warning == 0:
                wx.MessageBox("There are no problems in your current cadence scheme, and so no re-scheduling is neccessary!", "You don't need to use re-scheduling!")
                return

            isFirstValue = True
            cadence_schedule_string = ""
            for frame_number, cadence_value in relevant_frames_cadence_modulation.items():
                if not isFirstValue:
                    print(",", end="")
                    cadence_schedule_string = cadence_schedule_string + ","
                else:
                    print("{", end="")
                    cadence_schedule_string = cadence_schedule_string + "{"
                    isFirstValue = False
                print("\"" + str(frame_number) + "\":" + str(cadence_value), end="")
                cadence_schedule_string = cadence_schedule_string + "\"" + str(frame_number) + "\":" + str(cadence_value)
            print("}")
            cadence_schedule_string = cadence_schedule_string + "}"

            self.cadence_rescheduler_result_input_box.SetValue(cadence_schedule_string)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(cadence_schedule_string))
                wx.TheClipboard.Close()
                wx.MessageBox("The suggested cadence schedule has been sent to the clip-board, and you can use this to paste (\"Ctrl+v\" on Windows) it into the \"<Cadence Schedule Here>\"-input-box.", "Plz read")


        elif btn == "Use C.":
            if self.cadence_schedule_Checkbox.GetValue() == True:
                cadence_schedule_text = self.cadence_schedule_input_box.GetValue()
                if cadence_schedule_text == "":
                    wx.MessageBox("No cadence schedule has been given. No sanity checks are done (for now), so be careful to get it right, else Deforum may go haywire.", "Plz read")
                    self.cadence_schedule_Checkbox.SetValue(False)
                    self.writeValue("use_deforumation_cadence_scheduling", 0)
                else:
                    self.writeValue("use_deforumation_cadence_scheduling", 1)
                    self.writeValue("deforumation_cadence_scheduling_manifest", cadence_schedule_text)
            else:
                self.writeValue("use_deforumation_cadence_scheduling", 0)
        elif btn == "Stay on top":
            if should_stay_on_top:
                should_stay_on_top = False
                self.ToggleWindowStyle(wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
                if self.framer != None:
                    self.framer.ToggleWindowStyle(wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
            else:
                should_stay_on_top = True
                self.ToggleWindowStyle(wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
                if self.framer != None:
                    self.framer.ToggleWindowStyle(wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        #elif btn == "Use Deforumation prompt scheduling":
        #    if should_use_deforumation_prompt_scheduling == 0:
        #        should_use_deforumation_prompt_scheduling = 1
        #        self.writeValue("should_use_deforumation_prompt_scheduling", should_use_deforumation_prompt_scheduling)
        #    else:
        #        should_use_deforumation_prompt_scheduling = 0
        #        self.writeValue("should_use_deforumation_prompt_scheduling", should_use_deforumation_prompt_scheduling)
        elif btn == "SAVE PROMPTS":
            self.saveCurrentPrompt("P")
            self.saveCurrentPrompt("N")
            #Arrange the possitive prompts according to priority (now for some lazy programing):
            positive_prio = {int(self.positive_prompt_input_ctrl_prio.GetValue()):self.positive_prompt_input_ctrl.GetValue(), int(self.positive_prompt_input_ctrl_2_prio.GetValue()):self.positive_prompt_input_ctrl_2.GetValue(), int(self.positive_prompt_input_ctrl_3_prio.GetValue()):self.positive_prompt_input_ctrl_3.GetValue(), int(self.positive_prompt_input_ctrl_4_prio.GetValue()):self.positive_prompt_input_ctrl_4.GetValue()}
            sortedDict = sorted(positive_prio.items())
            #totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
            totalPossitivePromptString = sortedDict[0][1]
            if sortedDict[1][1] !="":
                totalPossitivePromptString += "," + sortedDict[1][1]
            if sortedDict[2][1] !="":
                totalPossitivePromptString += "," + sortedDict[2][1]
            if sortedDict[3][1] !="":
                totalPossitivePromptString += "," + sortedDict[3][1]

            self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
            self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
            self.writeValue("prompts_touched", 1)
            self.SetLabel(windowlabel + " -- Prompts saved to mediator, specifically to frame " + str(self.readValue("start_frame")))
        elif btn == "Use predefined motion" or btn.startswith("IMAGE_MOTION"):
            if btn == "Use predefined motion":
                motionNumber = self.predefined_motion_choice.GetSelection()
            else:
                motionNumber = int(btn[13:])
            if currently_active_motion != motionNumber:
                if currently_active_motion != -1 and (currently_active_motion <= (len(self.ctrl)-1)):
                    self.ctrl[currently_active_motion].Play()
                print("Using Predefined Values:" + str(self.predefined_motions_line[motionNumber]))
                FPS_end = self.predefined_motions_line[motionNumber].find(',')
                FPS = int(self.predefined_motions_line[motionNumber][0:FPS_end].strip(' '))
                predefValues = self.predefined_motions_line[motionNumber][FPS_end+1:].replace(":",",")
                predefValues = ast.literal_eval(predefValues)
                if type(predefValues) is tuple:
                    shouldContinue = True
                    if FPS != int(self.replay_fps_input_box.GetValue()):
                        dlg = wx.MessageDialog(self,
                                               "This motion was done for " + str(
                                                   FPS) + " FPS. If you aim to use " + self.replay_fps_input_box.GetValue() + " FPS, this motion will not be correct. Do you want to continue?",
                                               "Mismatching FPS", wx.YES_NO | wx.ICON_WARNING)
                        result = dlg.ShowModal()
                        if result == wx.ID_YES:
                            shouldContinue = True
                        else:
                            shouldContinue = False
                    if shouldContinue:
                        is_static_motion = False
                        self.writeValue("prepare_motion", predefValues)
                        self.writeValue("start_motion", 1)
                        self.ctrl[motionNumber].Stop()
                        currently_active_motion = motionNumber
                else:
                    is_static_motion = True
                    self.writeValue("start_motion", 0)
                    if not total_recall_movements_inside_range_and_active:
                        Translation_X = float(predefValues[0])
                        Translation_Y = float(predefValues[1])
                        Translation_Z = float(predefValues[2])
                        Rotation_3D_X = float(predefValues[4])
                        Rotation_3D_Y = float(predefValues[3])
                        Rotation_3D_Z = float(predefValues[5])
                        self.sendAllMotionValues()
                        self.ctrl[motionNumber].Stop()
                        currently_active_motion = motionNumber
            else:
                self.writeValue("start_motion", 0)
                if currently_active_motion != -1 and (currently_active_motion <= (len(self.ctrl)-1)):
                    self.ctrl[currently_active_motion].Play()
                currently_active_motion = -1
        elif btn == "Create pre-defined motion":
            if create_gif_animation_on_preview == 0:
                create_gif_animation_on_preview = 1
            else:
                create_gif_animation_on_preview = 0

        elif btn == "PAN_LEFT":
            if not total_recall_movements_inside_range_and_active and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    self.writeValue("start_zero_pan_motion_x", -2)
                    self.deforum_zero_pan_x_value_info_text.SetLabel("0-Pan_X: None")
                    Translation_X_SIRUP = Translation_X_SIRUP - float(self.pan_step_input_box.GetValue())
                    self.setTextColor(self.pan_X_Sirup_Value_Text, (0, 0, 0),str('%.2f' % float(Translation_X_SIRUP)))
                    if round(Translation_X_SIRUP,2) < 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_X_SIRUP,2) > 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
                else:
                    bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                    bmp = scale_bitmap(bmp, 22, 22)
                    self.transform_zero_button.SetBitmap(bmp)
                    zero_pan_active = False
                    self.writeValue("start_zero_pan_motion", 0)
                    self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")
                    Translation_X = float(self.readValue("translation_x"))
                    Translation_X_SIRUP = Translation_X_SIRUP - float(self.pan_step_input_box.GetValue())
                    # Prepare the bezier curve that should be followed:
                    bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                    bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                    bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')', '').replace(
                        ' ', '').split(',')
                    bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                    bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                    bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                    bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                    bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))
                    bezierArray = pyeaze.Animator(current_value=Translation_X, target_value=Translation_X_SIRUP, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                    self.writeValue("prepare_zero_pan_motion_x", bezierArray.values)
                    self.writeValue("start_zero_pan_motion_x", 1)
                    if round(Translation_X_SIRUP,2) < 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_X_SIRUP,2) > 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
            elif not total_recall_movements_inside_range_and_active and not should_use_total_recall_in_deforumation and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_DCLICK":
                print("ASKJLDHASOJKDGHSKJHLADGHKHJASDGASWKJH")
            elif not armed_pan and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Translation_X = 0
                    else:
                        Translation_X = Translation_X - float(self.pan_step_input_box.GetValue())
                    self.writeValue("translation_x", Translation_X)
            elif armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_X_ARMED = 0
                else:
                    Translation_X_ARMED =  round(Translation_X_ARMED - float(self.pan_step_input_box.GetValue()),2)
                if total_recall_movements_inside_range_and_active:
                #if should_use_total_recall:
                    self.writeValue("translation_x", Translation_X_ARMED)
        elif btn == "PAN_RIGHT":
            #if not total_recall_movements_inside_range_and_active and not should_use_total_recall_in_deforumation and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
            if not total_recall_movements_inside_range_and_active and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    self.writeValue("start_zero_pan_motion_x", -2)
                    self.deforum_zero_pan_x_value_info_text.SetLabel("0-Pan_X: None")
                    Translation_X_SIRUP = Translation_X_SIRUP + float(self.pan_step_input_box.GetValue())
                    self.setTextColor(self.pan_X_Sirup_Value_Text, (0, 0, 0),str('%.2f' % float(Translation_X_SIRUP)))
                    if round(Translation_X_SIRUP,2) < 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_X_SIRUP,2) > 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
                else:
                    bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                    bmp = scale_bitmap(bmp, 22, 22)
                    self.transform_zero_button.SetBitmap(bmp)
                    zero_pan_active = False
                    self.writeValue("start_zero_pan_motion", 0)
                    self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")
                    Translation_X = float(self.readValue("translation_x"))
                    Translation_X_SIRUP = Translation_X_SIRUP + float(self.pan_step_input_box.GetValue())
                    # Prepare the bezier curve that should be followed:
                    bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                    bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                    bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')','').replace(' ','').split(',')
                    bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                    bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                    bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                    bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                    bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))
                    bezierArray = pyeaze.Animator(current_value=Translation_X, target_value=Translation_X_SIRUP, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                    self.writeValue("prepare_zero_pan_motion_x", bezierArray.values)
                    self.writeValue("start_zero_pan_motion_x", 1)
                    if round(Translation_X_SIRUP,2) < 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_X_SIRUP,2) > 0:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_X_Sirup_Value_Text.SetForegroundColour((255, 255, 255))

            elif not armed_pan and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Translation_X = 0
                    else:
                        Translation_X = Translation_X + float(self.pan_step_input_box.GetValue())
                    self.writeValue("translation_x", Translation_X)
            elif armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_X_ARMED = 0
                else:
                    Translation_X_ARMED = round(Translation_X_ARMED + float(self.pan_step_input_box.GetValue()),2)
                if total_recall_movements_inside_range_and_active:
                #if should_use_total_recall:
                    self.writeValue("translation_x", Translation_X_ARMED)
        elif btn == "PAN_UP":
            if not total_recall_movements_inside_range_and_active and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    self.writeValue("start_zero_pan_motion_y", -2)
                    self.deforum_zero_pan_y_value_info_text.SetLabel("0-Pan_Y: None")
                    Translation_Y_SIRUP = Translation_Y_SIRUP + float(self.pan_step_input_box.GetValue())
                    self.setTextColor(self.pan_Y_Sirup_Value_Text, (0, 0, 0),str('%.2f' % float(Translation_Y_SIRUP)))
                    if round(Translation_Y_SIRUP,2) < 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_Y_SIRUP,2) > 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
                else:
                    bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                    bmp = scale_bitmap(bmp, 22, 22)
                    self.transform_zero_button.SetBitmap(bmp)
                    zero_pan_active = False
                    self.writeValue("start_zero_pan_motion", 0)
                    self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")
                    Translation_Y = float(self.readValue("translation_y"))
                    Translation_Y_SIRUP = Translation_Y_SIRUP + float(self.pan_step_input_box.GetValue())
                    # Prepare the bezier curve that should be followed:
                    bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                    bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                    bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')', '').replace(' ', '').split(',')
                    bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                    bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                    bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                    bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                    bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))
                    bezierArray = pyeaze.Animator(current_value=Translation_Y, target_value=Translation_Y_SIRUP, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                    self.writeValue("prepare_zero_pan_motion_y", bezierArray.values)
                    self.writeValue("start_zero_pan_motion_y", 1)
                    if round(Translation_Y_SIRUP,2) < 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_Y_SIRUP,2) > 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
            elif not armed_pan and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Translation_Y = 0
                    else:
                        Translation_Y = Translation_Y + float(self.pan_step_input_box.GetValue())
                    self.writeValue("translation_y", Translation_Y)
            elif armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_Y_ARMED = 0
                else:
                    Translation_Y_ARMED =  round(Translation_Y_ARMED + float(self.pan_step_input_box.GetValue()),2)
                if total_recall_movements_inside_range_and_active:
                #if should_use_total_recall:
                    self.writeValue("translation_y", Translation_Y_ARMED)
        elif btn == "PAN_DOWN":
            if not total_recall_movements_inside_range_and_active and self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    self.writeValue("start_zero_pan_motion_y", -2)
                    self.deforum_zero_pan_y_value_info_text.SetLabel("0-Pan_Y: None")
                    Translation_Y_SIRUP = Translation_Y_SIRUP - float(self.pan_step_input_box.GetValue())
                    self.setTextColor(self.pan_Y_Sirup_Value_Text, (0, 0, 0),str('%.2f' % float(Translation_Y_SIRUP)))
                    if round(Translation_Y_SIRUP,2) < 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_Y_SIRUP,2) > 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
                else:
                    bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                    bmp = scale_bitmap(bmp, 22, 22)
                    self.transform_zero_button.SetBitmap(bmp)
                    zero_pan_active = False
                    self.writeValue("start_zero_pan_motion", 0)
                    self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")
                    Translation_Y = float(self.readValue("translation_y"))
                    Translation_Y_SIRUP = Translation_Y_SIRUP - float(self.pan_step_input_box.GetValue())
                    # Prepare the bezier curve that should be followed:
                    bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                    bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                    bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')', '').replace(' ', '').split(',')
                    bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                    bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                    bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                    bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                    bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))
                    bezierArray = pyeaze.Animator(current_value=Translation_Y, target_value=Translation_Y_SIRUP, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                    self.writeValue("prepare_zero_pan_motion_y", bezierArray.values)
                    self.writeValue("start_zero_pan_motion_y", 1)
                    if round(Translation_Y_SIRUP,2) < 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                    elif round(Translation_Y_SIRUP,2) > 0:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                    else:
                        self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))
            elif not armed_pan and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Translation_Y = 0
                    else:
                        Translation_Y = Translation_Y - float(self.pan_step_input_box.GetValue())
                    self.writeValue("translation_y", Translation_Y)
            elif armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_Y_ARMED = 0
                else:
                    Translation_Y_ARMED =  round(Translation_Y_ARMED - float(self.pan_step_input_box.GetValue()),2)
                if total_recall_movements_inside_range_and_active:
                #if should_use_total_recall:
                    self.writeValue("translation_y", Translation_Y_ARMED)
        elif btn == "ZERO PAN":
            if self.eventDict[event.GetEventType()] == "EVT_MIDDLE_UP":
                self.writeValue("start_zero_pan_motion_y", -2)
                self.writeValue("start_zero_pan_motion_x", -2)
                self.deforum_zero_pan_y_value_info_text.SetLabel("0-Pan_Y: None")
                self.setTextColor(self.pan_Y_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_Y_SIRUP)))
                self.deforum_zero_pan_x_value_info_text.SetLabel("0-Pan_X: None")
                self.setTextColor(self.pan_X_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_X_SIRUP)))
            elif not zero_pan_active:
                self.writeValue("start_zero_pan_motion_y", -2)
                self.writeValue("start_zero_pan_motion_x", -2)
                self.deforum_zero_pan_y_value_info_text.SetLabel("0-Pan_Y: None")
                self.setTextColor(self.pan_Y_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_Y_SIRUP)))
                self.deforum_zero_pan_x_value_info_text.SetLabel("0-Pan_X: None")
                self.setTextColor(self.pan_X_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_X_SIRUP)))
                if round(Translation_Y_SIRUP, 2) < 0:
                    self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 0, 0))
                elif round(Translation_Y_SIRUP, 2) > 0:
                    self.pan_Y_Sirup_Value_Text.SetForegroundColour((0, 0, 255))
                else:
                    self.pan_Y_Sirup_Value_Text.SetForegroundColour((255, 255, 255))

                bmp = wx.Bitmap("./images/zero_active.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.transform_zero_button.SetBitmap(bmp)
                zero_pan_active = True
                # Prepare the bezier curve that should be followed:
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')','').replace(' ','').split(',')
                bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))

                bezierArray1 = pyeaze.Animator(current_value=Translation_X, target_value=Translation_X_ARMED, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                bezierArray2 = pyeaze.Animator(current_value=Translation_Y, target_value=Translation_Y_ARMED, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                bezierArray = [bezierArray1.values, bezierArray2.values]
                self.writeValue("prepare_zero_pan_motion", bezierArray)
                self.writeValue("start_zero_pan_motion", 1)
                zero_frame_start = int(self.readValue("start_frame"))
                print("-- ZERO PAN MOTION SET, FROM (X:" + str('%.2f' % Translation_X) + " -> X:" + str('%.2f' % Translation_X_ARMED) + ") & (Y:" + str('%.2f' % Translation_X) + " -> Y:" + str('%.2f' % Translation_Y_ARMED) + ") , in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                zero_pan_current_settings = "<\"0-P: x:" + str('%.2f' % Translation_X) + "->x:" + str('%.2f' % Translation_X_ARMED) + " & y:" + str('%.2f' % Translation_Y) + "->y:" + str('%.2f' % Translation_Y_ARMED) + " (fr:"+str(zero_frame_start)+" to:"+str(zero_frame_start+frame_steps)+")\">"
                print(zero_pan_current_settings)
                self.SetLabel(windowlabel + " -- ZERO PAN MOTION SET, FROM (X:" + str('%.2f' % Translation_X) + " -> X:" + str('%.2f' % Translation_X_ARMED) + ") & (Y:" + str('%.2f' % Translation_X) + " -> Y:" + str('%.2f' % Translation_Y_ARMED) + ") , in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                self.zero_pan_current_settings_Text.SetLabel(zero_pan_current_settings)
            else:
                stepit_pan = 0
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.transform_zero_button.SetBitmap(bmp)
                zero_pan_active = False
                self.writeValue("start_zero_pan_motion", 0)
                self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")

        elif btn == "ZOOM":
            currentEventTypeID = event.GetEventType()
            if not armed_zoom and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[currentEventTypeID] == "EVT_RIGHT_UP":
                        self.zoom_slider.SetValue(0)
                        self.zoom_value_text.SetLabel("0.00")
                        Translation_Z = 0.0
                        self.writeValue("translation_z", Translation_Z)
                        if is_fov_locked:
                            if is_reverse_fov_locked:
                                FOV_Scale = 70+(Translation_Z * -5)
                            else:
                                FOV_Scale = 70 + (Translation_Z * 5)
                            self.fov_slider.SetValue(int(FOV_Scale))
                            self.writeValue("fov", FOV_Scale)
                    else:
                        Translation_Z = self.zoom_slider.GetValue()/100
                        self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z)))

                        #print(str(Translation_Z))
                        self.writeValue("translation_z", Translation_Z)
                        if is_fov_locked:
                            if is_reverse_fov_locked:
                                FOV_Scale = 70+(Translation_Z * -5)
                            else:
                                FOV_Scale = 70 + (Translation_Z * 5)
                            self.fov_slider.SetValue(int(FOV_Scale))
                            self.writeValue("fov", FOV_Scale)
            elif armed_zoom:
                if self.eventDict[currentEventTypeID] == "EVT_RIGHT_UP":
                    self.zoom_slider.SetValue(0)
                    self.zoom_value_text.SetLabel("0.00")
                    Translation_Z_ARMED = 0.0
                    if is_fov_locked:
                        if is_reverse_fov_locked:
                            FOV_Scale = 70 + (Translation_Z_ARMED * -5)
                        else:
                            FOV_Scale = 70 + (Translation_Z_ARMED * 5)
                        self.fov_slider.SetValue(int(FOV_Scale))
                    if total_recall_movements_inside_range_and_active:
                    #if should_use_total_recall:
                        self.writeValue("translation_z", 0)
                else:
                    Translation_Z_ARMED = self.zoom_slider.GetValue() / 100
                    self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z_ARMED)))
                    # print(str(Translation_Z))
                    if is_fov_locked:
                        if is_reverse_fov_locked:
                            FOV_Scale = 70 + (Translation_Z_ARMED * -5)
                        else:
                            FOV_Scale = 70 + (Translation_Z_ARMED * 5)
                        self.fov_slider.SetValue(int(FOV_Scale))
                    if total_recall_movements_inside_range_and_active:
                    #if should_use_total_recall:
                        self.writeValue("translation_z", Translation_Z_ARMED)
        elif event.GetId() == 1333:
            rotate_step_input_box_value = self.rotate_step_input_box.GetValue()
        elif event.GetId() == 1334:
            pan_step_input_box_value = self.pan_step_input_box.GetValue()
        elif event.GetId() == 1335:
            minmaxval = self.zoom_step_input_box.GetValue()
            self.zoom_slider.SetMin(int(-float(minmaxval) * 100))
            self.zoom_slider.SetMax(int(float(minmaxval) * 100))
            self.zoom_value_high_text.SetLabel(minmaxval)
            self.zoom_value_low_text.SetLabel("-" + minmaxval)
            self.zoom_slider.SetTickFreq(int(float(minmaxval) * 100 / 10))
            zoom_step_input_box_value = minmaxval
            zoom_step_input_box_value = self.zoom_step_input_box.GetValue()
        elif event.GetId() == 1336:
            tilt_step_input_box_value = self.tilt_step_input_box.GetValue()

        elif event.GetId() == 1241:
            cadence_flow_factor = int(self.cadence_flow_factor_box.GetValue())
            self.writeValue("cadence_flow_factor", cadence_flow_factor)
        elif event.GetId() == 1242:
            generation_flow_factor = int(self.generation_flow_factor_box.GetValue())
            self.writeValue("generation_flow_factor", generation_flow_factor)

        elif event.GetId() == 151:
            minmaxval = self.zoom_step_input_box.GetValue()
            self.zoom_slider.SetMin(int(-float(minmaxval)*100))
            self.zoom_slider.SetMax(int(float(minmaxval)*100))
            self.zoom_value_high_text.SetLabel(minmaxval)
            self.zoom_value_low_text.SetLabel("-"+minmaxval)
            self.zoom_slider.SetTickFreq(int(float(minmaxval)*100/10))
            #float(minmaxval)/20
        elif btn == "ZERO ZOOM":
            if not zero_zoom_active:
                bmp = wx.Bitmap("./images/zero_active.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.zoom_zero_button.SetBitmap(bmp)
                zero_zoom_active = True
                # Prepare the bezier curve that should be followed:
                frame_steps = int(self.zero_zoom_step_input_box.GetValue())
                bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')','').replace(' ','').split(',')
                bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))

                bezierArray = pyeaze.Animator(current_value=Translation_Z, target_value=Translation_Z_ARMED, duration=1,fps=frame_steps, easing=bezierTupple, reverse=False)

                self.writeValue("prepare_zero_zoom_motion", bezierArray.values)
                self.writeValue("start_zero_zoom_motion", 1)
                zero_frame_start = int(self.readValue("start_frame"))
                print("-- ZERO ZOOM MOTION SET, FROM (Z:" + str('%.2f' % Translation_Z) + " -> Z:" + str('%.2f' % Translation_Z_ARMED) + "), in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                zero_zoom_current_settings = "<\"0-Z: " + str('%.2f' % Translation_Z) + "->" + str('%.2f' % Translation_Z_ARMED) + " (fr:"+str(zero_frame_start)+" to:"+str(zero_frame_start+frame_steps)+")\">"
                print(zero_zoom_current_settings)
                self.SetLabel(windowlabel + " -- ZERO ZOOM MOTION SET, FROM (Z:" + str('%.2f' % Translation_Z) + " -> Z:" + str('%.2f' % Translation_Z_ARMED) + "), in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                self.zero_zoom_current_settings_Text.SetLabel(zero_zoom_current_settings)
            else:
                stepit_zoom = 0
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.zoom_zero_button.SetBitmap(bmp)
                zero_zoom_active = False
                self.writeValue("start_zero_zoom_motion", 0)
                self.zero_zoom_current_settings_Text.SetLabel("<\"0-Z: None\">")

        elif btn == "STRENGTH SCHEDULE":
            if not total_recall_others_inside_range_and_active:
                Strength_Scheduler = float(self.strength_schedule_slider.GetValue())*0.01
                self.writeValue("strength", Strength_Scheduler)
        elif event.GetId() == 3: #Seed Input Box
            if not total_recall_others_inside_range_and_active:
                seedValue = int(self.seed_input_box.GetValue())
                self.writeValue("seed", seedValue)
                self.writeValue("seed_changed", 1)
        elif btn == "LOOK_LEFT":
            if not armed_rotation and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_Y = 0
                    else:
                        Rotation_3D_Y = Rotation_3D_Y - float(self.rotate_step_input_box.GetValue())
                    self.writeValue("rotation_y", Rotation_3D_Y)
            elif armed_rotation:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_Y_ARMED = 0
                else:
                    Rotation_3D_Y_ARMED =  round(Rotation_3D_Y_ARMED - float(self.rotate_step_input_box.GetValue()),2)
                if should_use_total_recall:
                    self.writeValue("rotation_y", Rotation_3D_Y_ARMED)

        elif btn == "LOOK_RIGHT":
            if not armed_rotation and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_Y = 0
                    else:
                        Rotation_3D_Y = Rotation_3D_Y + float(self.rotate_step_input_box.GetValue())
                    self.writeValue("rotation_y", Rotation_3D_Y)
            elif armed_rotation:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_Y_ARMED = 0
                else:
                    Rotation_3D_Y_ARMED =  round(Rotation_3D_Y_ARMED + float(self.rotate_step_input_box.GetValue()),2)
                if should_use_total_recall:
                    self.writeValue("rotation_y", Rotation_3D_Y_ARMED)
        elif btn == "LOOK_UP":
            if not armed_rotation and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_X = 0
                    else:
                        Rotation_3D_X = Rotation_3D_X + float(self.rotate_step_input_box.GetValue())
                    self.writeValue("rotation_x", Rotation_3D_X)
            elif armed_rotation:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_X_ARMED = 0
                else:
                    Rotation_3D_X_ARMED =  round(Rotation_3D_X_ARMED + float(self.rotate_step_input_box.GetValue()),2)
                if should_use_total_recall:
                    self.writeValue("rotation_x", Rotation_3D_X_ARMED)
        elif btn == "LOOK_DOWN":
            if not armed_rotation and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_X = 0
                    else:
                        Rotation_3D_X = Rotation_3D_X - float(self.rotate_step_input_box.GetValue())
                    self.writeValue("rotation_x", Rotation_3D_X)
            elif armed_rotation:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_X_ARMED = 0
                else:
                    Rotation_3D_X_ARMED =  round(Rotation_3D_X_ARMED - float(self.rotate_step_input_box.GetValue()),2)
                if should_use_total_recall:
                    self.writeValue("rotation_x", Rotation_3D_X_ARMED)
        elif btn == "ZERO ROTATE":
            if not zero_rotate_active:
                bmp = wx.Bitmap("./images/zero_active.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.rotate_zero_button.SetBitmap(bmp)
                zero_rotate_active = True
                # Prepare the bezier curve that should be followed:
                frame_steps = int(self.zero_rotate_step_input_box.GetValue())
                bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')','').replace(' ','').split(',')
                bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))

                bezierArray1 = pyeaze.Animator(current_value=Rotation_3D_X, target_value=Rotation_3D_X_ARMED, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                bezierArray2 = pyeaze.Animator(current_value=Rotation_3D_Y, target_value=Rotation_3D_Y_ARMED, duration=1, fps=frame_steps, easing=bezierTupple, reverse=False)
                bezierArray = [bezierArray1.values, bezierArray2.values]
                self.writeValue("prepare_zero_rotation_motion", bezierArray)
                self.writeValue("start_zero_rotation_motion", 1)
                zero_frame_start = int(self.readValue("start_frame"))
                print("-- ZERO ROTATION MOTION SET, FROM (RL:" + str('%.2f' % Rotation_3D_Y) + " -> RL:" + str('%.2f' % Rotation_3D_Y_ARMED) + ") & (UD:" + str('%.2f' % Rotation_3D_X) + " -> UD:" + str('%.2f' % Rotation_3D_X_ARMED) + ") , in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                zero_rotation_current_settings = "<\"0-R: rl:" + str('%.2f' % Rotation_3D_Y) + "->rl:" + str('%.2f' % Rotation_3D_Y_ARMED) + " & ud:" + str('%.2f' % Rotation_3D_X) + "->ud:" + str('%.2f' % Rotation_3D_X_ARMED) + " (fr:"+str(zero_frame_start)+" to:"+str(zero_frame_start+frame_steps)+")\">"
                print(zero_rotation_current_settings)
                self.SetLabel(windowlabel + " -- ZERO ROTATION MOTION SET, FROM (RL:" + str('%.2f' % Rotation_3D_Y) + " -> RL:" + str('%.2f' % Rotation_3D_Y_ARMED) + ") & (UD:" + str('%.2f' % Rotation_3D_X) + " -> UD:" + str('%.2f' % Rotation_3D_X_ARMED) + ") , in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                self.zero_rotate_current_settings_Text.SetLabel(zero_rotation_current_settings)
            else:
                stepit_rotate = 0
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.rotate_zero_button.SetBitmap(bmp)
                zero_rotate_active = False
                self.writeValue("start_zero_rotation_motion", 0)
                self.zero_rotate_current_settings_Text.SetLabel("<\"0-R: None\">")


        elif btn == "ROTATE_LEFT":
            if not armed_tilt and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_Z = 0
                    else:
                        Rotation_3D_Z = Rotation_3D_Z + float(self.tilt_step_input_box.GetValue())
                    self.writeValue("rotation_z", Rotation_3D_Z)
            elif armed_tilt:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_Z_ARMED = 0
                else:
                    Rotation_3D_Z_ARMED =  round(Rotation_3D_Z_ARMED + float(self.tilt_step_input_box.GetValue()),2)
                if should_use_total_recall:
                    self.writeValue("rotation_z", Rotation_3D_Z_ARMED)

        elif btn == "ROTATE_RIGHT":
            if not armed_tilt and not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        Rotation_3D_Z = 0
                    else:
                        Rotation_3D_Z = Rotation_3D_Z - float(self.tilt_step_input_box.GetValue())
                    self.writeValue("rotation_z", Rotation_3D_Z)
            elif armed_tilt:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Rotation_3D_Z_ARMED = 0
                else:
                    Rotation_3D_Z_ARMED = round(Rotation_3D_Z_ARMED - float(self.tilt_step_input_box.GetValue()), 2)
                if should_use_total_recall:
                    self.writeValue("rotation_z", Rotation_3D_Z_ARMED)

        elif btn == "ZERO TILT":
            if not zero_tilt_active:
                bmp = wx.Bitmap("./images/zero_active.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.tilt_zero_button.SetBitmap(bmp)
                zero_tilt_active = True
                # Prepare the bezier curve that should be followed:
                frame_steps = int(self.zero_tilt_step_input_box.GetValue())
                bezier_from_input_box_string = self.bezier_points_input_box.GetValue()
                bezier_from_input_box_string = "((0, 0)," + bezier_from_input_box_string + ",(1, 1))"
                bezier_from_input_box_array = bezier_from_input_box_string.replace('(', '').replace(')','').replace(' ','').split(',')
                bezierTupple = list(((0, 0), (0, 0), (0, 0), (0, 0)))
                bezierTupple[0] = (float(bezier_from_input_box_array[0]), float(bezier_from_input_box_array[1]))
                bezierTupple[1] = (float(bezier_from_input_box_array[2]), float(bezier_from_input_box_array[3]))
                bezierTupple[2] = (float(bezier_from_input_box_array[4]), float(bezier_from_input_box_array[5]))
                bezierTupple[3] = (float(bezier_from_input_box_array[6]), float(bezier_from_input_box_array[7]))

                bezierArray = pyeaze.Animator(current_value=Rotation_3D_Z, target_value=Rotation_3D_Z_ARMED, duration=1,fps=frame_steps, easing=bezierTupple, reverse=False)

                self.writeValue("prepare_zero_tilt_motion", bezierArray.values)
                self.writeValue("start_zero_tilt_motion", 1)
                zero_frame_start = int(self.readValue("start_frame"))
                print("-- ZERO TILT MOTION SET, FROM (RZ:" + str('%.2f' % Rotation_3D_Z) + " -> RZ:" + str('%.2f' % Rotation_3D_Z_ARMED) + "), in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                zero_tilt_current_settings = "<\"0-T: " + str('%.2f' % Rotation_3D_Z) + "->" + str('%.2f' % Rotation_3D_Z_ARMED) + " (fr:" + str(zero_frame_start) + " to:" + str(zero_frame_start + frame_steps) + ")\">"
                print(zero_tilt_current_settings)
                self.SetLabel(windowlabel + " -- ZERO ZOOM MOTION SET, FROM (Z:" + str('%.2f' % Rotation_3D_Z) + " -> Z:" + str('%.2f' % Rotation_3D_Z_ARMED) + "), in " + str(frame_steps) + " steps. Starting at frame:" + str(zero_frame_start))
                self.zero_tilt_current_settings_Text.SetLabel(zero_tilt_current_settings)
            else:
                stepit_zoom = 0
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.tilt_zero_button.SetBitmap(bmp)
                zero_tilt_active = False
                self.writeValue("start_zero_tilt_motion", 0)
                self.zero_tilt_current_settings_Text.SetLabel("<\"0-T: None\">")





        elif btn == "CFG SCALE":
            if not total_recall_others_inside_range_and_active:
                CFG_Scale = float(self.cfg_schedule_slider.GetValue())
                self.writeValue("cfg", CFG_Scale)
        elif btn == "ARM_ROTATION":
            if armed_rotation:
                armed_rotation = False
                bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_rotation_button.SetBitmap(bmp)
                self.arm_rotation_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
            else:
                armed_rotation = True
                bmp = wx.Bitmap("./images/arm_on.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_rotation_button.SetBitmap(bmp)
                self.arm_rotation_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
        elif btn == "ARM_PAN":
            if armed_pan:
                armed_pan = False
                bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_pan_button.SetBitmap(bmp)
                self.arm_pan_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
            else:
                armed_pan = True
                bmp = wx.Bitmap("./images/arm_on.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_pan_button.SetBitmap(bmp)
                self.arm_pan_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
        elif btn == "ARM_ZOOM":
            if armed_zoom:
                armed_zoom = False
                bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_zoom_button.SetBitmap(bmp)
                self.arm_zoom_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
            else:
                armed_zoom = True
                bmp = wx.Bitmap("./images/arm_on.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_zoom_button.SetBitmap(bmp)
                self.arm_zoom_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
        elif btn == "ARM_TILT":
            if armed_tilt:
                armed_tilt = False
                bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_tilt_button.SetBitmap(bmp)
                self.arm_tilt_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
            else:
                armed_tilt = True
                bmp = wx.Bitmap("./images/arm_on.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 10, 10)
                self.arm_tilt_button.SetBitmap(bmp)
                self.arm_tilt_button.SetSize(bmp.GetWidth()+10, bmp.GetHeight()+10)
        elif btn == "FOV":
            if not total_recall_movements_inside_range_and_active:
                if not should_use_total_recall_in_deforumation:
                    currentEventTypeID = event.GetEventType()
                    if self.eventDict[currentEventTypeID] == "EVT_RIGHT_UP":
                        FOV_Scale = 70
                        self.fov_slider.SetValue(int(FOV_Scale))
                    else:
                        FOV_Scale = float(self.fov_slider.GetValue())
                    self.writeValue("fov", FOV_Scale)
        elif btn == "LOCK FOV":
            if is_fov_locked:
                is_fov_locked = False
                self.fov_lock_button.SetBitmap(wx.Bitmap("./images/lock_off.bmp"))
            else:
                is_fov_locked = True
                self.fov_lock_button.SetBitmap(wx.Bitmap("./images/lock_on.bmp"))
                if is_reverse_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*-5))
                    self.fov_slider.SetValue(int(FOV_Scale))
                else:
                    FOV_Scale = float(70+(Translation_Z*5))
                    self.fov_slider.SetValue(int(FOV_Scale))
                self.writeValue("fov", FOV_Scale)
        elif btn == "REVERSE FOV":
            if is_reverse_fov_locked:
                is_reverse_fov_locked = False
                self.fov_reverse_lock_button.SetBitmap(wx.Bitmap("./images/reverse_fov_off.bmp"))
                if is_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*5))
                    self.fov_slider.SetValue(int(FOV_Scale))
                    self.writeValue("fov", FOV_Scale)
            else:
                is_reverse_fov_locked = True
                self.fov_reverse_lock_button.SetBitmap(wx.Bitmap("./images/reverse_fov_on.bmp"))
                if is_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*-5))
                    self.fov_slider.SetValue(int(FOV_Scale))
                    self.writeValue("fov", FOV_Scale)
        elif btn == "STEPS":
            if not total_recall_others_inside_range_and_active:
                STEP_Schedule = int(self.sample_schedule_slider.GetValue())
                self.writeValue("steps", STEP_Schedule)
        elif btn == "CADENCE":
            if not total_recall_others_inside_range_and_active:
                Cadence_Schedule = int(self.cadence_slider.GetValue())
                self.writeValue("cadence", Cadence_Schedule)
                cadenceArray[int(self.readValue("start_frame"))] = Cadence_Schedule
        elif btn == "Noise":
            if not total_recall_others_inside_range_and_active:
                noise_multiplier = float(self.noise_slider.GetValue())/100
                self.writeValue("noise_multiplier", noise_multiplier)
        elif btn == "Perlin Octaves":
            if not total_recall_others_inside_range_and_active:
                Perlin_Octave_Value = int(self.perlin_octave_slider.GetValue())
                self.writeValue("perlin_octaves", Perlin_Octave_Value)
        elif btn == "Perlin Persistence":
            if not total_recall_others_inside_range_and_active:
                Perlin_Persistence_Value = float(self.perlin_persistence_slider.GetValue())/100
                self.writeValue("perlin_persistence", Perlin_Persistence_Value)
        #########START OF CN STUFF#############################
        elif btn.startswith("CN WEIGHT"):
            if not total_recall_others_inside_range_and_active:
                CN_Weight[current_active_cn_index-1] = float(self.control_net_weight_slider[current_active_cn_index-1].GetValue())*0.01
                self.writeValue("cn_weight"+str(current_active_cn_index), CN_Weight[current_active_cn_index-1])
        elif btn.startswith("CN STEPSTART"):
            if not total_recall_others_inside_range_and_active:
                CN_StepStart[current_active_cn_index-1] = float(self.control_net_stepstart_slider[current_active_cn_index-1].GetValue()) * 0.01
                self.writeValue("cn_stepstart"+str(current_active_cn_index), CN_StepStart[current_active_cn_index-1])
        elif btn.startswith("CN STEPEND"):
            if not total_recall_others_inside_range_and_active:
                CN_StepEnd[current_active_cn_index-1] = float(self.control_net_stepend_slider[current_active_cn_index-1].GetValue()) * 0.01
                self.writeValue("cn_stepend"+str(current_active_cn_index), CN_StepEnd[current_active_cn_index-1])
        elif btn.startswith("CN LOWT"):
            if not total_recall_others_inside_range_and_active:
                CN_LowT[current_active_cn_index-1] = int(self.control_net_lowt_slider[current_active_cn_index-1].GetValue())
                self.writeValue("cn_lowt"+str(current_active_cn_index), CN_LowT[current_active_cn_index-1])
        elif btn.startswith("CN HIGHT"):
            if not total_recall_others_inside_range_and_active:
                CN_HighT[current_active_cn_index-1] = int(self.control_net_hight_slider[current_active_cn_index-1].GetValue())
                self.writeValue("cn_hight"+str(current_active_cn_index), CN_HighT[current_active_cn_index-1])
        elif btn.startswith("U.D.Cn"):
            if not total_recall_others_inside_range_and_active:
                CN_UDCn[current_active_cn_index-1] = int(self.control_net_active_checkbox[current_active_cn_index-1].GetValue())
                #self.writeValue("cn_udcn"+str(current_active_cn_index), CN_UDCn[current_active_cn_index-1])
                #self.writeValue("cn_weight"+str(current_active_cn_index), CN_Weight[current_active_cn_index-1])
                #self.writeValue("cn_stepstart"+str(current_active_cn_index), CN_StepStart[current_active_cn_index-1])
                #self.writeValue("cn_stepend"+str(current_active_cn_index), CN_StepEnd[current_active_cn_index-1])
                #self.writeValue("cn_lowt"+str(current_active_cn_index), CN_LowT[current_active_cn_index-1])
                #self.writeValue("cn_hight"+str(current_active_cn_index), CN_HighT[current_active_cn_index-1])
                SendBlock = []
                SendBlock.append(pickle.dumps([1, "cn_udcn"+str(current_active_cn_index), CN_UDCn[current_active_cn_index-1]]))
                SendBlock.append(pickle.dumps([1, "cn_weight"+str(current_active_cn_index), CN_Weight[current_active_cn_index-1]]))
                SendBlock.append(pickle.dumps([1, "cn_stepstart"+str(current_active_cn_index), CN_StepStart[current_active_cn_index-1]]))
                SendBlock.append(pickle.dumps([1, "cn_stepend"+str(current_active_cn_index), CN_StepEnd[current_active_cn_index-1]]))
                SendBlock.append(pickle.dumps([1, "cn_lowt"+str(current_active_cn_index), CN_LowT[current_active_cn_index-1]]))
                SendBlock.append(pickle.dumps([1, "cn_hight"+str(current_active_cn_index), CN_HighT[current_active_cn_index-1]]))
                self.writeValue("<BLOCK>", SendBlock)

        elif btn == "Backup All Images":
            if not os.path.isdir(deforumation_image_backup_folder):
                os.mkdir(deforumation_image_backup_folder)
            outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
            resume_timestring = str(readValue("resume_timestring"))
            #folder = outdir + "/" + resume_timestring + "_" + current_render_frame + ".png"
            if os.path.isdir(outdir):
                for item in os.listdir(deforumation_image_backup_folder):
                    os.remove(deforumation_image_backup_folder + item)
                numFiles = 0
                for item in os.listdir(outdir):
                    if not ".png" in item:
                        continue
                    else:
                        srcPath = outdir + "/" + item
                        dstPath = deforumation_image_backup_folder + item
                        shutil.copy(srcPath, dstPath)
                        numFiles += 1
                self.SetLabel(windowlabel + " -- Backup done, backed up " + str(numFiles) + " files.")
                print("Backup done, backed up " + str(numFiles) + " files.")
            else:
                self.SetLabel(windowlabel + " -- No ongoing render folder. No backup done.")
        elif btn == "Restore All Images":
            if not os.path.isdir(deforumation_image_backup_folder):
                os.mkdir(deforumation_image_backup_folder)
            outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
            resume_timestring = str(readValue("resume_timestring"))
            #folder = outdir + "/" + resume_timestring + "_" + current_render_frame + ".png"
            if os.path.isdir(outdir):
                backed_up_timestring = ""
                for item in os.listdir(deforumation_image_backup_folder):
                    if ".txt" in item or ".mp4" in item:
                        continue
                    frameNumberStart = item.rfind("_")
                    backed_up_timestring = item[:frameNumberStart]

                shouldContinue = True
                if resume_timestring != backed_up_timestring:
                    dlg = wx.MessageDialog(self, "Backup is from another timestring, do you really want to restore?", "Mismatching timestrings", wx.YES_NO | wx.ICON_WARNING)
                    result = dlg.ShowModal()
                    if result == wx.ID_YES:
                        shouldContinue = True
                    else:
                        shouldContinue = False

                if shouldContinue:
                    numFiles = 0
                    for item in os.listdir(outdir):
                        if ".txt" in item or ".mp4" in item:
                            continue
                        os.remove(outdir + "/" + item)
                    if(numFiles !=0):
                        print("Removed " + str(numFiles) + " files from original folder:"+str(outdir))
                    else:
                        print("No files removed from original folder:"+str(outdir))

                    numFiles = 0
                    #resume_timestring + "_" + current_render_frame + ".png"
                    for item in os.listdir(deforumation_image_backup_folder):
                        if ".txt" in item or ".mp4" in item:
                            continue
                        else:
                            frameNumberStart = item.rfind("_")
                            frameNumberEnd = item.rfind(".")
                            frameNumber = item[frameNumberStart+1:frameNumberEnd]
                            srcPath = deforumation_image_backup_folder + item
                            dstPath = outdir + "/" + resume_timestring + "_" + frameNumber + ".png"
                            shutil.copy(srcPath, dstPath)
                            numFiles += 1
                    self.SetLabel(windowlabel + " -- Restore done, restored " + str(numFiles) + " files.")
                    print("Restore done, restored " + str(numFiles) + " files.")
            else:
                self.SetLabel(windowlabel + " -- No ongoing render folder. No restore done.")


        #########END OF CN STUFF#############################
        elif btn == "Show current image" or btn == "REWIND" or btn == "FORWARD" or event.GetId() == 2 or btn == "REWIND_CLOSEST" or btn == "FORWARD_CLOSEST":
            frame_has_changed = True
            number_of_recalled_frames = int(self.readValue("get_number_of_recalled_frames"))
            self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))
            current_frame = str(self.readValue("start_frame"))
            #print("Got current start frame:" + current_frame)
            current_render_frame = int(current_frame)
            outdir = str(readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
            resume_timestring = str(readValue("resume_timestring"))
            if btn == "REWIND_CLOSEST":
                current_render_frame = self.frame_step_input_box.GetValue()
                if current_render_frame == "":
                    current_render_frame = 0
                current_render_frame = self.getClosestPrompt("R", int(current_render_frame))
            elif btn == "FORWARD_CLOSEST":
                current_render_frame = self.frame_step_input_box.GetValue()
                if current_render_frame == "":
                    current_render_frame = 0
                current_render_frame = self.getClosestPrompt("F", int(current_render_frame))
            elif btn == "REWIND":
                current_render_frame = self.frame_step_input_box.GetValue()
                if current_render_frame == '':
                    current_render_frame = 0
                if int(current_render_frame) > -1:
                    current_render_frame = str(int(current_render_frame)-1)
                if int(current_render_frame) < 0:
                    current_render_frame = 0
            elif btn == "FORWARD":
                current_render_frame = self.frame_step_input_box.GetValue()
                if current_render_frame == '':
                    current_render_frame = 0
                if int(current_render_frame) > -1:
                    current_render_frame = str(int(current_render_frame) + 1)
            elif event.GetId() == 2:
                current_render_frame = self.frame_step_input_box.GetValue()
            if should_use_total_recall and (int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue())) and (int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue())):
                self.setValuesFromSavedFrame(int(current_render_frame))
            else:
                self.loadCurrentPrompt("P", current_render_frame, 0)
                self.loadCurrentPrompt("N", current_render_frame, 0)
            current_render_frame = str(current_render_frame).zfill(9)
            imagePath = outdir + "/" + resume_timestring + "_" + current_render_frame + ".png"
            maxBackTrack = 100
            tmp_current_render_frame =  current_render_frame
            #print(str("Trying to load:"+imagePath))
            while not os.path.isfile(imagePath):
                if (int(current_render_frame) == 0):
                    break
                current_render_frame = int(current_render_frame) - 1
                imagePath = get_current_image_path_f(current_render_frame) #outdir + "/" + resume_timestring + "_" + current_render_frame + ".png" #imagePath = get_current_image_path()
                maxBackTrack = maxBackTrack - 1
                if maxBackTrack == 0:
                    break
            #print(str("Loaded:"+imagePath))
            if os.path.isfile(imagePath):
                #if self.bitmap != None:
                #    self.bitmap.Destroy()
                #    self.bitmap = None
                self.img = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                imgWidth = self.img.GetWidth()
                imgHeight = self.img.GetHeight()
                imageRatio = imgWidth/imgHeight
                imgHeight = 600
                imgWidth = int(imageRatio*imgHeight)
                self.img = self.img.Scale(int(imgWidth / 2), int(imgHeight / 2), wx.IMAGE_QUALITY_HIGH)
                #bitmap = wx.StaticBitmap(self, wx.ID_ANY, self.img, pos=(trbX + 650, tbrY - 120))
                bitmap = wx.Bitmap(self.img)
                #bitmap = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_OTHER,(256, 256))
                #self.bitmap = wx.StaticBitmap(self, wx.ID_ANY, self.img, pos=(trbX + 650, tbrY - 120))
                self.bitmap.SetBitmap(bitmap)
                self.frame_step_input_box.SetValue(str(int(current_render_frame)))

                #self.bitmap = wx.Bitmap(imagePath)
                #imgWidth = self.bitmap.GetWidth()
                #imgHeight = self.bitmap.GetHeight()
                #self.bitmap = scale_bitmap(self.bitmap, int(imgWidth / 2), int(imgHeight / 2))
                #self.bitmap
                self.panel.Layout()
                self.Refresh()
                #Destroy and repaint image
                #print(str(self.framer.bitmap))
                if self.framer != None:
                    if is_paused_rendering:
                        self.framer.DrawImage()
            elif should_use_total_recall or should_use_total_recall_in_deforumation:
                current_render_frame = tmp_current_render_frame
                self.frame_step_input_box.SetValue(str(int(tmp_current_render_frame)))

        elif btn == "Set current image":
            current_frame = self.frame_step_input_box.GetValue()
            current_render_frame = int(current_frame)
            self.loadCurrentPrompt("P", current_frame, 1)
            self.loadCurrentPrompt("N", current_frame, 1)
            self.writeValue("should_resume", 1)
            self.writeValue("start_frame", int(current_frame))
            proposedCadence = Cadence_Schedule
            for key, value in sorted(cadenceArray.items()):
                if int(current_frame) >= key:
                    proposedCadence = value
                else:
                    break
            #print("Suggest you use cadence:"+str(proposedCadence))
            self.cadence_suggestion.SetLabel("(hist cad: " + str(proposedCadence) + ")")
            number_of_recalled_frames = int(self.readValue("get_number_of_recalled_frames"))
            self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))

        elif btn == "USE DEFORUMATION STRENGTH":
            if should_use_deforumation_strength == 0:
                self.writeValue("should_use_deforumation_strength", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("strength", Strength_Scheduler)
                should_use_deforumation_strength = 1
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
            else:
                self.writeValue("should_use_deforumation_strength", 0)
                should_use_deforumation_strength = 0
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
        elif btn == "USE DEFORUMATION CFG":
            if should_use_deforumation_cfg == 0:
                self.writeValue("should_use_deforumation_cfg", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("cfg", CFG_Scale)
                should_use_deforumation_cfg = 1
            else:
                self.writeValue("should_use_deforumation_cfg", 0)
                should_use_deforumation_cfg = 0
        elif btn == "U.D.Ca":
            if should_use_deforumation_cadence == 0:
                self.writeValue("should_use_deforumation_cadence", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("cadence", Cadence_Schedule)
                should_use_deforumation_cadence = 1
            else:
                self.writeValue("should_use_deforumation_cadence", 0)
                should_use_deforumation_cadence = 0
        elif btn == "U.D.No":
            if should_use_deforumation_noise == 0:
                self.writeValue("should_use_deforumation_noise", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("noise_multiplier", float(noise_multiplier))
                should_use_deforumation_noise = 1
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("perlin_octaves", int(Perlin_Octave_Value))
                    self.writeValue("perlin_persistence", float(Perlin_Persistence_Value))
            else:
                self.writeValue("should_use_deforumation_noise", 0)
                should_use_deforumation_noise = 0
        elif btn == "U.D.Pa":
            if should_use_deforumation_panning == 0:
                self.writeValue("should_use_deforumation_panning", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("translation_x", Translation_X)
                    self.writeValue("translation_y", Translation_Y)
                should_use_deforumation_panning = 1
            else:
                self.writeValue("should_use_deforumation_panning", 0)
                should_use_deforumation_panning = 0
        elif btn == "U.D.Zo":
            if should_use_deforumation_zoomfov == 0:
                self.writeValue("should_use_deforumation_zoomfov", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("translation_z", Translation_Z)
                    self.writeValue("fov", FOV_Scale)
                should_use_deforumation_zoomfov = 1
            else:
                self.writeValue("should_use_deforumation_zoomfov", 0)
                should_use_deforumation_zoomfov = 0
        elif btn == "U.D.Ro":
            if should_use_deforumation_rotation == 0:
                self.writeValue("should_use_deforumation_rotation", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("rotation_x", Rotation_3D_X)
                    self.writeValue("rotation_y", Rotation_3D_Y)
                should_use_deforumation_rotation = 1
            else:
                self.writeValue("should_use_deforumation_rotation", 0)
                should_use_deforumation_rotation = 0
        elif btn == "U.D.Ti":
            if should_use_deforumation_tilt == 0:
                self.writeValue("should_use_deforumation_tilt", 1)
                if not total_recall_others_inside_range_and_active:
                    self.writeValue("rotation_z", Rotation_3D_Z)
                should_use_deforumation_tilt = 1
            else:
                self.writeValue("should_use_deforumation_tilt", 0)
                should_use_deforumation_tilt = 0
        elif btn == "REPLAY":
            if isReplaying == 0:
                #print("Starting Replay")
                replayFrom = int(self.replay_from_input_box.GetValue())
                replayTo = int(self.replay_to_input_box.GetValue())
                replayFPS = int(self.replay_fps_input_box.GetValue())
                if (replayFrom >= 0) and (replayFrom < replayTo):
                    imagePath = get_current_image_path_f(replayFrom)

                    if create_gif_animation_on_preview:
                        ffmpeg_image_path = create_ffmpeg_image_string()
                        ffmpegPath = self.ffmpeg_path_input_box.GetValue()
                        if ffmpegPath == "":
                            ffmpegPath = "ffmpeg"
                        is_ffmpegPath_correct = shutil.which(ffmpegPath)
                        if not is_ffmpegPath_correct is None:
                            crf = 20
                            cmd = [
                                ffmpegPath,
                                '-start_number', str(replayFrom),
                                '-framerate', str(float(replayFPS)),
                                # '-thread_queue_size 4096',
                                #'-r', str(float(replayFPS)),
                                #'-fps', '30',
                                '-y',
                                '-i', ffmpeg_image_path,
                                '-frames:v', str(int((replayTo - replayFrom)/(replayFPS/12))),
                                '-filter_complex', "fps=12,scale=128:-1:flags=lanczos",
                                '-pix_fmt', 'yuv420p',
                                '-crf', str(crf),
                                '-pattern_type', 'sequence'
                            ]
                            outPath = ""
                            motionName = ""
                            motionRange = "Not Applicable"
                            if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                                motionName = ask(message = "What will the motion be called? (push cancel to abort):", caption = "FPS dependent... (this is going to be a " + str(replayFPS) + " FPS motion).")
                                if motionName != "":
                                    motionRange = askRange(message="What range defines the motion?")
                                    outPath = gif_animation_output_path + motionName.replace(' ', '_') + "_" + "(" + str(replayFPS) + " FPS)" + "("+str(motionRange)+")" + ".gif"
                            else:
                                motionName = ask(message = "What will the motion be called? (push cancel to abort):", caption = "This motion is FPS independent.")
                                if motionName != "":
                                    motionRange = askRange(message="What range defines the motion?")
                                    outPath = gif_animation_output_path + motionName.replace(' ', '_') + "("+str(motionRange)+")" + ".gif"

                            if outPath != "":
                                cmd.append(outPath)
                                self.SetLabel(windowlabel + " -- Wait while Deofrumation creates pre-defined motion.")
                                parameter_container = []
                                ShouldProcessImages = True
                                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                                    parameter_container = pickle.loads(readValue_special("saved_frame_params", -1))
                                    if len(parameter_container) < (replayTo - replayFrom):
                                        wx.MessageBox('Not enough Total Recall points (check your To and From values)','Not enough data points', wx.OK | wx.ICON_ERROR)
                                        ShouldProcessImages = False
                                if ShouldProcessImages:
                                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                                    stdout, stderr = process.communicate()

                                    if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                                        if os.path.isfile(deforumationPredefinedMotionPathSettings):
                                            deforumFile = open(deforumationPredefinedMotionPathSettings, 'a')
                                        else:
                                            deforumFile = open(deforumationPredefinedMotionPathSettings, 'w')

                                        motionLine = "\n" + motionName + " (" + str(replayFPS) + " FPS)" + "("+str(motionRange)+")" + ", "
                                        motionLine += outPath + " ," + str(replayFPS) + " ,"
                                        for index in range(replayFrom, replayTo):
                                            motionLine += "["
                                            motionLine += str('%.2f' % parameter_container[index].translation_x) + ","
                                            motionLine += str('%.2f' % parameter_container[index].translation_y) + ","
                                            motionLine += str('%.2f' % parameter_container[index].translation_z) + ","
                                            motionLine += str('%.2f' % parameter_container[index].rotation_y) + ","
                                            motionLine += str('%.2f' % parameter_container[index].rotation_x) + ","
                                            motionLine += str('%.2f' % parameter_container[index].rotation_z) + "]"
                                            if (index != replayTo-1):
                                                motionLine += ":"

                                        deforumFile.write(motionLine)
                                        deforumFile.close()
                                        #subprocess.run(cmd)
                                        #stdout, stderr = process.communicate()
                                        self.SetLabel(windowlabel + " -- Pre-defined motion created.")
                                        self.loadPredefinedMotions()
                                        self.predefined_motion_choice.SetSelection(0)
                                        self.predefined_motion_fps_choice.SetSelection(0)
                                        self.predefined_motion_range_choice.SetSelection(0)

                                    else:
                                        if os.path.isfile(deforumationPredefinedMotionPathSettings):
                                            deforumFile = open(deforumationPredefinedMotionPathSettings, 'a')
                                        else:
                                            deforumFile = open(deforumationPredefinedMotionPathSettings, 'w')

                                        motionLine = "\n"+motionName + "("+str(motionRange)+")" +", "
                                        motionLine += outPath + " ," + "-1" + " ,"
                                        motionLine += "["
                                        motionLine += str('%.2f' % Translation_X) + ","
                                        motionLine += str('%.2f' % Translation_Y) + ","
                                        motionLine += str('%.2f' % Translation_Z) + ","
                                        motionLine += str('%.2f' % Rotation_3D_Y) + ","
                                        motionLine += str('%.2f' % Rotation_3D_X) + ","
                                        motionLine += str('%.2f' % Rotation_3D_Z) + "]"

                                        deforumFile.write(motionLine)
                                        deforumFile.close()
                                        #subprocess.run(cmd)
                                        #stdout, stderr = process.communicate()
                                        print("Done creating GIF-animation (FPS Dependent)")
                                        self.SetLabel(windowlabel + " -- Pre-defined motion created.")
                                        self.loadPredefinedMotions()
                                        self.predefined_motion_choice.SetSelection(0)
                                        self.predefined_motion_fps_choice.SetSelection(0)
                                        self.predefined_motion_range_choice.SetSelection(0)
                            else:
                                print("Canceled creating GIF-animation")
                        else:
                            wx.MessageBox('FFMPEG could not be found, please specify the path under \"Audio Playback Settings\".', 'FFMPEG error', wx.OK | wx.ICON_ERROR)

                    elif self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                        ffmpeg_image_path = create_ffmpeg_image_string()
                        ffmpegPath = self.ffmpeg_path_input_box.GetValue()
                        if ffmpegPath == "":
                            ffmpegPath = "ffmpeg"
                        self.kalle = threading.Thread(target=ffmpeg_stitch_video, args=(self, ffmpegPath, replayFPS, "out.mp4",replayFrom, replayTo - replayFrom, ffmpeg_image_path, self.audio_path2_input_box.GetPath()))
                        self.kalle.daemon = False
                        self.kalle.start()

                        #ffmpeg_stitch_video("ffmpeg", replayFPS, "out.mp4",
                        #                    replayFrom, replayTo - replayFrom,
                        #                    ffmpeg_image_path,
                        #                    audio_path='H:\\Deforumation_Competition\\snapshot2.wav')
                    else:
                        should_render_live = True
                        self.live_render_checkbox.SetValue(1)
                        if os.path.isfile(imagePath):
                            current_frame = str(replayFrom)
                            current_frame = current_frame.zfill(9)
                            self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                            imgWidth = self.img_render.GetWidth()
                            imgHeight = self.img_render.GetHeight()
                            if self.framer == None:
                                self.framer = render_window(self, 'Render Image')
                                self.framer.Show()
                                self.framer.SetSize(imgWidth + 18, imgHeight + 40)
                                self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                                self.framer.Refresh()
                                current_render_frame = int(current_frame)
                        isReplaying = 1
                        bmp = wx.Bitmap("./images/stop.bmp", wx.BITMAP_TYPE_BMP)
                        bmp = scale_bitmap(bmp, 18, 18)
                        self.replay_button.SetBitmap(bmp)
            else:
                isReplaying = 0
                bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 18, 18)
                self.replay_button.SetBitmap(bmp)
        elif btn == "Fix Aspect Ratio":
            if should_render_live == True:
                if not int(is_paused_rendering) or int(current_render_frame) < 0:
                    imagePath = get_current_image_path_f(current_frame)
                else:
                    imagePath = get_current_image_path_f(current_render_frame)
                if os.path.isfile(imagePath):
                    self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                    imgWidth = self.img_render.GetWidth()
                    imgHeight = self.img_render.GetHeight()
                    aspectRatio = imgHeight / imgWidth
                    framer_Width, framer_Height = self.framer.GetSize()
                    framer_Height = int(framer_Width * aspectRatio)
                    if int(is_paused_rendering):
                        self.img_render = self.img_render.Scale(framer_Width-18, framer_Height-40, wx.IMAGE_QUALITY_HIGH)
                        self.framer.SetSize(framer_Width, framer_Height)
                        self.framer.panel.current_width = framer_Width
                        self.framer.panel.current_height = framer_Height
                        self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                        self.framer.panel.resize(framer_Width, framer_Height)
                        self.framer.panel.bitmap = None
                        self.framer.Refresh()
                    else:
                        self.framer.SetSize(framer_Width, framer_Height) #18,40
                        self.framer.panel.resize(framer_Width, framer_Height)
                        self.framer.Layout()
                        self.framer.panel.Refresh()
        elif btn == "Use total recall...":
            if should_use_total_recall == 0:
                should_use_total_recall = 1
                self.writeValue("should_use_total_recall", 1)
                self.writeValue("total_recall_from", int(self.total_recall_from_input_box.GetValue()))
                self.writeValue("total_recall_to", int(self.total_recall_to_input_box.GetValue()))
                Translation_X_ARMED = 0
                Translation_Y_ARMED = 0
                Translation_Z_ARMED = 0
                Rotation_3D_X_ARMED = 0
                Rotation_3D_Y_ARMED = 0
                Rotation_3D_Z_ARMED = 0
                self.SetLabel(windowlabel + " -- Using total recall from frame " + str(self.total_recall_from_input_box.GetValue()) + " to frame " + self.total_recall_to_input_box.GetValue())
            else:
                self.writeValue("should_use_total_recall", 0)
                should_use_total_recall = 0
                self.writeValue("prompts_touched", 0)
                self.setAllComponentValues()
                self.sendAllValues()

        elif btn == "Optical flow on/off":
            if not total_recall_others_inside_range_and_active:
                if should_use_optical_flow == 0:
                    should_use_optical_flow = 1
                    self.writeValue("should_use_optical_flow", 1)
                else:
                    self.writeValue("should_use_optical_flow", 0)
                    should_use_optical_flow = 0
        elif btn == "View orig. values in Deforumation":
            if should_use_total_recall_in_deforumation == 0:
                should_use_total_recall_in_deforumation = 1
                self.SetLabel(windowlabel + " -- Now showing original values as recalled from original render.")
                self.copy_original_to_manual_button.Enable()
            else:
                should_use_total_recall_in_deforumation = 0
                self.setAllComponentValues()
                self.SetLabel(windowlabel + " -- Now showing manually set deforumation values.")
                self.copy_original_to_manual_button.Disable()
        elif btn == "Orig. val -> Manual val":
            self.copyAllOriginalValuesToManual(current_render_frame)
            #self.setAllComponentValues()
        elif btn == "Recall prompts":
            if should_use_total_recall_prompt == 0:
                should_use_total_recall_prompt = 1
                self.writeValue("should_use_total_recall_prompt", 1)
            else:
                should_use_total_recall_prompt = 0
                self.writeValue("should_use_total_recall_prompt", 0)
                self.writeValue("prompts_touched", 0)
                #self.loadCurrentPrompt("P", current_render_frame, 0)
                #self.loadCurrentPrompt("N", current_render_frame, 0)
                #self.setAllComponentValues()
                self.setAllPromptCopmponentValues()
                self.sendAllPropmptValues()
        elif btn == "Recall movements":
            if should_use_total_recall_movements == 0:
                should_use_total_recall_movements = 1
                self.writeValue("should_use_total_recall_movements", 1)
            else:
                should_use_total_recall_movements = 0
                self.writeValue("should_use_total_recall_movements", 0)
                self.setAllMotionComponentValues()
                self.sendAllMotionValues()
        elif btn == "Recall \"others\"":
            if should_use_total_recall_others == 0:
                should_use_total_recall_others = 1
                self.writeValue("should_use_total_recall_others", 1)
            else:
                should_use_total_recall_others = 0
                self.writeValue("should_use_total_recall_others", 0)
                self.setAllOtherComponentValues()
                self.sendAllOtherValues()

        elif btn == "Use Deforumation timestamp when resuming":
            if should_use_deforumation_timestring == 0:
                should_use_deforumation_timestring = 1
                self.writeValue("should_use_deforumation_timestring", 1)
            else:
                should_use_deforumation_timestring = 0
                self.writeValue("should_use_deforumation_timestring", 0)
        elif btn == "Erase total recall memory":
            self.writeValue("should_erase_total_recall_memory", 1)
            number_of_recalled_frames = int(self.readValue("get_number_of_recalled_frames"))
            self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))
        elif btn == "Load Recall Data":
            dlg = wx.FileDialog(None, "Load Recall file", wildcard="Recal files (*.obj)|*.obj", style=wx.FD_OPEN)
            #dlg = wx.DirDialog (None, "Choose Recall File", "",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
            if dlg.ShowModal() == wx.ID_OK:
                fileObjectPath = dlg.GetPath()
                self.writeValue("should_use_deforumation_timestring", 1)

                with open(fileObjectPath, 'rb') as fp:
                    parameter_container = pickle.load(fp)
                fp.close()
                bytesToSend = pickle.dumps(parameter_container)
                self.writeValue("upload_recall_file", bytesToSend)
                number_of_recalled_frames = int(self.readValue("get_number_of_recalled_frames"))
                self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))
        elif btn == "Total save":
            dlg = wx.FileDialog (None, "Save to file:", ".", "", "Zip (*.zip)|*.zip", wx.FD_SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                resume_timestring = str(readValue("resume_timestring"))
                frame_outdir = str(readValue("frame_outdir"))
                if resume_timestring == "":
                    print("No timestring found.")
                    resume_timestring = None
                else:
                    save_path_human_readable = dlg.GetPath()+'/'+resume_timestring+"_total_recall_data.txt"
                    save_path_object = dlg.GetPath() + '/' + resume_timestring + "_total_recall_data.obj"
                    shutil.make_archive(dlg.GetPath()+'/'+"deforum_images", 'zip', frame_outdir)

            if resume_timestring != None:
                print("kalle")
        elif btn == "Save Recall Data":
            parameter_container = pickle.loads(readValue_special("saved_frame_params", -1))
            #deforumFile = open(totalRecallFilePath, 'w')
            #anObject = []{}

            dlg = wx.DirDialog (None, "Choose save directory", "",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
            if dlg.ShowModal() == wx.ID_OK:
                resume_timestring = str(readValue("resume_timestring"))
                if resume_timestring == "":
                    print("No timestring found, will use 00000000000000")
                    resume_timestring = "00000000000000"
                save_path_human_readable = dlg.GetPath()+'/'+resume_timestring+"_total_recall_data.txt"
                save_path_object = dlg.GetPath() + '/' + resume_timestring + "_total_recall_data.obj"

                with open(save_path_human_readable, 'w') as fp:
                    for n in parameter_container:
                        numMembers = len(inspect.getmembers(parameter_container[n]))
                        indexI = 0
                        fp.write("('Frame_Number', '"+str(n)+"')")
                        for i in inspect.getmembers(parameter_container[n]):
                            # to remove private and protected
                            # functions
                            indexI += 1
                            if not i[0].startswith('_'):
                                # To remove other methods that
                                # doesnot start with a underscore
                                if not inspect.ismethod(i[1]):
                                    fp.write(str(i))
                                if indexI != numMembers:
                                    fp.write(',')
                        fp.write('\n')
                fp.close()

                with open(save_path_object, 'wb') as fp:
                    pickle.dump(parameter_container, fp)
                fp.close()


            #members2 = list(vars(parameter_container[0]).keys())
            #members = [attr for attr in dir(parameter_container[0]) if not callable(getattr(parameter_container[0], attr)) and not attr.startswith("__")]
            #print(members)
            #for n in parameter_container[0].steps():
            #    print(str(n))
                #pickle.dump(parameter_container, fp)
            #    json.dump(str(parameter_container[0]),fp)
            #deforumFile.write(json.dumps(parameter_container))
            #deforumFile.close()
        elif btn == "LIVE RENDER":
            current_frame = str(self.readValue("start_frame"))
            #print("should_render_live: "+str(should_render_live))
            if should_render_live == 0:
                should_render_live = 1
                outdir = str(self.readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
                resume_timestring = str(self.readValue("resume_timestring"))

                #current_frame = current_frame.zfill(9)
                #imagePath = get_current_image_path()
                if not int(is_paused_rendering) or int(current_render_frame) < 0:
                    imagePath = get_current_image_path_f(current_frame)
                else:
                    imagePath = get_current_image_path_f(current_render_frame)

                maxBackTrack = 100
                while not os.path.isfile(imagePath):
                    if (current_frame == 0):
                        break
                    current_frame = str(int(current_frame) - 1)
                    current_frame = current_frame.zfill(9)
                    if not is_paused_rendering or int(current_render_frame) < 0:
                        imagePath = get_current_image_path_f(current_frame)
                    else:
                        imagePath = get_current_image_path_f(current_render_frame)
                    maxBackTrack = maxBackTrack -1
                    if maxBackTrack == 0:
                        break
                if os.path.isfile(imagePath):
                        self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                        imgWidth = self.img_render.GetWidth()
                        imgHeight = self.img_render.GetHeight()
                        if self.framer == None:
                            self.framer = render_window(self, 'Render Image')
                            self.framer.Move(renderWindowX, renderWindowY)
                            self.framer.Show()
                        self.framer.SetSize(imgWidth+18, imgHeight+40) #18,40
                        self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                        self.framer.Refresh()
                        current_render_frame = int(current_frame)
            else:
                should_render_live = False
                if self.framer != None:
                    self.framer.Hide()
                    self.framer.Close()
                    self.framer = None
                current_render_frame = -1
        elif btn == "Use Deforumation prompt scheduling":
            if should_use_deforumation_prompt_scheduling == 0:
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
                self.writeValue("should_use_deforumation_prompt_scheduling", 1)
                should_use_deforumation_prompt_scheduling = 1
            else:
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
                self.writeValue("should_use_deforumation_prompt_scheduling", 0)
                should_use_deforumation_prompt_scheduling = 0
        elif btn == "Add before Deforum prompt.":
            if should_use_before_deforum_prompt == 0:
                should_use_before_deforum_prompt = 1
                self.writeValue("should_use_before_deforum_prompt", 1)
                self.loadCurrentPrompt("P", current_render_frame, 0)
                self.loadCurrentPrompt("N", current_render_frame, 0)

                self.saveCurrentPrompt("P")
                self.saveCurrentPrompt("N")
                # Arrange the possitive prompts according to priority (now for some lazy programing):
                positive_prio = {
                    int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                    int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                    int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                    int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                sortedDict = sorted(positive_prio.items())
                # totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
                totalPossitivePromptString = sortedDict[0][1]
                if sortedDict[1][1] != "":
                    totalPossitivePromptString += "," + sortedDict[1][1]
                if sortedDict[2][1] != "":
                    totalPossitivePromptString += "," + sortedDict[2][1]
                if sortedDict[3][1] != "":
                    totalPossitivePromptString += "," + sortedDict[3][1]

                self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
                self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
                self.writeValue("prompts_touched", 1)
                print("Use before deforum prompt ON")
            else:
                should_use_before_deforum_prompt = 0
                self.writeValue("should_use_before_deforum_prompt", 0)
                print("Use before deforum prompt OFF")
        elif btn == "Add after Deforum prompt.":
            if should_use_after_deforum_prompt == 0:
                should_use_before_deforum_prompt = 1
                self.writeValue("should_use_after_deforum_prompt", 1)
                self.loadCurrentPrompt("P", current_render_frame, 0)
                self.loadCurrentPrompt("N", current_render_frame, 0)

                self.saveCurrentPrompt("P")
                self.saveCurrentPrompt("N")
                # Arrange the possitive prompts according to priority (now for some lazy programing):
                positive_prio = {
                    int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                    int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                    int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                    int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                sortedDict = sorted(positive_prio.items())
                # totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
                totalPossitivePromptString = sortedDict[0][1]
                if sortedDict[1][1] != "":
                    totalPossitivePromptString += "," + sortedDict[1][1]
                if sortedDict[2][1] != "":
                    totalPossitivePromptString += "," + sortedDict[2][1]
                if sortedDict[3][1] != "":
                    totalPossitivePromptString += "," + sortedDict[3][1]

                self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', ''))
                self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', ''))
                self.writeValue("prompts_touched", 1)
                print("Use after deforum prompt ON")
            else:
                should_use_after_deforum_prompt = 0
                self.writeValue("should_use_after_deforum_prompt", 0)
                print("Use after deforum prompt OFF")
        elif event.GetId() == 73:
            if is_Parseq_Active == 0:
                is_Parseq_Active = 1
                urlToSend = str(self.Parseq_URL_input_box.GetValue()).strip()
                if len(urlToSend) > 5:
                    writeValue("parseq_manifest", urlToSend)
                    writeValue("use_parseq", 1)
            else:
                is_Parseq_Active = 0
                writeValue("use_parseq", 0)
        elif btn == "Send Deforum":
            urlToSend = str(self.Parseq_URL_input_box.GetValue()).strip()
            if len(urlToSend) > 5:
                writeValue("parseq_manifest", urlToSend)
        elif btn == "Live Values":
            if showLiveValues == False:
                showLiveValues = True
                self.live_values_thread = threading.Thread(target=self.LiveValues, args=())
                self.live_values_thread.daemon = True
                self.live_values_thread.start()
                self.SetLabel(windowlabel + " -- Live values is now activated.")
            else:
                showLiveValues = False
                self.SetLabel(windowlabel + " -- Live values is now de-activated.")
        elif btn == "Hide Total Recall box":
            if not should_hide_totalrecall_box:
                should_hide_totalrecall_box = True
                self.totalRecallSettingsField.Hide()
                self.totalRecallSettingsLine.Hide()
                self.should_use_total_recall_checkbox.Hide()
                self.should_use_total_recall_checkbox.Hide()
                self.total_recall_from_input_box_text.Hide()
                self.total_recall_from_input_box.Hide()
                self.total_recall_to_input_box_text.Hide()
                self.total_recall_to_input_box.Hide()
                self.should_use_total_recall_prompt_checkbox.Hide()
                self.should_use_total_recall_movement_checkbox.Hide()
                self.should_use_total_recall_others_checkbox.Hide()
                self.should_use_deforumation_start_string_checkbox.Hide()
                self.should_erase_total_recall_memory.Hide()
                self.download_recorded_data.Hide()
                self.upload_recorded_data.Hide()
                self.total_current_recall_frames_text.Hide()
                #self.save_project_as_zip.Hide()
                self.p2.SetPosition((int(screenWidth / 2) + 54, 304-130))
                self.predefined_motion_fps_choice.SetPosition((int(screenWidth / 2) + 13, 280-130))
                self.predefined_motion_range_choice.SetPosition((int(screenWidth / 2) + 160, 280-130))
                self.should_use_total_recall_in_deforumation_checkbox.SetPosition((int(screenWidth / 2) + 20, 200-70))
                self.copy_original_to_manual_button.SetPosition((int(screenWidth / 2) + 250, 200-70))
                self.parseqSettingsField.SetPosition((int(screenWidth / 2) + 14, 420-130))
                self.Parseq_URL_input_box_text.SetPosition((int(screenWidth / 2) + 40, 440-130))
                self.Parseq_activation_Checkbox.SetPosition((int(screenWidth / 2) + 20, 440-130))
                self.Parseq_URL_input_box.SetPosition((int(screenWidth / 2) + 20, 460-130))
                self.Send_URL_to_Deforum.SetPosition((int(screenWidth / 2) + 326, 460-130))
                self.record_button.SetPosition((int(screenWidth / 2) + 10, 334-130))

            else:
                should_hide_totalrecall_box = False
                self.totalRecallSettingsField.Show()
                self.totalRecallSettingsLine.Show()
                self.should_use_total_recall_checkbox.Show()
                self.should_use_total_recall_checkbox.Show()
                self.total_recall_from_input_box_text.Show()
                self.total_recall_from_input_box.Show()
                self.total_recall_to_input_box_text.Show()
                self.total_recall_to_input_box.Show()
                self.should_use_total_recall_in_deforumation_checkbox.Show()
                self.copy_original_to_manual_button.Show()
                self.should_use_total_recall_prompt_checkbox.Show()
                self.should_use_total_recall_movement_checkbox.Show()
                self.should_use_total_recall_others_checkbox.Show()
                self.should_use_deforumation_start_string_checkbox.Show()
                self.should_erase_total_recall_memory.Show()
                self.download_recorded_data.Show()
                self.upload_recorded_data.Show()
                self.total_current_recall_frames_text.Show()
                #self.save_project_as_zip.Show()
                self.p2.SetPosition((int(screenWidth / 2) + 54, 304))
                self.predefined_motion_fps_choice.SetPosition((int(screenWidth / 2) + 13, 280))
                self.predefined_motion_range_choice.SetPosition((int(screenWidth / 2) + 160, 280))
                self.should_use_total_recall_in_deforumation_checkbox.SetPosition((int(screenWidth / 2) + 20, 200))
                self.copy_original_to_manual_button.SetPosition((int(screenWidth / 2) + 250, 200))
                self.parseqSettingsField.SetPosition((int(screenWidth / 2) + 14, 420))
                self.Parseq_URL_input_box_text.SetPosition((int(screenWidth / 2) + 40, 440))
                self.Parseq_activation_Checkbox.SetPosition((int(screenWidth / 2) + 20, 440))
                self.Parseq_URL_input_box.SetPosition((int(screenWidth / 2) + 20, 460))
                self.Send_URL_to_Deforum.SetPosition((int(screenWidth / 2) + 326, 460))
                self.record_button.SetPosition((int(screenWidth / 2) + 10, 334))

        elif btn == "Hide PARSEQ box":
            if not should_hide_parseq_box:
                should_hide_parseq_box = True
                self.parseqSettingsField.Hide()
                self.Parseq_URL_input_box_text.Hide()
                self.Parseq_activation_Checkbox.Hide()
                self.Parseq_URL_input_box.Hide()
                self.Send_URL_to_Deforum.Hide()
            else:
                should_hide_parseq_box = False
                self.parseqSettingsField.Show()
                self.Parseq_URL_input_box_text.Show()
                self.Parseq_activation_Checkbox.Show()
                self.Parseq_URL_input_box.Show()
                self.Send_URL_to_Deforum.Show()

        elif btn == "Turn off tooltips":
            children = self.panel.GetChildren()
            for child in children:
                if hasattr(child, 'ToolTip'):
                    property = getattr(child, 'ToolTip')
                    if property != None:
                        property.Tip=""
                    else:
                        if hasattr(child, 'TextCtrl'):
                            property = getattr(child, 'TextCtrl')
                            property.Tip = ""

        self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
        self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
        if should_use_total_recall_in_deforumation and is_paused_rendering:
            if current_render_frame != -1:
                self.setValuesFromSavedFrame(int(current_render_frame))
        elif should_use_total_recall_in_deforumation and not is_paused_rendering:
                a_frame = int(readValue("start_frame"))
                if a_frame !=-1:
                    self.setValuesFromSavedFrame(int(readValue("start_frame")))
        elif should_use_total_recall and (int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue())) and (int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue())):
            if current_render_frame != -1:
                self.setValuesFromSavedFrame(int(current_render_frame))
        else:
            #else:
            #    self.loadCurrentPrompt("P", current_render_frame, 0)
            #    self.loadCurrentPrompt("N", current_render_frame, 0)

            if armed_pan:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
            else:
                if not showLiveValues:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
            self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
            if armed_rotation:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X_ARMED))
            else:
                if not showLiveValues:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X))
            if armed_zoom:
                self.zoom_value_text.SetLabel(str('%.2f' %Translation_Z_ARMED))
                self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))
            else:
                if not showLiveValues:
                    self.zoom_value_text.SetLabel(str('%.2f' %Translation_Z))
                    self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
                    #self.fov_slider.SetValue(int(FOV_Scale))
            if armed_tilt:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z_ARMED))
            else:
                if not showLiveValues:
                    self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))

            #if not showLiveValues:
            #    self.rotation_Z_Value_Text.SetLabel(str('%.2f' %Rotation_3D_Z))

        #obj.SetToolTip(obj_tooltip)
        self.writeAllValues()
    def StartMediaPlayback(self, mediaPath, backendType):
        Frame = MediaPanel(mediaPath, backendType)
        Frame.Show()

    def LiveValues(self):
        global seedValue
        global frame_has_changed
        global zero_pan_active
        global zero_zoom_active
        global zero_rotate_active
        global zero_tilt_active
        global currently_active_motion
        global Translation_X
        global Translation_Y
        frame_has_changed = True
        recalledFrame = -1
        current_frame_live = int(readValue("start_frame"))
        while showLiveValues:
            manyValues = readValue(["deforum_translation_x", "deforum_translation_y", "deforum_translation_z", "deforum_rotation_x", "deforum_rotation_y", "deforum_rotation_z", "deforum_strength", "deforum_cfg", "deforum_fov", "deforum_steps", "deforum_cadence", "deforum_noise_multiplier", "deforum_perlin_octaves", "deforum_perlin_persistence", "get_number_of_recalled_frames", "deforum_pdmotion_status", "deforum_panmotion_status", "deforum_zoommotion_status", "deforum_rotationmotion_status", "deforum_tiltmotion_status", "start_motion", "start_zero_pan_motion", "start_zero_zoom_motion", "start_zero_rotation_motion", "start_zero_tilt_motion", "deforum_panmotion_x_status","start_zero_pan_motion_x","deforum_panmotion_y_status", "start_zero_pan_motion_y"])

            deforum_translation_x = manyValues[0]
            deforum_translation_y = manyValues[1]
            deforum_translation_z = manyValues[2]
            deforum_rotation_x = manyValues[3]
            deforum_rotation_y = manyValues[4]
            deforum_rotation_z = manyValues[5]
            deforum_strength = manyValues[6]
            deforum_cfg = manyValues[7]
            deforum_fov = manyValues[8]
            deforum_steps = manyValues[9]
            deforum_cadence = manyValues[10]
            deforum_noise_multiplier = manyValues[11]
            deforum_Perlin_Octave_Value = manyValues[12]
            deforum_Perlin_Persistence_Value = manyValues[13]
            number_of_recalled_frames = int(manyValues[14])
            deforum_pdmotion_status = str(manyValues[15])
            deforum_pan_status = str(manyValues[16])
            deforum_zoom_status = str(manyValues[17])
            deforum_rotation_status = str(manyValues[18])
            deforum_tilt_status = str(manyValues[19])
            is_inside_a_motion = int(manyValues[20])
            start_zero_pan_motion = int(manyValues[21])
            start_zero_zoom_motion = int(manyValues[22])
            start_zero_rotation_motion = int(manyValues[23])
            start_zero_tilt_motion = int(manyValues[24])
            deforum_pan_x_status = str(manyValues[25])
            start_zero_pan_x_motion = int(manyValues[26])
            deforum_pan_y_status = str(manyValues[27])
            start_zero_pan_y_motion = int(manyValues[28])
            if start_zero_pan_motion == -1:
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.transform_zero_button.SetBitmap(bmp)
                zero_pan_active = False
                self.writeValue("start_zero_pan_motion", 0)
                self.zero_pan_current_settings_Text.SetLabel("<\"0-P: None\">")
            if start_zero_zoom_motion == -1:
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.zoom_zero_button.SetBitmap(bmp)
                zero_zoom_active = False
                self.writeValue("start_zero_zoom_motion", 0)
                self.zero_zoom_current_settings_Text.SetLabel("<\"0-Z: None\">")
            if start_zero_rotation_motion == -1:
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.rotate_zero_button.SetBitmap(bmp)
                zero_rotate_active = False
                self.writeValue("start_zero_rotation_motion", 0)
                self.zero_rotate_current_settings_Text.SetLabel("<\"0-R: None\">")
            if start_zero_tilt_motion == -1:
                bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
                bmp = scale_bitmap(bmp, 22, 22)
                self.tilt_zero_button.SetBitmap(bmp)
                zero_tilt_active = False
                self.writeValue("start_zero_tilt_motion", 0)
                self.zero_tilt_current_settings_Text.SetLabel("<\"0-T: None\">")
            if start_zero_pan_x_motion == -1:
                self.writeValue("start_zero_pan_motion_x", 0)
                self.deforum_zero_pan_x_value_info_text.SetLabel("0-Pan_X: None")
                for isk in range(0,10):
                    wx.CallAfter(self.setTextColor, self.pan_X_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_X_SIRUP)))
                Translation_X = Translation_X_SIRUP
                self.pan_X_Value_Text.SetLabel(str('%.2f' % float(Translation_X)))
            if start_zero_pan_y_motion == -1:
                self.writeValue("start_zero_pan_motion_y", 0)
                self.deforum_zero_pan_y_value_info_text.SetLabel("0-Pan_Y: None")
                for isk in range(0,10):
                    wx.CallAfter(self.setTextColor, self.pan_Y_Sirup_Value_Text, (0, 0, 0), str('%.2f' % float(Translation_Y_SIRUP)))
                Translation_Y = Translation_Y_SIRUP
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(Translation_Y)))

            self.total_current_recall_frames_text.SetLabel("Number of recall points: " + str(number_of_recalled_frames))
            if int(readValue("deforum_interrupted")):
                self.writeValue("deforum_interrupted", 0)
                seedValue = int(self.seed_input_box.GetValue())
                self.writeValue("seed", seedValue)
                print("Deforum was interrupted, restoring seed:"+str(seedValue))
            if is_inside_a_motion or should_use_total_recall_in_deforumation or (should_use_total_recall and (int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue())) and (int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue()))):
                if frame_has_changed:
                    current_frame_live = int(self.frame_step_input_box.GetValue())#int(readValue("start_frame"))
                    frame_has_changed = False
                if not is_paused_rendering:
                    a_frame = int(readValue("start_frame"))
                    if a_frame != -1:
                        current_frame_live = int(readValue("start_frame"))

                if int(current_frame_live) != -1:
                    if recalledFrame != current_frame_live:
                        wx.CallAfter(self.setValuesFromSavedFrame, current_frame_live)
                        recalledFrame = current_frame_live

                # Bottom Info Text
                self.deforum_strength_value_info_text.SetLabel("Strength:" + str('%.2f' % float(deforum_strength)))
                self.deforum_steps_value_info_text.SetLabel("Steps:" + str(deforum_steps))
                self.deforum_cfg_value_info_text.SetLabel("CFG:" + str(deforum_cfg))
                self.deforum_cadence_value_info_text.SetLabel("Cadence:" + str(deforum_cadence))
                self.deforum_pdmotion_value_info_text.SetLabel(str(deforum_pdmotion_status))
                self.deforum_trx_value_info_text.SetLabel("Tr X:" + str('%.2f' % float(deforum_translation_x)))
                self.deforum_try_value_info_text.SetLabel("Tr Y:" + str('%.2f' % float(deforum_translation_y)))
                self.deforum_trz_value_info_text.SetLabel("Tr Z:" + str('%.2f' % float(deforum_translation_z)))
                self.deforum_rox_value_info_text.SetLabel("Ro X:" + str('%.2f' % float(deforum_rotation_x)))
                self.deforum_roy_value_info_text.SetLabel("Ro Y:" + str('%.2f' % float(deforum_rotation_y)))
                self.deforum_roz_value_info_text.SetLabel("Ro Z:" + str('%.2f' % float(deforum_rotation_z)))
                self.deforum_zero_pan_value_info_text.SetLabel(str(deforum_pan_status))
                self.deforum_zero_zoom_value_info_text.SetLabel(str(deforum_zoom_status))
                self.deforum_zero_rotation_value_info_text.SetLabel(str(deforum_rotation_status))
                self.deforum_zero_tilt_value_info_text.SetLabel(str(deforum_tilt_status))
                self.deforum_zero_pan_x_value_info_text.SetLabel(str(deforum_pan_x_status))
                self.deforum_zero_pan_y_value_info_text.SetLabel(str(deforum_pan_y_status))

                time.sleep(0.25)
                continue
            if not is_inside_a_motion and not is_static_motion and currently_active_motion != -1:
                if (currently_active_motion <= (len(self.ctrl)-1)):
                    wx.CallAfter(self.startMotion, currently_active_motion)
                currently_active_motion = -1

            if armed_pan:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
            elif should_use_deforumation_panning:# and not is_paused_rendering:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            #else:
            #    self.pan_X_Value_Text.SetLabel(str('%.2f' % float(deforum_translation_x)))
            #    self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(deforum_translation_y)))
            self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
            self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))

            if armed_zoom:
                self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))
                self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z_ARMED)))
                self.fov_slider.SetValue(int(FOV_Scale))
            elif should_use_deforumation_zoomfov:# and not is_paused_rendering:
                self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
                self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z)))
                self.fov_slider.SetValue(int(FOV_Scale))
            #else:
            #    self.zoom_slider.SetValue(int(float(deforum_translation_z)*100))
            #    self.zoom_value_text.SetLabel(str('%.2f' % float(deforum_translation_z)))
            #    self.fov_slider.SetValue(int(float(deforum_fov)))

            if armed_rotation:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X_ARMED))
            elif should_use_deforumation_rotation:# and not is_paused_rendering:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
            #else:
            #    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_y)))
            #    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_x)))

            if armed_tilt:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Z_ARMED)))
            elif should_use_deforumation_tilt:# and not is_paused_rendering:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Z)))
            #else:
            #    self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_z)))

            if should_use_deforumation_noise:# and not is_paused_rendering:
                self.noise_slider.SetValue(int(float(noise_multiplier)*100))
                self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
                self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value)*100))
            #else:
            #    self.noise_slider.SetValue(int(float(deforum_noise_multiplier)*100))
            #    self.perlin_octave_slider.SetValue(int(deforum_Perlin_Octave_Value))
            #    self.perlin_persistence_slider.SetValue(int(float(deforum_Perlin_Persistence_Value)*100))




            if should_use_deforumation_strength:# and not is_paused_rendering:
                self.strength_schedule_slider.SetValue(int(float(Strength_Scheduler) * 100))
            #else:
            #    self.strength_schedule_slider.SetValue(int(float(deforum_strength)*100))

            if should_use_deforumation_cfg:# and not is_paused_rendering:
                self.cfg_schedule_slider.SetValue(int(CFG_Scale))
            #else:
            #    self.cfg_schedule_slider.SetValue(int(deforum_cfg))

            if should_use_deforumation_cadence:# and not is_paused_rendering:
                self.cadence_slider.SetValue(int(Cadence_Schedule))
            #else:
            #    self.cadence_slider.SetValue(int(deforum_cadence))

            #Bottom Info Text
            self.deforum_strength_value_info_text.SetLabel("Strength:" + str('%.2f' % float(deforum_strength)))
            self.deforum_steps_value_info_text.SetLabel("Steps:" + str(deforum_steps))
            self.deforum_cfg_value_info_text.SetLabel("CFG:" + str(deforum_cfg))
            self.deforum_cadence_value_info_text.SetLabel("Cadence:" + str(deforum_cadence))
            self.deforum_pdmotion_value_info_text.SetLabel(str(deforum_pdmotion_status))
            self.deforum_trx_value_info_text.SetLabel("Tr X:" + str('%.2f' % float(deforum_translation_x)))
            self.deforum_try_value_info_text.SetLabel("Tr Y:" + str('%.2f' % float(deforum_translation_y)))
            self.deforum_trz_value_info_text.SetLabel("Tr Z:" + str('%.2f' % float(deforum_translation_z)))
            self.deforum_rox_value_info_text.SetLabel("Ro X:" + str('%.2f' % float(deforum_rotation_x)))
            self.deforum_roy_value_info_text.SetLabel("Ro Y:" + str('%.2f' % float(deforum_rotation_y)))
            self.deforum_roz_value_info_text.SetLabel("Ro Z:" + str('%.2f' % float(deforum_rotation_z)))
            self.deforum_zero_pan_value_info_text.SetLabel(str(deforum_pan_status))
            self.deforum_zero_zoom_value_info_text.SetLabel(str(deforum_zoom_status))
            self.deforum_zero_rotation_value_info_text.SetLabel(str(deforum_rotation_status))
            self.deforum_zero_tilt_value_info_text.SetLabel(str(deforum_tilt_status))
            self.deforum_zero_pan_x_value_info_text.SetLabel(str(deforum_pan_x_status))
            self.deforum_zero_pan_y_value_info_text.SetLabel(str(deforum_pan_y_status))
            time.sleep(0.25)

        total_recall_movements_inside_range_and_active = False
        total_recall_others_inside_range_and_active = False
        total_recall_prompt_inside_range_and_active = False
        if (should_use_total_recall and int(current_render_frame) >= int(self.total_recall_from_input_box.GetValue()) and int(current_render_frame) <= int(self.total_recall_to_input_box.GetValue())):
            if should_use_total_recall_movements:
                total_recall_movements_inside_range_and_active = True
            if should_use_total_recall_others:
                total_recall_others_inside_range_and_active = True
            if should_use_total_recall_prompt:
                total_recall_prompt_inside_range_and_active = True

        if not should_use_total_recall and not should_use_total_recall_in_deforumation:
            self.setAllComponentValues()
        else:
            if not should_use_total_recall_in_deforumation:
                if should_use_total_recall and not total_recall_movements_inside_range_and_active:
                    if armed_pan:
                        self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
                    else:
                        self.pan_X_Value_Text.SetLabel(str('%.2f' % (Translation_X)))
                        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                    self.pan_X_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_X_SIRUP)))
                    self.pan_Y_Sirup_Value_Text.SetLabel(str('%.2f' % (Translation_Y_SIRUP)))
                    if armed_rotation:
                        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X_ARMED))
                    else:
                        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))

                    if armed_tilt:
                        self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z_ARMED))
                    else:
                        self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))

                    if armed_zoom:
                        self.zoom_slider.SetValue(int(float(Translation_Z_ARMED) * 100))
                        self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z_ARMED)))
                    else:
                        self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
                        self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z)))

                    self.fov_slider.SetValue(int(FOV_Scale))

                if should_use_total_recall and not total_recall_others_inside_range_and_active:
                    self.cfg_schedule_slider.SetValue(int(CFG_Scale))
                    self.strength_schedule_slider.SetValue(int(float(Strength_Scheduler)*100))
                    self.cadence_slider.SetValue(int(Cadence_Schedule))

        print("Ending Live Values Thread....")
    def OnExit(self, event):
        if self.framer != None:
            self.framer.Hide()
            self.framer.Close()
            self.framer = None
        print("CLOSING!")
        wx.Exit()

    def setXYRotation(self, event):
        global Rotation_3D_X
        global Rotation_3D_Y
        global Rotation_3D_Y_ARMED
        global Rotation_3D_X_ARMED

        pos = event.GetPosition()
        clicked_bitmap = event.GetEventObject()

        # Get the underlying image of the clicked bitmap
        image = clicked_bitmap.GetBitmap().ConvertToImage()

        # Get the image size
        image_width = image.GetWidth()
        image_height = image.GetHeight()

        print("x:", pos.x, " y:", pos.y, " width:", image_width, " height:", image_height)
        # Normalize the click position to a range of -7 to 7 on both axes
        #Old calculation below
        #normalized_x = (pos.x / image_width) * 14 - 7
        #normalized_y = (pos.y / image_height) * 14 - 7
        # New calculation reflects the zoom granularity
        zoom_granularity_value = float(self.zoom_step_input_box.GetValue())
        normalized_x = ((pos.x / image_width) * zoom_granularity_value*2) - zoom_granularity_value
        normalized_y = ((pos.y / image_height) * zoom_granularity_value*2) - zoom_granularity_value

        # Print the normalized click position
        print("Normalized Click Position:", normalized_x, normalized_y)
        Rotation_3D_Y_ARMED = 0.0
        Rotation_3D_X_ARMED = 0.0
        Rotation_3D_Y = normalized_x
        Rotation_3D_X = -normalized_y

        print("Normalized Click Position:", Rotation_3D_Y_ARMED, Rotation_3D_X_ARMED, Rotation_3D_Y, Rotation_3D_X)

    def on_mouse_right_down(self, event):
        self.setXYRotation(event)

        event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
        event.SetEventObject(self.rotate_zero_button)
        event.SetId(self.rotate_zero_button.GetId())
        self.rotate_zero_button.GetEventHandler().ProcessEvent(event)

    def on_mouse_left_down(self, event):
        self.bitmap.SetToolTip("")
        self.start_pos = event.GetPosition()
        print("Nerknapp")

    def on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self.start_pos:
            self.current_pos = event.GetPosition()
            self.rectangle = self.calculate_rectangle()
            self.Refresh()  # Redraw the bitmap with the rectangle

    def calculate_midpoint(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2

        midpoint_x = (x1 + x2) / 2
        midpoint_y = (y1 + y2) / 2

        midpoint = (midpoint_x, midpoint_y)

        return midpoint
    def on_mouse_left_up(self, event):
        if self.start_pos and self.current_pos:
            # Print rectangle position and size
            print("Rectangle Position:", self.rectangle.GetPosition())
            print("Rectangle Size:", self.rectangle.GetSize())
            # normalise
            image_size = self.bitmap.GetSize()
            rectangle_width = self.rectangle.GetSize()[0]
            rectangle_height = self.rectangle.GetSize()[1]
            if rectangle_width == 0 or rectangle_height == 0:
                return
            #Below, is OLD zoom_factor
            #zoom_factor = min(image_size[0] / rectangle_width, image_size[1] / rectangle_height)*3
            #Here is the new calculated zoom_factor
            zoom_granularity_value = float(self.zoom_step_input_box.GetValue())
            if rectangle_width <= rectangle_height:
                zoom_delta = zoom_granularity_value / (image_size[0] / rectangle_width)
                zoom_factor = zoom_granularity_value - zoom_delta
            else:
                zoom_delta = zoom_granularity_value / (image_size[1] / rectangle_height)
                zoom_factor = zoom_granularity_value - zoom_delta

            print("zoom_factor:", zoom_factor)
            self.Translation_Z_ARMED = 0.0
            self.Translation_Z = zoom_factor
            print("Translation_Z:" + str(self.Translation_Z))

            # fire slider event
            evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
            evt.SetEventObject(self.zoom_slider)
            evt.SetId(self.zoom_slider.GetId())
            self.zoom_slider.SetValue(int(self.Translation_Z * 100))
            self.zoom_slider.GetEventHandler().ProcessEvent(evt)

            # fire zero zoom button pressed
            event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId)
            event.SetEventObject(self.zoom_zero_button)
            event.SetId(self.zoom_zero_button.GetId())
            self.zoom_zero_button.GetEventHandler().ProcessEvent(event)

            # fire right mouse button on image
            midpoint = self.calculate_midpoint(self.start_pos, self.current_pos)
            print("midpoint", midpoint)
            # event = wx.PyCommandEvent(wx.EVT_RIGHT_DOWN.typeId)
            # event.SetEventObject(self.bitmap)
            # event.SetId(self.bitmap.GetId())
            # event.SetPosition(midpoint)
            # self.bitmap.GetEventHandler().ProcessEvent(event)

            event = wx.MouseEvent(wx.EVT_RIGHT_DOWN.typeId)
            event.SetEventObject(self.bitmap)
            event.SetId(self.bitmap.GetId())
            point = wx.Point(int(midpoint[0]), int(midpoint[1]))
            event.SetPosition(point)
            self.bitmap.ProcessEvent(event)

            self.start_pos = None
            self.current_pos = None
            self.Refresh()  # Redraw the bitmap without the rectangle
            self.bitmap.SetToolTip("This is a preview window, that will only update to the current image through using the \"Show current frame\"-button, or by using the controls for rewinding or forwarding.")

    def calculate_rectangle(self):
        x = min(self.start_pos.x, self.current_pos.x)
        y = min(self.start_pos.y, self.current_pos.y)
        width = abs(self.current_pos.x - self.start_pos.x)
        height = abs(self.current_pos.y - self.start_pos.y)

        return wx.Rect(x, y, width, height)

    def on_paint(self, event):
        try:
            if self.bitmap != None:
                dc = wx.BufferedPaintDC(self.bitmap)
                dc.Clear()
                dc.DrawBitmap(self.bitmap.GetBitmap(), 0, 0)

                if self.start_pos and self.current_pos:
                    self.draw_rectangle(dc)
            else:
                pass
        except Exception as e:
            print("Doing a non gracefull exit ;( ... (But who cares... culprit is \"on_paint(self, event)\")")

    def draw_rectangle(self, dc):
        pen = wx.Pen(wx.Colour(255, 0, 0), width=2)
        dc.SetPen(pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(self.rectangle)

class MediaPanel(wx.Frame):
    def __init__(self, videoPath, BACKEND):
        wx.Frame.__init__(self,None, size=(100,100))
        self.testMedia = wx.media.MediaCtrl(self, style=wx.SIMPLE_BORDER, szBackend=BACKEND)
        self.media = videoPath
        self.testMedia.Bind(wx.media.EVT_MEDIA_LOADED, self.play)
        self.testMedia.Bind(wx.media.EVT_MEDIA_FINISHED, self.quit)
        if self.testMedia.Load(self.media):
            pass
        else:
            print("Media not found")
            self.quit(None)

    def play(self, event):
        mediaSize = self.testMedia.GetBestSize()
        self.SetSize(mediaSize)
        self.testMedia.Play()

    def quit(self, event):
        self.Destroy()


def ffmpeg_stitch_video(self, ffmpeg_location=None, fps=None, outmp4_path=None, stitch_from_frame=0, stitch_to_frame=None, imgs_path=None, audio_path=None):
    crf = 20
    #start_time = time.time()
    print(f"Got a request to stitch frames to video using FFmpeg.\nFrames:\n{imgs_path}\nTo Video:\n{outmp4_path}")
    msg_to_print = f"Stitching *video*..."
    print("Stitching *video*...")
    if stitch_to_frame == -1:
        stitch_to_frame = 999999999
    if os.path.isfile(outmp4_path):
        print("removing temp video")
        os.remove(outmp4_path)
    try:
        cmd = [
            ffmpeg_location,
            '-start_number', str(stitch_from_frame),
            #'-framerate', str(float(fps)),
            #'-thread_queue_size 4096',
            '-r', str(float(fps)),
            '-i', imgs_path,
            '-frames:v', str(stitch_to_frame),
            '-pix_fmt', 'yuv420p',
            '-crf', str(crf),
            '-pattern_type', 'sequence'
        ]
        cmd.append(outmp4_path)
        # ffmpeg -y -r 30 -start_number 0 -i H:\stable-diffusion-webui\outputs/img2img-images\Deforum_20230705125910\20230705125910_%09d.png -frames:v 800 -c:v libx264 -vf fps=25 -pix_fmt yuv420p -crf 17 -preset veryslow -pattern_type sequence -vcodec png E:\Tools\Python_Scripts\deforum_remote\out.mp4
        # ffmpeg -y -start_number 0 -framerate 25 -r 25 -i H:\stable-diffusion-webui\outputs/img2img-images\Deforum_20230705125910\20230705125910_%09d.png -frames:v 200 -pix_fmt yuv420p -profile:v high -level:v 4.1 -crf:v 20 -movflags +faststart E:\Tools\Python_Scripts\deforum_remote\out.mp4
        # ffmpeg -y -i E:\Tools\Python_Scripts\deforum_remote\out.mp4 -ss 40 -i H:\Deforumation_Competition\snapshot2.wav -map 0:v -map 1:a -c:v copy -shortest E:\Tools\Python_Scripts\deforum_remote\out2.mp4

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        #subprocess.run(cmd)
        stdout, stderr = process.communicate()
    except FileNotFoundError:
        print("\r" + " " * len(msg_to_print), end="", flush=True)
        print(f"\r{msg_to_print}", flush=True)
        raise FileNotFoundError(
            "FFmpeg not found. Please make sure you have a working ffmpeg path under 'ffmpeg_location' parameter.")
    except Exception as e:
        print("\r" + " " * len(msg_to_print), end="", flush=True)
        print(f"\r{msg_to_print}", flush=True)
        raise Exception(f'Error stitching frames to video. Actual runtime error:{e}')
    print("Done Stitching *video*...")

    if os.path.isfile(outmp4_path+'.temp.mp4'):
        os.remove(outmp4_path+'.temp.mp4')
    if audio_path != 'None' and audio_path != "":
        audioDelay = float(stitch_from_frame/25)
        try:
            cmd = [
                ffmpeg_location,
                '-i',
                outmp4_path,
                '-ss', str(audioDelay),
                '-i',
                audio_path,
                '-map', '0:v',
                '-map', '1:a',
                '-c:v', 'copy',
                '-shortest',
                outmp4_path+'.temp.mp4'
            ]
            print("Stitching *audio*...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            #subprocess.run(cmd)
            print("Done stitching *audio*...")
            if process.returncode != 0:
                raise RuntimeError(stderr)
            os.replace(outmp4_path+'.temp.mp4', outmp4_path)
        except Exception as e:
            add_soundtrack_status = f"\rError adding audio to video: {e}"
            add_soundtrack_success = False
    wx.CallAfter(self.StartMediaPlayback, outmp4_path, self.backend_chooser_choice.GetString(self.backend_chooser_choice.GetSelection()))
    #self.StartMediaPlayback(outmp4_path, self.backend_chooser_choice.GetString(self.backend_chooser_choice.GetSelection()))
    #Frame = MediaPanel("E:\\Tools\\Python_Scripts\\deforum_remote\\out.mp4", "wxWMP10MediaBackend")
    #Frame.Show()
    #Frame = MediaPanel("E:\\Tools\\Python_Scripts\\deforum_remote\\out.mp4", self.backend_chooser_choice.GetString(self.backend_chooser_choice.GetSelection()))
    #Frame.Show()

class ParameterContainer():
    # Run/Steps
    steps = 25
    # Keyframes/Strength
    strength_value = 0.65
    # Keyframes/CFG
    cfg_scale = 6
    # Keyframes/3D/Motion
    rotation_x = 0.0
    rotation_y = 0.0
    rotation_z = 0.0
    translation_x = 0.0
    translation_y = 0.0
    translation_z = 0.0
    Prompt_Positive = "EMPTY"
    Prompt_Negative = "EMPTY"
    frame_outdir = ""
    resume_timestring = ""
    seed_value = -1
    did_seed_change = 0
    # Keyframes/Field Of View/FOV schedule
    fov = 70.0
    cadence = 2
    should_use_optical_flow = 1
    cadence_flow_factor = 1
    generation_flow_factor = 1
    cn_weight = []
    cn_stepstart = []
    cn_stepend = []
    cn_lowt = []
    cn_hight = []
    cn_udcn = []
    for i in range(5):
        cn_weight.append(1.0)
        cn_stepstart.append(0.0)
        cn_stepend.append(1.0)
        cn_lowt.append(0)
        cn_hight.append(255)
        cn_udcn.append(0)
    parseq_keys = 0
    use_parseq = 0
    parseq_manifest = ""
    parseq_strength = 0
    parseq_movements = 0
    parseq_prompt = 0

    noise_multiplier = 1.05
    perlin_octaves = 4
    perlin_persistence = 0.5

class Package:
    def __init__(self):
        self.files = []

if __name__ == '__main__':
    print("Special thank you to our patreons:")
    print("----------------------------------")
    print("eku Zhombi, spenza kwsx, Davy Smith, Anup prabhakar, Baptiste Perrin,\nvirusvjvisuals, make shimis, James, Jags, Wrenn Bunker-Koesters,\nesfera, cheng bei, Nenad Kuzmanovic, le000dv, Justin Weiss, Sergiy Dovgal, Pistons&Volts, IST")
    print("--------\n")
    print("Special thank you to our contributers:")
    print("--------------------------------------")
    print("Itzevil - for testing and giving superb feed-back")
    print("@nhoj - for rectangular zoom")
    print("--------\n")

    if len(sys.argv) < 2:
        print("Starting Deforumation with WebSocket communication")
        shouldUseNamedPipes = False
    else:
        print("Starting Deforumation with Named Pipes communication")
        shouldUseNamedPipes = True
    app = wx.App()


    if len(sys.argv) < 2:
        windowlabel = 'Deforumation_v2 @ Rakile & Lainol, 2023 (version 0.7.6 using WebSockets)'
        Mywin(None, windowlabel)
    else:
        windowlabel = 'Deforumation_v2 @ Rakile & Lainol, 2023 (version 0.7.6 using named pipes)'
        Mywin(None, windowlabel)
    app.MainLoop()
