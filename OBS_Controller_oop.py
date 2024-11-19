import obsws_python as obs
import json
import time
from datetime import datetime
import streamlink
import requests
import threading
import os
# rtmp://live.twitch.tv/app server live of twitch


class OBS_controller:
    def printJsonObject(self,object):
        print(json.dumps(object,indent=3))
        
        
    def printJsonObjectList(self,object_list):
        for object in object_list:
            self.printJsonObject(object)
            
    def __init__(self, streamlink, id , name , host='localhost', port=4455, password='123456', width = 1920, height  = 1080) -> None:
        
        self.id = id
        self.name = name
        self.streamlink = streamlink
        self.streamlink_m3u8 = None
        self.port = port
        self.host = host
        self.password = password
        self.height = height
        self.width = width
        self.url = "https://stream.lpnserver.net/report"
        self.__start_checking()
        # event and request client for obs websocket
        self.request_client = obs.ReqClient(host = self.host,port = self.port,password = self.password)
        self.event_client = obs.EventClient(host = self.host,port = self.port,password = self.password)
        
        
        # on reconnect handler
        self.on_reconnected = None
        self.mqtt_handler = None
        self.mqtt_topic = None
        self.have_idle = False
        
        # resgiter event want to listen
        self.event_client.callback.register(self.on_stream_state_changed)
    
        # self.event_client.callback.register(self.on_scene_item_transform_changed)
        # self.event_client.callback.register(self.on_media_input_playback_ended)
        
        # self.event_client.callback.register(self.on_media_input_action_triggered)
        # self.event_client.callback.register(self.on_scene_transition_video_ended)
        try:
            if self.check_stream_is_active():
                self.stop_stream()
        except:
            pass
        time.sleep(2)

        lists_input = self.request_client.get_input_list().inputs
        for item in lists_input:
            print("inputName is:", item['inputName'])
            self.request_client.remove_input(name=item['inputName'])
            time.sleep(1)
        time.sleep(2)
        lists_scene = self.request_client.get_scene_list().scenes
        for item in lists_scene:
            print("sceneName is:", item['sceneName'])
            if item['sceneName'] != "IDLE":
                print("sceneName delete:", item['sceneName'])
                self.request_client.remove_scene(name=item['sceneName'])
                time.sleep(1)
            else:
                self.have_idle = True
        time.sleep(2)
        # print(self.event_client.callback.get())

        try:
            if not self.have_idle:
                print("crate IDLE")
                self.create_scene("IDLE")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_scene("LIVE_M")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_scene("LIVE_V")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_scene("SCHEDULE")
        except:
            pass
        try:
            self.create_scene("SCHEDULE_S")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_scene("VTV")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_scene("LIVE_S")
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_vtv_input_source("LIVE_M","live_m",[""], self.width, self.height)
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_vlc_input_source("LIVE_V","live_v",[""], self.width, self.height)
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_vlc_input_source("SCHEDULE","mySource",[""], self.width, self.height)
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_slideshow(
                scene_name="SCHEDULE_S",
                source_name="slideshow_s", 
                image_list = [ 
                ],
                slide_time= 3000,
                transition="slide",
                transition_speed= 700,
                width=self.width,
                height=self.height,
                before_version_30=False
            )
        except:
            pass
        time.sleep(0.5)
        try:
            self.create_slideshow(
                scene_name="LIVE_S",
                source_name="slideshow_l", 
                image_list = [ 
                ],
                slide_time= 3000,
                transition="slide",
                transition_speed= 700,
                width=1920,
                height=1080,
                before_version_30=False
            )
        except:
            pass
         # Bắt đầu ghi log
        self.start_logging()

    def start_logging(self):
        log_thread = threading.Thread(target=self.log_stats, daemon=True)
        log_thread.start()

    def log_stats(self):
        os.makedirs('log', exist_ok=True)
        log_filename = os.path.join('log', f"{self.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M.txt')}")

        
        with open(log_filename, "a") as log_file:
            while True:
                stats = self.get_stats()  # Giả sử bạn có hàm này để lấy stats
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_stats = {
                    "cpu_usage": round(stats.cpu_usage, 2),  # % CPU usage
                    "memory_usage": round(stats.memory_usage, 2),  # Memory usage in MB
                    "available_disk_space": round(stats.available_disk_space, 2),  # Disk space in MB
                    "active_fps": round(stats.active_fps, 2),  # Active FPS
                    "average_frame_render_time": round(stats.average_frame_render_time, 2),  # Time per frame in ms
                    "render_skipped_frames": stats.render_skipped_frames,  # Skipped frames in render thread
                    "render_total_frames": stats.render_total_frames,  # Total frames rendered
                    "output_skipped_frames": stats.output_skipped_frames,  # Skipped frames in output thread
                    "output_total_frames": stats.output_total_frames,  # Total frames outputted
                    "websocket_session_incoming_messages": stats.web_socket_session_incoming_messages,  # Incoming WebSocket messages
                    "websocket_session_outgoing_messages": stats.web_socket_session_outgoing_messages  # Outgoing WebSocket messages
                }
                log_file.write(f"{timestamp} - {formatted_stats}\n")
                log_file.flush()
                time.sleep(30)  # Đợi 30 giây trước khi ghi log tiếp theo       


    def __start_checking(self):
        if self.id == None:
            return
        def run_check():
            while True:
                time.sleep(10)
                if self.__check_streamlink_error() == False:
                    self.__send_streamlink_to_server()
                

        thread = threading.Thread(target=run_check)
        thread.daemon = True  # Đảm bảo thread sẽ dừng khi chương trình chính kết thúc
        thread.start()

    def __check_streamlink_error(self):
        try:
            response = requests.get(self.streamlink_m3u8, timeout=10)
            # Kiểm tra mã trạng thái HTTP và content type
            if response.status_code == 200 and 'application/vnd.apple.mpegurl' in response.headers.get('Content-Type', ''):
                return True
            else:
                self.streamlink_m3u8 = None
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return False
        
    def __send_streamlink_to_server(self):
        if self.id is None:
            return
        time.sleep(10)
        link_url = None
        while not link_url:
            try:
                # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Try to get link m3u8 {self.name}")
                link =   streamlink.streams(self.streamlink)
                link_url = link.get("best").url
            except:
                pass
            time.sleep(1)

        self.streamlink_m3u8 = link_url
        # header = {
        #     'Content-Type': 'application/json'
        # }
        # data = {
        #     "user": "admin",
        #     "pass": "admin",
        #     "cs":"0123456789",
        #     "id":self.id,
        #     "name":self.name,
        #     "link":self.streamlink_m3u8
        # }
        # # print(self.streamlink_m3u8)
        # response = requests.post(self.url, headers=header, json=data)
        # timeout = 0
        # while timeout < 5 and response.status_code != 200:
        #     print(f"Send url fail, try again {timeout}:", response.status_code)
        #     response = requests.post(self.url, headers=header, json=data)
        #     timeout = timeout + 1
        #     time.sleep(0.5)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Post streamlink {self.name}")
        # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Post streamlink {self.name} res: {response.status_code}")


    def change_id(self, id, name):
        self.id = id
        self.name = name
        self.__send_streamlink_to_server()

    def get_stream_link(self):
        return self.streamlink_m3u8
    # --------------------------------- setter and getter -----------------------------------
    # reconnect callback setter and getter:
    def set_on_reconnected_callback(self,func):
        self.on_reconnected = func

    def call_on_reconnected(self):
        # if self.on_reconnected != None:
        #     self.on_reconnected()
        pass
    # MQTT handler setter
    def set_mqtt_handler(self,mqtt_handler):
        self.mqtt_handler = mqtt_handler
    
    def set_mqtt_topic(self,mqtt_topic):
        self.mqtt_topic = mqtt_topic

    #--------------------------------------------- on event handler methods obs websocket------------------------------------------
    def on_stream_state_changed(self,data):
        """ handler function when stream state changed:

        Args:
            data (dict): data of stream state
            - attr:
                + output_active: the output is active or not
                + output_state: The specific state of the output OBS_WEBSOCKET_OUTPUT_STARTING, OBS_WEBSOCKET_OUTPUT_STARTED,
                                OBS_WEBSOCKET_OUTPUT_STOPPING, OBS_WEBSOCKET_OUTPUT_STOPPED, OBS_WEBSOCKET_OUTPUT_RECONNECTING, OBS_WEBSOCKET_OUTPUT_RECONNECTED
        """
        # print("[Stream state change]")
        # print(data.attrs())
        # print("Output active", data.output_active)
        # print("Output state", data.output_state)
        # print(type(data.output_state))
        
        if data.output_state == "OBS_WEBSOCKET_OUTPUT_RECONNECTED":
            print("trigger reconnnected event")
            self.call_on_reconnected()
            
            
        # if data.output_state ==
    def on_scene_item_transform_changed(self, data):
        print("on trasnform")
        
    def  on_media_input_action_triggered(self,data):
        print("on media action")
        print(data.attrs())
        
    def on_scene_transition_video_ended(self,data):
        print("on media action")
        print(data.attrs())
        
    def on_media_input_playback_ended(self,data):
        print("[media input playback end]")
        print(data.attrs())
        
        
        
    # ------------------------------------------------------request method  obs websocket-----------------------------------------------
    def get_input_list(self,kind=None):
        """
        Get inputs of obs
        Args:
            kind (String, optional): Restrict the array to only inputs of the specified kind. Defaults to None.

        Returns:
        Object : response contain field "inputs" (Array<Object>)
        """
        
        response = self.request_client.get_input_list(kind)
        self.printJsonObjectList(response.inputs)
        return response.inputs
    
    def get_stats(self):
        return self.request_client.get_stats()

    def get_input_settings(self,name):
        """ 
        To create the entire settings object,
        overlay inputSettings over the defaultInputSettings provided by GetInputDefaultSettings

        Args:
            name (String): Name of the input to get the settings of

        Returns:
            Object contain:
                +input_settings(Object): Object of settings for the input
                +input_kind(String):The kind of the input
        """
        payload = {"inputName": name}
        response =  self.request_client.send("GetInputSettings", payload)
        print(response.attrs())
        print(response.input_kind)
        self.printJsonObject(response.input_settings)
        return response

        
    def set_input_settings(self, name, settings, overlay):
        """
        Sets the settings of an input.

        Args:
            name (String, optional): Name of the input to set the settings of
            settings (Object):
                -attr: can use get_input_settings to see an example
                    + playback_behavior(String): ex: "stop_restart"
                    + playlist(Array<object>):
                        -item:
                            hidden(bool): video is hidden or not
                            selected(bool):video is sellected 
                            value(string): path to video or source
                    + shuffle(bool): playlist is played random or not
            overlay (bool, optional):   True == apply the settings on top of existing ones, 
                                        False == reset the input to its defaults, then apply settings.

        Returns: None
        """
        # print("33333333")
        # print(settings)
        return self.request_client.set_input_settings(name, settings, overlay)   
    
    def get_scene_item_list(self,name):
        """ 
        get scene item list of an scene

        Args:
            name (String): Name of the scene

        Returns:
            Object contain:
                scene_items (Array<Objest>) : Array of scene items in the scene
        """
        payload = {"sceneName": name}
        response =  self.request_client.send("GetSceneItemList", payload)
        self.printJsonObject(response.scene_items)
        return response



    def get_stream_service_settings(self):
        """
        Gets the current stream service settings (stream destination)

        Returns:
            object:
            - attr:
                + stream_service_type (String): Stream service type, like rtmp_custom or rtmp_common
                + stream_service_settings(Object): Stream service settings
                    -attr:
                        + bwtest (Bool): bandwidth test option
                        + key (String): stream key of rtmp protocol
                        + protocol (String):  protocol is using
                        + server (String): server is used
                        + use_auth (Bool): use authentication or not
        """
        response =  self.request_client.get_stream_service_settings() 
        self.printJsonObject(response.stream_service_settings)
        print(response.stream_service_type)
        return response
    
    def set_stream_service_settings(self,stream_service_type,stream_service_settings):
        """
        Sets the current stream service settings (stream destination)
        Note: Simple RTMP settings can be set with type rtmp_custom and the settings fields server and key.
        

        Args:
            stream_service_type (String): type of stream service to apply. Example: rtmp_common or rtmp_custom
            stream_service_settings (Object): Settings to apply to the service, can use get_stream_service_settings to see an example
        """
        self.request_client.set_stream_service_settings(ss_type = stream_service_type, ss_settings = stream_service_settings)
                
    def start_stream(self):
        """
        start livestream on OBS
        """
        self.request_client.start_stream()
        
    def stop_stream(self):
        """
        Stop Livestream on OBS
        """
        self.request_client.stop_stream()
        
    def toggle_stream(self):
        """
        toggle Livestream on OBS
        """
        self.request_client.toggle_stream()
        
    def get_stream_status(self):
        """
        Gets the status of the stream output.
        Returns:
            Object: 
            -attr:
                + output_active (Bool): Whether the output is active
                + output_bytes (Boolean): Whether the output is active
                + output_timecode (String): Current formatted timecode string for the output
                + utput_duration (Number): Current duration in milliseconds for the output
                + output_congestion (Number): Congestion of the output
                + output_reconnecting (Number): Number of bytes sent by the output
                + output_skipped_frames (Number): Number of frames skipped by the output's process
                + output_total_frames (Number): Total number of frames delivered by the output's process
        """
        request = self.request_client.get_stream_status()
        print("Stream Status")
        print(f"\t output active: {request.output_active}")
        print(f"\t output bytes: {request.output_bytes}")
        print(f"\t output congestion: {request.output_congestion}")
        print(f"\t output duration: {request.output_duration}")
        print(f"\t output reconnecting: {request.output_reconnecting}")
        print(f"\t output skipped frames: {request.output_skipped_frames}")
        print(f"\t output timecode:{request.output_timecode}")
        print(f"\t output total frames:{request.output_total_frames}")
        return request
    
    def check_stream_is_active(self):
        response = self.get_stream_status()
        return response.output_active
    
    def is_exited_in_playlist(self,source_name,video_path):
        """
        check video is in playlist or not

        Args:
            source_name (String): name of source
            video_path (String): video path want to check is exited or not

        Returns:
            Bool: true if exist otherwise false if not
        """
        #load input_settings of source_name
        response = self.get_input_settings(source_name)
        input_settings = response.input_settings
        for item in input_settings.get('playlist'):
            if item.get("value") == video_path:
                return True
        return False
    
    def add_video_to_playlist(self, source_name, video_path, hidden = False, selected = False):
        """
        Add an video to playlist of the source 

        Args:
            source_name (String): Name of source
            path_video (String): path to the video in server run obs
        Return:
            Bool: true if success, false if not
        """
        
        #load input_settings of source_name
        response = self.get_input_settings(source_name)
        input_settings = response.input_settings
        # self.printJsonObject(input_settings.get('playlist'))
        # creating an item to add into list if this item is not exist in playlist
        if self.is_exited_in_playlist(source_name,video_path):
            return False
        item = {
                "hidden": hidden,
                "selected": selected,
                "value": video_path
        }
        input_settings.get('playlist').append(item)
        # self.printJsonObject(input_settings.get('playlist'))
        # update playlist
        self.request_client.set_input_settings(name = source_name, settings = input_settings,overlay = True)
        return True
    
    
    def remove_a_video_in_playlist(self, source_name, video_path):
        """
        Remove an video in playlist

        Args:
            source_name (String): name of source which you want to remove an video in playlist
            video_path (String): path of video you want to remove

        Returns:
            Bool: true if remove success, false if not
        """
        # load input_settings of source_name
        response = self.get_input_settings(source_name)
        input_settings_playlist = response.input_settings.get('playlist')
        # return false because playlist is empty: 
        if len(input_settings_playlist) == 0:
            return False
        
        # remove item playlist
        new_playlist = [item for item in  input_settings_playlist if item.get('value') != video_path]
        # update playlist
        if len(new_playlist) == len(input_settings_playlist):
            return False
        
        new_input_settings = {
            "playlist" : new_playlist
        }
        self.request_client.set_input_settings(name = source_name, settings =  new_input_settings ,overlay = True)
        return True
    
    def set_stream_service_key_server(self,streamkey,server):
        """
        Set stream key an server to obs websocket

        Args:
            streamkey (String): streamkey of rtmp protocol
            server (String): server name domain or ip
        """
        stream_service_type = "rtmp_custom"
        stream_service_settings = {
            "bwtest": False,
            "key": streamkey,
            "protocol": "RTMP",
            "server": server,
            "use_auth": False
        }
        self.set_stream_service_settings(stream_service_type,stream_service_settings)
    
    
    def set_input_playlist (self, video_path_list, source_name="mySource"):
        """
        Set video list to playlist 
        

        Args:
            video_path_list (_type_): _description_
        """
        playlist = []
        for idx,video in enumerate(video_path_list):
            item = {
                "hidden": False,
                "selected": True if idx == 0 else False,
                "value": video
            }

            playlist.append(item)

            
        settings = {
            "playback_behavior": "stop_restart",
            "playlist": playlist,
            "shuffle": False
        }
        
        self.set_input_settings(name=source_name, settings=settings, overlay= False )
        
                    
    def set_current_program_scene(self,scene_name):
        self.request_client.set_current_program_scene(scene_name)
    
    
    def get_scene_item_id(self,scene_name,source_name):
        """get id on an item in a scene

        Args:
            scene_name (String): name of scene contain item
            source_name (String): name of source of this item

        Returns:
            Object: 
                -attr:
                    + scene_item_id	(int): int ID of the scene item
        """
        
        response = self.request_client.get_scene_item_id(scene_name,source_name)
        return response.scene_item_id
            
    def get_scene_item_transform(self, scene_name, source_name):
        """get stransform of an item source
        Description: obs manger ui of an source by id -> get id from source name to use

        Args:
            scene_name (String): name of scene contain item
            source_name (String): name of source of this item
        Return:
            Object: 
                - attr:
                    + scene_item_transform(Object) Object containing scene item transform info: see detail in set_scene_item_transform at the args description
                    

        """
        id_source_name =  self.get_scene_item_id(scene_name, source_name)
        response = self.request_client.get_scene_item_transform(scene_name,id_source_name)
        self.printJsonObject(response.scene_item_transform)
        return response.scene_item_transform
    
    def set_scene_item_transform(self,scene_name, source_name,transform):
        """ Sets the transform and crop info of a scene item.
        Note:
            just change anything but except: sourceHeight,sourceWidth, height, width because there is read only, I add here for the explain the get_scene_item_transform
        Args:
            scene_name (String): name of scene contain item
            source_name (String): name of source of this item
            transform (object): {
                
                "sourceHeight" (READ_ONLY): original height of source
                "sourceWidth" (READ_ONLY): original width of source
                "width" (READ_ONLY): actial width of video when resize (by bouding, resizw or crop)
                "height (READ_ONLY)": actial height of video when resize ((by bouding, resizw or crop))
                
                "alignment": center(0),centeleft(1), centerright(2), topcenter(4), topleft(5), topright(6),bottomcenter(8) ,bottomleft(9), bottomright(10)
                "positionX","positionY":  x, y of source (top left point of rectangle)
                "rotation": ration in dergee of source (ex:90, -90, 45, ...)
                
                "scaleX": ratio = original width/sourceWidth,
                "scaleY": ratio = original height/sourceheight,
                
                "boundsType": 
                    "OBS_BOUNDS_NONE",
                    "OBS_BOUNDS_STRETCH",
                    "OBS_BOUNDS_SCALE_INNER", 
                    "OBS_BOUNDS_SCALE_OUTER" , 
                    "OBS_BOUNDS_SCALE_TO_WIDTH",
                    "OBS_BOUNDS_SCALE_TO_HEIGHT",
                    "OBS_BOUNDS_MAX_ONLY"
                    
                "boundsAlignment": center(0), centeleft(1), centerright(2), topcenter(4), topleft(5), topright(6),bottomcenter(8) ,bottomleft(9), bottomright(10)
                "boundsHeight": height of bounding box,
                "boundsWidth": weidth of bounding box,
                
                "cropToBounds": false,
                "cropLeft": number pixel video crop from left of source,
                "cropTop": number pixel video crop from top of source,
                "cropBottom": number pixel video crop from bottom of source,
                "cropRight": number pixel video crop from right of source, 
            }
        """
        id_source_name =  self.get_scene_item_id(scene_name, source_name)
        self.request_client.set_scene_item_transform(scene_name,id_source_name,transform)
        
    def get_original_source_size(self, scene_name,source_name):
        """ Get original size of source

        Args:
            scene_name (String): name of scene contain item
            source_name (String): name of source of this item

        Returns:
            _type_: _description_
        """
        
        response = self.get_scene_item_transform(scene_name,source_name)
        return response.get("sourceWidth"), response.get("sourceHeight")
        
        
        
    def set_size_of_source(self, scene_name, source_name, width, height):
        # original_width, original_height = self.get_original_source_size(scene_name, source_name)
        transform = {
            # "sourceHeight": 720.0,
            # "sourceWidth": 1080.0,
            
            "alignment": 5,
            "positionX": 0.0,
            "positionY": 0.0,
            "rotation": 0.0,
            
            # "width": 1080,
            # "height": 720,
            # "scaleX": width/original_width,
            # "scaleY": height/original_height,
            
            "boundsType": "OBS_BOUNDS_STRETCH",
            "boundsAlignment": 5,
            "boundsWidth": width,
            "boundsHeight": height,
            
            "cropToBounds": False,
            "cropLeft": 0,
            "cropTop": 0,
            "cropBottom": 0,
            "cropRight": 0,
        }
        self.set_scene_item_transform(scene_name, source_name,transform)
        
        
    def get_media_input_status(self, source_name):
        """ Get status of an media 
            "OBS_MEDIA_STATE_NONE",
            "OBS_MEDIA_STATE_PLAYING",
            "OBS_MEDIA_STATE_OPENING",
            "OBS_MEDIA_STATE_BUFFERNG",
            "OBS_MEDIA_STATE_PAUSED"
            "OBS_MEDIA_STATE_STOPPED",
            "OBS_MEDIA_STATE_ENDED",
            "OBS_MEDIA_STATE_ERROR"
        Args
            source_name (String): name of media source
        return:
            the reponse is an object with:
            -attr:
                + media_state (String): State of the media input
                + media_duration (Int): Total duration of the playing media in milliseconds. null if not playing
                + media_cursor (Int): Position of the cursor in milliseconds. null if not playing
        """
        response = self.request_client.get_media_input_status(source_name)
        
        return response.media_state
    
    def trigger_media_input_action(self,source_name, action):
        """ Trigger an action on media input

        Args:
            source_name (String): Name of the media input
            action (String): Identifier of the ObsMediaInputAction enum
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NONE
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT
                + OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS
                
        """
        self.request_client.trigger_media_input_action(source_name, action)
        
    def get_source_active(self,source_name):
        """ Gets the active and show state of a source.

        Args:
            source_name (String): name of source

        Returns:
            Object: 
            - attrs:
                + video_active (Boolean):	Whether the source is showing in Program
                + video_showing (Boolean): Whether the source is showing in the UI (Preview, Projector, Properties)
        """
        response = self.request_client.get_source_active(source_name)
        # self.printJsonObject(response)
        return response.video_active
    
    def get_output_list(self):
        """Gets the list of available outputs.

        Returns:
            Array<Object>:	Array of outputs
        """
        response = self.request_client.get_output_list()
        
        self.printJsonObjectList(response.outputs)
        return response
    

    def get_scene_item_enabled(self,scene_name,source_name):
        """get the enable state of a scene item.

        Args:
            scene_name (String): Name of the scene the item is in
            source_name (Strign): Name of the item source 

        Returns:
            bool: Whether the scene item is enabled. true for enabled, false for disabled
        """
        
        item_id = self.get_scene_item_id(scene_name,source_name)
        respone = self.request_client.get_scene_item_enabled(scene_name,item_id)
        # print(respone.scene_item_enabled)
        return respone.scene_item_enabled
        
    def set_scene_item_enabled(self,scene_name,source_name,is_enable):
        """ set the enable state of a scene item.

        Args:
            scene_name (String): Name of the scene the item is in
            source_name (Strign): Name of the item source 
            is_enable (bool): the state of item
        """
        item_id = self.get_scene_item_id(scene_name,source_name)
        self.request_client.set_scene_item_enabled(scene_name,item_id, is_enable)
        
    def toggle_scene_item_enabled(self,scene_name,source_name):
        """ toggle the enable state of a scene item.

        Args:
            scene_name (String): Name of the scene the item is in
            source_name (Strign): Name of the item source 
        """
        current = self.get_scene_item_enabled(scene_name,source_name)
        self.set_scene_item_enabled(scene_name,source_name,not current)
        # print(not current)
        time.sleep(1)
        # print(current)
        self.set_scene_item_enabled(scene_name,source_name,current)
        time.sleep(1)
        
    def create_scene(self, scene_name):
        """Creates a new scene in OBS.

        Args:
            scene_name (String): name of scene want to create
        """
        self.request_client.create_scene(scene_name)
        
    def remove_scene(self, scene_name):
        """ Removw a scene in OBS

        Args:
            scene_name (String): name of scene want to remove
        """
        self.request_client.remove_scene(scene_name)
        
    def set_scene_name(self, old_name, new_name):
        """ rename a scene

        Args:
            old_name (string): name of scene want to rename
            new_name (string): new name of scene
        """
        self.request_client.set_scene_name(old_name,new_name)
        
        
    def create_input(self, scene_name, input_name, input_kind, input_setting, scene_item_enable):
        """Creates a new input, adding it as a scene item to the specified scene.

        Args:
            scene_name (String): Name of the scene to add the input to as a scene item
            input_name (String): Name of the new input to created
            input_kind (String): The kind of input to be created_
            input_setting (Object):	Settings object to initialize the input with (use get input setting to get the template)
            scene_item_enable (Boolean)	Whether to set the created scene item to enabled or disabled
        Return:
            int : id of input created
        """
        response = self.request_client.create_input(scene_name, input_name, input_kind, input_setting, scene_item_enable)
        if response is None:
            print("Cannot create input")
            return None
        else:
            print(f"Create input {input_name}(kind: {input_kind}) success")
            return response.scene_item_id
            
            
    def remove_input(self, input_name):
        """ Removes an existing input.

        Args:
            input_name (String): Name of the input to remove
        """
        self.request_client.remove_input(input_name)
    
    def set_input_vtv(self, source_name , url):
        input_setting = {
            "input": url,
            "is_local_file": False,
            # "restart_on_activate": true
        }
        self.set_input_settings(name=source_name, settings=input_setting, overlay= False )
           
    def create_vtv_input_source(self, scene_name, source_name , url, width = 0 , height = 0):
        """ creating media source of obs to play and vtv url

        Args:
            scene_name (String): Name of the scene to add the input to as a scene item
            input_name (String): Name of the new input to created
            width (int): width of source
            height (int) height of source
        """
        input_kind = "ffmpeg_source" 
        input_setting = {
            "input": url,
            "is_local_file": False,
            # "restart_on_activate": true
        }
        scene_item_enable = True
        self.request_client.create_input(scene_name, source_name, input_kind, input_setting, scene_item_enable)
        if width == 0:
            width = self.width
        if height == 0:
            height = self.height
        self.set_size_of_source(scene_name, source_name, width, height)
        
    def create_vlc_input_source(self, scene_name, source_name , playlist, width = 0, height = 0):
        """ Creating vlc source of obs to play and vtv url

        Args:
            scene_name (String): Name of the scene to add the input to as a scene item
            input_name (String): Name of the new input to created
            width (int): width of source
            height (int) height of source
        """
        input_kind = "vlc_source" 
        playlist_setting = []
        for video in playlist:
            item = {
                "hidden": False,
                "selected": False,
                "value": video
            } 
            playlist_setting.append(item)
        input_setting = {
            "playlist": playlist_setting
        }
        scene_item_enable = True    
        self.request_client.create_input(scene_name, source_name, input_kind, input_setting, scene_item_enable)
        if width == 0:
            width = self.width
        if height == 0:
            height = self.height
        self.set_size_of_source(scene_name, source_name, width, height)
    
    
    def create_slideshow(self, scene_name, source_name , image_list, slide_time=2000, transition="slide",transition_speed = 700, width = 0, height = 0, before_version_30 = True):
        """ create slide show input

        Args:
            scene_name (String): Name of scene hold input.
            source_name (String): name of slideshow input want to create
            image_list (List<String>): list of file image path display on slideshow
            slide_time (int, optional): time to transition to next slide. Defaults to 2000.
            transition (str, optional): transition mode("cut", "fade", "swipe" and "slide"). Defaults to "slide".
            transition_speed (int, optional): time of effect transition slide. Defaults to "700".
            width (int, optional): width of slide. Defaults to 0.
            height (int, optional): height of slide. Defaults to 0.
        """
        image_files = [
            {
                "hidden":False,
                "selected":False,
                "value": image
            }
            for image in image_list
        ]
        input_setting = {
            "files": image_files,
            "slide_time": slide_time,
            "transition": transition,
            "transition_speed": transition_speed,
            "use_custom_size": f"{width}x{height}"
        }
        input_kind = "slideshow" if before_version_30 else "slideshow_v2"       
        scene_item_enable = True
        self.request_client.create_input(scene_name, source_name, input_kind, input_setting, scene_item_enable)        
    
    
    
    def set_slide_show_settings(self,source_name, image_list, slide_time=2000, transition="slide",transition_speed = 700, overlay=True):
        """ set slide show setting
        Args:
            source_name (String): name of slideshow input want to create
            image_list (List<String>): list of file image path display on slideshow
            slide_time (int, optional): time to transition to next slide. Defaults to 2000.
            transition (str, optional): transition mode("cut", "fade", "swipe" and "slide"). Defaults to "slide".
            transition_speed (int, optional): time of effect transition slide. Defaults to "700".
            width (int, optional): width of slide. Defaults to 0.
            height (int, optional): height of slide. Defaults to 0.
            overlay (bool, optional):   True == apply the settings on top of existing ones, 
                                        False == reset the input to its defaults, then apply settings.
        """
        image_files = [
            {
                "hidden":False,
                "selected":False,
                "value": image
            }
            for image in image_list
        ]
        input_setting = {
            "files": image_files,
            "slide_time": slide_time,
            "transition": transition,
            "transition_speed": transition_speed,
            "use_custom_size": f"{self.width}x{self.height}"
        }
        self.set_input_settings(source_name,input_setting, overlay)
        
    def add_image_to_slideshow(self,source_name, image_list):
        """ add a list of image to a slideshow

        Args:
            source_name (String): Name of slideshow input source
            image_list (List<String>): list of images want to add into
        """
        image_files = [
            {
                "hidden":False,
                "selected":False,
                "value": image
            }
            for image in image_list
        ]
        input_setting = self.get_input_settings(source_name).input_settings
        files = input_setting["files"]
        files.extend(image_files)
        input_setting["files"] = files
        self.set_input_settings(source_name,input_setting, overlay=True)
        
        
        
    def remove_image_to_slideshow(self,source_name, image_list):
        """ remove a list of image to a slideshow

        Args:
            source_name (String): Name of slideshow input source
            image_list (List<String>): list of images want to remove
        """
        image_files = [
            {
                "hidden":False,
                "selected":False,
                "value": image
            }
            for image in image_list
        ]
        input_setting = self.get_input_settings(source_name).input_settings
        files = input_setting["files"]
        files = [file for file in files if file not in image_files]
        input_setting["files"] = files
        self.set_input_settings(source_name,input_setting, overlay=True)
    
        
        
        
    
            
            
            
    
