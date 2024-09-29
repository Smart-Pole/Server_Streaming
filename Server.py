from flask import Flask, request, jsonify, abort,send_from_directory
from datetime import datetime, time, timedelta
from OBS_Controller_oop import OBS_controller
from mqtt import MyMQTTClient
from database import TaskDatabase
from TaskInfor import TaskInformation
from StreamScheduler import StreamScheduler
from Pole_infor import Pole_manager
import threading
import schedule
import json
import inspect
import re
import os
import time
import copy
from flask_cors import CORS
import streamlink 
import streamlink.stream
import sys

app = Flask(__name__)
CORS(app)

FolderVideoPath = "/home/streamlink1/Desktop/stream_server/Server_Streaming/video/"
OBSWidth = 1920
OBSHeight = 1080
UPLOAD_FOLDER = FolderVideoPath
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = FolderVideoPath

my_schedulers = [
    StreamScheduler(Stream=1, FileLog="log_thread1.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread1", OBSPass="123456", OBSPort=1131,OBSId="sctv1",OBSName="SCTV 1",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk", StreamLink="https://www.twitch.tv/gutsssssssss9", NameStream="gutsssssssss9"),
    StreamScheduler(Stream=2, FileLog="log_thread2.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread2", OBSPass="123456", OBSPort=1132,OBSId="sctv2",OBSName="SCTV 2",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1071558463_6geWoWQgWadKOjby2mqDj40qeiW9fg", StreamLink="https://www.twitch.tv/dat_live2", NameStream="dat_live2"),
    # StreamScheduler(Stream=3, FileLog="log_thread3.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread3", OBSPass="123456", OBSPort=1133,OBSId="sctv3",OBSName="SCTV 3",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1071557915_S0GK8ydVBO5EfOREfzEmAtJNbL09fL", StreamLink="https://www.twitch.tv/dat_live1", NameStream="dat_live1"),
    # StreamScheduler(Stream=4, FileLog="log_thread4.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread4", OBSPass="123456", OBSPort=1134,OBSId="vtv4",OBSName="VTV 4",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1039740022_rGAe65XCi8xif5QyFwQLeRLdVKtX2O", StreamLink="https://www.twitch.tv/hehe0088", NameStream="hehe0088"),
    # StreamScheduler(Stream=5, FileLog="log_thread5.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread5", OBSPass="123456", OBSPort=1135,OBSId="vtv5",OBSName="VTV 5",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1125130390_vqMoTYJF7jiOtTt8uM4oBS7DANMon8", StreamLink="https://www.twitch.tv/nhanlow", NameStream="nhanlow"),
    # StreamScheduler(Stream=6, FileLog="log_thread6.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread6", OBSPass="123456", OBSPort=1136,OBSId="vtv6",OBSName="VTV 6",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1044211682_Ol34MomAqRm3Ef7s0jwrKq0KNGj3Ku", StreamLink="https://www.twitch.tv/huynhnguyenhieunhan", NameStream="huynhnguyenhieunhan"),
    # StreamScheduler(Stream=7, FileLog="log_thread7.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread7", OBSPass="123456", OBSPort=1137,OBSId="vtv7",OBSName="VTV 7",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1127937398_28e30ICQkj916Yris7ysw3wSQnjkuQ", StreamLink="https://www.twitch.tv/nhanlow_v2", NameStream="nhanlow_v2"),
    # StreamScheduler(Stream=8, FileLog="log_thread8.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread8", OBSPass="123456", OBSPort=1138,OBSId="vtv8",OBSName="VTV 8",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1127041941_YqyrJHfYVm7NBtX7EIckVEZtMjuMde", StreamLink="https://www.twitch.tv/hehe0081", NameStream="hehe0081"),
    # StreamScheduler(Stream=9, FileLog="log_thread9.txt", VideoPath=FolderVideoPath, Database='task_infor.db', DataTable="thread9", OBSPass="123456", OBSPort=1139,OBSId="film",OBSName="Xem Phim",OBSWidth=OBSWidth,OBSHeight=OBSHeight, StreamKey="live_1127937001_mk0mXlFKsXjeqQ9UmVFroNbJAWxvxW", StreamLink="https://www.twitch.tv/hehe0082", NameStream="hehe0082"),
]

pole_manager = Pole_manager()

channel = {
           'Cartoon 1' : 'https://www.youtube.com/watch?v=Fjp2TdlTTIU',
           'Cartoon 2' : 'https://www.youtube.com/watch?v=cOLQACygN5A',
           'Disney 1' : 'https://www.youtube.com/watch?v=WFDbJY0eBGI',
           'Disney 2' : 'https://www.youtube.com/watch?v=x7I9aLJ4hKo',
           'Nat geo WILD' : 'https://www.youtube.com/watch?v=BJ3Yv572V1A',
           'ABC news' : 'https://www.youtube.com/watch?v=-mvUkiILTqI',
           'Nasa' : 'https://www.youtube.com/watch?v=0FBiyFpV__g',
           'THVL1' : 'https://www.thvli.vn/live/thvl1-hd',}
vtv_channel = {
           'VTV1' : 'http://127.0.0.1:9001/',
           'VTV2' : 'http://127.0.0.1:9002/',
           'VTV3' : 'http://127.0.0.1:9003/',
           'VTV4' : 'http://127.0.0.1:9004/',
           'VTV5' : 'http://127.0.0.1:9005/',}

################## begin MQTT

# AIO_USERNAME = "GutD"
# AIO_KEY = "aio_TNaU20Pmw9L7x41vHH4ifs3ZKSit"
# AIO_FEED_ID = ["live-stream"]
# mqtt_client = MyMQTTClient(AIO_USERNAME, AIO_KEY, AIO_FEED_ID)


# def publish_livestream(ID,link):
#     mess = {
#         "ID" : ID,
#         "link" : link
#     }
#     json_mess = json.dumps(mess)
#     mqtt_client.publish_data("live_stream",json_mess)


###################################################################################
def init():
    #start MQTT
    # mqtt_client.start()
    # publish_livestream([1,2,3],my_scheduler1.StreamLink)
    pass
    
def validateTimeformat(time_str):
    pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, time_str) is not None


def get_video_name():
    file_list = []
    for file_name in os.listdir(FolderVideoPath):
        if os.path.isfile(os.path.join(FolderVideoPath, file_name)):
            file_list.append(file_name)
    return file_list

def check_video_list(my_list):
    file_list = get_video_name()
    for item in my_list:
        if item not in file_list:
            return False
    return True

################################################################################################################################################################
@app.route('/get/stats')
def Get_Stats():
    performance_data = {}
    for scheduler in my_schedulers:
        name = f"stream_{scheduler.stream}"
        performance_data[name] =  scheduler.get_stats()
    return jsonify(performance_data), 200

@app.route('/change/streamInfo')
def Change_stream_Info():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    id   = request.args.get('id')
    name = request.args.get('name')
    if not id or not name:
        return jsonify({'error':  'Empty information'}), 400
    my_scheduler.change_stream_infor(id=id,name=name)
    return jsonify( {'success': {'message': 'Change information success'}}), 200



@app.route('/get/pole')
def Get_pole():
    pole_dict = {"Pole infomation": [pole.__dict__ for pole in pole_manager.pole_infor]}
    json_string = json.dumps(pole_dict, indent=4)
    return json_string, 200

@app.route('/set/poleArea')
def Set_pole_area():
    pole_id  = request.args.get('ID')
    area = request.args.get('area')

    pole_id = pole_id.split(',')
    pole_id = [int(id) for id in pole_id]
    my_pole_id = {pole.ID for pole in pole_manager.pole_infor}

    for ID in pole_id:
        if not (ID in my_pole_id):
            print(f"ID:{ID}")
            return jsonify({'error': 'Wrong ID'}), 400
        
    pole_manager.update_area(pole_id,area)
    return jsonify({'success': 'Update success'}), 400

@app.route('/set/poleStream/ID')
def Set_pole_stream_id():
    pole_id  = request.args.get('ID')
    stream  = request.args.get('stream')

    pole_id = pole_id.split(',')
    pole_id = [int(id) for id in pole_id]
    my_pole_id = {pole.ID for pole in pole_manager.pole_infor}
    print(my_pole_id)

    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    
    for ID in pole_id:
        if not (ID in my_pole_id):
            print(f"ID:{ID}")
            return jsonify({'error':  'Wrong ID'}), 400
        
    
    pole_manager.update_link_by_id(pole_ids=pole_id,new_link=my_scheduler.StreamLink,channel=my_scheduler.stream)
    # publish_livestream(pole_id,my_scheduler.StreamLink)

    return jsonify( {'success': {'message': 'Set stream'}}), 200

@app.route('/set/poleStream/area')
def Set_pole_stream_area():
    area  = request.args.get('area')
    stream  = request.args.get('stream')


    print(area)
    my_area = {pole.area for pole in pole_manager.pole_infor}

    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    

    if not (area in my_area):
        print(f"ID:{area}")
        return jsonify({'error':'Wrong area'}), 400
        
    
    pole_manager.update_link_by_area(area=area,new_link=my_scheduler.StreamLink,channel=my_scheduler.stream)
    # publish_livestream(pole_manager.get_ids_by_area(area),my_scheduler.StreamLink)

    return jsonify( {'success': {'message': 'Set stream'}}), 200
################################################################################################

@app.route('/get/video')
def Get_files_in_folder():
    file_list = get_video_name()
    return jsonify({'Video name': file_list}), 200

@app.route('/get/namestream')
def Get_NameStream():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'name twitch': f'{my_scheduler.NameStream}'}), 200

