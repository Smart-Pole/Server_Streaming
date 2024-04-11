from flask import Flask, request, jsonify
from datetime import datetime,date
from OBS_Controller_oop import OBS_controller
import threading
import schedule
import json
import inspect
import re
import os
import time
from flask_cors import CORS


def validateTimeformat(time_str):
    pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, time_str) is not None

my_obs = OBS_controller()

app = Flask(__name__)
CORS(app)
class TaskInformation:
    def __init__(self, ID,lable, video_name,duration,start_date,until, start_time, end_time ,onetime = 0 ):
        self.ID = ID
        self.lable = lable
        self.video_name = video_name
        self.duration = duration
        self.start_date = start_date
        self.until = until
        self.start_time  = start_time
        self.end_time = end_time
        self.onetime = onetime
        


    def __str__(self):
            return f"ID: {self.ID}, Video Name: {', '.join(self.video_name)}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

FilePath = "task_information.txt"
VideoPath = "d:/FINAL PROJECT/SERVER/video/"
FolderVideoPath = "video"
ID_count = 1
ListTask = []
FlagLive = 0
CurrentVideo = None
CurrentTask = None
FlagSetStreamKey = 0
FlagTaskRunning = 0
exitapp = False


mutex = threading.Lock()
mutex_setstreamkey = threading.Lock()
mutex_taskrunning = threading.Lock()

def set_flag_live(value):
    global FlagLive
    mutex.acquire()
    FlagLive = value
    mutex.release()


def get_flag_live():
    global FlagLive
    value  = 0
    mutex.acquire()
    value = FlagLive
    mutex.release()
    return value

def set_flag_streamkey(value):
    global FlagSetStreamKey
    mutex_setstreamkey.acquire()
    FlagSetStreamKey = value
    mutex_setstreamkey.release()

def get_flag_streamkey():
    global FlagSetStreamKey
    value  = 0
    mutex_setstreamkey.acquire()
    value = FlagSetStreamKey
    mutex_setstreamkey.release()
    return value

def set_flag_taskrunning(value):
    global FlagTaskRunning
    mutex_taskrunning.acquire()
    FlagTaskRunning = value
    mutex_taskrunning.release()

def get_flag_taskrunning():
    global FlagTaskRunning
    value  = 0
    mutex_taskrunning.acquire()
    value = FlagTaskRunning
    mutex_taskrunning.release()
    return value
###################################################################################
def init():
    global ID_count
    with open(FilePath, 'r') as file:

        for line in file:
            
            data = line.strip().split(';')
            ID = int(data[0].split(':')[1])
            video_name = data[1].split(':')[1].split(',')
            start_time = ':'.join([data[2].split(':')[1],data[2].split(':')[2]])
            if(data[3].split(':')[1] != "None"):
                end_time = ':'.join([data[3].split(':')[1],data[3].split(':')[2]])
            else:
                end_time = None
            until =  datetime.strptime(data[4].split(':')[1],"%Y-%m-%d")
            duration = data[5].split(':')[1]
            onetime = data[6].split(':')[1]
            start_date = datetime.strptime(data[7].split(':')[1],"%Y-%m-%d")
            lable = data[8].split(':')[1]

            task_info = TaskInformation(ID=ID,lable=lable, video_name=video_name,start_time=start_time,end_time=end_time,start_date=start_date,until=until,duration=duration,onetime=onetime)
            ListTask.append(task_info)
    if len(ListTask) == 0:
        print('No task')
    else:
        ID_count = ListTask[len(ListTask) - 1].ID + 1
        print(f'ID_count: {ID_count}')
        for task_info in ListTask:
            print(task_info)

    if not my_obs.check_stream_is_active():
        my_obs.start_stream()
        time.sleep(5)
   
    if my_obs.check_stream_is_active():
        print("INIT: SET FLAG STREAM KEY ")
        set_flag_streamkey(1)


