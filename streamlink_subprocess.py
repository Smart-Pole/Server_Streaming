import subprocess
import sys
import threading
# import undetected_chromedriver as uc 
# import time
from get_cookies_avoid_bot_detection import get_cookie
from OBS_Controller_oop import OBS_controller
import time

process = None
url =  "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv1-1.html"
port_ws = "9091"

def host_stream(url,port):
    global process
    if process is not None:
        process.terminate()
        time.sleep(3)
    aws_waf_token_cookie = get_cookie(url,"aws-waf-token")
    print(aws_waf_token_cookie)
    cmd = [
        "streamlink",
        # "web"
        # "--http-cookie", f"aws-waf-token={aws_waf_token_cookie}"
        "--player-external-http",
        "--player-external-http-port", port ,
        url, 
        "best"
    ]
    # Start the streamlink process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("run stream link proccess")
    time.sleep(3)
    # Monitor the output
    # while True:
    #     output = process.stdout.readline()
    #     # if output == '' and process.poll() is not None:
    #     #     break
    #     if output:
    #         print(output.strip())
    #     time.sleep(1)
    
def monitor_streamlink(host,port, password, source_name, interval):
    global subprocess, url, port_ws
    obs_monitor = OBS_controller(host, port, password)
    obs_monitor.trigger_media_input_action(source_name,"OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")
    count_end = 0
    while True:
        try:
            media_status = obs_monitor.get_media_input_status(source_name)
            print(media_status)
            if media_status == "OBS_MEDIA_STATE_ENDED":
                count_end += 1
                if count_end >= 5:
                    print("input get problem") 
                    if subprocess is not None:
                        host_stream(url,port_ws)
                        obs_monitor.trigger_media_input_action(source_name,"OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")
                    
            else:
                count_end = 0

            time.sleep(interval)
        except Exception as e:
            # obs_monitor.close()
            print(f"[ERROR:] {e}")
    
# t1 = threading.Thread(target=host_stream, args=(url,port,),daemon=True)
t2 = threading.Thread(target=monitor_streamlink, args=("10.128.106.80",4455,"123456","myscreen",10,),daemon=True)



if __name__ == "__main__":
    
    # host_stream(url, port)
    # t1.start()
    host_stream(url,port_ws)
    time.sleep(10)
    t2.start()
    while True:
        try:
            output, errors = process.communicate()
            print(output)
            time.sleep(1)
        except KeyboardInterrupt:
            break