def main():
    # stream_key = "live_1044211682_Ol34MomAqRm3Ef7s0jwrKq0KNGj3Ku"
    # server = "rtmp://live.twitch.tv/app"
    # my_obs.get_input_list()
    # my_obs.get_input_settings("mySource")
    # my_obs.get_scene_item_list('scene1')
    
    # my_obs.set_stream_service_key_server(streamkey=stream_key,server=server)
    # my_obs.start_stream()
    # my_obs.get_stream_service_settings()
    # my_obs.get_input_settings(name="mySource")
    # my_obs.add_video_to_playlist("mySource","C:/Users/NHAN/OneDrive/Desktop/workspace/CMS/mp4_videos/ship.mp4")
    # my_obs.remove_a_video_in_playlist("mySource","C:/Users/NHAN/OneDrive/Desktop/workspace/CMS/mp4_videos/ship.mp4")
    # while True:
    #     try: 
    #         time.sleep(1)
    #     except KeyboardInterrupt:
    #         my_obs.stop_stream()
    #         break
    pass
    
     
def test_for_failed_streamkey():
    my_obs1 = OBS_controller(port=4444,password="123456")

    my_obs1.set_stream_service_key_server(streamkey="live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk",server="rtmp://live.twitch.tv/app")
    # my_obs.set_stream_service_key_server(streamkey="abs",server="rtmp://live.twitch.tv/app")
    time.sleep(5)
    my_obs1.get_stream_service_settings()
    my_obs1.start_stream()

    time.sleep(1)
    my_obs1.get_stream_status()
    print("STREAM LINK")
    # my_obs1.set_input_playlist(["https://live3.thvli.vn/sJrg6YvmzZI2soZYl9hAnA/1713898152/thvli/thvl1-abr/thvl111220/thvl1-1080p/chunks.m3u8"])
    time.sleep(2)
    print("HIDDEN")
    my_obs1.set_current_program_scene("Scene")
    
    # print(f"stream is active : {my_obs.check_stream_is_active()}")
    while True:
        try: 
            time.sleep(1)
        except KeyboardInterrupt:
            if my_obs1.check_stream_is_active() :
                my_obs1.stop_stream()

            # if my_obs2.check_stream_is_active() :
            #     my_obs2.stop_stream()
            break


    
