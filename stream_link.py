import streamlink 
import json

import streamlink.stream




# url = "https://www.twitch.tv/gutsssssssss9"
# url = "https://www.twitch.tv/huynhnguyenhieunhan"
url = "https://www.thvli.vn/live/thvl1-hd"
stream = streamlink.streams(url)
# print(stream)

print(stream.get("720p").url)

for key, value in stream.items():
    print(f"Type:{key} ")
    # print(f"\t {value}")
    # print(f"\t {value.to_url()}")
    print(f'\t {value.to_manifest_url()}')
    print(f"\t {value.url}")
# print(stream)
 