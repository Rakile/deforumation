import wx
import asyncio
import websockets
import os
import time
import keyboard
import pickle
from threading import *
from pathlib import Path
import wx.lib.newevent
#import subprocess

deforumationSettingsPath="./deforumation_settings.txt"
deforumationSettingsPath_Keys = "./deforum_settings_keys.txt"
deforumationPromptsPath ="./prompts/"
USE_BUFFERED_DC = True
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
tbrY = 500
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
#KEYBOARD KEYS
pan_left_key = 0
pan_right_key = 0
pan_up_key = 0
pan_down_key = 0
zoom_down_key = 0
zoom_up_key = 0
async def sendAsync(value):
    async with websockets.connect("ws://localhost:8765") as websocket:
        await websocket.send(pickle.dumps(value))
        message = await websocket.recv()
        #print(str(message))
        return message


class render_window(wx.Frame):
    def __init__(self, parent, title):
        global render_frame_window_is_open
        render_frame_window_is_open = True
        super(render_window, self).__init__(parent, title=title, size=(100, 100))
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        panel.SetDoubleBuffered(True)
        self.bitmap = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
    def OnErase(self, evt):
        evt.Skip()
    def OnExit(self, event):
        global should_render_live
        global render_frame_window_is_open
        #print("CLOSING!")
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
        super(Mywin, self).__init__(parent, title=title, size=(1400, 700))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.framer = None
        #self.framer = render_window(None, 'Rendering Image')
        #wx.EVT_PAINT(self, self.OnPaint)
        #wx.EVT_SIZE(self, self.OnSize)
        #Timer Event
        ##############################################################################################################################################################################
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.updateRender, self.timer)
        self.timer.Start(200)

        #Positive Prompt
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.positivePromtText = wx.StaticText(panel, label="Positive prompt:")
        font = self.positivePromtText.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.positivePromtText.SetFont(font)
        sizer.Add(self.positivePromtText, 0, wx.ALL | wx.EXPAND, 5)
        self.positive_prompt_input_ctrl = wx.TextCtrl(panel,style=wx.TE_MULTILINE, size=(-1,100))
        sizer.Add(self.positive_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        if os.path.isfile(deforumationSettingsPath):
            promptfileRead = open(deforumationSettingsPath, 'r')
            self.positive_prompt_input_ctrl.SetValue(promptfileRead.readline())
        #Negative Prompt
        self.negativePromtText = wx.StaticText(panel, label="Negative prompt:")
        font = self.negativePromtText.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.negativePromtText.SetFont(font)
        sizer.Add(self.negativePromtText, 0, wx.ALL | wx.EXPAND, 5)
        self.negative_prompt_input_ctrl = wx.TextCtrl(panel,style=wx.TE_MULTILINE, size=(-1,100))
        sizer.Add(self.negative_prompt_input_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        if os.path.isfile(deforumationSettingsPath):
            self.negative_prompt_input_ctrl.SetValue(promptfileRead.readline())
            promptfileRead.close()

        panel.SetSizer(sizer)
        #SHOW LIVE RENDER CHECK-BOX
        self.live_render_checkbox = wx.CheckBox(panel, label="LIVE RENDER", pos=(trbX+1130, tbrY-110))
        self.live_render_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #OFF GRID BUTTON FOR KEYBOARD INPUT
        #self.off_grid_input_box = wx.Button(panel, label="", pos=(-1000, -1000))
        self.off_grid_input_box = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(1, 1), pos=(-100,-100))
        #self.off_grid_button.Bind(wx.EVT_BUTTON, self.OnClicked)

        #SHOW CURRENT IMAGE, BUTTON
        self.show_current_image = wx.Button(panel, label="Show current image", pos=(trbX+992, tbrY-110))
        self.show_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)
        #REWIND BUTTTON
        bmp = wx.Bitmap(".\\images\\left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1000, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_button.SetLabel("REWIND")
        #REWIND CLOSEST BUTTTON
        bmp = wx.Bitmap(".\\images\\rewind_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_closest_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+970, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_closest_button.SetLabel("REWIND_CLOSEST")
        #SET CURRENT FRAME INPUT BOX
        self.frame_step_input_box = wx.TextCtrl(panel, 2, size=(48,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1032, tbrY-74))
        self.frame_step_input_box.SetLabel("")
        self.frame_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=2)
        #FORWARD BUTTTON
        bmp = wx.Bitmap(".\\images\\right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1080, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_button.SetLabel("FORWARD")
        #FORWARD CLOSEST BUTTTON
        bmp = wx.Bitmap(".\\images\\forward_closest.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_closest_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1110, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_closest_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_closest_button.SetLabel("FORWARD_CLOSEST")
        #SET CURRENT IMAGE, BUTTON
        self.set_current_image = wx.Button(panel, label="Set current image", pos=(trbX+998, tbrY-40))
        self.set_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)

        #SHOW AN IMAGE
        #self.img = wx.EmptyImage(240,240)
        #self.img = wx.Image("E:\\Tools\\stable-diffusion-webui\\outputs\\img2img-images\\Deforum_20230330002842\\20230330002842_000000082.png", wx.BITMAP_TYPE_ANY)
        #self.imageCtrl = wx.StaticBitmap(panel, wx.ID_ANY, wx.BitmapFromImage(img))
        #self.bitmap = wx.StaticBitmap(panel, -1, self.img, pos=(trbX+700, tbrY-120))
        self.bitmap = None

        #SAVE PROMPTS BUTTON
        self.update_prompts = wx.Button(panel, label="SAVE PROMPTS")
        sizer.Add(self.update_prompts, 0, wx.ALL | wx.EXPAND, 5)
        self.update_prompts.Bind(wx.EVT_BUTTON, self.OnClicked)

        #PAN STEPS INPUT
        self.pan_step_input_box = wx.TextCtrl(panel, size=(40,20), pos=(trbX-15, 30+tbrY))
        self.pan_step_input_box.SetLabel("1.0")

        #LEFT PAN BUTTTON
        bmp = wx.Bitmap(".\\images\\left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_left_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(5+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_left_button.SetLabel("PAN_LEFT")

        #SET PAN VALUE X
        self.pan_X_Value_Text = wx.StaticText(panel, label=str(Translation_X), pos=(trbX-26, 55+tbrY+5))
        font = self.pan_X_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_X_Value_Text.SetFont(font)

        #SET PAN VALUE Y
        self.pan_Y_Value_Text = wx.StaticText(panel, label=str(Translation_Y), pos=(40+trbX, 5+tbrY))
        font = self.pan_Y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.pan_Y_Value_Text.SetFont(font)

        #UPP PAN BUTTTON
        bmp = wx.Bitmap(".\\images\\upp_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_upp_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 25+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_upp_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_upp_button.SetLabel("PAN_UP")

        #RIGHT PAN BUTTTON
        bmp = wx.Bitmap(".\\images\\right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_x_right_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(65+trbX, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_x_right_button.SetLabel("PAN_RIGHT")
        #DOWN PAN BUTTTON
        bmp = wx.Bitmap(".\\images\\down_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.transform_y_down_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(35+trbX, 85+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.transform_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.transform_y_down_button.SetLabel("PAN_DOWN")

        #ZOOM SLIDER
        self.zoom_slider = wx.Slider(panel, id=wx.ID_ANY, value=0, minValue=-10, maxValue=10, pos = (110+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE )
        self.zoom_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.zoom_slider.SetTickFreq(1)
        self.zoom_slider.SetLabel("ZOOM")
        self.ZOOM_X_Text = wx.StaticText(panel, label="Z", pos=(170+trbX, tbrY+40))
        self.ZOOM_X_Text2 = wx.StaticText(panel, label="O", pos=(170+trbX, tbrY+60))
        self.ZOOM_X_Text3 = wx.StaticText(panel, label="O", pos=(170+trbX, tbrY+80))
        self.ZOOM_X_Text4 = wx.StaticText(panel, label="M", pos=(169+trbX, tbrY+100))

        #FOV SLIDER
        self.fov_slider = wx.Slider(panel, id=wx.ID_ANY, value=70, minValue=20, maxValue=120, pos = (190+trbX, tbrY-5), size = (40, 150), style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.fov_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.fov_slider.SetTickFreq(1)
        self.fov_slider.SetLabel("FOV")
        self.FOV_Text = wx.StaticText(panel, label="F", pos=(250+trbX, tbrY+40))
        self.FOV_Text2 = wx.StaticText(panel, label="O", pos=(249+trbX, tbrY+60))
        self.FOV_Text3 = wx.StaticText(panel, label="V", pos=(250+trbX, tbrY+80))

        #LOCK FOV TO ZOOM BUTTON
        bmp = wx.Bitmap(".\\images\\lock_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_lock_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY-5), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_lock_button.SetLabel("LOCK FOV")

        #REVERSE FOV TO ZOOM BUTTON
        bmp = wx.Bitmap(".\\images\\reverse_fov_off.bmp", wx.BITMAP_TYPE_BMP)
        self.fov_reverse_lock_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(172+trbX, tbrY+120), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.fov_reverse_lock_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.fov_reverse_lock_button.SetLabel("REVERSE FOV")

        #STRENGTH SCHEDULE SLIDER
        self.strength_schedule_slider = wx.Slider(panel, id=wx.ID_ANY, value=65, minValue=1, maxValue=100, pos = (trbX-25, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.strength_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.strength_schedule_slider.SetTickFreq(1)
        self.strength_schedule_slider.SetLabel("STRENGTH SCHEDULE")
        self.strength_schedule_Text = wx.StaticText(panel, label="Strength Value (divided by 100)", pos=(trbX-25, tbrY-70))

        #SHOULD USE DEFORUMATION STRENGTH VALUES? CHECK-BOX
        self.should_use_deforumation_strength_checkbox = wx.CheckBox(panel, label="USE DEFORUMATION", pos=(trbX+160, tbrY-66))
        self.should_use_deforumation_strength_checkbox.Bind(wx.EVT_CHECKBOX, self.OnClicked)

        #SAMPLE STEP SLIDER
        self.sample_schedule_slider = wx.Slider(panel, id=wx.ID_ANY, value=25, minValue=1, maxValue=200, pos = (trbX-25, tbrY-50-70), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.sample_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.sample_schedule_slider.SetTickFreq(1)
        self.sample_schedule_slider.SetLabel("STEPS")
        self.strength_schedule_Text = wx.StaticText(panel, label="Steps", pos=(trbX-25, tbrY-70-64))

        #SEED INPUT BOX
        self.seed_schedule_Text = wx.StaticText(panel, label="Seed", pos=(trbX+340, tbrY-50-80))
        self.seed_input_box = wx.TextCtrl(panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+340, tbrY-50-60))
        self.seed_input_box.SetLabel("-1")
        self.seed_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=3)



        #CFG SCHEDULE SLIDER
        self.cfg_schedule_slider = wx.Slider(panel, id=wx.ID_ANY, value=7, minValue=1, maxValue=30, pos = (trbX+340, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cfg_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cfg_schedule_slider.SetTickFreq(1)
        self.cfg_schedule_slider.SetLabel("CFG SCALE")
        self.CFG_scale_Text = wx.StaticText(panel, label="CFG Scale", pos=(trbX+340, tbrY-70))


        #LOOK LEFT BUTTTON
        bmp = wx.Bitmap(".\\images\\look_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_left_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_left_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_left_button.SetLabel("LOOK_LEFT")

        #SET ROTATION VALUE X
        self.rotation_3d_x_Value_Text = wx.StaticText(panel, label=str(Rotation_3D_X), pos=(240+trbX-30+80, 55+tbrY+5))
        font = self.rotation_3d_x_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_x_Value_Text.SetFont(font)

        #ROTATE STEPS INPUT
        self.rotate_step_input_box = wx.TextCtrl(panel, size=(40,20), pos=(240+trbX-15+80, 30+tbrY))
        self.rotate_step_input_box.SetLabel("1.0")

        #LOOK UPP BUTTTON
        bmp = wx.Bitmap(".\\images\\look_upp.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_up_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY-30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_up_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_up_button.SetLabel("LOOK_UP")

        #SET ROTATION VALUE Y
        self.rotation_3d_y_Value_Text = wx.StaticText(panel, label=str(Rotation_3D_Y), pos=(240+trbX+35+80, 55+tbrY-48))
        font = self.rotation_3d_y_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_3d_y_Value_Text.SetFont(font)

        #LOOK RIGHT BUTTTON
        bmp = wx.Bitmap(".\\images\\look_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_x_right_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+57+80, 55+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_x_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_x_right_button.SetLabel("LOOK_RIGHT")

        #LOOK UPP BUTTTON
        bmp = wx.Bitmap(".\\images\\look_down.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_y_down_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(240+trbX+30+80, 55+tbrY+30), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_y_down_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_y_down_button.SetLabel("LOOK_DOWN")

        #ROTATE LEFT BUTTTON
        bmp = wx.Bitmap(".\\images\\rotate_left.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_right_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(300+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_right_button.SetLabel("ROTATE_LEFT")

        #ROTATE RIGHT BUTTTON
        bmp = wx.Bitmap(".\\images\\rotate_right.bmp", wx.BITMAP_TYPE_BMP)
        self.rotation_3d_z_right_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(380+trbX+57+80, 50+tbrY), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rotation_3d_z_right_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rotation_3d_z_right_button.SetLabel("ROTATE_RIGHT")

        #SET ROTATION VALUE Z
        self.rotation_Z_Value_Text = wx.StaticText(panel, label=str(Rotation_3D_Z), pos=(360+trbX+46+80, 60+tbrY))
        font = self.rotation_Z_Value_Text.GetFont()
        font.PointSize += 1
        font = font.Bold()
        self.rotation_Z_Value_Text.SetFont(font)

        #TILT STEPS INPUT
        self.tilt_step_input_box = wx.TextCtrl(panel, size=(40,20), pos=(360+trbX+38+80, 30+tbrY))
        self.tilt_step_input_box.SetLabel("1.0")

        #PAUSE VIDEO RENDERING
        if is_paused_rendering:
            self.pause_rendering = wx.Button(panel, label="PUSH TO RESUME RENDERING")
        else:
            self.pause_rendering = wx.Button(panel, label="PUSH TO PAUSE RENDERING")
        sizer.Add(self.pause_rendering, 0, wx.ALL | wx.EXPAND, 5)
        self.pause_rendering.Bind(wx.EVT_BUTTON, self.OnClicked)

        self.Centre()
        self.Show()
        self.Fit()

        self.loadAllValues()
        #KEYBOARD INPUT EVNTG HANDLER
        self.off_grid_input_box.Bind(wx.EVT_KEY_DOWN, self.KeyDown)
        self.off_grid_input_box.SetFocus()
        panel.Bind(wx.EVT_LEFT_DOWN, self.PanelClicked)

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
        global is_paused_rendering
        global should_use_deforumation_strength
        global pan_left_key,pan_right_key,pan_up_key,pan_down_key,zoom_up_key,zoom_down_key
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
            deforumFile = open(deforumationSettingsPath, 'r')
            is_paused_rendering = int(deforumFile.readline())
            self.positive_prompt_input_ctrl.SetValue(deforumFile.readline())
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
            asyncio.run(sendAsync([1, "is_paused_rendering", is_paused_rendering]))
            asyncio.run(sendAsync([1, "positive_prompt", self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n"]))
            asyncio.run(sendAsync([1, "negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n"]))
            asyncio.run(sendAsync([1, "strength", Strength_Scheduler]))
            asyncio.run(sendAsync([1, "cfg", CFG_Scale]))
            asyncio.run(sendAsync([1, "steps", STEP_Schedule]))
            asyncio.run(sendAsync([1, "fov", FOV_Scale]))
            asyncio.run(sendAsync([1, "translation_x", Translation_X]))
            asyncio.run(sendAsync([1, "translation_y", Translation_Y]))
            asyncio.run(sendAsync([1, "translation_z", Translation_Z]))
            asyncio.run(sendAsync([1, "rotation_x", Rotation_3D_X]))
            asyncio.run(sendAsync([1, "rotation_y", Rotation_3D_Y]))
            asyncio.run(sendAsync([1, "rotation_z", Rotation_3D_Z]))
            asyncio.run(sendAsync([1, "rotation_z", Rotation_3D_Z]))
            asyncio.run(sendAsync([1, "should_use_deforumation_strength", int(should_use_deforumation_strength)]))

    def writeAllValues(self):
        try:
            asyncio.run(sendAsync([1, "is_paused_rendering", is_paused_rendering]))
            asyncio.run(sendAsync([1, "positive_prompt", self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n"]))
            asyncio.run(sendAsync([1, "negative_prompt", self.negative_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n"]))
            asyncio.run(sendAsync([1, "strength", Strength_Scheduler]))
            asyncio.run(sendAsync([1, "cfg", CFG_Scale]))
            asyncio.run(sendAsync([1, "steps", STEP_Schedule]))
            asyncio.run(sendAsync([1, "fov", FOV_Scale]))
            asyncio.run(sendAsync([1, "translation_x", Translation_X]))
            asyncio.run(sendAsync([1, "translation_y", Translation_Y]))
            asyncio.run(sendAsync([1, "translation_z", Translation_Z]))
            asyncio.run(sendAsync([1, "rotation_x", Rotation_3D_X]))
            asyncio.run(sendAsync([1, "rotation_y", Rotation_3D_Y]))
            asyncio.run(sendAsync([1, "rotation_z", Rotation_3D_Z]))
            asyncio.run(sendAsync([1, "rotation_z", Rotation_3D_Z]))
        except Exception as e:
            print(e)
        deforumFile = open(deforumationSettingsPath, 'w')
        deforumFile.write(str(int(is_paused_rendering))+"\n")
        deforumFile.write(self.positive_prompt_input_ctrl.GetValue().strip().replace('\n', '')+"\n")
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

        deforumFile.close()

    def getClosestPrompt(self, forwardrewindType, p_current_frame):
        resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
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

    def loadCurrentPrompt(self, promptType):
        resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
        if os.path.isfile(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt"):
            promptFile = open(deforumationPromptsPath + resume_timestring + "_" + promptType + ".txt", 'r')
            old_lines = promptFile.readlines()
            promptFile.close()
            promptToShow =  self.positive_prompt_input_ctrl.GetValue()
            for index in range(0, len(old_lines), 2):
                param = old_lines[index].strip('\n').replace(" ", "").split(',')
                frame_index = param[0]
                type = param[1]
                if int(current_frame) >= int(frame_index):
                    promptToShow = old_lines[index+1]
                else:
                    break
            if promptType == "P":
                self.positive_prompt_input_ctrl.SetValue(str(promptToShow))
            else:
                self.negative_prompt_input_ctrl.SetValue(str(promptToShow))


    def saveCurrentPrompt(self, promptType):
        resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
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
        btn = event.GetEventObject().GetLabel()
        #print("Label of pressed button = ", str(event.GetId()))
        if btn == "PUSH TO PAUSE RENDERING":
            self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            is_paused_rendering = True
        elif btn == "PUSH TO RESUME RENDERING":
            self.pause_rendering.SetLabel("PUSH TO PAUSE RENDERING")
            is_paused_rendering = False
        elif btn == "SAVE PROMPTS":
            self.saveCurrentPrompt("P")
            self.saveCurrentPrompt("N")
        elif btn == "PAN_LEFT":
            Translation_X = Translation_X - float(self.pan_step_input_box.GetValue())
        elif btn == "PAN_RIGHT":
            Translation_X = Translation_X + float(self.pan_step_input_box.GetValue())
        elif btn == "PAN_UP":
            Translation_Y = Translation_Y + float(self.pan_step_input_box.GetValue())
        elif btn == "PAN_DOWN":
            Translation_Y = Translation_Y - float(self.pan_step_input_box.GetValue())
        elif btn == "ZOOM":
            Translation_Z = self.zoom_slider.GetValue()
            if is_fov_locked:
                if is_reverse_fov_locked:
                    FOV_Scale = 70+(Translation_Z * -5)
                else:
                    FOV_Scale = 70 + (Translation_Z * 5)
                self.fov_slider.SetValue(FOV_Scale)

        elif btn == "STRENGTH SCHEDULE":
            Strength_Scheduler = float(self.strength_schedule_slider.GetValue())*0.01
        elif event.GetId() == 3: #Seed Input Box
            seedValue = int(self.seed_input_box.GetValue())
            print("SeedValue:"+str(seedValue))
            asyncio.run(sendAsync([1, "seed", seedValue])) #This is handled here, because it is not suitable to be written every time by writeAllValues()
        elif btn == "LOOK_LEFT":
            Rotation_3D_Y = Rotation_3D_Y - float(self.rotate_step_input_box.GetValue())
        elif btn == "LOOK_RIGHT":
            Rotation_3D_Y = Rotation_3D_Y + float(self.rotate_step_input_box.GetValue())
        elif btn == "LOOK_UP":
            Rotation_3D_X = Rotation_3D_X + float(self.rotate_step_input_box.GetValue())
        elif btn == "LOOK_DOWN":
            Rotation_3D_X = Rotation_3D_X - float(self.rotate_step_input_box.GetValue())
        elif btn == "ROTATE_LEFT":
            Rotation_3D_Z = Rotation_3D_Z + float(self.tilt_step_input_box.GetValue())
        elif btn == "ROTATE_RIGHT":
            Rotation_3D_Z = Rotation_3D_Z - float(self.tilt_step_input_box.GetValue())
        elif btn == "CFG SCALE":
            CFG_Scale = float(self.cfg_schedule_slider.GetValue())
        elif btn == "FOV":
            FOV_Scale = float(self.fov_slider.GetValue())
        elif btn == "LOCK FOV":
            if is_fov_locked:
                is_fov_locked = False
                self.fov_lock_button.SetBitmap(wx.Bitmap(".\\images\\lock_off.bmp"))
            else:
                is_fov_locked = True
                self.fov_lock_button.SetBitmap(wx.Bitmap(".\\images\\lock_on.bmp"))
                if is_reverse_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*-5))
                    self.fov_slider.SetValue(int(FOV_Scale))
                else:
                    FOV_Scale = float(70+(Translation_Z*5))
                    self.fov_slider.SetValue(int(FOV_Scale))
        elif btn == "REVERSE FOV":
            if is_reverse_fov_locked:
                is_reverse_fov_locked = False
                self.fov_reverse_lock_button.SetBitmap(wx.Bitmap(".\\images\\reverse_fov_off.bmp"))
                if is_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*5))
                    self.fov_slider.SetValue(int(FOV_Scale))
            else:
                is_reverse_fov_locked = True
                self.fov_reverse_lock_button.SetBitmap(wx.Bitmap(".\\images\\reverse_fov_on.bmp"))
                if is_fov_locked:
                    FOV_Scale = float(70+(Translation_Z*-5))
                    self.fov_slider.SetValue(int(FOV_Scale))
        elif btn == "STEPS":
            STEP_Schedule = int(self.sample_schedule_slider.GetValue())
        elif btn == "Show current image" or btn == "REWIND" or btn == "FORWARD" or event.GetId() == 2 or btn == "REWIND_CLOSEST" or btn == "FORWARD_CLOSEST":
            current_frame = str(int(asyncio.run(sendAsync([0, "start_frame", 0]))))
            current_render_frame = int(current_frame)
            #current_frame = str(intcurrent_frame) - 1)
            outdir = str(asyncio.run(sendAsync([0, "frame_outdir", 0]))).replace('/', '\\').replace('\n', '')
            resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
            if btn == "REWIND_CLOSEST":
                current_frame = self.frame_step_input_box.GetValue()
                if current_frame == "":
                    current_frame = 0
                current_frame = self.getClosestPrompt("R", int(current_frame))
            elif btn == "FORWARD_CLOSEST":
                current_frame = self.frame_step_input_box.GetValue()
                if current_frame == "":
                    current_frame = 0
                current_frame = self.getClosestPrompt("F", int(current_frame))
            elif btn == "REWIND":
                current_frame = self.frame_step_input_box.GetValue()
                if current_frame == '':
                    current_frame = 0
                if int(current_frame) > -1:
                    current_frame = str(int(current_frame)-1)
                if int(current_frame) < 0:
                    current_frame = 0
            elif btn == "FORWARD":
                current_frame = self.frame_step_input_box.GetValue()
                if current_frame == '':
                    current_frame = 0
                if int(current_frame) > -1:
                    current_frame = str(int(current_frame) + 1)
            elif event.GetId() == 2:
                current_frame = self.frame_step_input_box.GetValue()
            self.loadCurrentPrompt("P")
            self.loadCurrentPrompt("N")
            current_frame = str(current_frame).zfill(9)
            imagePath = outdir + "\\" + resume_timestring + "_" + current_frame + ".png"
            maxBackTrack = 20
            #print(str("Trying to load:"+imagePath))
            while not os.path.isfile(imagePath):
                if (current_frame == 0):
                    break
                current_frame = str(int(current_frame)-1)
                current_frame = current_frame.zfill(9)
                imagePath = outdir + "\\" + resume_timestring + "_" + current_frame + ".png"
                maxBackTrack = maxBackTrack -1
                if maxBackTrack == 0:
                    break
            #print(str("Loaded:"+imagePath))
            if os.path.isfile(imagePath):
                if self.bitmap != None:
                    self.bitmap.Destroy()
                    self.bitmap = None
                self.img = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                imgWidth = self.img.GetWidth()
                imgHeight = self.img.GetHeight()
                self.img = self.img.Scale(int(imgWidth / 2), int(imgHeight / 2), wx.IMAGE_QUALITY_HIGH)
                self.bitmap = wx.StaticBitmap(self, -1, self.img, pos=(trbX + 650, tbrY - 120))
                self.frame_step_input_box.SetValue(str(int(current_frame)))
                self.Refresh()
                #Destroy and repaint image
                #print(str(self.framer.bitmap))
                if self.framer != None:
                    if self.framer.bitmap != None:
                        self.framer.bitmap.Destroy()
                        self.framer.bitmap = None
                    self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                    if self.framer:
                        self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                        self.framer.Refresh()

        elif btn == "Set current image":
            current_frame = self.frame_step_input_box.GetValue()
            current_render_frame = int(current_frame)
            asyncio.run(sendAsync([1, "start_frame", int(current_frame)]))
            asyncio.run(sendAsync([1, "should_resume", 1]))
        elif btn == "USE DEFORUMATION":
            print("CURRENT IS:"+str(should_use_deforumation_strength))
            if should_use_deforumation_strength == 0:
                asyncio.run(sendAsync([1, "should_use_deforumation_strength", 1]))
                should_use_deforumation_strength = 1
                print("NOW IT IS:"+str(should_use_deforumation_strength))
            else:
                asyncio.run(sendAsync([1, "should_use_deforumation_strength", 0]))
                should_use_deforumation_strength = 0
                print("NOW IT IS:"+str(should_use_deforumation_strength))
        elif btn == "LIVE RENDER":
            current_frame = str(int(asyncio.run(sendAsync([0, "start_frame", 0]))))
            #print("should_render_live: "+str(should_render_live))
            if should_render_live == False:
                should_render_live = True
                outdir = str(asyncio.run(sendAsync([0, "frame_outdir", 0]))).replace('/', '\\').replace('\n', '')
                resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
                current_frame = current_frame.zfill(9)
                imagePath = outdir + "\\" + resume_timestring + "_" + current_frame + ".png"
                maxBackTrack = 20
                while not os.path.isfile(imagePath):
                    if (current_frame == 0):
                        break
                    current_frame = str(int(current_frame) - 1)
                    current_frame = current_frame.zfill(9)
                    imagePath = outdir + "\\" + resume_timestring + "_" + current_frame + ".png"
                    maxBackTrack = maxBackTrack -1
                    if maxBackTrack == 0:
                        break
                if os.path.isfile(imagePath):
                        self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                        imgWidth = self.img_render.GetWidth()
                        imgHeight = self.img_render.GetHeight()
                        self.framer = render_window(None, 'Render Image')
                        self.framer.Show()
                        self.framer.SetSize(imgWidth + 18, imgHeight + 40)
                        self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                        self.framer.Refresh()
            else:
                should_render_live = False
                if self.framer:
                    self.framer.Hide()
                    self.framer.Close()
                    self.framer.Destroy()
                current_render_frame = -1
        self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X))
        self.rotation_Z_Value_Text.SetLabel(str('%.2f' %Rotation_3D_Z))

        self.writeAllValues()

    def OnExit(self, event):
        #self.worker.abort()
        print("CLOSING!")
        wx.Exit()

    def updateRender(self, event):
        global current_render_frame
        global should_render_live
        if should_render_live == False:
            self.live_render_checkbox.SetValue(0)
        if should_render_live == True:
            current_frame = int(asyncio.run(sendAsync([0, "start_frame", 0])))
            is_paused = asyncio.run(sendAsync([0, "is_paused_rendering", 0]))
            if current_render_frame < current_frame or int(is_paused) == 0:
                current_render_frame = current_frame
                outdir = str(asyncio.run(sendAsync([0, "frame_outdir", 0]))).replace('/', '\\').replace('\n', '')
                resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
                imagePath = outdir + "\\" + resume_timestring + "_" + str(current_render_frame-2).zfill(9) + ".png"
                maxBackTrack = 10
                while not os.path.isfile(imagePath):
                    if (current_frame == 0):
                        return
                    current_frame = int(current_frame) - 1
                    str_current_frame = current_frame
                    str_current_frame = str(current_frame).zfill(9)
                    imagePath = outdir + "\\" + resume_timestring + "_" + str_current_frame + ".png"
                    maxBackTrack = maxBackTrack - 1
                    if maxBackTrack == 0:
                        return
                #Destroy and repaint image
                #print(str(self.framer.bitmap))
                #imagePath = "lkjlkjlk"
                wx.Log.EnableLogging(False)
                try:
                    if self.framer != None:
                        if self.framer.bitmap != None:
                            self.framer.bitmap.Destroy()
                            self.framer.bitmap = None
                        self.img_render = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                        if self.framer:
                            self.framer.bitmap = wx.StaticBitmap(self.framer, -1, self.img_render)
                            self.framer.Refresh()
                except Exception as e:
                    print("ERROR LOADING IMAGE:" + imagePath)
                    print("File Size:" + str(Path(imagePath).stat().st_size))
                    print(str(e))
                wx.Log.EnableLogging(True)
if __name__ == '__main__':
    #subprocess.run(["python", "mediator.py"])
    #print("SLEEP")
    #time.sleep(5)
    app = wx.App()
    Mywin(None, 'Deforumation @ Rakile & Lainol, 2023')
    app.MainLoop()
