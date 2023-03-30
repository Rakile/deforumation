# deforumation
A GUI to remotely steer the Deforum motions, strengths, and prompts, in real time. It is also possible to rewind, forward and resume, in order to fix a bad outcome.

## Dependencies
wxPython (pip install wxPython).

The version of deforum needs to be "Deforum extension for auto1111 webui, v2.3b".

More precisely I changed the animation.py with sha1sum of (1aca4ae71fefabe2a8b17f977fc28f3157c14d56),
and render.py with the sha1sum of (94121a91bf88d36c065cdaa07ea72c8c7a8b0aa2).

## Introduction
As a big fan of deforum, I did this small "Hack" in order to remotely be able to change motion values while deforum is rendering.

## Getting started
In order for deforumation to work, the files "animation.py" and "render.py" need to be replaced with the ones provided in "deforum-for-automatic1111-webui\scripts\deforum_helpers".

Two files will be created in "C:\Temp" when the application is started, "prompt.txt" and "prompt.txt.locked", so be sure that you have a Temp folder on "C:\".
These two files are used as the communication between Deforum and Deforumation.

## How it works
In the Deforum extention in the Keyframes TAB, you have to choose "3D", else it will not work.
Before pushing "Generate" in the deforum extention, prime the communication by inserting a Positive and a Negative prompt in the Deforumation GUI.

To apply any text changes, you then have to push the "SAVE PROMPTS" button (this will create a file in your path C:\Temp\prompt.txt)
You may also set any strength value or other values in beforehand.

Now that this is done, push the "Generate" button in the Deforum extention.
You may now play around with all the values (Panning, Rotating, Tilting, Zoom, Strength Value, CFG value, Sample steps, and of course Prompts, positive and negative) as deforum keeps generating images and applying the new values.

![img](github_images/output.gif)

Easy to control exakt motions (above, doing a Panning left while at the same time Rotating right, creatinging an orbit camera movement around the person). The settings for this movement is shown in the Deforumation interface below.

![img](github_images/interface.png)

## Pause, rewind, and rerender
Deforumation allows you to rewind to a given frame, and gives you the ability to start generating from that given frame. This is good for when something in your creativity "goes bananas". Maybe that clown shouldn't have appeard all of a sudden ;P

In order to use this functionality, you have to turn on "Resume from timestring".
![img](github_images/resume.PNG)
The suggested method is to just start generating without this functionality turned on. Then Deforum will create a folder for you with a timestring. Interupt the generation, and use that time string in the "Resume timestring" field. Then turn on "Resume from timestring", and you should be good to go.

![img](github_images/smile.gif)

Here is an example of LIVE prompt changing for facial expression during rendering.

Positive Prompt: Beatifull (smiling:0.1), bear girl, focus on face

Here we just increase the "(smiling:0.1)" value upwards. 

## Trouble shooting
If the rendering shouldn't work (freezes), it might be because there is still a lock file that hasn't been released (C:\TEMP\prompt.txt.locked). This file is used in order for Deforum and Deforumation not to deadlock each-other. Just manually delete it if that should happen.
Normally, you will see alot of "Waiting for lock file", in the command line interface that you started Automatic1111 from.
