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
import wx.lib.newevent
import threading
#import subprocess

deforumationSettingsPath="./deforumation_settings.txt"
deforumationSettingsPath_Keys = "./deforum_settings_keys.txt"
deforumationPromptsPath ="./prompts/"
screenWidth = 1500
screenHeight = 1050
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
should_use_deforum_prompt_scheduling = 0
#ControlNet
CN_Weight = 0
CN_StepStart = 0
CN_StepEnd = 100
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
zero_pan_active = False
zero_rotate_active = False
stepit_pan = 0
stepit_rotate = 0
isReplaying = 0
replayFrom = 0
replayTo = 0
replayFPS = 30

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
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
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
                    maxBackTrack = 10
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
                        parent.bitmap = wx.Bitmap(imagePath)
                        bitmap_width, bitmap_height = parent.parent.GetSize()
                        parent.bitmap = scale_bitmap(parent.bitmap, bitmap_width, bitmap_height)
                        parent.Refresh()
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
        if is_paused_rendering:
            imagePath = get_current_image_path_paused()
        else:
            imagePath = get_current_image_path()
        self.bitmap = wx.Bitmap(imagePath)
        bitmap_width, bitmap_height = self.parent.GetSize()
        self.bitmap = scale_bitmap(self.bitmap, bitmap_width, bitmap_height)
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
        super(Mywin, self).__init__(parent, title=title, size=(screenWidth, screenHeight))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.framer = None
        #self.framer = render_window(None, 'Rendering Image')
        #wx.EVT_PAINT(self, self.OnPaint)
        #wx.EVT_SIZE(self, self.OnSize)
        #Timer Event
        ##############################################################################################################################################################################
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.updateRender, self.timer)
        #self.timer.Start(200)


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

        self.positive_prompt_input_ctrl_hide_box = wx.CheckBox(self.panel, id=101, label="Hide")
        self.positive_prompt_input_ctrl_hide_box.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer2.Add(self.positive_prompt_input_ctrl_hide_box, 0, wx.ALL, 0)
        sizer.Add(sizer2, 0, wx.ALL, 0)


        self.positive_prompt_input_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,100))
        sizer.Add(self.positive_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_2_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer3.Add(self.positive_prompt_input_ctrl_2_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_2_prio.SetValue("2")

        self.positive_prompt_input_ctrl_hide_box_2 = wx.CheckBox(self.panel, id=102, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_2.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer3.Add(self.positive_prompt_input_ctrl_hide_box_2, 0, wx.ALL, 0)
        sizer.Add(sizer3, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_2 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        sizer.Add(self.positive_prompt_input_ctrl_2, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_3_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer4.Add(self.positive_prompt_input_ctrl_3_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_3_prio.SetValue("3")

        self.positive_prompt_input_ctrl_hide_box_3 = wx.CheckBox(self.panel, id=103, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_3.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer4.Add(self.positive_prompt_input_ctrl_hide_box_3, 0, wx.ALL, 0)
        sizer.Add(sizer4, 0, wx.ALL, 0)


        self.positive_prompt_input_ctrl_3 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        sizer.Add(self.positive_prompt_input_ctrl_3, 0, wx.ALL | wx.EXPAND, 0)

        self.positive_prompt_input_ctrl_4_prio = wx.TextCtrl(self.panel, size=(20,20))
        sizer5.Add(self.positive_prompt_input_ctrl_4_prio, 0, wx.ALL, 0)
        self.positive_prompt_input_ctrl_4_prio.SetValue("4")

        self.positive_prompt_input_ctrl_hide_box_4 = wx.CheckBox(self.panel, id=104, label="Hide")
        self.positive_prompt_input_ctrl_hide_box_4.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer5.Add(self.positive_prompt_input_ctrl_hide_box_4, 0, wx.ALL, 0)
        sizer.Add(sizer5, 0, wx.ALL, 0)

        self.positive_prompt_input_ctrl_4 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(-1,50))
        sizer.Add(self.positive_prompt_input_ctrl_4, 0, wx.ALL | wx.EXPAND, 0)

        #Should use Deforum prompt scheduling?
        self.shouldUseDeforumPromptScheduling_Checkbox = wx.CheckBox(self.panel, label="Use Deforum prompt scheduling", pos=(trbX+600, 10))
        self.shouldUseDeforumPromptScheduling_Checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)
        #Stay On Top
        self.stayOnTop_Checkbox = wx.CheckBox(self.panel, label="Stay on top", pos=(trbX+1130, 10))
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
        self.negative_prompt_input_ctrl_hide_box.Bind(wx.EVT_CHECKBOX, self.OnShouldHide)
        sizer7.Add(self.negative_prompt_input_ctrl_hide_box, 0, wx.ALL, 0)
        sizer6.Add(sizer7, 0, wx.ALL, 0)
        sizer.Add(sizer6, 0, wx.ALL, 0)


        self.negative_prompt_input_ctrl = wx.TextCtrl(self.panel,style=wx.TE_MULTILINE, size=(-1,100))
        sizer.Add(self.negative_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 0)
        #if os.path.isfile(deforumationSettingsPath):
        #    self.negative_prompt_input_ctrl.SetValue(promptfileRead.readline())
        #    promptfileRead.close()

        self.panel.SetSizer(sizer)
        #SHOW LIVE RENDER CHECK-BOX
        self.live_render_checkbox = wx.CheckBox(self.panel, label="LIVE RENDER", pos=(trbX+1130-340, tbrY-110))
        self.live_render_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #OFF GRID BUTTON FOR KEYBOARD INPUT
        #self.off_grid_input_box = wx.Button(panel, label="", pos=(-1000, -1000))
        self.off_grid_input_box = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, size=(1, 1), pos=(-100,-100))
        #self.off_grid_button.Bind(wx.EVT_BUTTON, self.OnClicked)

        #SHOW CURRENT IMAGE, BUTTON
        self.show_current_image = wx.Button(self.panel, label="Show current image", pos=(trbX+992-340, tbrY-110))
        self.show_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)
        #REWIND BUTTTON
        bmp = wx.Bitmap("./images/left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1000-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_button.SetLabel("REWIND")
        #REWIND CLOSEST BUTTTON
        bmp = wx.Bitmap("./images/rewind_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_closest_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+970-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_closest_button.SetLabel("REWIND_CLOSEST")
        #SET CURRENT FRAME INPUT BOX
        self.frame_step_input_box = wx.TextCtrl(self.panel, 2, size=(48,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1032-340, tbrY-74))
        self.frame_step_input_box.SetLabel("")
        self.frame_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=2)
        #FORWARD BUTTTON
        bmp = wx.Bitmap("./images/right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1080-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_button.SetLabel("FORWARD")
        #FORWARD CLOSEST BUTTTON
        bmp = wx.Bitmap("./images/forward_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_closest_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1110-340, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_closest_button.SetLabel("FORWARD_CLOSEST")
        #SET CURRENT IMAGE, BUTTON
        self.set_current_image = wx.Button(self.panel, label="Set current image", pos=(trbX+998-340, tbrY-40))
        self.set_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)

        #SHOW AN IMAGE
        #self.img = wx.EmptyImage(240,240)
        #self.img = wx.Image("E:\\Tools\\stable-diffusion-webui\\outputs\\img2img-images\\Deforum_20230330002842\\20230330002842_000000082.png", wx.BITMAP_TYPE_ANY)
        #self.imageCtrl = wx.StaticBitmap(panel, wx.ID_ANY, wx.BitmapFromImage(img))
        #self.bitmap = wx.StaticBitmap(panel, -1, self.img, pos=(trbX+700, tbrY-120))
        #self.bitmap = None
        img = wx.Image(256, 256)
        self.bitmap = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(img), pos=(trbX + 650 +340, tbrY - 100))
        #REPLAY BUTTON
        self.replay_input_box_text = wx.StaticText(self.panel, label="Replay", pos=(trbX+990, tbrY-130))
        self.replay_from_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1030, tbrY-131))
        self.replay_from_input_box.SetValue("0")
        self.replay_to_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1090, tbrY-131))
        self.replay_to_input_box.SetValue("0")
        self.replay_input_divider_box_text = wx.StaticText(self.panel, label="-", pos=(trbX+1077, tbrY-130))
        bmp = wx.Bitmap("./images/play.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 18, 18)
        self.replay_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX + 1145, tbrY -135), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.replay_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.replay_button.SetLabel("REPLAY")
        #REPLAY FPS BOX
        self.fps_input_box_text = wx.StaticText(self.panel, label="fps", pos=(trbX+1180, tbrY-130))
        self.replay_fps_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+1200, tbrY-131))
        self.replay_fps_input_box.SetValue("30")

        #SAVE PROMPTS BUTTON
        self.update_prompts = wx.Button(self.panel, label="SAVE PROMPTS")
        sizer.Add(self.update_prompts, 0, wx.ALL | wx.EXPAND, 5)
        self.update_prompts.Bind(wx.EVT_BUTTON, self.OnClicked)

        #PAN STEPS INPUT
        self.pan_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX-15, 30+tbrY))
        self.pan_step_input_box.SetLabel("1.0")

        #LEFT PAN BUTTTON
        bmp = wx.Bitmap("./images/left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(5+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_left_button.SetLabel("PAN_LEFT")

        #SET PAN VALUE X
        self.pan_X_Value_Text = wx.StaticText(self.panel, label=str(Translation_X), pos=(trbX-26, 55+tbrY+5))
        font = self.pan_X_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_X_Value_Text.SetFont(font)

        #SET PAN VALUE Y
        self.pan_Y_Value_Text = wx.StaticText(self.panel, label=str(Translation_Y), pos=(40+trbX, 5+tbrY))
        font = self.pan_Y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_Y_Value_Text.SetFont(font)

        #UPP PAN BUTTTON
        bmp = wx.Bitmap("./images/upp_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_upp_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 25+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_upp_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_upp_button.SetLabel("PAN_UP")

        #RIGHT PAN BUTTTON
        bmp = wx.Bitmap("./images/right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(65+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_right_button.SetLabel("PAN_RIGHT")
        #DOWN PAN BUTTTON
        bmp = wx.Bitmap("./images/down_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 85+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_down_button.SetLabel("PAN_DOWN")

        #ZERO PAN BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 22, 22)
        self.transform_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 56+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_zero_button.SetLabel("ZERO PAN")

        #ZERO PAN STEP INPUT BOX STRING
        self.zero_pan_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(trbX+74, tbrY+14))
        #ZERO PAN STEP INPUT BOX
        self.zero_pan_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(trbX+70, tbrY+30))
        self.zero_pan_step_input_box.SetLabel("0")

        #ZOOM SLIDER
        self.zoom_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=0, minValue=-10, maxValue=10, pos = (110+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE )
        self.zoom_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.zoom_slider.SetTickFreq(1)
        self.zoom_slider.SetLabel("ZOOM")
        self.ZOOM_X_Text = wx.StaticText(self.panel, label="Z", pos=(170+trbX, tbrY+40))
        self.ZOOM_X_Text2 = wx.StaticText(self.panel, label="O", pos=(170+trbX, tbrY+60))
        self.ZOOM_X_Text3 = wx.StaticText(self.panel, label="O", pos=(170+trbX, tbrY+80))
        self.ZOOM_X_Text4 = wx.StaticText(self.panel, label="M", pos=(169+trbX, tbrY+100))

        #FOV SLIDER
        self.fov_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=70, minValue=20, maxValue=120, pos = (190+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.fov_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.fov_slider.SetTickFreq(1)
        self.fov_slider.SetLabel("FOV")
        self.FOV_Text = wx.StaticText(self.panel, label="F", pos=(250+trbX, tbrY+40))
        self.FOV_Text2 = wx.StaticText(self.panel, label="O", pos=(249+trbX, tbrY+60))
        self.FOV_Text3 = wx.StaticText(self.panel, label="V", pos=(250+trbX, tbrY+80))

        #LOCK FOV TO ZOOM BUTTON
        bmp = wx.Bitmap("./images/lock_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_lock_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY-5), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_lock_button.SetLabel("LOCK FOV")

        #REVERSE FOV TO ZOOM BUTTON
        bmp = wx.Bitmap("./images/reverse_fov_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_reverse_lock_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY+120), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_reverse_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_reverse_lock_button.SetLabel("REVERSE FOV")

        #STRENGTH SCHEDULE SLIDER
        self.strength_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=65, minValue=1, maxValue=100, pos = (trbX-25, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.strength_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.strength_schedule_slider.SetTickFreq(1)
        self.strength_schedule_slider.SetLabel("STRENGTH SCHEDULE")
        self.step_schedule_Text = wx.StaticText(self.panel, label="Strength Value (divided by 100)", pos=(trbX-25, tbrY-70))

        #SHOULD USE DEFORUMATION STRENGTH VALUES? CHECK-BOX
        self.should_use_deforumation_strength_checkbox = wx.CheckBox(self.panel, label="USE DEFORUMATION", pos=(trbX+160, tbrY-66))
        self.should_use_deforumation_strength_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SAMPLE STEP SLIDER
        self.sample_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=25, minValue=1, maxValue=200, pos = (trbX-25, tbrY-50-70), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.sample_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.sample_schedule_slider.SetTickFreq(1)
        self.sample_schedule_slider.SetLabel("STEPS")
        self.strength_schedule_Text = wx.StaticText(self.panel, label="Steps", pos=(trbX-25, tbrY-70-64))

        #SEED INPUT BOX
        self.seed_schedule_Text = wx.StaticText(self.panel, label="Seed", pos=(trbX+340, tbrY-50-80))
        self.seed_input_box = wx.TextCtrl(self.panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+340, tbrY-50-60))
        self.seed_input_box.SetLabel("-1")
        self.seed_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=3)



        #CFG SCHEDULE SLIDER
        self.cfg_schedule_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=7, minValue=1, maxValue=30, pos = (trbX+340, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cfg_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cfg_schedule_slider.SetTickFreq(1)
        self.cfg_schedule_slider.SetLabel("CFG SCALE")
        self.CFG_scale_Text = wx.StaticText(self.panel, label="CFG Scale", pos=(trbX+340, tbrY-70))


        #LOOK LEFT BUTTTON
        bmp = wx.Bitmap("./images/look_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_left_button.SetLabel("LOOK_LEFT")

        #SET ROTATION VALUE X
        self.rotation_3d_x_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_X), pos=(240+trbX-30+80, 55+tbrY+5))
        font = self.rotation_3d_x_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_x_Value_Text.SetFont(font)

        #ROTATE STEPS INPUT
        self.rotate_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(240+trbX-15+80, 30+tbrY))
        self.rotate_step_input_box.SetLabel("1.0")

        #LOOK UPP BUTTTON
        bmp = wx.Bitmap("./images/look_upp.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_up_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY-30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_up_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_up_button.SetLabel("LOOK_UP")

        #ZERO PAN STEP INPUT BOX STRING
        self.zero_rotate_step_input_box_text = wx.StaticText(self.panel, label="0-Steps", pos=(240+trbX+43+100, 55+tbrY-40))
        #ZERO PAN STEP INPUT BOX
        self.zero_rotate_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(240+trbX+40+100, 55+tbrY-25))
        self.zero_rotate_step_input_box.SetLabel("0")

        #SET ROTATION VALUE Y
        self.rotation_3d_y_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_Y), pos=(240+trbX+35+80, 55+tbrY-48))
        font = self.rotation_3d_y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_y_Value_Text.SetFont(font)

        #LOOK RIGHT BUTTTON
        bmp = wx.Bitmap("./images/look_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+57+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_right_button.SetLabel("LOOK_RIGHT")

        #LOOK UPP BUTTTON
        bmp = wx.Bitmap("./images/look_down.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_down_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY+30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_down_button.SetLabel("LOOK_DOWN")

        #ROTATE LEFT BUTTTON
        bmp = wx.Bitmap("./images/rotate_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_left_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(300+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_left_button.SetLabel("ROTATE_LEFT")

        #ZERO ROTATE BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 20, 20)
        self.rotate_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotate_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotate_zero_button.SetLabel("ZERO ROTATE")

        #ROTATE RIGHT BUTTTON
        bmp = wx.Bitmap("./images/rotate_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_right_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(380+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_right_button.SetLabel("ROTATE_RIGHT")

        #SET ROTATION VALUE Z
        self.rotation_Z_Value_Text = wx.StaticText(self.panel, label=str(Rotation_3D_Z), pos=(360+trbX+46+80, 60+tbrY))
        font = self.rotation_Z_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_Z_Value_Text.SetFont(font)

        #ZERO TILT BUTTTON
        bmp = wx.Bitmap("./images/zero.bmp", wx.BITMAP_TYPE_BMP)
        bmp = scale_bitmap(bmp, 32, 32)
        self.tilt_zero_button = wx.BitmapButton(self.panel, id=wx.ID_ANY, bitmap=bmp, pos=(360+trbX+36+80, 88+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.tilt_zero_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.tilt_zero_button.SetLabel("ZERO TILT")

        #TILT STEPS INPUT
        self.tilt_step_input_box = wx.TextCtrl(self.panel, size=(40,20), pos=(360+trbX+38+80, 30+tbrY))
        self.tilt_step_input_box.SetLabel("1.0")

        #PAUSE VIDEO RENDERING
        if is_paused_rendering:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO RESUME RENDERING")
        else:
            self.pause_rendering = wx.Button(self.panel, label="PUSH TO PAUSE RENDERING")
        sizer.Add(self.pause_rendering, 0, wx.ALL | wx.EXPAND, 5)
        self.pause_rendering.Bind(wx.EVT_BUTTON, self.OnClicked)

        #CADENCE SLIDER
        self.cadence_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(Cadence_Schedule), minValue=1, maxValue=20, pos = (trbX+1000-340, tbrY+20), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cadence_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cadence_slider.SetTickFreq(1)
        self.cadence_slider.SetLabel("CADENCE")
        self.cadence_slider_Text = wx.StaticText(self.panel, label="Cadence Scale", pos=(trbX+1000-340, tbrY))

        #ControlNet Sliders
        ###############################################################
        #CONTROLNET WEIGHT
        self.control_net_weight_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_Weight), minValue=0, maxValue=200, pos = (trbX-40, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_weight_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_weight_slider.SetTickFreq(1)
        self.control_net_weight_slider.SetLabel("CN WEIGHT")
        self.control_net_weight_slider_Text = wx.StaticText(self.panel, label="ControlNet - Weight", pos=(trbX-40, tbrY+160))

        #CONTROLNET STARTING CONTROL STEP
        self.control_net_stepstart_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepStart), minValue=0, maxValue=100, pos = (trbX+300, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_stepstart_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_stepstart_slider.SetTickFreq(1)
        self.control_net_stepstart_slider.SetLabel("CN STEPSTART")
        self.control_net_stepstart_slider_Text = wx.StaticText(self.panel, label="ControlNet - Starting Control Step", pos=(trbX+300, tbrY+160))

        #CONTROLNET ENDING CONTROL STEP
        self.control_net_stepend_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_StepEnd), minValue=0, maxValue=100, pos = (trbX+640, tbrY+180), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_stepend_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_stepend_slider.SetTickFreq(1)
        self.control_net_stepend_slider.SetLabel("CN STEPEND")
        self.control_net_stepend_slider_Text = wx.StaticText(self.panel, label="ControlNet - Ending Control Step", pos=(trbX+640, tbrY+160))

        #CONTROLNET LOW THRESHOLD
        self.control_net_lowt_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_LowT), minValue=0, maxValue=255, pos = (trbX-40, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_lowt_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_lowt_slider.SetTickFreq(1)
        self.control_net_lowt_slider.SetLabel("CN LOWT")
        self.control_net_lowt_slider_Text = wx.StaticText(self.panel, label="ControlNet - Low Threshold", pos=(trbX-40, tbrY+240))

        #CONTROLNET HIGH THRESHOLD
        self.control_net_hight_slider = wx.Slider(self.panel, id=wx.ID_ANY, value=int(CN_HighT), minValue=0, maxValue=255, pos = (trbX+300, tbrY+260), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.control_net_hight_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.control_net_hight_slider.SetTickFreq(1)
        self.control_net_hight_slider.SetLabel("CN HIGHT")
        self.control_net_hight_slider_Text = wx.StaticText(self.panel, label="ControlNet - High Threshold", pos=(trbX+300, tbrY+240))

        self.Centre()
        self.Show()
        self.Fit()

        self.loadAllValues()
        #KEYBOARD INPUT EVNTG HANDLER
        self.off_grid_input_box.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.off_grid_input_box.SetFocus()

        self.Layout()
        self.Bind(wx.EVT_SIZING, self.OnResize)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.PanelClicked)

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
        self.shouldUseDeforumPromptScheduling_Checkbox.SetPosition((trbX + 600, 10))
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
        self.zoom_slider.SetPosition((110 + trbX, tbrY - 5))
        self.ZOOM_X_Text.SetPosition((170 + trbX, tbrY + 40))
        self.ZOOM_X_Text2.SetPosition((170 + trbX, tbrY + 60))
        self.ZOOM_X_Text3.SetPosition((170 + trbX, tbrY + 80))
        self.ZOOM_X_Text4.SetPosition((169 + trbX, tbrY + 100))
        self.fov_slider.SetPosition((190 + trbX, tbrY - 5))
        self.FOV_Text.SetPosition((250 + trbX, tbrY + 40))
        self.FOV_Text2.SetPosition((249 + trbX, tbrY + 60))
        self.FOV_Text3.SetPosition((250 + trbX, tbrY + 80))
        self.fov_lock_button.SetPosition((172 + trbX, tbrY - 5))
        self.fov_reverse_lock_button.SetPosition((172 + trbX, tbrY + 120))
        self.strength_schedule_slider.SetPosition((trbX - 25, tbrY - 50))
        self.step_schedule_Text.SetPosition((trbX - 25, tbrY - 70))
        self.should_use_deforumation_strength_checkbox.SetPosition((trbX + 160, tbrY - 66))
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
        self.replay_input_box_text.SetPosition((trbX+990, tbrY-130))
        self.replay_from_input_box.SetPosition((trbX+1030, tbrY-131))
        self.replay_to_input_box.SetPosition((trbX+1090, tbrY-131))
        self.replay_input_divider_box_text.SetPosition((trbX+1077, tbrY-130))
        self.replay_button.SetPosition((trbX + 1145, tbrY -135))
        self.fps_input_box_text.SetPosition((trbX+1180, tbrY-130))
        self.replay_fps_input_box.SetPosition((trbX+1200, tbrY-131))
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
            self.zoom_slider.SetValue(self.zoom_slider.GetValue()+1)
            self.zoom_slider.GetEventHandler().ProcessEvent(evt)
        elif event.GetKeyCode() == zoom_down_key:
            evt = wx.PyCommandEvent(wx.EVT_SCROLL.typeId)
            evt.SetEventObject(self.zoom_slider)
            evt.SetId(self.zoom_slider.GetId())
            self.zoom_slider.SetValue(self.zoom_slider.GetValue()-1)
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
        global is_paused_rendering
        global should_use_deforumation_strength
        global pan_left_key,pan_right_key,pan_up_key,pan_down_key,zoom_up_key,zoom_down_key
        global CN_Weight
        global CN_StepStart
        global CN_StepEnd
        global CN_LowT
        global CN_HighT

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
                is_paused_rendering = int(deforumFile.readline())
                if is_paused_rendering:
                    self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
                else:
                    self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")

                self.positive_prompt_input_ctrl.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_2.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_3.SetValue(deforumFile.readline())
                self.positive_prompt_input_ctrl_4.SetValue(deforumFile.readline())
                self.negative_prompt_input_ctrl.SetValue(deforumFile.readline())
                Strength_Scheduler = float(deforumFile.readline())
                self.strength_schedule_slider.SetValue(int(Strength_Scheduler*100))
                CFG_Scale = float(deforumFile.readline())
                self.cfg_schedule_slider.SetValue(int(CFG_Scale))
                STEP_Schedule = int(deforumFile.readline())
                self.sample_schedule_slider.SetValue(STEP_Schedule)
                FOV_Scale = float(deforumFile.readline())
                self.fov_slider.SetValue(int(FOV_Scale))
                Translation_X = float(deforumFile.readline())
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                Translation_Y = float(deforumFile.readline())
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                Translation_Z = float(deforumFile.readline())
                self.zoom_slider.SetValue(int(Translation_Z))
                Rotation_3D_X = float(deforumFile.readline())
                Rotation_3D_Y = float(deforumFile.readline())
                Rotation_3D_Z = float(deforumFile.readline())
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                self.rotation_Z_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Z))
                should_use_deforumation_strength = int(deforumFile.readline())
                self.should_use_deforumation_strength_checkbox.SetValue(int(should_use_deforumation_strength))
                self.pan_step_input_box.SetValue(deforumFile.readline())
                self.rotate_step_input_box.SetValue(deforumFile.readline())
                self.tilt_step_input_box.SetValue(deforumFile.readline())
                self.cadence_slider.SetValue(int(deforumFile.readline()))
                Cadence_Schedule = int(self.cadence_slider.GetValue())
                self.zero_pan_step_input_box.SetValue(deforumFile.readline())
                self.zero_rotate_step_input_box.SetValue(deforumFile.readline())
                CN_Weight = float(deforumFile.readline())
                self.control_net_weight_slider.SetValue(int(CN_Weight*100))
                CN_StepStart = float(deforumFile.readline())
                self.control_net_stepstart_slider.SetValue(int(CN_StepStart*100))
                CN_StepEnd = float(deforumFile.readline())
                self.control_net_stepend_slider.SetValue(int(CN_StepEnd*100))
                CN_LowT = int(deforumFile.readline())
                self.control_net_lowt_slider.SetValue(CN_LowT)
                CN_HighT = int(deforumFile.readline())
                self.control_net_hight_slider.SetValue(CN_HighT)
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
            self.writeValue("rotation_z", Rotation_3D_Z)
            self.writeValue("should_use_deforumation_strength", int(should_use_deforumation_strength))
            self.writeValue("cadence", int(Cadence_Schedule))
            self.writeValue("cn_weight", float(CN_Weight))
            self.writeValue("cn_stepstart", float(CN_StepStart))
            self.writeValue("cn_stepend", float(CN_StepEnd))
            self.writeValue("cn_lowt", float(CN_LowT))
            self.writeValue("cn_hight", float(CN_HighT))

    def writeValue(self, param, value):
        checkerrorConnecting = True
        while checkerrorConnecting:
            try:
                asyncio.run(sendAsync([1, param, value]))
                checkerrorConnecting = False
            except Exception as e:
                print("Deforumation Mediator Error:" + str(e))
                print("The XDeforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...writing:"+str(param))
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
                print("The XDeforumation Mediator, is probably not connected (waiting 5 seconds, before trying to reconnect...)...ererror:reading:"+str(param))
                time.sleep(5)

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
        #print("WRITING:" + str(should_use_deforumation_strength))
        deforumFile.write(str(int(should_use_deforumation_strength))+"\n")
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
        deforumFile.write(str(CN_HighT))
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
            for index in range(0, len(positive_lines), 2):
                param = positive_lines[index].strip('\n').replace(" ", "").split(',')
                frame_index = param[0]
                type = param[1]
                if forwardrewindType == "R" and int(p_current_frame-1) >= int(frame_index):
                    positive_promptToShow = positive_lines[index + 1]
                    negative_promptToShow = negative_lines[index + 1]
                    returnFrame = frame_index
                elif forwardrewindType == "F" and int(p_current_frame+1) <= int(frame_index):
                    positive_promptToShow = positive_lines[index + 1]
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
            for index in range(0, len(old_lines), 2):
                if not didWriteNewPrompt:
                    param = old_lines[index].strip('\n').replace(" ", "").split(',')
                    frame_index = param[0]
                    type = param[1]
                    if int(current_frame) == int(frame_index):
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
                    elif int(current_frame) < int(frame_index):
                        new_lines[0] = str(current_frame) + "," + type
                        if promptType == "P":
                            new_lines[1] = self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        else:
                            new_lines[1] = self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')
                            if new_lines[1] == "":
                                new_lines[1] = " "
                        promptFile.write(str(new_lines[0]) + "\n")
                        promptFile.write(str(new_lines[1]) + "\n")
                        promptFile.write(frame_index + "," + type + "\n")
                        promptFile.write(old_lines[index + 1])
                        didWriteNewPrompt = True
                    else:
                        promptFile.write(old_lines[index])
                        promptFile.write(old_lines[index + 1])

                else:
                    promptFile.write(old_lines[index])
                    promptFile.write(old_lines[index + 1])
            if not didWriteNewPrompt:
                new_lines[0] = str(current_frame) + "," + promptType
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
    def ZeroStepper(self, parameter_value, frame_steps):
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
        if zero_frame_steps == 0:
            return
        now_frame = int(readValue("start_frame"))
        zero_frame_steps_n_frame = 0
        if parameter_value == "translation_x":
            stepit_pan = 1
            if Translation_X != 0:
                zero_frame_steps_n_frame = float(Translation_X / zero_frame_steps)
            if Translation_X < 0:
                is_negative = 1
        elif parameter_value == "translation_y":
            stepit_pan = 1
            if Translation_Y != 0:
                zero_frame_steps_n_frame = float(Translation_Y / zero_frame_steps)
                if Translation_Y < 0:
                    is_negative = 1
        elif parameter_value == "rotation_x":
            stepit_rotate = 1
            if Rotation_3D_X != 0:
                zero_frame_steps_n_frame = float(Rotation_3D_X / zero_frame_steps)
                if Rotation_3D_X < 0:
                    is_negative = 1
        elif parameter_value == "rotation_y":
            stepit_rotate = 1
            if Rotation_3D_Y != 0:
                zero_frame_steps_n_frame = float(Rotation_3D_Y / zero_frame_steps)
                if Rotation_3D_Y < 0:
                    is_negative = 1

        #print("Stepper thread activated")
        while (stepit_pan or stepit_rotate) and zero_frame_steps_n_frame != 0:
            current_step_frame = int(readValue("start_frame"))
            if (int(current_step_frame) > int(now_frame)):
                now_frame = current_step_frame
                if parameter_value == "translation_x":
                    Translation_X = Translation_X - float(zero_frame_steps_n_frame)
                elif parameter_value == "translation_y":
                    Translation_Y = Translation_Y - float(zero_frame_steps_n_frame)
                elif parameter_value == "rotation_x":
                    Rotation_3D_X = Rotation_3D_X - float(zero_frame_steps_n_frame)
                elif parameter_value == "rotation_y":
                    Rotation_3D_Y = Rotation_3D_Y - float(zero_frame_steps_n_frame)

                if parameter_value == "translation_x":
                    if is_negative:
                        if Translation_X >= 0:
                            Translation_X = 0
                            self.writeValue(parameter_value, Translation_X)
                            self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                            break
                    elif Translation_X <= 0:
                        Translation_X = 0
                        self.writeValue(parameter_value, Translation_X)
                        self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                        break
                elif parameter_value == "translation_y":
                    if is_negative:
                        if Translation_Y >= 0:
                            Translation_Y = 0
                            self.writeValue(parameter_value, Translation_Y)
                            self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                            break
                    elif Translation_Y <= 0:
                        Translation_Y = 0
                        self.writeValue(parameter_value, Translation_Y)
                        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                        break
                elif parameter_value == "rotation_x":
                    if is_negative:
                        if Rotation_3D_X >= 0:
                            Rotation_3D_X = 0
                            self.writeValue(parameter_value, Rotation_3D_X)
                            self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                            break
                    elif Rotation_3D_X <= 0:
                        Rotation_3D_X = 0
                        self.writeValue(parameter_value, Rotation_3D_X)
                        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                        break
                elif parameter_value == "rotation_y":
                    if is_negative:
                        if Rotation_3D_Y >= 0:
                            Rotation_3D_Y = 0
                            self.writeValue(parameter_value, Rotation_3D_Y)
                            self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                            break
                    elif Rotation_3D_Y <= 0:
                        Rotation_3D_Y = 0
                        self.writeValue(parameter_value, Rotation_3D_Y)
                        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                        break

            if parameter_value == "translation_x":
                self.writeValue(parameter_value, Translation_X)
                self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
                print("Translation_X:" + str(Translation_X))
            elif parameter_value == "translation_y":
                self.writeValue(parameter_value, Translation_Y)
                self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
                print("Translation_Y:" + str(Translation_Y))
            elif parameter_value == "rotation_x":
                self.writeValue(parameter_value, Rotation_3D_X)
                self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' % Rotation_3D_X))
                print("Rotaion_X:" + str(Rotation_3D_X))
            elif parameter_value == "rotation_y":
                self.writeValue(parameter_value, Rotation_3D_Y)
                self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
                print("Rotaion_Y:" + str(Rotation_3D_Y))
            time.sleep(0.25)
        self.writeAllValues()
        zero_pan_active = False
        zero_rotate_active = False
        print("Ending stepper thread")
#"translation_x"
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
        global should_stay_on_top
        global should_use_deforum_prompt_scheduling
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
        btn = event.GetEventObject().GetLabel()
        #print("Label of pressed button = ", str(event.GetId()))
        if btn == "PUSH TO PAUSE RENDERING":
            self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            is_paused_rendering = True
            self.writeValue("is_paused_rendering", is_paused_rendering)
        elif btn == "PUSH TO RESUME RENDERING":
            self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            self.loadCurrentPrompt("P", current_frame, 1)
            self.loadCurrentPrompt("N", current_frame, 1)
            is_paused_rendering = False
            self.writeValue("is_paused_rendering", is_paused_rendering)
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
        elif btn == "Use Deforum prompt scheduling":
            if should_use_deforum_prompt_scheduling == 0:
                should_use_deforum_prompt_scheduling = 1
                self.writeValue("should_use_deforum_prompt_scheduling", should_use_deforum_prompt_scheduling)
            else:
                should_use_deforum_prompt_scheduling = 0
                self.writeValue("should_use_deforum_prompt_scheduling", should_use_deforum_prompt_scheduling)
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
            Translation_X = Translation_X - float(self.pan_step_input_box.GetValue())
            self.writeValue("translation_x", Translation_X)
        elif btn == "PAN_RIGHT":
            Translation_X = Translation_X + float(self.pan_step_input_box.GetValue())
            self.writeValue("translation_x", Translation_X)
        elif btn == "PAN_UP":
            Translation_Y = Translation_Y + float(self.pan_step_input_box.GetValue())
            self.writeValue("translation_y", Translation_Y)
        elif btn == "PAN_DOWN":
            Translation_Y = Translation_Y - float(self.pan_step_input_box.GetValue())
            self.writeValue("translation_y", Translation_Y)
        elif btn == "ZERO PAN":
            if not zero_pan_active:
                #Start a ZERO step thread.
                frame_steps = int(self.zero_pan_step_input_box.GetValue())
                if frame_steps == 0:
                    Translation_X = 0
                    Translation_Y = 0
                    self.writeValue("translation_x", Translation_X)
                    self.writeValue("translation_y", Translation_Y)
                elif Translation_X == 0 and Translation_Y == 0:
                    zero_pan_active = False
                else:
                    zero_pan_active = True
                    if Translation_X != 0:
                        self.zero_step_thread_x = threading.Thread(target=self.ZeroStepper, args=("translation_x", frame_steps))
                        self.zero_step_thread_x.daemon = True
                        self.zero_step_thread_x.start()
                    if Translation_Y != 0:
                        self.zero_step_thread_y = threading.Thread(target=self.ZeroStepper, args=("translation_y", frame_steps))
                        self.zero_step_thread_y.daemon = True
                        self.zero_step_thread_y.start()
            else:
                stepit_pan = 0
                zero_pan_active = False

        elif btn == "ZOOM":
            Translation_Z = self.zoom_slider.GetValue()
            self.writeValue("translation_z", Translation_Z)
            if is_fov_locked:
                if is_reverse_fov_locked:
                    FOV_Scale = 70+(Translation_Z * -5)
                else:
                    FOV_Scale = 70 + (Translation_Z * 5)
                self.fov_slider.SetValue(FOV_Scale)
                self.writeValue("fov", FOV_Scale)

        elif btn == "STRENGTH SCHEDULE":
            Strength_Scheduler = float(self.strength_schedule_slider.GetValue())*0.01
            self.writeValue("strength", Strength_Scheduler)
        elif event.GetId() == 3: #Seed Input Box
            seedValue = int(self.seed_input_box.GetValue())
            #print("SeedValue:"+str(seedValue))
            self.writeValue("seed", seedValue)
        elif btn == "LOOK_LEFT":
            Rotation_3D_Y = Rotation_3D_Y - float(self.rotate_step_input_box.GetValue())
            self.writeValue("rotation_y", Rotation_3D_Y)
        elif btn == "LOOK_RIGHT":
            Rotation_3D_Y = Rotation_3D_Y + float(self.rotate_step_input_box.GetValue())
            self.writeValue("rotation_y", Rotation_3D_Y)
        elif btn == "LOOK_UP":
            Rotation_3D_X = Rotation_3D_X + float(self.rotate_step_input_box.GetValue())
            self.writeValue("rotation_x", Rotation_3D_X)
        elif btn == "LOOK_DOWN":
            Rotation_3D_X = Rotation_3D_X - float(self.rotate_step_input_box.GetValue())
            self.writeValue("rotation_x", Rotation_3D_X)
        elif btn == "ZERO ROTATE":
            #Rotation_3D_X = 0
            #Rotation_3D_Y = 0
            #self.writeValue("rotation_x", Rotation_3D_X)
            #self.writeValue("rotation_y", Rotation_3D_Y)

            if not zero_rotate_active:
                #Start a ZERO step thread.
                frame_steps = int(self.zero_rotate_step_input_box.GetValue())
                if frame_steps == 0:
                    Rotation_3D_X = 0
                    Rotation_3D_Y = 0
                    self.writeValue("rotation_x", Rotation_3D_X)
                    self.writeValue("rotation_y", Rotation_3D_Y)
                elif Rotation_3D_X == 0 and Rotation_3D_Y == 0:
                    zero_rotate_active = False
                else:
                    zero_rotate_active = True
                    if Rotation_3D_X != 0:
                        self.zero_rotate_thread_x = threading.Thread(target=self.ZeroStepper, args=("rotation_x", frame_steps))
                        self.zero_rotate_thread_x.daemon = True
                        self.zero_rotate_thread_x.start()
                    if Rotation_3D_Y != 0:
                        self.zero_rotate_thread_y = threading.Thread(target=self.ZeroStepper, args=("rotation_y", frame_steps))
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
            maxBackTrack = 20
            #print(str("Trying to load:"+imagePath))
            while not os.path.isfile(imagePath):
                if (current_render_frame == 0):
                    break
                current_render_frame = int(current_render_frame) - 1
                imagePath = get_current_image_path()
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
        elif btn == "USE DEFORUMATION":
            #print("CURRENT IS:"+str(should_use_deforumation_strength))
            if should_use_deforumation_strength == 0:
                self.writeValue("should_use_deforumation_strength", 1)
                should_use_deforumation_strength = 1
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
            else:
                self.readValue("should_use_deforumation_strength")
                should_use_deforumation_strength = 0
                #print("NOW IT IS:"+str(should_use_deforumation_strength))
        elif btn == "REPLAY":
            if isReplaying == 0:
                #print("Starting Replay")
                replayFrom = int(self.replay_from_input_box.GetValue())
                replayTo = int(self.replay_to_input_box.GetValue())
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
                current_frame = current_frame.zfill(9)
                imagePath = outdir + "/" + resume_timestring + "_" + current_frame + ".png"
                imagePath = get_current_image_path()
                maxBackTrack = 20
                while not os.path.isfile(imagePath):
                    if (current_frame == 0):
                        break
                    current_frame = str(int(current_frame) - 1)
                    current_frame = current_frame.zfill(9)
                    imagePath = outdir + "/" + resume_timestring + "_" + current_frame + ".png"
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
                        self.framer.SetSize(imgWidth + 18, imgHeight + 40)
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
        self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X))
        self.rotation_Z_Value_Text.SetLabel(str('%.2f' %Rotation_3D_Z))

        self.writeAllValues()

    def OnExit(self, event):
        if self.framer != None:
            self.framer.Hide()
            self.framer.Close()
            self.framer = None
        print("CLOSING!")
        wx.Exit()

if __name__ == '__main__':
    #subprocess.run(["python", "mediator.py"])
    #print("SLEEP")
    #time.sleep(5)
    blaha = random.randint(0, 2**32 - 1)
    app = wx.App()
    Mywin(None, 'Deforumation @ Rakile & Lainol, 2023')
    app.MainLoop()