@app.route('/get/currentTask')
def Get_Current_Task():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400


    if not my_scheduler.CurrentTask:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'Current Task': "None"}), 200
    # Convert datetime objects to strings
    task = copy.deepcopy(my_scheduler.CurrentTask)
    if task:
        task.start_date = task.start_date.strftime("%Y-%m-%d")
        task.until = task.until.strftime("%Y-%m-%d") if task.until and task.until != "None" else None
        
    # Create dictionary
    task_dict = {'stream' : f'{my_scheduler.stream}' ,"Current Task": task.__dict__}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(task_dict, indent=4)
    
    return json_string


@app.route('/get/schedule')
def Get_schedule():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    # Convert datetime objects to strings
    mylist = copy.deepcopy(my_scheduler.ListTask)
    for task in mylist:
        task.start_date = task.start_date.strftime("%Y-%m-%d")
        task.until = task.until.strftime("%Y-%m-%d") if task.until and task.until != "None" else None

    # Create dictionary
    schedule_dict = {'stream' : f'{my_scheduler.stream}' ,"Schedule": [task.__dict__ for task in mylist]}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(schedule_dict, indent=4)

    return json_string

@app.route('/get/streamkey')
def Get_streamkey():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
    stream_key = my_scheduler.get_stream_key()
    print(stream_key)
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'Stream key': stream_key}), 200

