from flask import Flask, request, jsonify
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



app = Flask(__name__)
CORS(app)


# FilePath = "task_information.txt"
# VideoPath = ""
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
FolderVideoPath = "video"

my_scheduler1 = StreamScheduler(Stream=1,FileLog="log_thread1.txt",VideoPath="d:/FINAL PROJECT/SERVER/video/",Database='task_infor.db',DataTable="thread1",OBSPass="123456",OBSPort=4444,StreamKey="live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk",StreamLink = "https://www.twitch.tv/gutsssssssss9")
my_scheduler2 = StreamScheduler(Stream=2,FileLog="log_thread2.txt",VideoPath="d:/FINAL PROJECT/SERVER/video/",Database='task_infor.db',DataTable="thread2",OBSPass="123456",OBSPort=5555,StreamKey="live_1071558463_6geWoWQgWadKOjby2mqDj40qeiW9fg",StreamLink = "https://www.twitch.tv/huynhnguyenhieunhan")

pole_manager = Pole_manager()

################## begin MQTT

AIO_USERNAME = "GutD"
AIO_KEY = "aio_PgQw50qqopzjctjPAKbeq1plM8Rk"
AIO_FEED_ID = ["live-stream"]
mqtt_client = MyMQTTClient(AIO_USERNAME, AIO_KEY, AIO_FEED_ID)


def publish_livestream(ID,link):
    mess = {
        "ID" : ID,
        "link" : link
    }
    json_mess = json.dumps(mess)
    mqtt_client.publish_data("live_stream",json_mess)


###################################################################################
def init():
    #start MQTT
    mqtt_client.start()
    publish_livestream([1,2,3],my_scheduler1.StreamLink)
    
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
            return jsonify({'error': {'message': 'Wrong ID'}}), 400
        
    pole_manager.update_area(pole_id,area)
    return jsonify({'success': {'message': 'Update success'}}), 400

@app.route('/set/poleLink/ID')
def Set_pole_link_id():
    pole_id  = request.args.get('ID')
    stream  = request.args.get('stream')

    pole_id = pole_id.split(',')
    pole_id = [int(id) for id in pole_id]
    my_pole_id = {pole.ID for pole in pole_manager.pole_infor}
    print(my_pole_id)

    if stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    else:
        return jsonify({'error': {'message': 'Wrong stream'}}), 400
    
    for ID in pole_id:
        if not (ID in my_pole_id):
            print(f"ID:{ID}")
            return jsonify({'error': {'message': 'Wrong ID'}}), 400
        
    
    pole_manager.update_link_by_id(pole_id,my_scheduler.StreamLink)
    publish_livestream(pole_id,my_scheduler.StreamLink)

    return jsonify( {'success': {'message': 'Set stream'}}), 200

@app.route('/set/poleLink/area')
def Set_pole_link_area():
    area  = request.args.get('area')
    stream  = request.args.get('stream')


    print(area)
    my_area = {pole.area for pole in pole_manager.pole_infor}

    if stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    else:
        return jsonify({'error': {'message': 'Wrong stream'}}), 400
    

    if not (area in my_area):
        print(f"ID:{area}")
        return jsonify({'error': {'message': 'Wrong area'}}), 400
        
    
    pole_manager.update_link_by_area(area=area,new_link=my_scheduler.StreamLink)
    publish_livestream(pole_manager.get_ids_by_area(area),my_scheduler.StreamLink)

    return jsonify( {'success': {'message': 'Set stream'}}), 200


@app.route('/get/video')
def Get_files_in_folder():
    file_list = get_video_name()
    return jsonify({'Video name': file_list}), 200

@app.route('/get/currentTask')
def Get_Current_Task():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    else:
        return jsonify({'error': {'message': 'Wrong stream'}}), 400

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
    schedule_dict = {'stream' : f'{my_scheduler.stream}' ,"Schedule": [task.__dict__ for task in mylist]}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(schedule_dict, indent=4)

    return json_string

@app.route('/get/streamkey')
def Get_streamkey():
    # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
    stream_key = my_scheduler.get_stream_key()
    print(stream_key)
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'Stream key': stream_key}), 200

@app.route('/set/streamkey')
def Set_Stream_Parameter():
    return jsonify({'error' : 'not allow'}), 200

@app.route('/live')
def Live_Steam():
        # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2

    # list = request.args.get('list')
    link  = request.args.get('link')
    if not link:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'List empty'}}), 400
    
    # listvideo = list.split(',')
    # if not check_video_list(listvideo):
    #     return jsonify({'error': {'message': 'Wrong file name'}}), 400
    
    my_scheduler.live(link=link)
    
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Live stream'}}), 200

@app.route('/stoplive')
def Stop_Live_Steam():
        # CHOOSE THE STREAM CHANEL
    stream  = request.args.get('stream')
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    my_scheduler.stop_live()
    return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Stop live stream'}}), 200

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
    # CHOOSE THE STREAM CHANEL
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
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong duration'}}), 400
    
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
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'until in the past'}}), 400
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    #CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'List empty'}}), 400

    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong file name'}}), 400
    print(f"List Video: {video_list}")
    
    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong start date format'}}), 400
        
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

    # CHOOSE THE STREAM CHANEL
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
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong duration'}}), 400
    
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
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'until in the past'}}), 400
        
    deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")

    # CHECK LIST
    if not list:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'List empty'}}), 400
    
    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong file name'}}), 400
    print(f"List Video: {video_list}")

    # CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong start date format'}}), 400
        
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
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'List empty'}}), 400
    
    video_list = list.split(',')
    if not check_video_list(video_list):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong file name'}}), 400

    print(f"List Video: {video_list}")

    #CHECK START DATE
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            
        except ValueError:
            return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Wrong start date format'}}), 400
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
    if not stream or stream == "1":
        my_scheduler =  my_scheduler1
    elif stream == "2":
        my_scheduler = my_scheduler2
        
    id = request.args.get('id')
    label = request.args.get('label')
    print(id)
    if not id and not label:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'ID and label empty'}}), 400
    
    if not  my_scheduler.delete_task(id,label):
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'error': {'message': 'Cannot deleta'}}), 400
    else:
        return jsonify({'stream' : f'{my_scheduler.stream}' ,'success': {'message': 'Delete task', 'ID': f'{id}'}}), 200
    


def main():
    
    init()
    my_scheduler1.run()
    my_scheduler2.run()
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
        


