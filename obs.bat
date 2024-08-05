@echo off
set obsPath="D:\APPDATA\OBS\obs-studio\bin\64bit"
@REM set obsPath="D:\application\obs-studio\bin\64bit"
start /d %obsPath% obs64.exe -m --websocket_port 3344 --websocket_password "123456" --minimize-to-tray
start /d %obsPath% obs64.exe -m --websocket_port 5544 --websocket_password "123456" --minimize-to-tray

    