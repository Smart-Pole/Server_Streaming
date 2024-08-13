import streamlink
import subprocess
import sys
import threading
# import undetected_chromedriver as uc 
# import time
from OBS_Controller_oop import OBS_controller
import time
import undetected_chromedriver as uc 
import json
import argparse

parser = argparse.ArgumentParser(description='VTV argument')
parser.add_argument('--channel', type=str, help='vtv option',default="vtv1")
parser.add_argument('--port', type=str, help='port number want hosting stream',default="9091")
args = parser.parse_args()
channel =  args.channel
port = args.port
class VTV_Input_Stream():
    def __init__(self, url: str, port: str, browser_path="C:/Program Files/Google/Chrome/Application/chrome.exe",quality="best"):
        self.url = url
        self.port = port
        self.browser_path = browser_path
        self.quality = quality
        self.streamlink_subprocess: subprocess = None
        
    def get_cookie(self,url, name):
        # headless flag must be fail
        try: 
            self.driver = uc.Chrome(headless=False,use_subprocess=True) 
            self.driver.get(url)
            time.sleep(2)
            my_cookie = self.driver.get_cookie(name)
            print (json.dumps(my_cookie,indent=4))
            # self.driver.close()
            # very importance if remove will raise an error
            time.sleep(1)
            return my_cookie.get("value") 
        except Exception as e:
                print(f"[ERROR]: {e}")
                return None
        finally:
            if self.driver:
                self.driver.close()
                # very important; if removed, may raise an error
                time.sleep(1)
            
    def host_stream(self):
        while True:
            try:
                # aws_waf_token_cookie = self.get_cookie(self.url,"aws-waf-token")
                # print(aws_waf_token_cookie)
                cmd = [
                    "streamlink",
                    "--webbrowser-executable",  self.browser_path,
                    # "--http-cookie", f"aws-waf-token={aws_waf_token_cookie}",
                    "--player-external-http-continuous", "0",
                    "--player-external-http",
                    "--player-external-http-port", self.port,
                    self.url, "best"
                ]
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    # Nếu có lỗi, in ra stderr và khởi động lại
                    print(f"ERROR: {result.stderr}")
                    print("Restarting stream due to error...")
                    time.sleep(5)
            except KeyboardInterrupt:
                break
       
        
        
        
if __name__ == "__main__":
    vtv_chanel = {
        "vtv1" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv1-1.html",
        "vtv2" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv2-2.html",
        "vtv3" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv3-3.html",
        "vtv4" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv4-4.html",
        "vtv5" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv5-5.html",
        "vtv6" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv-c%E1%BA%A7n-th%C6%A1-6.html",
        "vtv7" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv7-27.html",
        "vtv8" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv8-36.html",
        "vtv9" : "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv9-39.html"
    }
    myvtv = VTV_Input_Stream(
        url = vtv_chanel.get(channel),
        port=  port
    )
    myvtv.host_stream()