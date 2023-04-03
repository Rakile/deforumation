import wx
import asyncio
import websockets
import os
import time
import pickle
#import subprocess

deforumationSettingsPath="./deforumation_settings.txt"
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
async def sendAsync(value):
    async with websockets.connect("ws://localhost:8765") as websocket:
        await websocket.send(pickle.dumps(value))
        message = await websocket.recv()
        #print(str(message))
        return message

class Mywin(wx.Frame):
    def __init__(self, parent, title):
        super(Mywin, self).__init__(parent, title=title, size=(1400, 700))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(100, 100, 100))
        #wx.EVT_PAINT(self, self.OnPaint)
        #wx.EVT_SIZE(self, self.OnSize)
        #Timer Event
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.frameUpdater, self.timer)
        #self.timer.Start(1000)

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
        #SHOW CURRENT IMAGE, BUTTON
        self.show_current_image = wx.Button(panel, label="Show current image", pos=(trbX+992, tbrY-110))
        self.show_current_image.Bind(wx.EVT_BUTTON, self.OnClicked)
        #REWIND BUTTTON
        bmp = wx.Bitmap(".\\images\\left_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.rewind_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1000, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.rewind_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.rewind_button.SetLabel("REWIND")
        #SET CURRENT FRAME INPUT BOX
        self.frame_step_input_box = wx.TextCtrl(panel, 2, size=(48,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+1032, tbrY-74))
        self.frame_step_input_box.SetLabel("")
        self.frame_step_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=2)
        #FORWARD BUTTTON
        bmp = wx.Bitmap(".\\images\\right_arrow.bmp", wx.BITMAP_TYPE_BMP)
        self.forward_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp, pos=(trbX+1080, tbrY-80), size=(bmp.GetWidth() + 10, bmp.GetHeight() + 10))
        self.forward_button.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.forward_button.SetLabel("FORWARD")
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

        #PAUSE VIDEO RENDERING
        self.pause_rendering = wx.Button(panel, label="PUSH TO PAUS RENDERING")
        sizer.Add(self.pause_rendering, 0, wx.ALL | wx.EXPAND, 5)
        self.pause_rendering.Bind(wx.EVT_BUTTON, self.OnClicked)

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
        self.strength_schedule_Text = wx.StaticText(panel, label="Strength Value - (slider value is divided by 100)", pos=(trbX-25, tbrY-70))

        #SAMPLE STEP SLIDER
        self.sample_schedule_slider = wx.Slider(panel, id=wx.ID_ANY, value=25, minValue=1, maxValue=200, pos = (trbX-25, tbrY-50-70), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.sample_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.sample_schedule_slider.SetTickFreq(1)
        self.sample_schedule_slider.SetLabel("STEPS")
        self.strength_schedule_Text = wx.StaticText(panel, label="Steps", pos=(trbX-25, tbrY-70-64))

        #SEED INPUT BOX
        self.seed_schedule_Text = wx.StaticText(panel, label="Seed", pos=(trbX+300, tbrY-50-80))
        self.seed_input_box = wx.TextCtrl(panel, 3, size=(300,20), style = wx.TE_PROCESS_ENTER, pos=(trbX+300, tbrY-50-60))
        self.seed_input_box.SetLabel("-1")
        self.seed_input_box.Bind(wx.EVT_TEXT_ENTER, self.OnClicked, id=3)



        #CFG SCHEDULE SLIDER
        self.cfg_schedule_slider = wx.Slider(panel, id=wx.ID_ANY, value=7, minValue=1, maxValue=30, pos = (trbX+325, tbrY-50), size = (300, 40), style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.cfg_schedule_slider.Bind(wx.EVT_SCROLL, self.OnClicked)
        self.cfg_schedule_slider.SetTickFreq(1)
        self.cfg_schedule_slider.SetLabel("CFG SCALE")
        self.CFG_scale_Text = wx.StaticText(panel, label="CFG Scale", pos=(trbX+325, tbrY-70))


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

        self.Centre()
        self.Show()
        self.Fit()
        self.loadAllValues()

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
        if os.path.isfile(deforumationSettingsPath):
            deforumFile = open(deforumationSettingsPath, 'r')
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
        except Exception as e:
            print(e)
        deforumFile = open(deforumationSettingsPath, 'w')
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
        deforumFile.close()

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
        btn = event.GetEventObject().GetLabel()
        #print("Label of pressed button = ", str(event.GetId()))
        if btn == "PUSH TO PAUS RENDERING":
            self.pause_rendering.SetLabel("PUSH TO RESUME RENDERING")
            is_paused_rendering = True
        elif btn == "PUSH TO RESUME RENDERING":
            self.pause_rendering.SetLabel("PUSH TO PAUS RENDERING")
            is_paused_rendering = False
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
        elif btn == "Show current image" or btn == "REWIND" or btn == "FORWARD" or event.GetId() == 2:
            current_frame = int(asyncio.run(sendAsync([0, "start_frame", 0])))
            #print("current_frame:"+ str(current_frame))
            current_frame = str(int(current_frame) - 1)
            outdir = str(asyncio.run(sendAsync([0, "frame_outdir", 0]))).replace('/', '\\').replace('\n', '')
            #print("outdir:"+ str(outdir))
            resume_timestring = str(asyncio.run(sendAsync([0, "resume_timestring", 0])))
            #print("resume_timestring:"+ str(resume_timestring))
            # arne = len(str(current_frame))
            # fillings = 11 - len(str(current_frame))
            if btn == "REWIND":
                current_frame = self.frame_step_input_box.GetValue()
                if int(current_frame) != 0:
                    current_frame = str(int(current_frame)-1)
            elif btn == "FORWARD":
                current_frame = self.frame_step_input_box.GetValue()
                if int(current_frame) != 0:
                    current_frame = str(int(current_frame) + 1)
            elif event.GetId() == 2:
                current_frame = self.frame_step_input_box.GetValue()

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
                if self.bitmap != None:
                    self.bitmap.Destroy()
                    self.bitmap = None
                self.img = wx.Image(imagePath, wx.BITMAP_TYPE_ANY)
                self.img = self.img.Scale(int(self.img.GetWidth() / 2), int(self.img.GetHeight() / 2), wx.IMAGE_QUALITY_HIGH)
                self.bitmap = wx.StaticBitmap(self, -1, self.img, pos=(trbX + 700, tbrY - 120))
                self.frame_step_input_box.SetValue(str(int(current_frame)))
                self.Refresh()
        elif btn == "Set current image":
            current_frame = self.frame_step_input_box.GetValue()
            asyncio.run(sendAsync([1, "start_frame", int(current_frame)]))
            asyncio.run(sendAsync([1, "should_resume", 1]))
        self.pan_X_Value_Text.SetLabel(str('%.2f' % Translation_X))
        self.pan_Y_Value_Text.SetLabel(str('%.2f' % Translation_Y))
        self.rotation_3d_x_Value_Text.SetLabel(str('%.2f' % Rotation_3D_Y))
        self.rotation_3d_y_Value_Text.SetLabel(str('%.2f' %Rotation_3D_X))
        self.rotation_Z_Value_Text.SetLabel(str('%.2f' %Rotation_3D_Z))

        self.writeAllValues()


if __name__ == '__main__':
    #subprocess.run(["python", "mediator.py"])
    #print("SLEEP")
    #time.sleep(5)
    app = wx.App()
    Mywin(None, 'Deforumation @ Rakile & Lainol, 2023')
    app.MainLoop()
