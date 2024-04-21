from flask import Flask, request, jsonify
from datetime import datetime, time, timedelta
from OBS_Controller_oop import OBS_controller
from mqtt import MyMQTTClient
from database import TaskDatabase
from TaskInfor import TaskInformation
from StreamScheduler import StreamScheduler
import threading
import schedule
import json
import inspect
import re
import os
import time
import copy
from flask_cors import CORS



app = Flask(__name__)
CORS(app)


# FilePath = "task_information.txt"
# VideoPath = ""
FolderVideoPath = "video"
# ID_count = 1
# ListTask = []
# FlagLive = 0
# CurrentVideo = None
# CurrentTask = None
# FlagSetStreamKey = 0
# FlagTaskRunning = 0
# exitapp = False
# StreamKey = "live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk"
# StreamLink = "https://www.twitch.tv/gutsssssssss9"
# task_db = TaskDatabase('task_infor.db')

my_scheduler1 = StreamScheduler(FileLog="log_thread1.txt",VideoPath="d:/FINAL PROJECT/SERVER/video/",Database='task_infor.db',DataTable="thread1",OBSPass="123456",OBSPort=4444,StreamKey="live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk",StreamLink = "https://www.twitch.tv/gutsssssssss9")
my_scheduler2 = StreamScheduler(FileLog="log_thread2.txt",VideoPath="d:/FINAL PROJECT/SERVER/video/",Database='task_infor.db',DataTable="thread2",OBSPass="123456",OBSPort=5555,StreamKey="live_1044211682_Ol34MomAqRm3Ef7s0jwrKq0KNGj3Ku",StreamLink = "https://www.twitch.tv/gutsssssssss9")


################## begin MQTT

AIO_USERNAME = "GutD"
AIO_KEY = "aio_ylYf65J1E1PHtUIuXc70qDfe3i6N"
AIO_FEED_ID = ["live-stream"]
mqtt_client = MyMQTTClient(AIO_USERNAME, AIO_KEY, AIO_FEED_ID)


def publish_livestream(link):
    mqtt_client.publish_data("live_stream",link)


###################################################################################
def init():
    #start MQTT
    mqtt_client.start()
    # publish_livestream(my_scheduler.StreamLink)
    
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

@app.route('/get/video')
def Get_files_in_folder():
    file_list = get_video_name()
    return jsonify({'Video name': file_list}), 200

@app.route('/get/currentTask')
def Get_Current_Task():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2

    if not my_scheduler.CurrentTask:
        return jsonify({'Current Task': "None"}), 200
    # Convert datetime objects to strings
    task = copy.deepcopy(my_scheduler.CurrentTask)
    if task:
        task.start_date = task.start_date.strftime("%Y-%m-%d")
        task.until = task.until.strftime("%Y-%m-%d") if task.until and task.until != "None" else None
        
    # Create dictionary
    task_dict = {"Current Task": task.__dict__}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(task_dict, indent=4)
    
    return json_string


@app.route('/get/schedule')
def Get_schedule():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    # Convert datetime objects to strings
    mylist = copy.deepcopy(my_scheduler.ListTask)
    for task in mylist:
        task.start_date = task.start_date.strftime("%Y-%m-%d")
        task.until = task.until.strftime("%Y-%m-%d") if task.until and task.until != "None" else None

    # Create dictionary
    schedule_dict = {"Schedule": [task.__dict__ for task in mylist]}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(schedule_dict, indent=4)

    return json_string

@app.route('/get/streamkey')
def Get_streamkey():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    stream_key = my_scheduler.get_stream_key()
    print(stream_key)
    return jsonify({'Stream key': stream_key}), 200

@app.route('/set/streamkey')
def Set_Stream_Parameter():
    pass

@app.route('/live')
def Live_Steam():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2

    list = request.args.get('list')
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    listvideo = list.split(',')
    if not check_video_list(listvideo):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400
    
    my_scheduler.live(listvideo)
    
    return jsonify({'success': {'message': 'Live stream'}}), 200

@app.route('/stoplive')
def Stop_Live_Steam():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    my_scheduler.stop_live()
    return jsonify({'success': {'message': 'Stop live stream'}}), 200

