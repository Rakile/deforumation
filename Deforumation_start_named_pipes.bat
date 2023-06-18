@echo off
start python mediator.py pipes
timeout /t 0.5 /nobreak > NUL
start python deforumation.py pipes