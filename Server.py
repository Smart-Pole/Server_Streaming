from flask import Flask, request, jsonify
from datetime import datetime, timedelta, time
import threading
import schedule
import json
import inspect
import re
import os
from flask_cors import CORS

def validateTimeformat(time_str):
    pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, time_str) is not None



app = Flask(__name__)
CORS(app)
class TaskInformation:
    def __init__(self, ID, video_name,duration,until, time_start, time_end ,oneshot = 0):
        self.ID = ID
        self.video_name = video_name
        self.duration = duration
        self.until = until
        self.time_start  = time_start
        self.time_end = time_end
        self.oneshot = oneshot


    def __str__(self):
            return f"ID: {self.ID}, Video Name: {', '.join(self.video_name)}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

FilePath = "task_information.txt"
FolderVideoPath = "video"
ID_count = 1
ListTask = []

def init():
    global ID_count
    with open(FilePath, 'r') as file:

        for line in file:
            data = line.strip().split(';')
            ID = int(data[0].split(':')[1])
            video_name = data[1].split(':')[1].split(',')
            time_start = ':'.join([data[2].split(':')[1],data[2].split(':')[2]])
            if(data[3].split(':')[1] != "None"):
                time_end = ':'.join([data[3].split(':')[1],data[3].split(':')[2]])
            else:
                time_end = None
            until =  data[4].split(':')[1]
            duration = data[5].split(':')[1]
            oneshot = data[6].split(':')[1]
            
            task_info = TaskInformation(ID, video_name=video_name,time_start=time_start,time_end=time_end,until=until,duration=duration,oneshot=oneshot)
            ListTask.append(task_info)
    if len(ListTask) == 0:
        print('No task')
    else:
        ID_count = ListTask[len(ListTask) - 1].ID + 1
        print(f'ID_count: {ID_count}')
        for task_info in ListTask:
            print(task_info)


# This function is used to save data to a TXT file. 
# If type = 0, it is used for saving data after deleting a task or adding many tasks, whereas if type = 1, it is used when adding a new task.
def saveTask(type = 0):
    if type == 0:
        open(FilePath, "w").close()
        with open(FilePath, 'w') as file:
            for task_info in ListTask:
                file.write(f"ID:{task_info.ID};Video Name:{','.join(task_info.video_name)};Time start:{task_info.time_start};Time end:{task_info.time_end};Until:{task_info.until};Duration:{task_info.duration};One shot:{task_info.oneshot}\n")
    elif type == 1:
        with open(FilePath, 'a') as file:
                file.write(f"ID:{ListTask[len(ListTask) - 1].ID};Video Name:{','.join(ListTask[len(ListTask) - 1].video_name)};Time start:{ListTask[len(ListTask) - 1].time_start};Time end:{ListTask[len(ListTask) - 1].time_end};Until:{ListTask[len(ListTask) - 1].until};Duration:{ListTask[len(ListTask) - 1].duration};One shot:{ListTask[len(ListTask) - 1].oneshot}\n")

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

def job():
    print('Hello world')

def oneshot_task(function,streamkey, server, videolist):
    function(streamkey,server,videolist)
    return schedule.CancelJob

def daily_task(function,streamkey, server, videolist):
    function(streamkey,server,videolist)

def schedule_thread():
    while True:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            time.sleep(n)
        schedule.run_pending()

@app.route('/schedule/addTask/everydays')
def Add_Task_Everydays():
    time_start = request.args.get('timestart')
    time_end = request.args.get('timeend')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    streamkey = request.args.get('streamkey')
    server = request.args.get('server')
    deadline = None
    global ID_count
    print(duration)
    print(duration.isdigit())
    # Cheking parameter
    if not streamkey:
        return jsonify({'error': {'message': 'Stream key empty'}}), 400
    
    if not duration:
        int_duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
        
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
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
    

    video_list = list.split(',')
    print(f"List Video: {video_list}")
    if not time_start:
        now = datetime.now()
        time_start = now.strftime("%H:%M")
        print("Current Time =", time_start)
        

    else:

        if validateTimeformat(time_start) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(time_start)


    
    new_task = TaskInformation(ID_count, video_list,duration=duration,until=until,time_start=time_start,time_end=time_end,oneshot=0)
    ID_count += 1
    ListTask.append(new_task)
    schedule.every(int_duration).days.at(time_start).until(deadline).do(job).tag(f'{new_task.ID}')
    print(schedule.get_jobs())
    saveTask(1)

    #for cancel job at time.
    if time_end:
        schedule.every(int_duration).days.at(time_end).until(deadline).do(job).tag(f'{new_task.ID}')

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200





@app.route('/schedule/addTask/oneshot')
def Add_Task_Oneshot():
    time_start = request.args.get('timestart')
    time_end = request.args.get('timeend')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    streamkey = request.args.get('streamkey')
    server = request.args.get('server')
    deadline = None
    global ID_count
    print(duration)
    print(duration.isdigit())
    # Cheking parameter
    if not streamkey:
        return jsonify({'error': {'message': 'Stream key empty'}}), 400
    
    if not duration:
        int_duration = 1
    elif duration.isdigit():
        int_duration = int(duration)
    else:
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
        
    if not list:
        return jsonify({'error': {'message': 'List empty'}}), 400
    
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
    

    video_list = list.split(',')
    print(f"List Video: {video_list}")
    if not time_start:
        now = datetime.now()
        time_start = now.strftime("%H:%M")
        print("Current Time =", time_start)
        

    else:

        if validateTimeformat(time_start) == False:
             return jsonify({'error': 'Wrong time format'}) ,400
        print(time_start)

    new_task = TaskInformation(ID_count, video_list,duration=duration,until=until,time_start=time_start,time_end=time_end,oneshot=1)
    ID_count += 1
    ListTask.append(new_task)
    schedule.every(int_duration).days.at(time_start).do(job).tag(f'{new_task.ID}') 
    print(schedule.get_jobs())
    saveTask(1)

    #for cancel job at time.
    if time_end:
        schedule.every(int_duration).days.at(time_end).until(deadline).do(job).tag(f'{new_task.ID}')

    return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200

@app.route('/get/video')
def Get_files_in_folder():
    file_list = []
    for file_name in os.listdir(FolderVideoPath):
        if os.path.isfile(os.path.join(FolderVideoPath, file_name)):
            file_list.append(file_name)
    return jsonify({'Video name': file_list}), 200

@app.route('/get/schedule')
def Get_schedule():
    schedule_dict = {"Schedule": [task.__dict__ for task in ListTask]}
    json_string = json.dumps(schedule_dict, indent=4)
    return json_string

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
    # schedule.every().days.at("08:50").do(job)
    print(schedule.get_jobs())




if __name__ == '__main__':
    init()

    # Create thread for scheduler
    schedule_thread = threading.Thread(target=schedule_thread)
    schedule_thread.start()
    # testing()
    # Running app
    app.run(debug=True)