# This function is used to save data to a TXT file. 
# If type = 0, it is used for saving data after deleting a task or adding many tasks, whereas if type = 1, it is used when adding a new task.
def saveTask(type = 0):
    if type == 0:
        open(FilePath, "w").close()
        with open(FilePath, 'w') as file:
            for task_info in ListTask:
                file.write(f"ID:{task_info.ID};Video Name:{','.join(task_info.video_name)};Start time:{task_info.start_time};End time:{task_info.end_time};Until:{task_info.until.year}-{task_info.until.month}-{task_info.until.day};Duration:{task_info.duration};One Time:{task_info.onetime};Start date:{task_info.start_date.year}-{task_info.start_date.month}-{task_info.start_date.day};Lable:{task_info.lable}")
    elif type == 1:
        with open(FilePath, 'a') as file:
                file.write(f"ID:{ListTask[len(ListTask) - 1].ID};Video Name:{','.join(ListTask[len(ListTask) - 1].video_name)};Start time:{ListTask[len(ListTask) - 1].start_time};End time:{ListTask[len(ListTask) - 1].end_time};Until:{ListTask[len(ListTask) - 1].until.year}-{ListTask[len(ListTask) - 1].until.month}-{ListTask[len(ListTask) - 1].until.day};Duration:{ListTask[len(ListTask) - 1].duration};One Time:{ListTask[len(ListTask) - 1].onetime};Start date:{ListTask[len(ListTask) - 1].start_date.year}-{ListTask[len(ListTask) - 1].start_date.month}-{ListTask[len(ListTask) - 1].start_date.day};Lable:{ListTask[len(ListTask) - 1].lable}\n")

def get_link_video(list_video):
    global VideoPath
    my_video_list = [f"{VideoPath}{item}" for item in list_video]
    print(f"List Video: {my_video_list}")
    return my_video_list

def removeTask(target_id):
    index_to_remove = None
    for i, task_info in enumerate(ListTask):
        if task_info.ID == target_id:
            index_to_remove = i
            break

    if index_to_remove is not None:
        del ListTask[index_to_remove]
        print(f"Deleted at index {target_id}")

        with open(FilePath, 'r') as file:
            lines = file.readlines()
        del lines[index_to_remove]
        with open(FilePath, "w") as f:
            for line in lines:
                f.write(line)
        return True
    else:
        print(f"Cannot find ID {target_id}")
        return False


def printTaskInfor():

    if len(ListTask) == 0:
        print('No task')
    else:
        ID_count = ListTask[len(ListTask) - 1].ID
        print(f'ID_count: {ID_count}')
        for task_info in ListTask:
            print(task_info)

def is_time_valid(start_time,end_time):
    # Check if the end time is later than the start time
    if not end_time or end_time == "None":
        start_time = datetime.strptime(start_time, "%H:%M")

        for i, Task in enumerate(ListTask):
            if Task.end_time:
                if (datetime.strptime(Task.end_time, "%H:%M") >=  start_time and datetime.strptime(Task.start_time, "%H:%M") <=  start_time):
                    print("1")
                    return False
        return True
    else:
        start_time = datetime.strptime(start_time, "%H:%M")
        end_time = datetime.strptime(end_time, "%H:%M")
        if end_time < start_time:
            print("4")
            return False
        for i, Task in enumerate(ListTask):
            if Task.end_time or Task.end_time != "None":
                if (datetime.strptime(Task.start_time, "%H:%M") <= end_time and datetime.strptime(Task.start_time, "%H:%M") >=  start_time):
                    print("3")
                    return False
            else:
                if (datetime.strptime(Task.start_time, "%H:%M") <= end_time and datetime.strptime(Task.end_time, "%H:%M") >= end_time):
                    print("2")
                    return False
                if(datetime.strptime(Task.start_time, "%H:%M") <= start_time and datetime.strptime(Task.end_time, "%H:%M") >= start_time):
                    print("5")
                    return False
                if(datetime.strptime(Task.start_time, "%H:%M") >= start_time and datetime.strptime(Task.start_time, "%H:%M") <= end_time):
                    print("5")
                    return False
                if(datetime.strptime(Task.end_time, "%H:%M") >= start_time and datetime.strptime(Task.end_time, "%H:%M") <= end_time):
                    print("5")
                    return False
        return True



def live(videolist):
    myvideolist = get_link_video(videolist)
    my_obs.set_input_playlist(myvideolist)
    my_obs.get_input_settings("mySource")
    print('LIVE')
    set_flag_live(1)

def stop_live():
    global CurrentVideo
    set_flag_live(0)
    if not CurrentVideo:
        cancle_link = get_link_video(["idle.mp4"])
        my_obs.set_input_playlist(cancle_link)
    else:
        my_obs.set_input_playlist(CurrentVideo)

