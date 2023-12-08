@echo off
start python -m pip install -r requirements.txt
timeout /t 0.5 /nobreak > NUL
