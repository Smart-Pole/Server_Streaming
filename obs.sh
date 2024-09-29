#!/bin/bash

# Set the path to the OBS executable
obsPath="/usr/bin/obs"

# Start OBS instances with different websocket ports and passwords without output
"$obsPath" -m --websocket_port 1131 --websocket_password "123456" --minimum-to-tray > /dev/null 2>&1 &
"$obsPath" -m --websocket_port 1132 --websocket_password "123456" --minimum-to-tray > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1133 --websocket_password "123456" --minimum-to-tray > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1134 --websocket_password "123456" --minimum-to-tray > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1135 --websocket_password "123456" --minimum-to-tray > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1136 --websocket_password "123456" > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1137 --websocket_password "123456" > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1138 --websocket_password "123456" > /dev/null 2>&1 &
# "$obsPath" -m --websocket_port 1139 --websocket_password "123456" > /dev/null 2>&1 &