@app.route('/schedule/addTask/weekly')
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

    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    #CHECK DURATION
    print(duration)
    if not duration:
        int_duration = 1
        duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
    
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
            return jsonify({'error': {'message': 'until in the past'}}), 400
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    #CHECK LIST
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400

    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400
    print(f"List Video: {video_list}")
    
    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'error': {'message': 'Wrong start date format'}}), 400
        
    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")

    #CHECK START TIME
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(start_time)
    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(end_time)
    else:
        return jsonify({'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'error': 'Start time greater than end time'}) ,400
    
    # CHECK DAYS
    if not days:
        return jsonify({'error': 'Empty days'}) ,400
    else:
        days = days.split(',')
        list_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for day in days:
            if day not in list_days:
                return jsonify({'error': 'Wrong date'}) ,400

    #CHECK LABEL
    if not label:
        return jsonify({'error': 'Empty label'}) ,400

    
    new_task = TaskInformation(ID=None,label=label,days=days, video_name=video_list,start_date=start_date,duration=int(duration),until=deadline,start_time=start_time,end_time=end_time,typetask="weekly")
   
    my_scheduler.weekly_task(new_task)

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200

@app.route('/schedule/addTask/daily')
def Add_Task_Everydays():
    
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

    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    # CHECK DURATION 
    if not duration:
        int_duration = 1
        duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
    
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
            return jsonify({'error': {'message': 'until in the past'}}), 400
        
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    # CHECK LIST
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400
    print(f"List Video: {video_list}")

    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'error': {'message': 'Wrong start date format'}}), 400
        
    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
   # CHECK START TIME 
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(start_time)
    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(end_time)
    else:
        return jsonify({'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'error': 'Start time greater than end time'}) ,400
    
    #CHECK LABEL

    if not label:
        return jsonify({'error': 'Empty label'}) ,400

    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    
    #CREATE NEW TASK
    new_task = TaskInformation(ID=None,label=label,days = [], video_name=video_list,start_date=start_date,duration=int(duration),until=deadline,start_time=start_time,end_time=end_time,typetask="daily")
    my_scheduler.daily_task(new_task)

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200



@app.route('/schedule/addTask/onetime')
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
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    #CHECK LIST
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    video_list = list.split(',')
    if not check_video_list(video_list):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400

    print(f"List Video: {video_list}")

    #CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            
        except ValueError:
            return jsonify({'error': {'message': 'Wrong start date format'}}), 400
    #CHECK START TIME
    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:

        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(start_time)

    #CHECK END TIME
    if end_time:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(end_time)
        str_end_time = datetime.strptime(end_time, "%H:%M")
    else:
        return jsonify({'error': 'Empty end time'}) ,400
    
    if(datetime.strptime(end_time, "%H:%M") <= datetime.strptime(start_time, "%H:%M")):
        return jsonify({'error': 'Start time greater than end time'}) ,400


    if str_end_time.time() <= datetime.strptime(start_time, "%H:%M").time():
        until = datetime.combine(start_date.date() + timedelta(days=1), str_end_time.time())
    else:
        until = datetime.combine(start_date.date(), str_end_time.time())

    start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
    until = until.strftime("%Y-%m-%d %H:%M:%S")
    if not label:
        return jsonify({'error': 'Empty label'}) ,400
    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    
    new_task = TaskInformation(ID=None,label=label ,video_name=video_list,duration=0,start_date=start_date,until=until,start_time=start_time,end_time=end_time,typetask="onetime",days=[])
    my_scheduler.onetime_task(new_task)

    # if end_time:
    #     schedule.every().days.at(end_time).do(cancel_task,start_date,0).tag(f'{new_task.ID}')

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200


@app.route('/schedule/deleteTask')
def Delete_Task():
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    id = request.args.get('id')
    label = request.args.get('label')
    print(id)
    if not id and not label:
        return jsonify({'error': {'message': 'ID and label empty'}}), 400
    
    if not  my_scheduler.delete_task(id,label):
        return jsonify({'error': {'message': 'Cannot deleta'}}), 400
    else:
        return jsonify({'success': {'message': 'Delete task', 'ID': f'{id}'}}), 200
    


def main():
    
    init()
    my_scheduler1.run()
    # my_scheduler2.run()
    # my_obs.get_input_list()
    # my_obs.get_input_settings("mySource")
    # my_obs.get_scene_item_list('scene1')
    # Running app
    app.run(debug=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise
        