@app.route('/set/streamkey')
def Set_Stream_Parameter():
    return jsonify({'error' : 'not allow'}), 200


@app.route('/get/TVchannel')
def get_TVchannel():
    combined_channel = {**channel, **vtv_channel}
    return jsonify({'TV channel' : f'{list(combined_channel.keys())}'})

@app.route('/live/TVchannel')
def Live_Steam_TV():
     # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400

    tv_channel  = request.args.get('tvchannel')
    
    if channel.get(tv_channel):
        channel_url = channel.get(tv_channel)
        
        streams = streamlink.streams(channel_url)

        best_stream_url = streams.get("720p").url

        counter = 0
        while not best_stream_url:
            print("3")
            best_stream_url = streams.get("720p").url

            counter+=1

            if(counter > 4):
                return jsonify({'error':  'Couldnt take the link'}), 400

            time.sleep(0.5)

        my_scheduler.live(link=best_stream_url)
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Live stream'}}), 200
    elif vtv_channel.get(tv_channel):
        # print(vtv_channel.get(tv_channel))
        my_scheduler.live_vtv(vtv_channel.get(tv_channel))
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Live stream'}}), 200
        pass
    else:
        return jsonify({'error':  'Wrong TV channel'}), 400

@app.route('/live/video')
def Live_Video():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400

    list  = request.args.get('list')
    # CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'List empty'}), 400
    
    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Wrong file name'}), 400
    print(f"List Video: {video_list}")

    my_scheduler.live(videolist=video_list)

    # my_scheduler.live(link=link)
    
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Live stream'}}), 200

