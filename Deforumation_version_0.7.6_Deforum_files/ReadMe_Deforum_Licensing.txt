In order to accomadate Deforum GNU AFFERO GENERAL PUBLIC LICENSE V3
I we are including the files that have been modified in order for out GUI to communicate with Deforum:
render.py
animation.py

We also included mediator.py which is a bridge between Deforum and Deforumation (Our GUI).
We have not included our GUI (deforumation.py, where all the actual original work is being made to create the graphical interface)
Deforumation.py which mainly consists of the GUI to controlling Deforum, communicates with the mediator to receive relevant information
on what is going on in the generation of images that Deforum produces. I sometimes also gives Deforum instructions how to behave, through the mediator.

Anyone can build their own connection/GUI through the publicly available mediator.py if they choose so.

In The patreon wall that we have, the only file that is not released on github publically, is deforumation.py (our GUI).