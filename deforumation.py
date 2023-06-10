import wx
import asyncio
import websockets
import os
import time
import random
import keyboard
import pickle
from threading import *
from pathlib import Path
import json
import wx.lib.newevent
import threading
import requests
import collections
#import pyeaze

#import subprocess
cadenceArray = {}
deforumationSettingsPath="./deforumation_settings.txt"
deforumationSettingsPath_Keys = "./deforum_settings_keys.txt"
deforumationPromptsPath ="./prompts/"
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
#ControlNet
CN_Weight = 1.0
CN_StepStart = 0.0
CN_StepEnd = 1.0
CN_LowT = 0
CN_HighT = 255
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
stepit_pan = 0
stepit_rotate = 0
isReplaying = 0
replayFrom = 0
replayTo = 0
replayFPS = 30
armed_rotation = False
armed_pan = False
#pstb = False
#pmob = False
is_Parseq_Active = False
showLiveValues = False
pan_step_input_box_value = "1.0"
rotate_step_input_box_value = "1.0"
tilt_step_input_box_value = "1.0"
zero_pan_step_input_box_value = "0"
zero_rotate_step_input_box_value = "0"

async def sendAsync(value):
    async with websockets.connect("ws://localhost:8765") as websocket:
        #await websocket.send(pickle.dumps(value))
        try:
            await asyncio.wait_for(websocket.send(pickle.dumps(value)), timeout=10.0)
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        except TimeoutError:
            print('timeout!')
        if message == None:
            message = "-NO CONNECTION-"

        #asyncio.ensure_future(message=websocket.recv())
        #print(str(message))
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
            print("Deforumation Mediator Error:" + str(e))
            print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(5)

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
            print("Deforumation Mediator Error:" + str(e))
            print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)")
            time.sleep(5)

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
                                print("Thread destroyed")
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
    print("Thread destroyed")
class MyPanel(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self,parent,id=-1)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.parent = parent
        self.shouldRun = True
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.bitmap = None
        self.t = threading.Thread(target=changeBitmapWorker, args=(self,))
        self.t.daemon = True
        self.t.start()
    def OnExit(self, event):
        self.shouldRun = False
    def OnPaint(self, evt):
        if self.bitmap != None:
            dc = wx.BufferedPaintDC(self)
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0,0)
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
        #panel = wx.Panel(self)
        self.panel = MyPanel(self)
        self.panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.panel.SetDoubleBuffered(True)
        self.bitmap = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
    def OnResize(self, evt):
        self.current_width, self.current_height = self.GetSize()
        self.panel.resize(self.current_width, self.current_height)
        #print("width=" + str(self.current_width))
        #print("height=" + str(self.current_height))
    def OnErase(self, evt):
        evt.Skip()
    def DrawImage(self):
        self.current_width, self.current_height = self.GetSize()
        self.panel.resize(self.current_width, self.current_height)
        #print("width=" + str(self.current_width))
        #print("height=" + str(self.current_height))
    def OnExit(self, event):
        global should_render_live
        global render_frame_window_is_open
        self.panel.DeInitialize()
        self.panel.Hide()
        self.panel.Close()
        self.panel.Destroy()
        self.panel = None
        self.parent.framer = None
        self.parent.live_render_checkbox.SetValue(0)
        print("Cloing render window!")
        self.Destroy()
        render_frame_window_is_open = False
        should_render_live = False
        if self.bitmap != None:
            self.bitmap.Destroy()
            self.bitmap = None
        should_render_live = False
        #print("CLOSING, framer.bitmap is:"+ str(self.bitmap))


