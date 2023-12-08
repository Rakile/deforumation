@echo off
start python mediator.py
timeout /t 0.5 /nobreak > NUL
start python deforumation.py