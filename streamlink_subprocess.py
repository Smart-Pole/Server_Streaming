import subprocess
import sys
# import undetected_chromedriver as uc 
# import time
from get_cookies_avoid_bot_detection import get_cookie


def main():
    url =  "https://vtvgo.vn/xem-truc-tuyen-kenh-vtv1-1.html"
    aws_waf_token_cookie = get_cookie(url,"aws-waf-token")
    print(aws_waf_token_cookie)
    cmd = [
        "streamlink",
        # "web"
        # "--http-cookie", f"aws-waf-token={aws_waf_token_cookie}"
        "--player-external-http",
        "--player-external-http-port", "9091",
        
        url, 
        "best"
    ]
    # Start the streamlink process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Monitor the output
    while True:
        output = process.stdout.readline()
        # if output == '' and process.poll() is not None:
        #     break
        if output:
            print(output.strip())

            
            # Check for specific error messages here
            if "Unable to fetch new streams" in output or "Failed to resolve" in output:
                print("Error detected, exiting...")
                process.kill()  # Kill the streamlink process
                sys.exit(1)
        # time.sleep(1)
    # Ensure the process is properly terminated
    rc = process.poll()
    sys.exit(rc)


if __name__ == "__main__":
    main()