def test_on_stream_state_changed():
    my_obs1 = OBS_controller(port=4455,password="123456")
    my_obs1.start_stream()
    while True:
        try: 
            time.sleep(1)
        except KeyboardInterrupt:
            if my_obs1.check_stream_is_active() :
                my_obs1.stop_stream()
            break
        
        
def test_transfrom():
    my_obs1 = OBS_controller(id=None,name = 0 , streamlink="http://www.twitch/nhanlow",host="localhost",port=1139,password="123456")
 
    while True:
        try: 
            my_obs1.get_stats()
            time.sleep(1)
        except KeyboardInterrupt:

            break

def test_api_get_stats():
    my_obs = OBS_controller( id="live_1127937001_mk0mXlFKsXjeqQ9UmVFroNbJAWxvxW", streamlink="https://www.twitch.tv/hehe0082", name="hehe0082", port=1133,password="123456")
    while(1):
        stats = my_obs.get_stats()
        formatted_stats = {
            "cpu_usage": round(stats.cpu_usage, 2),  # % CPU usage
            "memory_usage": round(stats.memory_usage, 2),  # Memory usage in MB
            "available_disk_space": round(stats.available_disk_space, 2),  # Disk space in MB
            "active_fps": round(stats.active_fps, 2),  # Active FPS
            "average_frame_render_time": round(stats.average_frame_render_time, 2),  # Time per frame in ms
            "render_skipped_frames": stats.render_skipped_frames,  # Skipped frames in render thread
            "render_total_frames": stats.render_total_frames,  # Total frames rendered
            "output_skipped_frames": stats.output_skipped_frames,  # Skipped frames in output thread
            "output_total_frames": stats.output_total_frames,  # Total frames outputted
            "websocket_session_incoming_messages": stats.web_socket_session_incoming_messages,  # Incoming WebSocket messages
            "websocket_session_outgoing_messages": stats.web_socket_session_outgoing_messages  # Outgoing WebSocket messages
        }

        # In ra kết quả
        print(formatted_stats)
        time.sleep(2)

