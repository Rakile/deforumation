The following version is for Deforum version 0.7.6
-------------------------------------------------------------
Pre-requisits:
--------------
Python 3.10 or higher... Deforumation was developed to work with python version 3.10 (version 3.11 or 3.12 have not been validated or tested).

Installation:
-------------
Install dependencies by opening a terminal in the root folder of deforumation, and then run: python -m pip install -r requirements.txt
or (for Windows users), run the "run_me_first_install_requirements.bat" file.
!! For MAC users you will get an error that pywin32 can not be found or something... Ignor that error, because, it is only used for the "named pipes",
version of Deforumation (which MAC users will not use, and so are not affected by not having installed pywin32).

For MAC users, copy the websocket version of Deforum ("Deforum_version\Websockets_version_of_deforum\deforum-for-automatic1111-webui" (inside the deforum-for-automatic1111-webui.zip file))
to your extentions folder in Automatic1111. (Be sure to delete any old folder of Deforum, or overwrite the old one when asked.)
Then, after installing deforumation, start the mediator with "python mediator_ws.py" and then "python deforumation_ws.py"

For users that want to use named pipes version (recommended for Windows and Linux users) of deforum/deforumation, copy the folder "Deforum_version\Named_Pipes_version_of_deforum\deforum-for-automatic1111-webui" (Also needs to be unpacked from deforum-for-automatic1111-webui.zip file).
to your extentions folder in Automatic1111. (Be sure to delete any old folder of Deforum, or overwrite the old one when asked.)
Then, after installing deforumation, start it normally with: "python mediator.py piped" and "python deforumation.py piped" or for Windows users, run the bat-script called "Deforumation_start_named_pipes.bat".

For users that want to use websocket version of deforum/deforumation, copy the folder (unpack the deforum-for-automatic1111-webui.zip file) "Deforum_version\Websockets_version_of_deforum\deforum-for-automatic1111-webui" to your extentions folder in Automatic1111. (Be sure to delete any old folder of Deforum, or overwrite the old one when asked.)
Then, after installing deforumation, start it normally with: "python mediator.py" and "python deforumation.py" or for Windows users, run the bat-script
called "Deforumation_start_websockets.bat". The named pipes version is recommended before the websocket version, and should only be used if you
are having problems with named pipes (which I doubt).

For colab users you should use the files located inside "./deforumation/colab_files". Please look at: https://github.com/rozidev/deforumation-golab
The process is not straight forward, so if you are having any issues, please see the Deforumation discord server @ https://discord.gg/rbKFVh9v87 and don't be afraid to ask for help.

Need further help?
Ask in the Discord server.
https://discord.gg/rbKFVh9v87
