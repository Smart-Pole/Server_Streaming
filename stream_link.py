import streamlink 
import json
import time
import streamlink.stream




# url = "https://www.youtube.com/live/MLxwCqRvJiw"
url = "http://103.171.91.5:80/anhphong/anhphong/1.m3u8"
# url = "https://www.youtube.com/watch?v=iCpX7Y2zCbg"
stream = streamlink.streams(url)
# print(stream)zzz

# dem = 0
# while 1:
#     dem = dem + 1
#     print(f"Tx {dem}")
#     time.sleep(1)

for key, value in stream.items():
    print(f"Type:{key} ")
    print(f"\t {value}")
    print(f"\t {value.to_url()}")
    # print(f'\t {value.to_manifest_url()}')
    print(f"\t {value.url}")
# print(stream)