def test_api_input_slideshow():
    my_obs = OBS_controller( id="live_1127937001_mk0mXlFKsXjeqQ9UmVFroNbJAWxvxW", streamlink="https://www.twitch.tv/hehe0082", name="gutsssssssss9", port=1133,password="123456")
    # my_obs.get_input_list()
    
    my_obs.create_slideshow(
        scene_name="VTV",
        source_name="slideshow", 
        image_list = [ 
            "D:/background/wall1.jpg",
            "D:/background/wall2.jpg",
        ],
        slide_time= 3000,
        transition="cut",
        transition_speed= 700,
        width=1920,
        height=1080
    )
    my_obs.get_input_settings("slideshow")
    my_obs.set_slide_show_settings(
        source_name="slideshow", 
        image_list = [ 
            "D:/background/wall1.jpg",
            "D:/background/wall2.jpg",
            "D:/background/wall3.jpg",
            "D:/background/wall4.jpg", 
            "D:/background/wall5.jpg",
            "D:/background/wall6.jpg"
        ],
        slide_time= 2000,
        transition="slide",
        transition_speed= 500,
    )
    # # my_obs.get_input_settings("slideshow")
    
    my_obs.add_image_to_slideshow(
        source_name = "slideshow", 
        image_list = [
            "D:/background/wall7.jpg",
            "D:/background/wall8.jpg",    
        ]
    )
    # my_obs.get_input_settings("slideshow")
    
    # my_obs.remove_image_to_slideshow(
    #     source_name = "slideshow", 
    #     image_list = [
    #         "D:/background/wall7.jpg",
    #         "D:/background/wall8.jpg",    
    #     ]
    # )
    # my_obs.get_input_settings("slideshow")
    
    # my_obs.remove_input("slideshow")
    
    

if __name__ == "__main__":

    test_api_get_stats()

    