def daily_task(taskinfor):
    global CurrentVideo

    if get_flag_taskrunning():
        print(f"Task id: {taskinfor.ID} has been BLOCKED")
        return False
    if(datetime.now() < taskinfor.start_date):
        print("NOT RUN NOW")
        return False
    if taskinfor.duration:
        if (abs(datetime.now() - taskinfor.start_date).days) % taskinfor.duration != 0:
            return False
    myvideolist = get_link_video(taskinfor.video_name)
    CurrentVideo = myvideolist
    my_obs.set_input_playlist(myvideolist)
    print('Daily_task')
    set_flag_taskrunning(1)
    global CurrentTask
    CurrentTask = taskinfor
    if taskinfor.end_time and taskinfor.end_time != "None":
        schedule.every().days.at(taskinfor.end_time).until(taskinfor.until).do(cancel_task,taskinfor.start_date,taskinfor.duration).tag(f'{taskinfor.ID}')



def onetime_task(taskinfor):
    if get_flag_taskrunning():
        print(f"Task id: {taskinfor.ID} has been BLOCKED")
        return False
    if(datetime.now() < taskinfor.start_date):
        print("NOT RUN NOW")
        return False
    global CurrentVideo
    removeTask(id)
    myvideolist = get_link_video(taskinfor.video_name)
    CurrentVideo = myvideolist
    my_obs.set_input_playlist(myvideolist)
    print('onetime_task')
    set_flag_taskrunning(1)
    global CurrentTask
    CurrentTask = taskinfor
    if taskinfor.end_time and taskinfor.end_time != "None":
        schedule.every().days.at(taskinfor.end_time).do(cancel_task,taskinfor.start_date,taskinfor.duration).tag(f'{taskinfor.ID}')
    return schedule.CancelJob

def cancel_task(start_date,repeatDuration):
    if not get_flag_taskrunning():
        return False
    if(datetime.now() < start_date):
        print("NOT RUN NOW")
        return False
    if repeatDuration:
        if (abs(datetime.now() - start_date).days) % repeatDuration != 0:
            return False
    global CurrentVideo
    CurrentVideo = []
    cancle_link = get_link_video(["idle.mp4"])
    my_obs.set_input_playlist(cancle_link)
    set_flag_taskrunning(0)
    global CurrentTask
    CurrentTask = None
    if repeatDuration == 0:
        print("Cancel task onetime")
        return schedule.CancelJob
    
    return True
def job():
    print('Hello world')
    print(schedule.get_jobs())



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
def schedule_thread1():
    global exitapp
    while not exitapp:
        if not get_flag_live():
            schedule.run_pending()
        time.sleep(1)

################################################################################################################################################################

@app.route('/get/video')
def Get_files_in_folder():
    file_list = get_video_name()
    return jsonify({'Video name': file_list}), 200
@app.route('/get/currentTask')
def Get_Current_Task():
    global CurrentTask
    
    # Convert datetime objects to strings
    task = CurrentTask
    task.start_date = task.start_date.strftime("%Y-%m-%d %H:%M:%S")
    task.until = task.until.strftime("%Y-%m-%d %H:%M:%S") if task.until and task.until != "None" else None
    
    # Create dictionary
    task_dict = {"Current Task": task.__dict__}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(task_dict, indent=4)
    
    return json_string


@app.route('/get/schedule')
def Get_schedule():
    # Convert datetime objects to strings
    global ListTask
    mylist = ListTask
    for task in mylist:
        task.start_date = task.start_date.strftime("%Y-%m-%d %H:%M:%S")
        task.until = task.until.strftime("%Y-%m-%d %H:%M:%S") if task.until and task.until != "None" else None

    # Create dictionary
    schedule_dict = {"Schedule": [task.__dict__ for task in ListTask]}
    
    # Convert dictionary to JSON string
    json_string = json.dumps(schedule_dict, indent=4)

    return json_string

@app.route('/get/streamkey')
def Get_streamkey():
    stream_key = my_obs.get_stream_service_settings().stream_service_settings.get("key")
    print(stream_key)
    return jsonify({'Stream key': stream_key}), 200

@app.route('/set/streamkey')
def Set_Stream_Parameter():
    stream_key = request.args.get('streamkey')
    server = None
    

    if not stream_key:
        return jsonify({'error': {'message': 'Empty stream key'}}), 400
    
    if not server or server == "twitch" :
        server = "rtmp://live.twitch.tv/app"

    if my_obs.check_stream_is_active():
        my_obs.stop_stream()
        time.sleep(1)
    

    my_obs.set_stream_service_key_server(streamkey=stream_key,server=server)
    set_flag_streamkey(1)
    if not my_obs.check_stream_is_active():
        my_obs.start_stream()

    return jsonify({'success': {'message': 'Set stream key success'}}), 200

