# deforumation
A GUI to remotely steer the Deforum motions, strengths, and prompts, in real time.

## Dependencies
wxPython (pip install wxPython)
The version of deforum needs to be "Deforum extension for auto1111 webui, v2.3b"

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
You may now play around with all the values (PANNING, ROTATING, TILTING, ZOOM, Strength Value and of course Prompts) as deforum keeps generating images and applying the new values.

## Trouble shooting
If the rendering shouldn't work (freezes), it might be because there is still a lock file that hasn't been released (C:\TEMP\prompt.txt.locked). This file is used in order for Deforum and Deforumation not to deadlock each-other. Just manually delete it if that should happen.
Normally, you will see alot of "Waiting for lock file", in the command line interface that you started Automatic1111 from.