@app.route('/live')
def Live_Steam():
        # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400

    link  = request.args.get('link')
    if not link:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':'List empty'}), 400
    
    # listvideo = list.split(',')
    # if not check_video_list(listvideo):
    #     return jsonify({'error': 'Wrong file name'}), 400
    streams = streamlink.streams(link)
    best_stream_url = streams.get("best").url if "best" in streams else None
    counter = 0
    while not best_stream_url:
            best_stream_url = streams.get("720p").url if "720p" in streams else None

            counter+=1

            if(counter > 4):
                return jsonify({'error':  'Couldnt take the link'}), 400

            time.sleep(0.5)

    my_scheduler.live(link=best_stream_url)

    # my_scheduler.live(link=link)
    
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Live stream'}}), 200

@app.route('/stoplive')
def Stop_Live_Steam():
        # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400

        
    my_scheduler.stop_live()
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Stop live stream'}}), 200

@app.route('/schedule/addTask/weekly',methods=['GET'])
def Add_Task_Everyweeks():
    start_time = request.args.get('starttime')
    end_time = request.args.get('endtime')
    start_date = request.args.get('startdate')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    label = request.args.get('label')
    days = request.args.get('days')

    deadline = None
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
        
    #CHECK DURATION
    print(duration)
    if not duration:
        int_duration = 1
        duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Wrong duration'}), 400
    
    #CHECK UNTIL
    if not until:
        my_year = 2100
        my_month = 12
        my_day = 12
        deadline = datetime(year=my_year,month=my_month,day=my_day,hour=23,minute=59,second=59)
    else:
        my_year = int(until.split('-')[0])
        my_month = int(until.split('-')[1])
        my_day = int(until.split('-')[2])
        deadline = datetime(year=my_year,month=my_month,day=my_day,hour=23,minute=59,second=59)
        if(deadline < datetime.now()):
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'until in the past'}), 400
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    #CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'List empty'}), 400

    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong file name'}), 400
    print(f"List Video: {video_list}")
    
    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong start date format'}), 400
        
    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")

    #CHECK START TIME
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(start_time)
    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(end_time) 
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Start time greater than end time'}) ,400
    
    # CHECK DAYS
    if not days:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty days'}) ,400
    else:
        days = days.split(',')
        list_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for day in days:
            if day not in list_days:
                return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong date'}) ,400

    #CHECK LABEL
    if not label:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty label'}) ,400

    
    new_task = TaskInformation(ID=None,label=label,days=days, video_name=video_list,start_date=start_date,duration=int(duration),until=deadline,start_time=start_time,end_time=end_time,typetask="weekly")
   
    my_scheduler.weekly_task(new_task)

    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Create task', 'ID': new_task.ID}}), 200

