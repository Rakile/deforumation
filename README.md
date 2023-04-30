`BIG DISCLAIMER!!!`

`!!!THERE WILL BE NO DEFORUM SUPPORT IF YOU USE THIS EXTENSION!!!`
`!!!THERE WILL BE NO DEFORUM SUPPORT IF YOU USE THIS EXTENSION!!!`
`!!!THERE WILL BE NO DEFORUM SUPPORT IF YOU USE THIS EXTENSION!!!`
`!!!THERE WILL BE NO DEFORUM SUPPORT IF YOU USE THIS EXTENSION!!!`

Here they are by the way: [Deforum Extension for Automatic1111](https://github.com/deforum-art/deforum-for-automatic1111-webui)

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
5. [Compatibility](#compatibility)
6. [Usage and Tips](#usage-and-tips)
7. [Disclaimer](#disclaimer) 

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
2. Installed Deforum Extension for AUTOMATIC1111 ([deforum-art/deforum-stable-diffusion](https://github.com/deforum-art/deforum-stable-diffusion)) 

Installation Guide<a name="installation-guide"></a>
-------------------
1. **Clone or download** the git repository  `git clone https://github.com/Rakile/deforumation`  (https://github.com/Rakile/deforumation) and unpack the zip file. Keep deforumation folder outside your `"stable-diffusion-webui"` path.
3. **Replace files** (render.py, animation.py, deforum_mediator.py) in the Automatic1111 path ".\deforumation\deforum-for-automatic1111-webui\scripts\deforum_helpers\" with the downloaded files from Deforumation.
4. **Install dependencies** by running `python -m pip install -r requirements.txt` or using the `"run_me_first_install_requirements.bat"` file.
5. **Run the Mediator** (mediator.py) and the **Deforumation GUI** (deforumation.py) in CMD inside deforumation path. Or use the `"Deforumation_start.bat"` file.

Compatibility<a name="compatibility"></a>
-------------
Deforumation may not be compatible with all versions of Deforum. For now Deforum does not have the communication module in there core files.
For now we try to update Deforumation as Deforum is updated.

Usage and Tips<a name="usage-and-tips"></a>
--------------
Deforumation is a valuable tool for understanding how different parameters affect the image generation process. However, it is essential to remember that using Deforumation may result in some issues, as it is not an officially supported extension. 


- Be sure that your Deforum extension does work berfore installing Deforumation.
- Make sure the Mediator is running to ensure proper communication between Deforum and Deforumation.
- Experiment with different settings to find the most effective values for your specific project.

Disclaimer<a name="disclaimer"></a>
----------
By using Deforumation, you understand and acknowledge that it is an unofficial, third-party extension for Deforum. There will be no official support provided for Deforum when using this extension. Use it at your own risk.


------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Discord Channel

[Welcome To Deforumation](https://discord.gg/WrQbnPyc)

# Deforumation
A GUI to remotely steer the Deforum motions, strengths, and prompts, in real time. It is also possible to rewind, forward and resume, in order to fix a bad outcome.
Be aware that if you choose to install Deforumation, it needs to be (at current moment), running, always, in order for Deforum to work when rendering.

## Dependencies, And deforum version

When Deforum is updated deforumation will stop working. As of now 2023-04-21 it works.

If the latest version of Deforum shouldn't be working with Deforumation:

Working version
[Working version of Deforum](https://drive.google.com/file/d/1Fx414-fONjiy7p7SHL1JTi-DkPoIz4HV/view?usp=share_link)


* Ask someone in the community if they have an older version of Deforum, that is actually working with Deforumation
* Wait until Deforum has been updated to work with the latest version of Deforumation

(It is always recommended that you save a working copy of Deforum that works with the latest version of Deforumation)... This has to be done, until Deforum has
implemented internal support.



## Ongoing work

Below you se the draft for the new Deforumation UI.  Many new features like the ability to customize the layout
and choose what values you work with during the animation rendering process. There will also be support to control
the movements using a joystick or game-pad. The paus, rewind and redo function will be the "animation player".

The prompting can be done in traditional way by having the complete prompt in one prompt-input box. 
But as shown in the UI you will also have the ability to make separate prompting input boxes(and adjust the prio) for easier prompting.

And to the left there will be a drop down list for automated macros, like facial expression styles, automated blinking.
Or whatever your imagination can come up with.

![img](github_images/deforumation_design_01.jpg)







## Installation Tutorial

Installation Tutorial can be found here [Installation Tutorial](https://youtu.be/7KmtmPlhzNs)  

In the Totorial we go through  Installation process of Deforum. And checking that deforum is working.

Cloning of the git repo to a suitable folder using CMD git clone command.

Making backup copys of the two files (render.py animation.py) that you need to replace inside , deforum-for-automatic1111-webui\scripts\deforum_helpers\.
And copying those files render.py animation.py and the deforum_mediator.py that is needed for Deforumation to run.

Installing requirements, in CMD or using the "run_me_first_install_requirements.bat"

Starting Deforumation. Running mediator.py and deforumation.py in CMD or using the "Deforumation_start.bat"

And a small test render and showing that Deforumation is controlling the animation in Deforum.

## Installation

Get the repo through: `git clone https://github.com/Rakile/deforumation`  or download the zip file and unpack somewhere and unpack it.

Replace the now three files, located in your Automatic1111 path: ".\stable-diffusion-webui\extensions\deforum-for-automatic1111-webui\scripts\deforum_helpers\"
with the three files downloaded from deforumation: ".\deforumation\deforum-for-automatic1111-webui\scripts\deforum_helpers\"

Be sure to restart Automatic1111 after this.

You need to have python3 for Deforumation to work properly (I think).
So if you still are using 2.7, google how to install python3.

On linux you also have to have to have GTK+ in order for wxPython to work....Follow this guide: https://www.pixelstech.net/article/1599647177-Problem-and-Solution-for-Installing-wxPython-on-Ubuntu-20-04 (Or the likes)... On MAC.... I have no clue, only I know that people got it working. On Windows, just continue.

Go into the deforumation folder in your terminal and start by running:

`python -m pip install -r requirements.txt`

Or just use the. .Bat file. "run me first

## Running
There are two parts, the "Mediator" and the Application (Deforumation GUI).

Start by running the Mediator, which is located in the deforumation folder (mediator.py):

`python mediator.py`

Keep the mediator CMD/Terminal open, its needed for the communication between deforum and deforumation.

Then you can start the acctual application from a new terminal, with:

`python deforumation.py`


Or just use the    .Bat files 👍

## Introduction
As a big fan of deforum, I did this small "Hack" in order to remotely be able to change motion values and others, while deforum is rendering.

The Mediator is running a websocket server that becomes the communication channel between Deforum and deforumation... Altough, any application could communicate with deforum through the Mediator (So go make some video editing applications that look better than mine ;P)

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

## Interface
![img](github_images/newinterface4.png)

As we talked about before, all motion scheduled values in Deforum are added to the manual motions done through Deforumation... with one exception, and that is the "Strength Value". This value has a specific check box ("USE DEFORUMATION"), which can be turned on and off during rendering to switch between full Deforum controll or Deforumation strength controll. This means, that if you are using Deforum to schedule a beat/pulse throughout your video, you can choose to go manual (overriding the the Deforum strength schedule, and vice versa).

There are alot of controls, but here comes the basics:
Panning:

![img](github_images/panning.PNG)

The buttons will move the camera. So if you push the left arrow, the camera will go left, and the "object" will pan right... etc

Think of yourself being the eyes (the camera view)  and the image that you see... so if you push the left button, then it's like YOU are sidestepping left... etc

The "1.0" box decides how much of the value will be applied when you push a button.

![img](github_images/rotation.PNG)

Think of yourself being the eyes (the camera view)  and the image that you see... so if you push the left button, then you'r head will turn left... etc

The "1.0" box decides how much of the value will be applied when you push a button.

![img](github_images/tilt.PNG)

Tilt is tilt... It will rotate the image clock or counter clock-wise.

The "1.0" box decides how much of the value will be applied when you push a button.

![img](github_images/rewindforward.PNG)

Deforumation allows you to rewind to a given frame, and gives you the ability to start generating from that given frame. This is good for when something in your creativity "goes bananas". Maybe that clown shouldn't have appeard all of a sudden ;P

This part is useful to rewind and forward througout a rendering. When you have started a rendering, you can look at the current image by pressing the "Show current image" or you can also click anywhere else that is bnot a button on the GUI, to update the image.

A suggestion before using any of these option is to push the "PUSH TO PAUSE RENDERING BUTTON". The rendering will pause and you can more easily explore the functionalities.

The "left-arrow"-button shows you the image previous to the current, and the "right-arrow"-button" shows you the next image to the current.

Typing a frame number in the input box and pushing RETURN will directly transport you to that fram (if it exists).

The "double-left-arrow" will jump to your closest saved prompt towards the beginning relative to your current frame, and the "double-right-arrow" will jump to your closest saved prompt towards the end relative to your current frame.


![img](github_images/resume.PNG)

When you know you did a misstake, start by pressing the "PUSH TO PAUS RENDERING"-button. Then click "Show current image"-button. This will give you the current image, and the current actual frame number. Use the arrows to rewind or forward... or you could just type in a frame number and press enter to jump to that frame... When you found the frame where you want to resume rendering from, press the "Set current image"-button, and then, to resume rendering, push the "PUSH TO RESUME RENDERING"-button. EASY!!!

Pushing the "SAVE PROMPTS" button will save your current prompts (positive and negative), as files inside the "prompts" folde in your deforumation folder. Depending on your current generation (timestring), seperate files will be saved for that particular "project". That means that your prompts can be recalled during a generation of a specific project. E.g. Push "SAVE PROMPT" on fram 0, then on fram 50 change your prompts, and push again "SAVE PROMPTS", and they will update as you rewind/forward throughout you generated frames... You'll get a hang of it ;) (Else ask in the discord).

![img](github_images/smile.gif)

To change the seed, just type a new seed in the seed-input box, and push return. It will then be loyal to whatever you have choosen in the Deforum GUI, iterative, etc.

## Random example
Here is an example of LIVE prompt changing for facial expression during rendering.

Positive Prompt: Beatifull (smiling:0.1), bear girl, focus on face

Here we just increase the "(smiling:0.1)" value upwards. 

## A tool for learning
Deforumation is a perfect tool to learn how different parameters, like Steps, Strength Value and CFG scale, because, in a combination they affect the image generation over time. The best way (I have found, to get as a stable outcome as possible with all other settings you have in Deforum), is to know your values.

One way to achieve this is to have No motion at all, and make every render not go into "Bananas"... Because the most effective values differ alot between samplers, checkpoints, SD VAE's and all other specific settings that you are currently having. Get a feel of what values, keep a balance with your current choices. Note them down, and play around ;P

## Tips and tricks
When you push "Interupt", sometimes Deforum buggs out and it doesn't stich up your video correctly. An easy way to avoid/bypass this with the help of Deforumation, is to first push the "PUSH TO PAUS RENDERING OPTION", and after the rendering has paused, then push the "Interrupt"-button. Then in Deforumation resume the flow again by pushing the "PUSH TO RESUME BUTTON" in Deforum. This will mostly get Deforum to get the stitching correctly started.

## Trouble shooting
Be sure that the Mediator is upp and running! Else no communication can be had between Deforum and Deforumation!

## Examples of using Deforumation (Give a shout if you want to be here)
By Lainol, Live prompting, facial expression:
[![Watch the video](github_images/Linol_1.PNG)](https://www.youtube.com/watch?v=UKYZEQVljRE)

## Example 2
By Lainol, Live prompting.

Ai-xite.

[![Watch the video](github_images/aixite.png)](https://youtu.be/YH0Q8J1NjIA)

## Last thoughts
There might be an ongoing discussions on how to implement this into Deforum, so that updates will be more smoth and accordance with Deforum... As of now it remains a Hack... Never the less, we encourage users to test Deforumation, and understand how vital this concept is for creating anything with precision (not looking like an LSD trip). Please post videos, tutorials or, whatever, whith how you use Deforum, through Deforumation to your advantage. Join the r/deforumation channel (https://www.reddit.com/r/deforumation/).
