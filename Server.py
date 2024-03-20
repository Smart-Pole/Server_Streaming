from flask import Flask, request, jsonify
from datetime import datetime, timedelta, time
import threading
import schedule
import json
import inspect
import re


def validateTimeformat(time_str):
    pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, time_str) is not None



app = Flask(__name__)

class TaskInformation:
    def __init__(self, ID, video_name):
        self.ID = ID
        self.video_name = video_name

    def __str__(self):
            return f"ID: {self.ID}, Video Name: {', '.join(self.video_name)}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

FilePath = "task_information.txt"
ID_count = 1
ListTask = []

def init():
    global ID_count
    with open(FilePath, 'r') as file:

        for line in file:

            data = line.strip().split(';')
            ID = int(data[0].split(':')[1])
            video_name = data[1].split(':')[1].split(',')
            task_info = TaskInformation(ID, video_name)
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
                file.write(f"ID:{task_info.ID};Video Name:{','.join(task_info.video_name)}\n")
    elif type == 1:
        with open(FilePath, 'a') as file:
                file.write(f"ID:{ListTask[len(ListTask) - 1].ID};Video Name:{','.join(ListTask[len(ListTask) - 1].video_name)}\n")

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
    time = request.args.get('time')
    list = request.args.get('list')
    duration = request.args.get('duration')
    until = request.args.get('until')
    deadline = None
    global ID_count

    # Cheking parameter
    if not duration:
        int_duration = 1
    elif duration.isdigit():
        return jsonify({'error': {'message': 'Wrong duration'}}), 400
    else:
        int_duration = int(duration)
        
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
    if not time:
        new_task = TaskInformation(ID_count, video_list)
        ID_count += 1
        ListTask.append(new_task)
        schedule.every(int_duration).days.until(deadline).do(job).tag(f'{new_task.ID}')
        print(schedule.get_jobs())
        saveTask(1)
        return jsonify({'success': {'message': 'Create task', 'ID': new_task.ID}}), 200
    else:

        if validateTimeformat(time) == False:
             return jsonify({'error': 'Wrong time format'}) ,400

        print(time)
        new_task = TaskInformation(ID_count, video_list)
        ID_count += 1
        ListTask.append(new_task)
        schedule.every(int_duration).days.at(time).until(deadline).do(job).tag(f'{new_task.ID}')
        print(schedule.get_jobs())
        saveTask(1)
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
