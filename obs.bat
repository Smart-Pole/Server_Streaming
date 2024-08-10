@echo off
set obsPath="D:\APPDATA\OBS\obs-studio\bin\64bit"
@REM set obsPath="D:\application\obs-studio\bin\64bit"
start /d %obsPath% obs64.exe -m --websocket_port 1122 --websocket_password "123456" 
start /d %obsPath% obs64.exe -m --websocket_port 9632 --websocket_password "123456" 
start /d %obsPath% obs64.exe -m --websocket_port 6688 --websocket_password "123456" 

    