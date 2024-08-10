@echo off
cmd /c "obs.bat"
timeout /t 20 /nobreak
python Server.py