class Mywin(wx.Frame):
    def __init__(self, parent, title):
        #global pmob
        #global pstb
        global ppb
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

        #Positive Prompt
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0, 0))
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer7 = wx.BoxSizer(wx.VERTICAL)
        self.positivePromtText = wx.StaticText(self.panel, label="Positive prompt:", size=(200, 25))
        font = self.positivePromtText.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.positivePromtText.SetFont(font)
        sizer.Add(self.positivePromtText, 0, wx.ALL , 0)

        self.positive_prompt_input_ctrl_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer2.Add(self.positive_prompt_input_ctrl_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_prio.SetValue("1")
        self.positive_prompt_input_ctrl_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box = wx.CheckBox(self.panel, id=101, label="Hide")
        self.positive_prompt_input_ctrl_hide_box.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer2.Add(self.positive_prompt_input_ctrl_hide_box, 0, wx.ALL, 0)
        sizer.Add(sizer2, 0, wx.ALL, 0)


        self.positive_prompt_input_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,100))
        self.positive_prompt_input_ctrl.SetToolTip("This is the main positive prompt window. When \"Save Prompts\" is pushed, this prompt will belong to the current image frame.")
        sizer.Add(self.positive_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_2_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer3.Add(self.positive_prompt_input_ctrl_2_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_2_prio.SetValue("2")
        self.positive_prompt_input_ctrl_2_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_2 = wx.CheckBox(self.panel, id=102, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_2.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_2.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer3.Add(self.positive_prompt_input_ctrl_hide_box_2, 0, wx.ALL, 0)
        sizer.Add(sizer3, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_2 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        self.positive_prompt_input_ctrl_2.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_2, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_3_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer4.Add(self.positive_prompt_input_ctrl_3_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_3_prio.SetValue("3")
        self.positive_prompt_input_ctrl_3_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_3 = wx.CheckBox(self.panel, id=103, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_3.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_3.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer4.Add(self.positive_prompt_input_ctrl_hide_box_3, 0, wx.ALL, 0)
        sizer.Add(sizer4, 0, wx.ALL, 0)


        self.positive_prompt_input_ctrl_3 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        self.positive_prompt_input_ctrl_3.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_3, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_4_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer5.Add(self.positive_prompt_input_ctrl_4_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_4_prio.SetValue("4")
        self.positive_prompt_input_ctrl_4_prio.SetToolTip("The value decides how Deforumation will send the collected positive prompts to Deforum (Lowest will be added first, and highest last).")

        self.positive_prompt_input_ctrl_hide_box_4 = wx.CheckBox(self.panel, id=104, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_4.SetToolTip("Minimize or maximize this prompt window.")
        self.positive_prompt_input_ctrl_hide_box_4.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer5.Add(self.positive_prompt_input_ctrl_hide_box_4, 0, wx.ALL, 0)
        sizer.Add(sizer5, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_4 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        self.positive_prompt_input_ctrl_4.SetToolTip("This is a secondary positive prompt window. When \"Save Prompts\" is pushed, it will be part of the combined positive prompts. It doesn't belong to a certain frame.")
        sizer.Add(self.positive_prompt_input_ctrl_4, 0, wx.ALL | wx.EXPAND, 0)

        #Should use Deforum prompt scheduling?
        #self.shouldUseDeforumPromptScheduling_text = wx.StaticText(self.panel, label="Use Deforumation prompt scheduling...", pos=(trbX+580, 10))
        self.shouldUseDeforumPromptScheduling_Checkbox = wx.CheckBox(self.panel, label="Use Deforumation prompt scheduling", pos=(trbX+600, 10))
        self.shouldUseDeforumPromptScheduling_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #Stay On Top
        self.stayOnTop_Checkbox = wx.CheckBox(self.panel, label="Stay on top", pos=(trbX+1130, 10))
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


        self.negative_prompt_input_ctrl = wx.TextCtrl(self.panel,style=wx.TE_MULTILINE, size=(-1,100))
        self.negative_prompt_input_ctrl.SetToolTip("This is the negative prompt window. When \"Save Prompts\" is pushed, this prompt will belong to the current image frame.")
        sizer.Add(self.negative_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 0)
        #if os.path.isfile(deforumationSettingsPath):
        #    self.negative_prompt_input_ctrl.SetValue(promptfileRead.readline())
        #    promptfileRead.close()

        self.panel.SetSizer(sizer)
        #SHOW LIVE RENDER CHECK-BOX
        self.live_render_checkbox = wx.CheckBox(self.panel, label="LIVE RENDER", pos=(trbX+1130-340, tbrY-110))
        self.live_render_checkbox.SetToolTip("Shows another window, that displays the current frame that is being generated, or if in paused mode, the frame choosen with the \"frame picker input box\".")
        self.live_render_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

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
        self.replay_button.SetToolTip("This will replay the range given in the input boxes to the left. The replay will take place in the Live Render window.")
        self.replay_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.replay_button.SetLabel("REPLAY")
        #REPLAY FPS BOX
        self.fps_input_box_text = wx.StaticText(self.panel, label="fps", pos=(trbX+1180, tbrY-130))
        self.replay_fps_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1200, tbrY-131))
        self.replay_fps_input_box.SetToolTip("When doing a replay, this is the fps that should be used to replay the images. How ever, because the replay is done through converting .PNG files to bitmaps (takes a long time), the speed will not be accurate.")
        self.replay_fps_input_box.SetValue("30")

        #SAVE PROMPTS BUTTON
        self.update_prompts = wx.Button(self.panel, label="SAVE PROMPTS")
        self.update_prompts.SetToolTip("When pushing this, the current Positive Prompt, and the current Negative Prompt will be saved on the currently set frame. While generating, the current frame will be increasing, and your prompts will be saved along with it.")
        sizer.Add(self.update_prompts, 0, wx.ALL | wx.EXPAND, 5)
        self.update_prompts.Bind(wx.EVT_BUTTON, self.OnClicked)

        #ARM PAN VALUE BUTTON
        bmp = wx.Bitmap("./images/arm_off.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 10, 10)
        self.arm_pan_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX-15, tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.arm_pan_button.SetToolTip("When activated, you enter arming mode for panning. In arming mode, these panning values are separate from the actual panning values. These values are the end point when doing a transitioning of the current panning values. Such a transition is started by pushing the \"0\"-button.")
        self.arm_pan_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.arm_pan_button.SetLabel("ARM_PAN")

        #PAN STEPS INPUT
        self.pan_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX-15, 30+tbrY))
        self.pan_step_input_box.SetToolTip("Sets the granularity of how much the panning value should change, when using the panning buttons.")
        self.pan_step_input_box.SetLabel("1.0")

        #LEFT PAN BUTTTON
        bmp = wx.Bitmap("./images/left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(5+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_left_button.SetToolTip("Decreases the X-axel panning value.")
        self.transform_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_left_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_x_left_button.SetLabel("PAN_LEFT")

        #SET PAN VALUE X
        self.pan_X_Value_Text = wx.StaticText(self.panel, label=str(Translation_X), pos=(trbX-26, 55+tbrY+5))
        self.pan_X_Value_Text.SetToolTip("Current X-panning value.")
        font = self.pan_X_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_X_Value_Text.SetFont(font)

        #SET PAN VALUE Y
        self.pan_Y_Value_Text = wx.StaticText(self.panel, label=str(Translation_Y), pos=(40+trbX, 5+tbrY))
        self.pan_Y_Value_Text.SetToolTip("Current Y-panning value.")
        font = self.pan_Y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_Y_Value_Text.SetFont(font)

        #UPP PAN BUTTTON
        bmp = wx.Bitmap("./images/upp_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_upp_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 25+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_upp_button.SetToolTip("Increases the Y-axel panning value.")
        self.transform_y_upp_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_upp_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_y_upp_button.SetLabel("PAN_UP")

        #RIGHT PAN BUTTTON
        bmp = wx.Bitmap("./images/right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(65+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_right_button.SetToolTip("Increases the X-axel panning value.")
        self.transform_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_right_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_x_right_button.SetLabel("PAN_RIGHT")
        #DOWN PAN BUTTTON
        bmp = wx.Bitmap("./images/down_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 85+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_down_button.SetToolTip("Decreases the Y-axel panning value.")
        self.transform_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_down_button.Bind(wx.EVT_RIGHT_UP, self.OnClicked)
        self.transform_y_down_button.SetLabel("PAN_DOWN")

        #ZERO PAN BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 22, 22)
        self.transform_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 56+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_zero_button.SetToolTip("Will start a transition from the current panning values, to the armed panning values.")
        self.transform_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_zero_button.SetLabel("ZERO PAN")

        #ZERO PAN STEP INPUT BOX STRING
        self.zero_pan_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(trbX+74, tbrY+14))
        #ZERO PAN STEP INPUT BOX
        self.zero_pan_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+70, tbrY+30))
        self.zero_pan_step_input_box.SetToolTip("The number of frames that it will take a for a panning transition to go from the current panning value to the armed panning value.")
        self.zero_pan_step_input_box.SetLabel("0")

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
        self.zoom_step_input_box = wx.TextCtrl(self.panel, 151, size=(30,20), style = wx.TE_PROCESS_ENTER, pos=(105+trbX, tbrY+115))
        self.zoom_step_input_box.SetToolTip("The granularity of the Zoom slider.")
        self.zoom_step_input_box.SetLabel("10")
        self.zoom_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=151)
        #self.seed_input_box =      wx.TextCtrl(self.panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+340, tbrY-50-60))

        #FOV SLIDER
        self.fov_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=70, minValue=20, maxValue=120, pos = (190+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.fov_slider.SetToolTip("Sets the current Field Of View (70 is default).")
        self.fov_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
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

        #STRENGTH SCHEDULE SLIDER
        self.strength_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=65, minValue=1, maxValue=100, pos = (trbX-25, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.strength_schedule_slider.SetToolTip("Sets the Strength value. The scale shown is 100 times larger than the actual value (so when using strength==100 it's actually 1.0)")
        self.strength_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.strength_schedule_slider.SetTickFreq(1)
        self.strength_schedule_slider.SetLabel("STRENGTH SCHEDULE")
        self.step_schedule_Text = wx.StaticText(self.panel, label="Strength Value", pos=(trbX-25, tbrY-70))

        #PROMPT ON/OFF BUTTON
        #bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
        #ppb = True
        #bmp = scale_bitmap(bmp, 15, 15)
        #self.parseq_prompt_button = wx.BitmapButton(self.panel, bitmap=bmp, id=wx.ID_ANY, pos=(trbX+560, 10), size=(bmp.GetWidth() + 2, bmp.GetHeight() + 2))
        #self.parseq_prompt_button.SetToolTip("When activated (red), Deforumations prompt system will be in use, else it will use Deforum's or Parseq's. If Parseq is activated it overrides Deforum's.")
        #self.parseq_prompt_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        #self.parseq_prompt_button.SetLabel("Use Deforumation prompt scheduling")

        #PARSEQ STRENGTH ON/OFF BUTTON
       # if int(readValue("parseq_strength")) == 1:
       #     bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
       #     pstb = True
       # else:
       #     bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
       #     pstb = False
       # bmp = scale_bitmap(bmp, 15, 15)
       # self.parseq_strength_button = wx.BitmapButton(self.panel, bitmap=bmp, id=wx.ID_ANY, pos=(trbX-45, tbrY-46), size=(bmp.GetWidth() + 2, bmp.GetHeight() + 2))
       # self.parseq_strength_button.SetToolTip("When activated (red), both Deforumations Strength and CFG-slider will be used.If not activated, Deforum's or Parseq's values will be used for CFG and maybe Strength (depending on if the \"USE DEFORUMATION\"-checkbox for strength is activated or not. Parseq always overrides Deforum's values if it is active.")
       # self.parseq_strength_button.Bind(wx.EVT_BUTTON, self.OnClicked)
       # self.parseq_strength_button.SetLabel("pstb")

        #PARSEQ MOVEMENTS ON/OFF BUTTON
        #if int(readValue("parseq_movements")) == 1:
        #    bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
        #    pmob = True
        #else:
        #    bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
        #    pmob = False
        #bmp = scale_bitmap(bmp, 20, 20)
        #self.parseq_movements_button = wx.BitmapButton(self.panel, bitmap=bmp, id=wx.ID_ANY, pos = (trbX+280, tbrY+100), size=(bmp.GetWidth() + 2, bmp.GetHeight() + 2))
        #self.parseq_movements_button.SetToolTip("When activated (red), Deforumations motion controls will be in use (PAN, ROTATION, ZOOM, FOV and TILT). If not activated, Deforum's or Parseq's motion values are added to Deforum's motion values.")
        #self.parseq_movements_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        #self.parseq_movements_button.SetLabel("pmob")

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
        self.should_use_deforumation_zoomfov_checkbox = wx.CheckBox(self.panel, label="U.D.Zo", pos=(trbX+172, tbrY-8))
        self.should_use_deforumation_zoomfov_checkbox.SetToolTip("When activated, Deforumations ZOOM and FOV values will be used.")
        self.should_use_deforumation_zoomfov_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION ROTATION VALUES? CHECK-BOX
        self.should_use_deforumation_rotation_checkbox = wx.CheckBox(self.panel, label="U.D.Ro", pos=(trbX+354, tbrY-8))
        self.should_use_deforumation_rotation_checkbox.SetToolTip("When activated, Deforumations Rotation values will be used.")
        self.should_use_deforumation_rotation_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SHOULD USE DEFORUMATION TILT VALUES? CHECK-BOX
        self.should_use_deforumation_tilt_checkbox = wx.CheckBox(self.panel, label="U.D.Ti", pos=(trbX+480, tbrY+12))
        self.should_use_deforumation_tilt_checkbox.SetToolTip("When activated, Deforumations Tilt values will be used.")
        self.should_use_deforumation_tilt_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

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
        self.rotation_3d_x_left_button.SetLabel("LOOK_LEFT")

        #SET ROTATION VALUE X
        self.rotation_3d_x_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_X), pos=(240+trbX-30+80, 55+tbrY+5))
        self.rotation_3d_x_Value_Text.SetToolTip("Current X-Rotation value.")
        font = self.rotation_3d_x_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_x_Value_Text.SetFont(font)

        #ROTATE STEPS INPUT
        self.rotate_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(240+trbX-15+80, 30+tbrY))
        self.rotate_step_input_box.SetToolTip("The X Rotation granularity.")
        self.rotate_step_input_box.SetLabel("1.0")

        #LOOK UPP BUTTTON
        bmp = wx.Bitmap("./images/look_upp.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_up_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY-30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_up_button.SetToolTip("How many degrees it should continuously rotate upwards.")
        self.rotation_3d_y_up_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_up_button.SetLabel("LOOK_UP")

        #ZERO ROTATE STEP INPUT BOX STRING
        self.zero_rotate_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(240+trbX+43+100, 55+tbrY-40))
        #ZERO ROTATE STEP INPUT BOX
        self.zero_rotate_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(240+trbX+40+100, 55+tbrY-25))
        self.zero_rotate_step_input_box.SetToolTip("The number of frames that it will take a for a rotation transition to go from the current rotation values to the armed panning values.")
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
        self.rotation_3d_x_right_button.SetLabel("LOOK_RIGHT")

        #LOOK DOWN BUTTTON
        bmp = wx.Bitmap("./images/look_down.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY+30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_down_button.SetToolTip("How many degrees it should continuously rotate downwards.")
        self.rotation_3d_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_down_button.SetLabel("LOOK_DOWN")

        #SPIN BUTTTON
        bmp = wx.Bitmap("./images/rotate_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(300+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_left_button.SetToolTip("How many degrees it should continuously spin anti-clock-wise.")
        self.rotation_3d_z_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
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
        self.tilt_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(360+trbX+38+80, 30+tbrY))
        self.tilt_step_input_box.SetToolTip("Sets the granularity of how many degrees it should tilt, when using the Tilt buttons.")
        self.tilt_step_input_box.SetLabel("1.0")

        #PAUSE VIDEO RENDERING
        if is_paused_rendering:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO RESUME RENDERING")
            self.pause_rendering.SetToolTip("Push this button to resume the paused image generation.")
        else:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO PAUSE RENDERING")
            self.pause_rendering.SetToolTip("Push this button to pause the ongoing image generation.")
        sizer.Add(self.pause_rendering, 0, wx.ALL | wx.EXPAND, 5)
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

        #NOISE SLIDER
        self.noise_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=105, minValue=0, maxValue=200, pos = (trbX+950-340, tbrY+110), size = (360, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.noise_slider.SetToolTip("How much uniformed noise should Deforum use. Lower values will loose detail (smoothing things out), and higher values will add more detail making it sharper (too much will result in a scrambled image).")
        self.noise_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.noise_slider.SetTickFreq(1)
        self.noise_slider.SetLabel("Noise")
        self.noise_slider_Text = wx.StaticText(self.panel, label="Noise", pos=(trbX+1000-340, tbrY+95))
        self.noise_slider.Hide()
        self.noise_slider_Text.Hide()

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

        #ControlNet Sliders
        ###############################################################
        #CONTROLNET WEIGHT
        self.control_net_weight_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_Weight*100), minValue=0, maxValue=200, pos = (trbX-40, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_weight_slider.SetToolTip("Tells, if activated, the first ControlNet, what weight it should use. The slider value is scaled by 100 (actual value 100 times smaller)")
        self.control_net_weight_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_weight_slider.SetTickFreq(1)
        self.control_net_weight_slider.SetLabel("CN WEIGHT")
        self.control_net_weight_slider_Text = wx.StaticText(self.panel, label="ControlNet - Weight", pos=(trbX-40, tbrY+160))

        #CONTROLNET STARTING CONTROL STEP
        self.control_net_stepstart_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepStart*100), minValue=0, maxValue=100, pos = (trbX+300, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_stepstart_slider.SetToolTip("Tells, if activated, the first ControlNet, what step it should start on. The slider value is scaled by 100 (actual value 100 times smaller)")
        self.control_net_stepstart_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_stepstart_slider.SetTickFreq(1)
        self.control_net_stepstart_slider.SetLabel("CN STEPSTART")
        self.control_net_stepstart_slider_Text = wx.StaticText(self.panel, label="ControlNet - Starting Control Step", pos=(trbX+300, tbrY+160))

        #CONTROLNET ENDING CONTROL STEP
        self.control_net_stepend_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepEnd*100), minValue=0, maxValue=100, pos = (trbX+640, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_stepend_slider.SetToolTip("Tells, if activated, the first ControlNet, what step it should end on. The slider value is scaled by 100 (actual value 100 times smaller)")
        self.control_net_stepend_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_stepend_slider.SetTickFreq(1)
        self.control_net_stepend_slider.SetLabel("CN STEPEND")
        self.control_net_stepend_slider_Text = wx.StaticText(self.panel, label="ControlNet - Ending Control Step", pos=(trbX+640, tbrY+160))

        #CONTROLNET LOW THRESHOLD
        self.control_net_lowt_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_LowT), minValue=0, maxValue=255, pos = (trbX-40, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_lowt_slider.SetToolTip("Tells, if activated, the first ControlNet, what the lower threshold should be. Values below the low threshold always get discarded. Values in between the the two thresholds may get kept or may get discarded depending on various rules and maths.")
        self.control_net_lowt_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_lowt_slider.SetTickFreq(1)
        self.control_net_lowt_slider.SetLabel("CN LOWT")
        self.control_net_lowt_slider_Text = wx.StaticText(self.panel, label="ControlNet - Low Threshold", pos=(trbX-40, tbrY+240))

        #CONTROLNET HIGH THRESHOLD
        self.control_net_hight_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_HighT), minValue=0, maxValue=255, pos = (trbX+300, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_hight_slider.SetToolTip("Tells, if activated, the first ControlNet, what the higher threshold should be. Values below the low threshold always get discarded. Values above the high threshold always get kept. Values in between the the two thresholds may get kept or may get discarded depending on various rules and maths.")
        self.control_net_hight_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_hight_slider.SetTickFreq(1)
        self.control_net_hight_slider.SetLabel("CN HIGHT")
        self.control_net_hight_slider_Text = wx.StaticText(self.panel, label="ControlNet - High Threshold", pos=(trbX+300, tbrY+240))

        #PARSEQ URL INPUT BOX
        self.Parseq_URL_input_box_text = wx.StaticText(self.panel, label="Use PARSEQ as Guide: ", pos = (trbX + 640, tbrY + 245))
        self.Parseq_activation_Checkbox = wx.CheckBox(self.panel, id=73, pos=(trbX+770, tbrY + 245))
        self.Parseq_activation_Checkbox.SetToolTip("Tells, Deforum and Deforumation that Parseq is to be used as scheduler.")
        self.Parseq_activation_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        self.Parseq_URL_input_box = wx.TextCtrl(self.panel, 28, size=(300,20), style = wx.TE_PROCESS_ENTER, pos = (trbX + 640, tbrY + 265))
        self.Parseq_URL_input_box.SetToolTip("This should point to a URL that contains a JSON file, as generated by the online Parseq application (https://sd-parseq.web.app).")
        self.Parseq_URL_input_box.SetHint("<URL to Parseq JSON File here>")
        #PARSEQ SEND TO DEFORUM BUTTON
        self.Send_URL_to_Deforum = wx.Button(self.panel, id=wx.ID_ANY, label="Send Deforum", pos=(trbX + 820, tbrY + 242), size=(120, 20))
        self.Send_URL_to_Deforum.SetToolTip("This sends the actual URL to Deforum, so that it knows what Parseq file it should use during scheduling.")
        self.Send_URL_to_Deforum.Bind(wx.EVT_BUTTON, self.OnClicked)

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


        #self.cadence_rescheduler_url_input_box.Bind(wx.EVT_SET_FOCUS, self.OnFocus)


        #Checkbox stuff
        #self.cadence_schedule_Checkbox = wx.CheckBox(self.panel, label = "Use C.", id=73, pos=(trbX+1000-66, tbrY-20))
        #self.cadence_schedule_Checkbox.SetToolTip("When checked, tells Deforum to use this Cadence Schedule.")
        #self.cadence_schedule_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)


        self.Centre()
        self.Show()
        self.Fit()

        self.loadAllValues()
        self.setAllComponentValues()
        #KEYBOARD INPUT EVNTG HANDLER
        self.off_grid_input_box.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.off_grid_input_box.SetFocus()

        self.Layout()
        self.Bind(wx.EVT_SIZING, self.OnResize)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.PanelClicked)

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
        self.transform_x_left_button.SetPosition((5 + trbX, 55 + tbrY))
        self.pan_X_Value_Text.SetPosition((trbX - 26, 55 + tbrY + 5))
        self.pan_Y_Value_Text.SetPosition((40 + trbX, 5 + tbrY))
        self.transform_y_upp_button.SetPosition((35 + trbX, 25 + tbrY))
        self.transform_x_right_button.SetPosition((65 + trbX, 55 + tbrY))
        self.transform_y_down_button.SetPosition((35 + trbX, 85 + tbrY))
        self.transform_zero_button.SetPosition((35 + trbX, 56 + tbrY))
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
        self.strength_schedule_slider.SetPosition((trbX - 25, tbrY - 50))
        #self.parseq_strength_button.SetPosition((trbX-45, tbrY-46))
        #self.parseq_movements_button.SetPosition((trbX+280, tbrY+100))
        self.step_schedule_Text.SetPosition((trbX - 25, tbrY - 70))
        self.should_use_deforumation_strength_checkbox.SetPosition((trbX + 160, tbrY - 66))
        self.should_use_deforumation_cfg_checkbox.SetPosition((trbX+460, tbrY-66))
        self.should_use_deforumation_cadence_checkbox.SetPosition((trbX+780, tbrY))
        self.should_use_deforumation_noise_checkbox.SetPosition((trbX+720, tbrY+74))
        self.should_use_deforumation_panning_checkbox.SetPosition((trbX+40, tbrY-8))
        self.should_use_deforumation_zoomfov_checkbox.SetPosition((trbX + 172, tbrY - 8))
        self.should_use_deforumation_rotation_checkbox.SetPosition((trbX+354, tbrY-8))
        self.should_use_deforumation_tilt_checkbox.SetPosition((trbX+480, tbrY+12))

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
        self.tilt_step_input_box.SetPosition((360 + trbX + 38 + 80, 30 + tbrY))
        self.cadence_slider.SetPosition((trbX + 1000-340, tbrY + 20))
        self.cadence_slider_Text.SetPosition((trbX + 1000-340, tbrY))
        self.cadence_schedule_input_box.SetPosition((trbX+1000-220, tbrY-22))
        self.cadence_schedule_Checkbox.SetPosition((trbX+1000-66, tbrY-20))
        self.cadence_suggestion.SetPosition((trbX+1000-140, tbrY))
        self.control_net_weight_slider.SetPosition((trbX-40, tbrY+180))
        self.control_net_weight_slider_Text.SetPosition((trbX-40, tbrY+160))
        self.control_net_stepstart_slider.SetPosition((trbX+300, tbrY+180))
        self.control_net_stepstart_slider_Text.SetPosition((trbX+640, tbrY+160))
        self.control_net_stepend_slider.SetPosition((trbX+640, tbrY+180))
        self.control_net_stepend_slider_Text.SetPosition((trbX+300, tbrY+160))
        self.control_net_lowt_slider.SetPosition((trbX-40, tbrY+260))
        self.control_net_lowt_slider_Text.SetPosition((trbX-40, tbrY+240))
        self.control_net_hight_slider.SetPosition((trbX+300, tbrY+260))
        self.control_net_hight_slider_Text.SetPosition((trbX+300, tbrY+240))
        self.Send_URL_to_Deforum.SetPosition((trbX + 820, tbrY + 242))
        self.Parseq_URL_input_box.SetPosition((trbX + 640, tbrY + 265))
        self.Parseq_URL_input_box_text.SetPosition((trbX + 640, tbrY + 245))
        self.Parseq_activation_Checkbox.SetPosition((trbX+760, tbrY + 245))
        self.replay_input_box_text.SetPosition((trbX+990, tbrY-130))
        self.replay_from_input_box.SetPosition((trbX+1030, tbrY-131))
        self.replay_to_input_box.SetPosition((trbX+1090, tbrY-131))
        self.replay_input_divider_box_text.SetPosition((trbX+1077, tbrY-130))
        self.replay_button.SetPosition((trbX + 1145, tbrY -135))
        self.fps_input_box_text.SetPosition((trbX+1180, tbrY-130))
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
        global shouldUseDeforumPromptScheduling
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
                self.positive_prompt_input_ctrl.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_2.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_3.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_4.SetValue(deforumFile.readline())
                self.negative_prompt_input_ctrl.SetValue(deforumFile.readline())
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
                CN_Weight = float(deforumFile.readline().strip().strip('\n'))
                self.control_net_weight_slider.SetValue(int(CN_Weight*100))
                CN_StepStart = float(deforumFile.readline().strip().strip('\n'))
                self.control_net_stepstart_slider.SetValue(int(CN_StepStart*100))
                CN_StepEnd = float(deforumFile.readline().strip().strip('\n'))
                self.control_net_stepend_slider.SetValue(int(CN_StepEnd*100))
                CN_LowT = int(deforumFile.readline().strip().strip('\n'))
                self.control_net_lowt_slider.SetValue(CN_LowT)
                CN_HighT = int(deforumFile.readline().strip().strip('\n'))
                self.control_net_hight_slider.SetValue(CN_HighT)

                noise_multiplier = float(deforumFile.readline().strip().strip('\n'))
                self.noise_slider.SetValue(int(float(noise_multiplier)*100))
                Perlin_Octave_Value = int(deforumFile.readline().strip().strip('\n'))
                self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
                Perlin_Persistence_Value = float(deforumFile.readline().strip().strip('\n'))
                #print("Perlin_Persistence_Value"+str('%.2f' % Perlin_Persistence_Value))
                self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value)*100))

            except Exception as e:
                print(e)
            self.writeValue("is_paused_rendering", is_paused_rendering)
            positive_prio = {
                int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
            sortedDict = sorted(positive_prio.items())
            totalPossitivePromptString = sortedDict[0][1] + "," + sortedDict[1][1] + "," + sortedDict[2][1] + "," + \
                                         sortedDict[3][1]
            self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', '') + "\n")
            self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '') + "\n")
            #self.writeValue("positive_prompt", self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
            #self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
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
            self.writeValue("cn_weight", float(CN_Weight))
            self.writeValue("cn_stepstart", float(CN_StepStart))
            self.writeValue("cn_stepend", float(CN_StepEnd))
            self.writeValue("cn_lowt", float(CN_LowT))
            self.writeValue("cn_hight", float(CN_HighT))

            self.writeValue("noise_multiplier", float(noise_multiplier))
            self.writeValue("perlin_octaves", int(Perlin_Octave_Value))
            self.writeValue("perlin_persistence", float(Perlin_Persistence_Value))
            self.writeValue("use_deforumation_cadence_scheduling", 0)

        else:
            self.writeAllValues()
    def writeValue(self, param, value):
        checkerrorConnecting = True
        while checkerrorConnecting:
            try:
                asyncio.run(sendAsync([1, param, value]))
                checkerrorConnecting = False
            except Exception as e:
                print("Deforumation Mediator Error:" + str(e))
                print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...writing:"+str(param))
                time.sleep(5)

    def readValue(self, param):
        checkerrorConnecting = True
        while checkerrorConnecting:
            try:
                return_value = asyncio.run(sendAsync([0, param, 0]))
                #print("All good reading:" + str(param))
                return return_value
            except Exception as e:
                print("Deforumation Mediator Error:" + str(e))
                print("The Deforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...ererror:reading:"+str(param))
                time.sleep(5)
    def setAllComponentValues(self):
        try:
            if is_paused_rendering:
                self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            else:
                self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            self.strength_schedule_slider.SetValue(int(Strength_Scheduler * 100))
            self.cfg_schedule_slider.SetValue(int(CFG_Scale))
            self.sample_schedule_slider.SetValue(STEP_Schedule)
            self.fov_slider.SetValue(int(FOV_Scale))
            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            self.zoom_slider.SetValue(int(Translation_Z) * 100)
            self.zoom_value_text.SetLabel('%.2f' % (Translation_Z))
            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
            self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))
            if should_use_deforumation_prompt_scheduling:
                #bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
                #bmp = scale_bitmap(bmp, 15, 15)
                #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
                self.writeValue("should_use_deforumation_prompt_scheduling", 1)
            else:
                #bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
                #bmp = scale_bitmap(bmp, 15, 15)
                #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
                self.writeValue("should_use_deforumation_prompt_scheduling", 0)
            self.should_use_deforumation_strength_checkbox.SetValue(int(should_use_deforumation_strength))
            self.should_use_deforumation_cfg_checkbox.SetValue(int(should_use_deforumation_cfg))
            self.should_use_deforumation_cadence_checkbox.SetValue(int(should_use_deforumation_cadence))
            self.should_use_deforumation_noise_checkbox.SetValue(int(should_use_deforumation_noise))
            self.should_use_deforumation_panning_checkbox.SetValue(int(should_use_deforumation_panning))
            self.should_use_deforumation_zoomfov_checkbox.SetValue(int(should_use_deforumation_zoomfov))
            self.should_use_deforumation_rotation_checkbox.SetValue(int(should_use_deforumation_rotation))
            self.should_use_deforumation_tilt_checkbox.SetValue(int(should_use_deforumation_tilt))
            self.pan_step_input_box.SetValue(pan_step_input_box_value)
            self.rotate_step_input_box.SetValue(rotate_step_input_box_value)
            self.tilt_step_input_box.SetValue(tilt_step_input_box_value)
            self.cadence_slider.SetValue(Cadence_Schedule)
            self.zero_pan_step_input_box.SetValue(zero_pan_step_input_box_value)
            self.zero_rotate_step_input_box.SetValue(zero_rotate_step_input_box_value)
            self.control_net_weight_slider.SetValue(int(CN_Weight * 100))
            self.control_net_stepstart_slider.SetValue(int(CN_StepStart * 100))
            self.control_net_stepend_slider.SetValue(int(CN_StepEnd * 100))
            self.control_net_lowt_slider.SetValue(CN_LowT)
            self.control_net_hight_slider.SetValue(CN_HighT)

            self.noise_slider.SetValue(int(float(noise_multiplier) * 100))
            self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
            self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value) * 100))

        except Exception as e:
            print(e)

    def writeAllValues(self):
        try:
            if is_paused_rendering:
                # Arrange the possitive prompts according to priority (now for some lazy programing):
                positive_prio = {
                    int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                    int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                    int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                    int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                sortedDict = sorted(positive_prio.items())
                totalPossitivePromptString = sortedDict[0][1] + "," + sortedDict[1][1] + "," + sortedDict[2][1] + "," + sortedDict[3][1]
                self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', '') + "\n")
                self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
        except Exception as e:
            print(e)
        deforumFile = open(deforumationSettingsPath, 'w')
        deforumFile.write(str(int(is_paused_rendering))+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_2.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_3.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl_4.GetValue().strip().replace('\n', '')+"\n")
        deforumFile.write(self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
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
        deforumFile.write(str('%.2f' % CN_Weight)+"\n")
        deforumFile.write(str('%.2f' % CN_StepStart)+"\n")
        deforumFile.write(str('%.2f' % CN_StepEnd)+"\n")
        deforumFile.write(str(CN_LowT)+"\n")
        deforumFile.write(str(CN_HighT)+"\n")
        deforumFile.write(str('%.2f' % noise_multiplier)+"\n")
        deforumFile.write(str(Perlin_Octave_Value)+"\n")
        deforumFile.write(str('%.2f' % Perlin_Persistence_Value))

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
            promptToShow =  self.positive_prompt_input_ctrl.GetValue()
            for index in range(0, len(old_lines), 2):
                param = old_lines[index].strip('\n').replace(" ", "").split(',')
                frame_index = param[0]
                type = param[1]
                if int(frame_start) >= int(frame_index):
                    promptToShow = old_lines[index+1]
                else:
                    break
            if showType == 0:
                if promptType == "P":
                    self.positive_prompt_input_ctrl.SetValue(str(promptToShow))
                else:
                    self.negative_prompt_input_ctrl.SetValue(str(promptToShow))
            elif showType == 1:
                if promptType == "P":
                    # Arrange the possitive prompts according to priority (now for some lazy programing):
                    positive_prio = {
                        int(self.positive_prompt_input_ctrl_prio.GetValue()): self.positive_prompt_input_ctrl.GetValue(),
                        int(self.positive_prompt_input_ctrl_2_prio.GetValue()): self.positive_prompt_input_ctrl_2.GetValue(),
                        int(self.positive_prompt_input_ctrl_3_prio.GetValue()): self.positive_prompt_input_ctrl_3.GetValue(),
                        int(self.positive_prompt_input_ctrl_4_prio.GetValue()): self.positive_prompt_input_ctrl_4.GetValue()}
                    sortedDict = sorted(positive_prio.items())
                    totalPossitivePromptString = sortedDict[0][1] + "," + sortedDict[1][1] + "," + sortedDict[2][1] + "," + sortedDict[3][1]
                    self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', '') + "\n")
                else:
                    self.writeValue("negative_prompt", promptToShow.strip().replace('\n', '')+"\n")


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
            print("Writing prompt at frame:" + str(copy_of_current))
            for index in range(0, len(old_lines), 2):
                if not didWriteNewPrompt:
                    param = old_lines[index].strip('\n').replace(" ", "").split(',')
                    frame_index = param[0]
                    type = param[1]
                    if int(copy_of_current) == int(frame_index):
                        new_lines[0] = frame_index + "," + type
                        if promptType == "P":
                            new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        else:
                            new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        promptFile.write(str(new_lines[0]) + "\n")
                        promptFile.write(str(new_lines[1]))
                        if index+2 != len(old_lines):
                            promptFile.write("\n")
                        didWriteNewPrompt = True
                    elif int(copy_of_current) < int(frame_index):
                        new_lines[0] = str(copy_of_current) + "," + type
                        if promptType == "P":
                            new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        else:
                            new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')
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

                else:
                    promptFile.write(old_lines[index])
                    promptFile.write(old_lines[index + 1])
            if not didWriteNewPrompt:
                new_lines[0] = str(copy_of_current) + "," + promptType
                if promptType == "P":
                    new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                    if new_lines[1] == "":
                        new_lines[1] = " "
                else:
                    new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                    if new_lines[1] == "":
                        new_lines[1] = " "
                if fileAlreadyExists:
                    promptFile.write("\n")
                promptFile.write(str(new_lines[0]) + "\n")
                promptFile.write(str(new_lines[1]))
            promptFile.close()
    def ZeroStepper(self, parameter_value, frame_steps, want_value):
        global Translation_X
        global Translation_Y
        global Rotation_3D_X
        global Rotation_3D_Y
        global stepit_pan
        global stepit_rotate
        global zero_pan_active
        global zero_rotate_active
        print("Zero stepper thread started for:"+str(parameter_value))
        is_negative = 0
        zero_frame_steps = frame_steps
        if zero_frame_steps == want_value:
            return
        now_frame = int(readValue("start_frame"))
        zero_frame_steps_n_frame = want_value
        if parameter_value == "translation_x":
            stepit_pan = 1
            if Translation_X != want_value:
                zero_frame_steps_n_frame = float((want_value - Translation_X) / zero_frame_steps)
            if Translation_X < 0:
                is_negative = 1
        elif parameter_value == "translation_y":
            stepit_pan = 1
            if Translation_Y != want_value:
                zero_frame_steps_n_frame = float((want_value - Translation_Y) / zero_frame_steps)
                if Translation_Y < 0:
                    is_negative = 1
        elif parameter_value == "rotation_x":
            stepit_rotate = 1
            if Rotation_3D_X != want_value:
                zero_frame_steps_n_frame = float((want_value-Rotation_3D_X) / zero_frame_steps)
                #print("zero_frame_steps:" + str(zero_frame_steps_n_frame))
                if Rotation_3D_Y < 0:
                    is_negative = 1
        elif parameter_value == "rotation_y":
            stepit_rotate = 1
            if Rotation_3D_Y != want_value:
                zero_frame_steps_n_frame = float((want_value-Rotation_3D_Y) / zero_frame_steps)
                #print("zero_frame_steps:" + str(zero_frame_steps_n_frame))
                if Rotation_3D_Y < 0:
                    is_negative = 1

        while zero_frame_steps_n_frame != 0:
            if (parameter_value == "translation_x" or parameter_value == "translation_y") and stepit_pan == 0:
                break
            if (parameter_value == "rotation_x" or parameter_value == "rotation_y") and stepit_rotate == 0:
                break

            current_step_frame = int(readValue("start_frame"))
            if (int(current_step_frame) > int(now_frame)):
                now_frame = current_step_frame
                if parameter_value == "translation_x":
                    Translation_X = Translation_X + float(zero_frame_steps_n_frame)
                elif parameter_value == "translation_y":
                    Translation_Y = Translation_Y + float(zero_frame_steps_n_frame)
                elif parameter_value == "rotation_x":
                    Rotation_3D_X = Rotation_3D_X + float(zero_frame_steps_n_frame)
                elif parameter_value == "rotation_y":
                    Rotation_3D_Y = Rotation_3D_Y + float(zero_frame_steps_n_frame)

                if parameter_value == "translation_x":
                    if zero_frame_steps_n_frame > 0:
                        if Translation_X >= want_value:
                            Translation_X = want_value
                            self.writeValue(parameter_value, Translation_X)
                            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                            break
                    elif zero_frame_steps_n_frame < 0:
                        if Translation_X <= want_value:
                            Translation_X = want_value
                            self.writeValue(parameter_value, Translation_X)
                            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                            break
                elif parameter_value == "translation_y":
                    if zero_frame_steps_n_frame > 0:
                        if Translation_Y >= want_value:
                            Translation_Y = want_value
                            self.writeValue(parameter_value, Translation_Y)
                            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                            break
                    elif zero_frame_steps_n_frame < 0:
                        if Translation_Y <= want_value:
                            Translation_Y = want_value
                            self.writeValue(parameter_value, Translation_Y)
                            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                            break
                elif parameter_value == "rotation_x":
                    if zero_frame_steps_n_frame > 0:
                        if Rotation_3D_X >= want_value:
                            Rotation_3D_X = want_value
                            self.writeValue(parameter_value, Rotation_3D_X)
                            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                            break
                    elif zero_frame_steps_n_frame < 0:
                        if Rotation_3D_X <= want_value:
                            Rotation_3D_X = want_value
                            self.writeValue(parameter_value, Rotation_3D_X)
                            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                            break
                elif parameter_value == "rotation_y":
                    if zero_frame_steps_n_frame > 0:
                        if Rotation_3D_Y >= want_value:
                            Rotation_3D_Y = want_value
                            self.writeValue(parameter_value, Rotation_3D_Y)
                            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                            break
                    elif zero_frame_steps_n_frame < 0:
                        if Rotation_3D_Y <= want_value:
                            Rotation_3D_Y = want_value
                            self.writeValue(parameter_value, Rotation_3D_Y)
                            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                            break

            if parameter_value == "translation_x":
                self.writeValue(parameter_value, Translation_X)
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                #print("Translation_X:" + str(Translation_X))
            elif parameter_value == "translation_y":
                self.writeValue(parameter_value, Translation_Y)
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                #print("Translation_Y:" + str(Translation_Y))
            elif parameter_value == "rotation_x":
                self.writeValue(parameter_value, Rotation_3D_X)
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                #print("Rotaion_X:" + str(Rotation_3D_X))
            elif parameter_value == "rotation_y":
                self.writeValue(parameter_value, Rotation_3D_Y)
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                #print("Rotaion_Y:" + str(Rotation_3D_Y))
            time.sleep(0.25)
        self.writeAllValues()
        if (parameter_value == "translation_x" or parameter_value == "translation_y"):
            zero_pan_active = False
        if (parameter_value == "rotation_x" or parameter_value == "rotation_y"):
            zero_rotate_active = False


        print("Ending stepper thread")

    def OnFocus(self, event):
        #if event.GetId() == 1233:
        print("Entered Input box!")
        self.cadence_schedule_Checkbox.SetValue(False)
        self.writeValue("use_deforumation_cadence_scheduling", 0)
        #self.cadence_schedule_Checkbox.SetCursor(0)
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
        global stepit_pan
        global stepit_rotate
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT
        global isReplaying
        global replayFrom
        global replayTo
        global replayFPS
        global cadenceArray
        global armed_rotation
        global armed_pan
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
        btn = event.GetEventObject().GetLabel()
        #print("Label of pressed button = ", str(event.GetId()))
        if btn == "PUSH TO PAUSE RENDERING":
            self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            is_paused_rendering = True
            self.writeValue("is_paused_rendering", is_paused_rendering)
            #print(dict(sorted(cadenceArray.items())))
        elif btn == "PUSH TO RESUME RENDERING":
            self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            self.loadCurrentPrompt("P", current_frame, 1)
            self.loadCurrentPrompt("N", current_frame, 1)
            is_paused_rendering = False
            self.writeValue("is_paused_rendering", is_paused_rendering)
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
            totalPossitivePromptString = sortedDict[0][1]+","+sortedDict[1][1]+","+sortedDict[2][1]+","+sortedDict[3][1]
            self.writeValue("positive_prompt", totalPossitivePromptString.strip().replace('\n', '') + "\n")
            self.writeValue("negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '') + "\n")
        elif btn == "PAN_LEFT":
            if not armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_X = 0
                else:
                    Translation_X = Translation_X - float(self.pan_step_input_box.GetValue())
                self.writeValue("translation_x", Translation_X)
            else:
                Translation_X_ARMED =  round(Translation_X_ARMED - float(self.pan_step_input_box.GetValue()),2)
        elif btn == "PAN_RIGHT":
            if not armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_X = 0
                else:
                    Translation_X = Translation_X + float(self.pan_step_input_box.GetValue())
                self.writeValue("translation_x", Translation_X)
            else:
                Translation_X_ARMED = round(Translation_X_ARMED + float(self.pan_step_input_box.GetValue()),2)
        elif btn == "PAN_UP":
            if not armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_Y = 0
                else:
                    Translation_Y = Translation_Y + float(self.pan_step_input_box.GetValue())
                self.writeValue("translation_y", Translation_Y)
            else:
                Translation_Y_ARMED =  round(Translation_Y_ARMED + float(self.pan_step_input_box.GetValue()),2)
        elif btn == "PAN_DOWN":
            if not armed_pan:
                if self.eventDict[event.GetEventType()] == "EVT_RIGHT_UP":
                    Translation_Y = 0
                else:
                    Translation_Y = Translation_Y - float(self.pan_step_input_box.GetValue())
                self.writeValue("translation_y", Translation_Y)
            else:
                Translation_Y_ARMED =  round(Translation_Y_ARMED - float(self.pan_step_input_box.GetValue()),2)
        elif btn == "ZERO PAN":
            if not zero_pan_active:
                #Start a ZERO step thread.
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    Translation_X = 0
                    Translation_Y = 0
                    self.writeValue("translation_x", Translation_X)
                    self.writeValue("translation_y", Translation_Y)
                elif (Translation_X == 0 and Translation_Y == 0 and Translation_X_ARMED == 0 and Translation_Y_ARMED == 0) or (Translation_X == Translation_X_ARMED and Translation_Y == Translation_Y_ARMED):
                    zero_pan_active = False
                else:
                    zero_pan_active = True
                    if Translation_X != Translation_X_ARMED:
                        self.zero_step_thread_x = threading.Thread(target=self.ZeroStepper, args=("translation_x", frame_steps, Translation_X_ARMED))
                        self.zero_step_thread_x.daemon = True
                        self.zero_step_thread_x.start()
                    if Translation_Y != Translation_Y_ARMED:
                        self.zero_step_thread_y = threading.Thread(target=self.ZeroStepper, args=("translation_y", frame_steps, Translation_Y_ARMED))
                        self.zero_step_thread_y.daemon = True
                        self.zero_step_thread_y.start()
            else:
                stepit_pan = 0
                zero_pan_active = False

        elif btn == "ZOOM":
            currentEventTypeID = event.GetEventType()

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
        elif event.GetId() == 151:
            minmaxval = self.zoom_step_input_box.GetValue()
            self.zoom_slider.SetMin(int(-float(minmaxval)*100))
            self.zoom_slider.SetMax(int(float(minmaxval)*100))
            self.zoom_value_high_text.SetLabel(minmaxval)
            self.zoom_value_low_text.SetLabel("-"+minmaxval)
            self.zoom_slider.SetTickFreq(int(float(minmaxval)*100/10))
            #float(minmaxval)/20

        elif btn == "STRENGTH SCHEDULE":
            Strength_Scheduler = float(self.strength_schedule_slider.GetValue())*0.01
            self.writeValue("strength", Strength_Scheduler)
        elif event.GetId() == 3: #Seed Input Box
            seedValue = int(self.seed_input_box.GetValue())
            print("SeedValue:"+str(seedValue))
            self.writeValue("seed", seedValue)
        elif btn == "LOOK_LEFT":
            if not armed_rotation:
                Rotation_3D_Y = Rotation_3D_Y - float(self.rotate_step_input_box.GetValue())
                self.writeValue("rotation_y", Rotation_3D_Y)
            else:
                Rotation_3D_Y_ARMED =  round(Rotation_3D_Y_ARMED - float(self.rotate_step_input_box.GetValue()),2)
        elif btn == "LOOK_RIGHT":
            if not armed_rotation:
                Rotation_3D_Y = Rotation_3D_Y + float(self.rotate_step_input_box.GetValue())
                self.writeValue("rotation_y", Rotation_3D_Y)
            else:
                Rotation_3D_Y_ARMED =  round(Rotation_3D_Y_ARMED + float(self.rotate_step_input_box.GetValue()),2)
        elif btn == "LOOK_UP":
            if not armed_rotation:
                Rotation_3D_X = Rotation_3D_X + float(self.rotate_step_input_box.GetValue())
                self.writeValue("rotation_x", Rotation_3D_X)
            else:
                Rotation_3D_X_ARMED =  round(Rotation_3D_X_ARMED + float(self.rotate_step_input_box.GetValue()),2)
        elif btn == "LOOK_DOWN":
            if not armed_rotation:
                Rotation_3D_X = Rotation_3D_X - float(self.rotate_step_input_box.GetValue())
                self.writeValue("rotation_x", Rotation_3D_X)
            else:
                Rotation_3D_X_ARMED =  round(Rotation_3D_X_ARMED - float(self.rotate_step_input_box.GetValue()),2)
        elif btn == "ZERO ROTATE":
            if not zero_rotate_active:
                #Start a ZERO step thread.
                frame_steps = int(self.zero_rotate_step_input_box.GetValue())
                if frame_steps == 0:
                    Rotation_3D_X = 0
                    Rotation_3D_Y = 0
                    self.writeValue("rotation_x", Rotation_3D_X)
                    self.writeValue("rotation_y", Rotation_3D_Y)
                elif (Rotation_3D_X == 0 and Rotation_3D_Y == 0 and Rotation_3D_X_ARMED == 0 and Rotation_3D_Y_ARMED == 0) or (Rotation_3D_X == Rotation_3D_X_ARMED and Rotation_3D_Y == Rotation_3D_Y_ARMED):
                    zero_rotate_active = False
                else:
                    zero_rotate_active = True
                    if Rotation_3D_X != Rotation_3D_X_ARMED:
                        self.zero_rotate_thread_x = threading.Thread(target=self.ZeroStepper, args=("rotation_x", frame_steps, Rotation_3D_X_ARMED))
                        self.zero_rotate_thread_x.daemon = True
                        self.zero_rotate_thread_x.start()
                    if Rotation_3D_Y != Rotation_3D_Y_ARMED:
                        self.zero_rotate_thread_y = threading.Thread(target=self.ZeroStepper, args=("rotation_y", frame_steps, Rotation_3D_Y_ARMED))
                        self.zero_rotate_thread_y.daemon = True
                        self.zero_rotate_thread_y.start()
            else:
                stepit_rotate = 0
                zero_rotate_active = False

        elif btn == "ROTATE_LEFT":
            Rotation_3D_Z = Rotation_3D_Z + float(self.tilt_step_input_box.GetValue())
            self.writeValue("rotation_z", Rotation_3D_Z)
        elif btn == "ROTATE_RIGHT":
            Rotation_3D_Z = Rotation_3D_Z - float(self.tilt_step_input_box.GetValue())
            self.writeValue("rotation_z", Rotation_3D_Z)
        elif btn == "ZERO TILT":
            Rotation_3D_Z = 0
            self.writeValue("rotation_z", Rotation_3D_Z)
        elif btn == "CFG SCALE":
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
        elif btn == "FOV":
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
            STEP_Schedule = int(self.sample_schedule_slider.GetValue())
            self.writeValue("steps", STEP_Schedule)
        elif btn == "CADENCE":
            Cadence_Schedule = int(self.cadence_slider.GetValue())
            self.writeValue("cadence", Cadence_Schedule)
            cadenceArray[int(self.readValue("start_frame"))] = Cadence_Schedule
        elif btn == "Noise":
            noise_multiplier = float(self.noise_slider.GetValue())/100
            self.writeValue("noise_multiplier", noise_multiplier)
        elif btn == "Perlin Octaves":
            Perlin_Octave_Value = int(self.perlin_octave_slider.GetValue())
            self.writeValue("perlin_octaves", Perlin_Octave_Value)
        elif btn == "Perlin Persistence":
            Perlin_Persistence_Value = float(self.perlin_persistence_slider.GetValue())/100
            self.writeValue("perlin_persistence", Perlin_Persistence_Value)
        elif btn == "CN WEIGHT":
            CN_Weight = float(self.control_net_weight_slider.GetValue())*0.01
            self.writeValue("cn_weight", CN_Weight)
        elif btn == "CN STEPSTART":
            CN_StepStart = float(self.control_net_stepstart_slider.GetValue()) * 0.01
            self.writeValue("cn_stepstart", CN_StepStart)
        elif btn == "CN STEPEND":
            CN_StepEnd = float(self.control_net_stepend_slider.GetValue()) * 0.01
            self.writeValue("cn_stepend", CN_StepEnd)
        elif btn == "CN LOWT":
            CN_LowT = int(self.control_net_lowt_slider.GetValue())
            self.writeValue("cn_lowt", CN_LowT)
        elif btn == "CN HIGHT":
            CN_HighT = int(self.control_net_hight_slider.GetValue())
            self.writeValue("cn_hight", CN_HighT)
        elif btn == "Show current image" or btn == "REWIND" or btn == "FORWARD" or event.GetId() == 2 or btn == "REWIND_CLOSEST" or btn == "FORWARD_CLOSEST":
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
            self.loadCurrentPrompt("P", current_render_frame, 0)
            self.loadCurrentPrompt("N", current_render_frame, 0)
            current_render_frame = str(current_render_frame).zfill(9)
            imagePath = outdir + "/" + resume_timestring + "_" + current_render_frame + ".png"
            maxBackTrack = 100
            #print(str("Trying to load:"+imagePath))
            while not os.path.isfile(imagePath):
                if (current_render_frame == 0):
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
        elif btn == "USE DEFORUMATION STRENGTH":
            if should_use_deforumation_strength == 0:
                self.writeValue("should_use_deforumation_strength", 1)
                should_use_deforumation_strength = 1
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
            else:
                self.writeValue("should_use_deforumation_strength", 0)
                should_use_deforumation_strength = 0
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
        elif btn == "USE DEFORUMATION CFG":
            if should_use_deforumation_cfg == 0:
                self.writeValue("should_use_deforumation_cfg", 1)
                should_use_deforumation_cfg = 1
            else:
                self.writeValue("should_use_deforumation_cfg", 0)
                should_use_deforumation_cfg = 0
        elif btn == "U.D.Ca":
            if should_use_deforumation_cadence == 0:
                self.writeValue("should_use_deforumation_cadence", 1)
                should_use_deforumation_cadence = 1
            else:
                self.writeValue("should_use_deforumation_cadence", 0)
                should_use_deforumation_cadence = 0
        elif btn == "U.D.No":
            if should_use_deforumation_noise == 0:
                self.writeValue("should_use_deforumation_noise", 1)
                should_use_deforumation_noise = 1
            else:
                self.writeValue("should_use_deforumation_noise", 0)
                should_use_deforumation_noise = 0
        elif btn == "U.D.Pa":
            if should_use_deforumation_panning == 0:
                self.writeValue("should_use_deforumation_panning", 1)
                should_use_deforumation_panning = 1
            else:
                self.writeValue("should_use_deforumation_panning", 0)
                should_use_deforumation_panning = 0
        elif btn == "U.D.Zo":
            if should_use_deforumation_zoomfov == 0:
                self.writeValue("should_use_deforumation_zoomfov", 1)
                should_use_deforumation_zoomfov = 1
            else:
                self.writeValue("should_use_deforumation_zoomfov", 0)
                should_use_deforumation_zoomfov = 0
        elif btn == "U.D.Ro":
            if should_use_deforumation_rotation == 0:
                self.writeValue("should_use_deforumation_rotation", 1)
                should_use_deforumation_rotation = 1
            else:
                self.writeValue("should_use_deforumation_rotation", 0)
                should_use_deforumation_rotation = 0
        elif btn == "U.D.Ti":
            if should_use_deforumation_tilt == 0:
                self.writeValue("should_use_deforumation_tilt", 1)
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
                    should_render_live = True
                    self.live_render_checkbox.SetValue(1)
                    imagePath = get_current_image_path_f(replayFrom)
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
        elif btn == "LIVE RENDER":
            current_frame = str(self.readValue("start_frame"))
            #print("should_render_live: "+str(should_render_live))
            if should_render_live == False:
                should_render_live = True
                outdir = str(self.readValue("frame_outdir")).replace('\\', '/').replace('\n', '')
                resume_timestring = str(self.readValue("resume_timestring"))

                #current_frame = current_frame.zfill(9)
                #imagePath = get_current_image_path()
                if not is_paused_rendering or current_render_frame < 0:
                    imagePath = get_current_image_path_f(current_frame)
                else:
                    imagePath = get_current_image_path_f(current_render_frame)

                maxBackTrack = 100
                while not os.path.isfile(imagePath):
                    if (current_frame == 0):
                        break
                    current_frame = str(int(current_frame) - 1)
                    current_frame = current_frame.zfill(9)
                    if not is_paused_rendering or current_render_frame < 0:
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
                #bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
                #bmp = scale_bitmap(bmp, 15, 15)
                #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(1)
                self.writeValue("should_use_deforumation_prompt_scheduling", 1)
                should_use_deforumation_prompt_scheduling = 1
            else:
                #bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
                #bmp = scale_bitmap(bmp, 15, 15)
                #self.parseq_prompt_button.SetBitmap(wx.Bitmap(bmp))
                self.shouldUseDeforumPromptScheduling_Checkbox.SetValue(0)
                self.writeValue("should_use_deforumation_prompt_scheduling", 0)
                should_use_deforumation_prompt_scheduling = 0
       # elif btn == "pstb":
       #     if pstb:
       #         bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
       #         bmp = scale_bitmap(bmp, 15, 15)
       #         self.parseq_strength_button.SetBitmap(wx.Bitmap(bmp))
       #         self.writeValue("parseq_strength", 0)
       #         pstb = False
       #     else:
       #         bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
       #         bmp = scale_bitmap(bmp, 15, 15)
       #         self.parseq_strength_button.SetBitmap(wx.Bitmap(bmp))
       #         self.writeValue("parseq_strength", 1)
       #         pstb = True
        #elif btn == "pmob":
        #    if pmob:
        #        bmp = wx.Bitmap("./images/parseq_on.bmp", wx.BITMAP_TYPE_BMP)
        #        bmp = scale_bitmap(bmp, 20, 20)
        #        self.parseq_movements_button.SetBitmap(wx.Bitmap(bmp))
        #        self.writeValue("parseq_movements", 0)
        #        pmob = False
        #    else:
        #        bmp = wx.Bitmap("./images/parseq_off.bmp", wx.BITMAP_TYPE_BMP)
        #        bmp = scale_bitmap(bmp, 20, 20)
        #        self.parseq_movements_button.SetBitmap(wx.Bitmap(bmp))
        #        self.writeValue("parseq_movements", 1)
        #        pmob = True

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
            else:
                showLiveValues = False

        if not showLiveValues:
            if armed_pan:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
            else:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            if armed_rotation:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X_ARMED))
            else:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X))

            self.rotation_Z_Value_Text.SetLabel(str('%.2f' %Rotation_3D_Z))

        self.writeAllValues()

    def LiveValues(self):
        while showLiveValues:
            deforum_translation_x = readValue("deforum_translation_x")
            deforum_translation_y = readValue("deforum_translation_y")
            deforum_translation_z = readValue("deforum_translation_z")
            deforum_rotation_x = readValue("deforum_rotation_x")
            deforum_rotation_y = readValue("deforum_rotation_y")
            deforum_rotation_z = readValue("deforum_rotation_z")
            deforum_strength = readValue("deforum_strength")
            deforum_cfg = readValue("deforum_cfg")
            deforum_fov = readValue("deforum_fov")
            deforum_steps = readValue("deforum_steps")
            deforum_cadence = readValue("deforum_cadence")
            deforum_noise_multiplier = readValue("deforum_noise_multiplier")
            deforum_Perlin_Octave_Value = readValue("deforum_perlin_octaves")
            deforum_Perlin_Persistence_Value = readValue("deforum_perlin_persistence")
            if should_use_deforumation_panning:
                if armed_pan:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
                else:
                    self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                    self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
            else:
                self.pan_X_Value_Text.SetLabel(str('%.2f' % float(deforum_translation_x)))
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % float(deforum_translation_y)))

            if should_use_deforumation_zoomfov:
                self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
                self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z)))
                self.fov_slider.SetValue(int(FOV_Scale))
            else:
                self.zoom_slider.SetValue(int(float(deforum_translation_z)*100))
                self.zoom_value_text.SetLabel(str('%.2f' % float(deforum_translation_z)))
                self.fov_slider.SetValue(int(float(deforum_fov)))

            if should_use_deforumation_rotation:
                if armed_rotation:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X_ARMED))
                else:
                    self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                    self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
            else:
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_y)))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_x)))

            if should_use_deforumation_tilt:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Z)))
            else:
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(deforum_rotation_z)))

            if should_use_deforumation_noise:
                self.noise_slider.SetValue(int(float(noise_multiplier)*100))
                self.perlin_octave_slider.SetValue(int(Perlin_Octave_Value))
                self.perlin_persistence_slider.SetValue(int(float(Perlin_Persistence_Value)*100))
            else:
                self.noise_slider.SetValue(int(float(deforum_noise_multiplier)*100))
                self.perlin_octave_slider.SetValue(int(deforum_Perlin_Octave_Value))
                self.perlin_persistence_slider.SetValue(int(float(deforum_Perlin_Persistence_Value)*100))




            if should_use_deforumation_strength:
                self.strength_schedule_slider.SetValue(int(float(Strength_Scheduler) * 100))
            else:
                self.strength_schedule_slider.SetValue(int(float(deforum_strength)*100))

            if should_use_deforumation_cfg:
                    self.cfg_schedule_slider.SetValue(int(CFG_Scale))
            else:
                self.cfg_schedule_slider.SetValue(int(deforum_cfg))

            if should_use_deforumation_cadence:
                self.cadence_slider.SetValue(int(Cadence_Schedule))
            else:
                self.cadence_slider.SetValue(int(deforum_cadence))

            #Bottom Info Text
            self.deforum_strength_value_info_text.SetLabel("Strength:" + str('%.2f' % float(deforum_strength)))
            self.deforum_steps_value_info_text.SetLabel("Steps:" + str(deforum_steps))
            self.deforum_cfg_value_info_text.SetLabel("CFG:" + str(deforum_cfg))
            self.deforum_cadence_value_info_text.SetLabel("Cadence:" + str(deforum_cadence))
            self.deforum_trx_value_info_text.SetLabel("Tr X:" + str('%.2f' % float(deforum_translation_x)))
            self.deforum_try_value_info_text.SetLabel("Tr Y:" + str('%.2f' % float(deforum_translation_y)))
            self.deforum_trz_value_info_text.SetLabel("Tr Z:" + str('%.2f' % float(deforum_translation_z)))
            self.deforum_rox_value_info_text.SetLabel("Ro X:" + str('%.2f' % float(deforum_rotation_x)))
            self.deforum_roy_value_info_text.SetLabel("Ro Y:" + str('%.2f' % float(deforum_rotation_y)))
            self.deforum_roz_value_info_text.SetLabel("Ro Z:" + str('%.2f' % float(deforum_rotation_z)))

            time.sleep(0.25)

        if armed_pan:
            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X_ARMED))
            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y_ARMED))
        else:
            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
        if armed_rotation:
            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y_ARMED))
            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X_ARMED))
        else:
            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))

        self.rotation_Z_Value_Text.SetLabel(str('%.2f' % float(Rotation_3D_Z)))
        self.fov_slider.SetValue(int(FOV_Scale))
        self.zoom_slider.SetValue(int(float(Translation_Z) * 100))
        self.zoom_value_text.SetLabel(str('%.2f' % float(Translation_Z)))
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


if __name__ == '__main__':

    #anim = pyeaze.Animator(current_value=0, target_value=100, duration=1, fps=40, easing='ease-in-out', reverse=False)
    app = wx.App()
    Mywin(None, 'Deforumation @ Rakile & Lainol, 2023 (version 0.4.8)')
    app.MainLoop()