@app.route('/live')
def Live_Steam():
    if not get_flag_streamkey():
        return jsonify({'error': {'message': 'Empty stream key'}}), 400
    
    list = request.args.get('list')
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    
    listvideo = list.split(',')
    if not check_video_list(listvideo):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400
    
    live(listvideo)
    
    return jsonify({'success': {'message': 'Live stream'}}), 200

@app.route('/stoplive')
def Stop_Live_Steam():

    stop_live()
    return jsonify({'success': {'message': 'Stop live stream'}}), 200

@app.route('/schedule/addTask/daily')
def Add_Task_Everydays():
    if not get_flag_streamkey():
        return jsonify({'error': {'message': 'Empty stream key'}}), 400
    
    start_time = request.args.get('starttime')
    end_time = request.args.get('endtime')
    start_date = request.args.get('startdate')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    lable = request.args.get('lable')
    deadline = None
    global ID_count

    print(duration)

    if not duration:
        int_duration = 1
        duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
    
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

    
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.strptime(start_date,"%Y-%m-%d")

    video_list = list.split(',')

    if not check_video_list(video_list):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400
    print(f"List Video: {video_list}")

    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(start_time)

    if not lable:
        lable = ID_count

    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    
    new_task = TaskInformation(ID=ID_count,lable=lable, video_name=video_list,start_date=start_date,duration=int(duration),until=deadline,start_time=start_time,end_time=end_time,onetime=0)
    ID_count += 1
    ListTask.append(new_task)
    schedule.every().days.at(start_time).until(deadline).do(daily_task, new_task).tag(f'{new_task.ID}')
    print(schedule.get_jobs())
    saveTask(1)

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200



@app.route('/schedule/addTask/onetime')
def Add_Task_onetime():
    if not get_flag_streamkey():
        return jsonify({'error': {'message': 'Empty stream key'}}), 400
    start_time = request.args.get('starttime')
    end_time = request.args.get('endtime')
    start_date = request.args.get('startdate')
    list = request.args.get('list')
    lable = request.args.get('lable')
    global ID_count

    # Cheking parameter

    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
    video_list = list.split(',')
    if not check_video_list(video_list):
        return jsonify({'error': {'message': 'Wrong file name'}}), 400

    print(f"List Video: {video_list}")

    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.strptime(start_date,"%Y-%m-%d")

    if not start_time:
        now = datetime.now()
        start_time = now.strftime("%H:%M")
        print("Current Time =", start_time)
    else:
        if validateTimeformat(start_time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(start_time)

    if not lable:
        lable = ID_count
    # if is_time_valid(start_time,end_time) == False :
    #     return jsonify({'error': 'Wrong time format'}) ,400
    
    new_task = TaskInformation(ID=ID_count,lable=lable ,video_name=video_list,duration=0,start_date=start_date,until=datetime.now(),start_time=start_time,end_time=end_time,onetime=1)
    ID_count += 1
    ListTask.append(new_task)
    schedule.every().days.at(start_time).do(onetime_task,new_task).tag(f'{new_task.ID}')
    print(schedule.get_jobs())
    saveTask(1)

    # if end_time:
    #     schedule.every().days.at(end_time).do(cancel_task,start_date,0).tag(f'{new_task.ID}')

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200


@app.route('/schedule/deleteTask')
def Delete_Task():
    id = request.args.get('id')
    print(id)
    if not id:
        return jsonify({'error': {'message': 'ID empty'}}), 400
    elif id == "all":
        schedule.clear()
        print(schedule.get_jobs())
        return jsonify({'success': {'message': 'Delete all task', 'ID': 'all'}}), 200
    else:
        if removeTask(int(id)):
            schedule.clear(id)
            print(schedule.get_jobs())
            return jsonify({'success': {'message': 'Delete task', 'ID': id}}), 200
        else:
            return jsonify({'error': {'message': 'Cannot find ID', 'ID': id}}), 400




def testing():
    schedule.every(10).seconds.do(job)
    print(schedule.get_jobs())



def main():
    
    init()

    schedule_thread = threading.Thread(target=schedule_thread1)
    schedule_thread.start()
    # my_obs.get_input_list()
    # my_obs.get_input_settings("mySource")
    # my_obs.get_scene_item_list('scene1')
    testing()
    # Running app
    app.run(debug=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise
        


