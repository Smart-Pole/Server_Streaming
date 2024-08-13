@echo off
set obsPath="D:\APPDATA\OBS\obs-studio\bin\64bit"
@REM set obsPath="D:\application\obs-studio\bin\64bit"
start /d %obsPath% obs64.exe -m --websocket_port 1131 --websocket_password "123456" 
start /d %obsPath% obs64.exe -m --websocket_port 1132 --websocket_password "123456" 
start /d %obsPath% obs64.exe -m --websocket_port 1133 --websocket_password "123456" 

    