@app.route('/schedule/addTask/daily' , methods=['GET'])
def Add_Task_Everydays():
    if request.method == 'OPTIONS':
        return jsonify({'error':'Wrong stream'}), 400
    
    start_time = request.args.get('starttime')
    end_time = request.args.get('endtime')
    start_date = request.args.get('startdate')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    label = request.args.get('label')
    deadline = None
    global ID_count

    print(duration)

    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
        
    # CHECK DURATION 
    if not duration:
        int_duration = 1
        duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Wrong duration'}), 400
    
    #CHECK UNTIL
    if not until:
        my_year = 2100
        my_month = 12
        my_day = 12
        deadline = datetime(year=my_year,month=my_month,day=my_day,hour=23,minute=59,second=59)
    else:
        my_year = int(until.split('-')[0])
        my_month = int(until.split('-')[1])
        my_day = int(until.split('-')[2])
        deadline = datetime(year=my_year,month=my_month,day=my_day,hour=23,minute=59,second=59)
        if(deadline < datetime.now()):
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'until in the past'}), 400
        
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    # CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'List empty'}), 400
    
    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Wrong file name'}), 400
    print(f"List Video: {video_list}")

    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong start date format'}), 400
        
    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
   # CHECK START TIME 
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(start_time)
    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(end_time)
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Start time greater than end time'}) ,400
    
    #CHECK LABEL

    if not label:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty label'}) ,400

    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    
    #CREATE NEW TASK
    new_task = TaskInformation(ID=None,label=label,days = [], video_name=video_list,start_date=start_date,duration=int(duration),until=deadline,start_time=start_time,end_time=end_time,typetask="daily")
    my_scheduler.daily_task(new_task)

    return jsonify({'stream' : f'{my_scheduler.stream}','success': {'message': 'Create task', 'ID': new_task.ID}}), 200



@app.route('/schedule/addTask/onetime',methods=['GET'])
def Add_Task_onetime():
    start_time = request.args.get('starttime')
    end_time = request.args.get('endtime')
    start_date = request.args.get('startdate')
    list = request.args.get('list')
    label = request.args.get('label')
    global ID_count    
    until = None

    # Cheking parameter
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
        
    #CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'List empty'}), 400
    
    video_list = list.split(',')
    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong file name'}), 400

    print(f"List Video: {video_list}")
    
    #CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Wrong start date format'}), 400
    #CHECK START TIME
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:

        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(start_time)

    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Wrong time format'}) ,400
        print(end_time)
        str_end_time = datetime.strptime(end_time, "%H:%M")
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Start time greater than end time'}) ,400


    if str_end_time.time() <= datetime.strptime(start_time, "%H:%M").time():
        until = datetime.combine(start_date.date() + timedelta(days=1), str_end_time.time())
    else:
        until = datetime.combine(start_date.date(), str_end_time.time())

    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
    until = until.strftime("%Y-%m-%d %H:%M:%S")

    if not label:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': 'Empty label'}) ,400
    
    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    new_task = TaskInformation(ID=None,label=label ,video_name=video_list,duration=0,start_date=start_date,until=until,start_time=start_time,end_time=end_time,typetask="onetime",days=[])
    my_scheduler.onetime_task(new_task)
    


    # if end_time:
    #     schedule.every().days.at(end_time).do(cancel_task,start_date,0).tag(f'{new_task.ID}')

    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Create task', 'ID': new_task.ID}}), 200


@app.route('/schedule/deleteTask')
def Delete_Task():
        # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    my_scheduler = None
    for scheduler in my_schedulers:
        if scheduler.stream == int(stream):
            my_scheduler = scheduler
    if my_scheduler == None:
        return jsonify({'error':  'Wrong stream'}), 400
        
    id = request.args.get('id')
    label = request.args.get('label')
    print(id)
    if not id and not label:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'ID and label empty'}), 400
    
    if not  my_scheduler.delete_task(id,label):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error':  'Cannot deleta'}), 400
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Delete task', 'ID': f'{id}'}}), 200
    
#-----------------------------------------------------------




@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return 'No video part in the request'
    
    file = request.files['video']
    if file.filename == '':
        return 'No selected video'
    
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'Video uploaded successfully and saved to {filepath}'
    
    return 'Failed to upload video'

@app.route('/videocontent/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def main():
    
    init()
    for scheduler in my_schedulers:
        scheduler.run()
    # my_obs.get_input_list()
    # my_obs.get_input_settings("mySource")
    # my_obs.get_scene_item_list('scene1')
    # Running app
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise
        


