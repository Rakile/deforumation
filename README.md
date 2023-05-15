
`DISCLAIMER!!!`
===============================================
`!!!THERE WILL BE NO DEFORUM SUPPORT IF YOU USE THIS EXTENSION!!!`
===============================================
---------------------------------------------------------------------------------------------------------------------------------------

Deforumation: Unofficial Extension for Deforum
===============================================

**IMPORTANT: No official Deforum support will be provided if you use this extension.**

Table of Contents
-----------------
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Key Features](#key-features)
4. [Installation Guide](#installation-guide)
5. [Installation Tutorial](#installation-Tutorial)
6. [Compatibility](#compatibility)
7. [Usage and Tips](#usage-and-tips)
8. [Disclaimer](#disclaimer) 
9. [Discord Channel](#Discord-Channel)
10. [Ongoing Work](#Ongoing-Work)
11. [in-depth information](#in-depth-information)

Latest version / features
-----------------
[Latest version](#Latest-version)   (2023-05-03)


Introduction<a name="introduction"></a>
------------
Deforumation is an unofficial extension for Deforum that provides a Graphical User Interface (GUI) to remotely control Deforum 3D motions, zoom and angle , strength value (toggle to use deforum strenght schedule), CFG Scale, sampler steps, seed, cadense scale  and prompts in real-time. It also offers pausing, rewinding, forwarding, and resuming by setting current image to fix any undesired outcomes during the rendering process.

Key Features<a name="key-features"></a>
------------
- Separate prompting input boxes with prioritising possibility  
- Controlling movements while rendering 
- Live manipulation of key values that effects the animation
- Pause, rewind, and redo functions

Prerequisites<a name="prerequisites"></a>
------------
1. Local instance of SD ([AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)) 
2. Installed Deforum Extension for AUTOMATIC1111 ([deforum-art/deforum-for-automatic1111-webui](https://github.com/deforum-art/deforum-for-automatic1111-webui)) 

Installation Guide<a name="installation-guide"></a>
-------------------
1. **Clone or download** the git repository  `git clone https://github.com/Rakile/deforumation`  (https://github.com/Rakile/deforumation) and unpack the zip file. Keep deforumation folder outside your `"stable-diffusion-webui"` path.
3. **Replace files** (render.py, animation.py, deforum_mediator.py) in the Automatic1111 path ".\deforumation\deforum-for-automatic1111-webui\scripts\deforum_helpers\" with the downloaded files from Deforumation.
4. **Install dependencies** by running `python -m pip install -r requirements.txt` or using the `"run_me_first_install_requirements.bat"` file.
5. **Run the Mediator** (mediator.py) and the **Deforumation GUI** (deforumation.py) in CMD inside deforumation path. Or use the `"Deforumation_start.bat"` file.
6. **Set to 3D in keyframes TAB** In the Deforum extention in the `Keyframes TAB, you have to choose "3D"`, else it will not work.

Installation Tutorial<a name="installation-Tutorial"></a>
-------------
[Installation Tutorial](https://youtu.be/7KmtmPlhzNs)

Compatibility<a name="compatibility"></a>
-------------
Deforumation may not be compatible with all versions of Deforum. For now Deforum does not have the communication module in there core files.
For now we try to update Deforumation as Deforum is updated.

Usage and Tips<a name="usage-and-tips"></a>
--------------
Deforumation is a valuable tool for understanding how different parameters affect the image generation process. However, it is essential to remember that using Deforumation may result in some issues, as it is not an officially supported extension. 


- In the Deforum extention in the Keyframes TAB, you have to choose "3D", else it will not work. Before pushing "Generate" in the deforum extention, prime the communication by inserting a Positive and a Negative prompt in the Deforumation GUI.
- Be sure that your Deforum extension does work berfore installing Deforumation.
- Make sure the Mediator is running to ensure proper communication between Deforum and Deforumation.
- Experiment with different settings to find the most effective values for your specific project.
- Change "live preview" settings in automatic1111 to draft for faster rendering.
- Check the "LIVE RENDER" box in deforumation to se generated frames.  


Disclaimer<a name="disclaimer"></a>
----------
By using Deforumation, you understand and acknowledge that it is an unofficial, third-party extension for Deforum. There will be no official support provided for Deforum when using this extension. Use it at your own risk.



Discord Channel<a name="Discord-Channel"></a>
----------

[Welcome To Deforumation] (https://discord.gg/rbKFVh9v87) 


Ongoing Work<a name="Ongoing-Work"></a>
----------

Below you se the draft for the new Deforumation UI.  Many new features like the ability to customize the layout
and choose what values you work with during the animation rendering process. There will also be support to control
the movements using a joystick or game-pad. The paus, rewind and redo function will be the "animation player".

The prompting can be done in traditional way by having the complete prompt in one prompt-input box. 
But as shown in the UI you will also have the ability to make separate prompting input boxes(and adjust the prio) for easier prompting.

And to the left there will be a drop down list for automated macros, like facial expression styles, automated blinking.
Or whatever your imagination can come up with.

![img](github_images/deforumation_design_01.jpg)




Latest version<a name="Latest-version"></a>
----------
<details>
  <summary>Latest Version Info</summary>

   2023-05-15
  Lots of added stuff
- Gentle Zero can now go from any motion to any other motion in panning and rotation values
- ControlNet in Deforum, can now be controlled by Deforumation
- Live Render can now replay a range of images (no stitching), to get a fast view of how the animation is going to look
   

</details>

<details>
  <summary>Latest Version Info</summary>

   2023-05-03 (later in the evening)
  
- Introducing another "Gentle Zero" for rotation. It works separate from "Gentle Zero" for panning.  
  
![img](github_images/current_version_gentle_zero_rotation.png)
  

</details>

<details>
  <summary>Latest Version Info</summary>

   2023-05-03
  
- Separate prompting input boxes with prioritising possibility  
  
- All prompts can now be minimized, making the window smaller, 
  and maybe some people will find this easier to work with.
  
![img](github_images/current_version.png)
  

</details>


In-depth information<a name="in-depth-information"></a>
----------


<details>
  <summary>How it works</summary>
    ## How it works
Watch this video to get a feeling of how to use Deforumation... or read on below.
[![Watch the video](github_images/Deforumation_Tutorial.png)](https://www.youtube.com/watch?v=v1h2jo3f5U4)

## Recommended setting

In settings, Live previews recommends this setting. This gives you better visual feedback. 

![img](github_images/Live_preview.png)


In the Deforum extention in the Keyframes TAB, you have to choose "3D", else it will not work.
Before pushing "Generate" in the deforum extention, prime the communication by inserting a Positive and a Negative prompt in the Deforumation GUI.

To apply any text changes, you then have to push the "SAVE PROMPTS" button.
You may also set any strength value or other values in beforehand. Also, moving any sliders or pushing any buttons will automatically save all other values (prompts included). The file that is being saved is located inside the deforumation folder (deforumation_settings.txt), and will keep you settings during a restarts.

Now that this is done, push the "Generate" button in the Deforum extention.
You may now play around with all the values (Panning, Rotating, Tilting, Zoom, Strength Value, CFG value, Sample steps, and of course Prompts, positive and negative) as deforum keeps generating images and applying the new values.

!!!BE AWARE!!!
Deforumation now adds the values to any scheduled motion. That means that if you have scheduled ANY motions inside of Deforum, like "Translation X" or "Rotation 3D Y", or whatever, they will be added to your manual values done through Deforumation. Be aware that "Translation Z" is by default set to "0:(1.75)"... If you don't want this influence, and only want Deforumation to controll all values, you need to set this to 0:(0). We added this feature, because we think you still want to add a musical flow through the Deforum scheduling.


![img](github_images/output.gif)
 
</details>


<details>
  <summary>Interface</summary>
  
 ## Interface
![img](github_images/newinterface5.png)

As we talked about before, all motion scheduled values in Deforum are added to the manual motions done through Deforumation... with one exception, and that is the "Strength Value". This value has a specific check box ("USE DEFORUMATION"), which can be turned on and off during rendering to switch between full Deforum controll or Deforumation strength controll. This means, that if you are using Deforum to schedule a beat/pulse throughout your video, you can choose to go manual (overriding the the Deforum strength schedule, and vice versa).

There are alot of controls, but here comes the basics:

**Panning**

![img](github_images/panning.PNG)

The buttons will move the camera. So if you push the left arrow, the camera will go left, and the "object" will pan right... etc

Think of yourself being the eyes (the camera view)  and the image that you see... so if you push the left button, then it's like YOU are sidestepping left... etc

The "0.2" box decides how much of the value will be applied when you push a button.

**Rotation**
  
![img](github_images/rotation.PNG)

Think of yourself being the eyes (the camera view)  and the image that you see... so if you push the left button, then you'r head will turn left... etc

**Arming On and Off**
  
The panning buttons have 2 modes, "ARMED" or "NOT ARMED", which can be switched between by pushing the small button above the "0.2 box":

  ARMED: ![img](github_images/arm_on.bmp)

NOT ARMED: ![img](github_images/arm_off.bmp) 
  
In ARMED mode, the values that you choose through the pann buttons, will be a guide for the "NOT ARMED" values. So the ARMED and the NOT ARMED mode can have totally separate values.
When you then push the big ZERO-icon in the middle:

![img](github_images/zero.bmp)
  
Your current NOT ARMED values will go towards your ARMED values. And they will do it in the number of frames that you have specified in the "0-Steps" input box.
  
**Tilt**
  
The "0.2" box decides how much of the value will be applied when you push a button.

![img](github_images/tilt.PNG)

Tilt is tilt... It will rotate the image clock or counter clock-wise.

The "1.0" box decides how much of the value will be applied when you push a button.

**Pause and Rewind**
  
![img](github_images/rewindforward.PNG)

Deforumation allows you to rewind to a given frame, and gives you the ability to start generating from that given frame. This is good for when something in your creativity "goes bananas". Maybe that clown shouldn't have appeard all of a sudden ;P

This part is useful to rewind and forward througout a rendering. When you have started a rendering, you can look at the current image by pressing the "Show current image" or you can also click anywhere else that is bnot a button on the GUI, to update the image.

A suggestion before using any of these option is to push the "PUSH TO PAUSE RENDERING BUTTON". The rendering will pause and you can more easily explore the functionalities.

The "left-arrow"-button shows you the image previous to the current, and the "right-arrow"-button" shows you the next image to the current.

Typing a frame number in the input box and pushing RETURN will directly transport you to that fram (if it exists).

The "double-left-arrow" will jump to your closest saved prompt towards the beginning relative to your current frame, and the "double-right-arrow" will jump to your closest saved prompt towards the end relative to your current frame.


![img](github_images/resume.PNG)

When you know you did a misstake, start by pressing the "PUSH TO PAUS RENDERING"-button. Then click "Show current image"-button. This will give you the current image, and the current actual frame number. Use the arrows to rewind or forward... or you could just type in a frame number and press enter to jump to that frame... When you found the frame where you want to resume rendering from, press the "Set current image"-button, and then, to resume rendering, push the "PUSH TO RESUME RENDERING"-button. EASY!!!

**Prompts**
  
Pushing the "SAVE PROMPTS" button will save your current prompts (positives and negative), as files inside the "prompts" folde in your deforumation folder. Depending on your current generation (timestring), seperate files will be saved for that particular "project". That means that your prompts can be recalled during a generation of a specific project. E.g. Push "SAVE PROMPT" on fram 0, then on fram 50 change your prompts, and push again "SAVE PROMPTS", and they will update as you rewind/forward throughout you generated frames... You'll get a hang of it ;) (Else ask in the discord).

**Replay**
  
![img](github_images/replay.PNG)

During a generation session, you can directly watched any range of images, by inserting the range you want to play, and then pressing the Play button. 
  
  
![img](github_images/smile.gif)

To change the seed, just type a new seed in the seed-input box, and push return. It will then be loyal to whatever you have choosen in the Deforum GUI, iterative, etc.

  
**ControlNet** 

![img](github_images/controlnet.PNG)
  
Deforumation can control Deforum's ControlNet values
  
</details>




<details>
  <summary>Example</summary>
  
  ## Example
Here is an example of LIVE prompt changing for facial expression during rendering.

Positive Prompt: Beatifull (smiling:0.1), bear girl, focus on face

Here we just increase the "(smiling:0.1)" value upwards. 
  
  
  
  </details>
  
  
  
  
  <details>
  <summary>A tool for learning</summary>
  
## A tool for learning
Deforumation is a perfect tool to learn how different parameters, like Steps, Strength Value and CFG scale, because, in a combination they affect the image generation over time. The best way (I have found, to get as a stable outcome as possible with all other settings you have in Deforum), is to know your values.

One way to achieve this is to have No motion at all, and make every render not go into "Bananas"... Because the most effective values differ alot between samplers, checkpoints, SD VAE's and all other specific settings that you are currently having. Get a feel of what values, keep a balance with your current choices. Note them down, and play around ;P
  
  </details>
  
  
  
  <details>
  <summary>Tips and tricks</summary>
  
  ## Tips and tricks
When you push "Interupt", sometimes Deforum buggs out and it doesn't stich up your video correctly. An easy way to avoid/bypass this with the help of Deforumation, is to first push the "PUSH TO PAUS RENDERING OPTION", and after the rendering has paused, then push the "Interrupt"-button. Then in Deforumation resume the flow again by pushing the "PUSH TO RESUME BUTTON" in Deforum. This will mostly get Deforum to get the stitching correctly started.


</details>

  <details>
  <summary>Examples of using Deforumation</summary>
  
  ## Examples of using Deforumation (Give a shout if you want to be here)
  
By Lainol, Live prompting, facial expression:
  
[![Watch the video](github_images/Linol_1.PNG)](https://www.youtube.com/watch?v=UKYZEQVljRE)

## Example 2
  
By Lainol, Live prompting.

Ai-xite.

[![Watch the video](github_images/aixite.png)](https://youtu.be/YH0Q8J1NjIA)

  
</details>

  <details>
  <summary>Thoughts</summary>
  
  ## Last thoughts
There might be an ongoing discussions on how to implement this into Deforum, so that updates will be more smoth and accordance with Deforum... As of now it remains a Hack... Never the less, we encourage users to test Deforumation, and understand how vital this concept is for creating anything with precision (not looking like an LSD trip). Please post videos, tutorials or, whatever, whith how you use Deforum, through Deforumation to your advantage. Join the r/deforumation channel (https://www.reddit.com/r/deforumation/).

</details>

  
 




