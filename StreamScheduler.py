from datetime import datetime, time, timedelta
from OBS_Controller_oop import OBS_controller
from database import TaskDatabase
from TaskInfor import TaskInformation
import threading
import schedule
import json
import inspect
import re
import os
import time
import copy

class StreamScheduler:
    def __init__(self,FileLog,VideoPath,StreamKey,StreamLink,OBSPort,OBSPass,Database,DataTable):
        self.__my_obs = OBS_controller(port=OBSPort,password=OBSPass)
        self.__Start_Schedule = schedule.Scheduler()
        self.__Stop_Schedule = schedule.Scheduler()
        self.__mutex = threading.Lock()
        self.__mutex_setstreamkey = threading.Lock()
        self.__mutex_taskrunning = threading.Lock()
        self.__task_db = TaskDatabase(db_name=Database,table_name=DataTable)
        self.ListTask = []
        self.FlagLive = 0
        self.FlagSetStreamKey = 0
        self.FlagTaskRunning = 0
        self.CurrentVideo = None
        self.CurrentTask = None
        self.StreamServer = "rtmp://live.twitch.tv/app"
        self.StreamKey=StreamKey
        self.StreamLink=StreamLink
        self.FileLog = FileLog
        self.VideoPath = VideoPath
        self.ListTask = self.__task_db.get_all_tasks()
        if not self.__my_obs.check_stream_is_active():
            self.__my_obs.set_stream_service_key_server(streamkey=self.StreamKey,server=self.StreamServer)
            self.__my_obs.start_stream()
            time.sleep(5)
        else:
            self.__my_obs.stop_stream()
            time.sleep(2)
            self.__my_obs.set_stream_service_key_server(streamkey=self.StreamKey,server=self.StreamServer)
            time.sleep(2)
            self.__my_obs.start_stream()

        if self.__my_obs.check_stream_is_active():
            print("INIT: SET FLAG STREAM KEY ")
            self.__set_flag_streamkey(1)

    def __set_flag_live(self,value):
        self.__mutex.acquire()
        self.FlagLive = value
        self.__mutex.release()


    def __get_flag_live(self):
        value  = 0
        self.__mutex.acquire()
        value = self.FlagLive
        self.__mutex.release()
        return value

    def __set_flag_streamkey(self,value):
        self.__mutex_setstreamkey.acquire()
        self.FlagSetStreamKey = value
        self.__mutex_setstreamkey.release()

    def __get_flag_streamkey(self):
        value  = 0
        self.__mutex_setstreamkey.acquire()
        value = self.FlagSetStreamKey
        self.__mutex_setstreamkey.release()
        return value

    def __set_flag_taskrunning(self,value):
        self.__mutex_taskrunning.acquire()
        self.FlagTaskRunning = value
        self.__mutex_taskrunning.release()

    def __get_flag_taskrunning(self):
        value  = 0
        self.__mutex_taskrunning.acquire()
        value = self.FlagTaskRunning
        self.__mutex_taskrunning.release()
        return value

    def saveTask(self,type = 0):
        if type == 0:
            open(self.FileLog, "w").close()
            with open(self.FileLog, 'w') as file:
                for task_info in self.ListTask:
                    file.write(f"ID:{task_info.ID};Video Name:{','.join(task_info.video_name)};Start time:{task_info.start_time};End time:{task_info.end_time};Until:{task_info.until.year}-{task_info.until.month}-{task_info.until.day};Duration:{task_info.duration};Type task:{task_info.typetask};Start date:{task_info.start_date.year}-{task_info.start_date.month}-{task_info.start_date.day};label:{task_info.label};Days:{','.join(task_info.days)}")
        elif type == 1:
            with open(self.FileLog, 'a') as file:
                    file.write(f"ID:{self.ListTask[len(self.ListTask) - 1].ID};Video Name:{','.join(self.ListTask[len(self.ListTask) - 1].video_name)};Start time:{self.ListTask[len(self.ListTask) - 1].start_time};End time:{self.ListTask[len(self.ListTask) - 1].end_time};Until:{self.ListTask[len(self.ListTask) - 1].until.year}-{self.ListTask[len(self.ListTask) - 1].until.month}-{self.ListTask[len(self.ListTask) - 1].until.day};Duration:{self.ListTask[len(self.ListTask) - 1].duration};Type task:{self.ListTask[len(self.ListTask) - 1].typetask};Start date:{self.ListTask[len(self.ListTask) - 1].start_date.year}-{self.ListTask[len(self.ListTask) - 1].start_date.month}-{self.ListTask[len(self.ListTask) - 1].start_date.day};label:{self.ListTask[len(self.ListTask) - 1].label};Days:{','.join(self.ListTask[len(self.ListTask) - 1].days)}\n")
    
    def __removeTask_byid(self,target_id):
        index_to_remove = None
        for i, task_info in enumerate(self.ListTask):
            if task_info.ID == target_id:
                index_to_remove = i
                break
            
        if index_to_remove is not None:
            del self.ListTask[index_to_remove]
            print(f"Deleted at index {target_id}")

            with open(self.FileLog, 'r') as file:
                lines = file.readlines()
            del lines[index_to_remove]
            with open(self.FileLog, "w") as f:
                for line in lines:
                    f.write(line)
            return True
        else:
            print(f"Cannot find ID {target_id}")
            return False
        
    def __removeTask_bylabel(self,label):
        indices_to_remove = [] 
        for i, task_info in enumerate(self.ListTask):
            if task_info.label == label:
                indices_to_remove.append(i)

        if len(indices_to_remove) == 0:
            return False
        
        for index in reversed(indices_to_remove):
            del self.ListTask[index]

        return True
    
    def get_link_video(self,list_video):
        my_video_list = [f"{self.VideoPath}{item}" for item in list_video]
        print(f"List Video: {my_video_list}")
        return my_video_list
    
    def live(self,videolist):
        myvideolist = self.get_link_video(videolist)
        self.__my_obs.set_input_playlist(myvideolist)
        self.__my_obs.get_input_settings("mySource")
        self.__set_flag_live(1)
        print('LIVE')

    def stop_live(self):
        self.__set_flag_live(0)
        if not self.CurrentVideo:
            cancle_link = self.get_link_video(["idle.mp4"])
            self.__my_obs.set_input_playlist(cancle_link)
        else:
            self.__my_obs.set_input_playlist(self.CurrentVideo)

    def __cancel_task(self,start_date,repeatDuration):
        if not self.__get_flag_taskrunning():
            return False
        if(datetime.now() < start_date):
            print("NOT RUN NOW")
            return False
        if repeatDuration:
            if (abs(datetime.now() - start_date).days) % repeatDuration != 0:
                return False
        self.CurrentVideo = []
        cancle_link = self.get_link_video(["idle.mp4"])
        self.__my_obs.set_input_playlist(cancle_link)
        self.__set_flag_taskrunning(0)
        self.CurrentTask = None
        if repeatDuration == 0:
            print("Cancel task onetime")
            return schedule.CancelJob
        
        return True
    
    def __task(self,taskinfor):
        if self.__get_flag_taskrunning():
            print(f"Task id: {taskinfor.ID} has been BLOCKED")
            return False
        if(datetime.now() < taskinfor.start_date):
            print("NOT RUN NOW")
            return False
        if taskinfor.duration:
            value = (abs(datetime.now() - taskinfor.start_date).days )// 7
            print("NOT RUN WEEKLY TASK NOW")
            print(value)
            if value % taskinfor.duration != 0:
                return False
            
        if datetime.strptime(taskinfor.end_time, "%H:%M").time() > datetime.strptime(taskinfor.start_time, "%H:%M").time():
            if datetime.now().time() >= datetime.strptime(taskinfor.end_time, "%H:%M").time():
                print(f"DELETE TASK: {taskinfor.ID}")
                return False
        else:
            pass
        
        self.CurrentVideo
        self.CurrentTask
        myvideolist = self.get_link_video(taskinfor.video_name)
        self.CurrentVideo = myvideolist
        self.__my_obs.set_input_playlist(myvideolist)
        print('WEEKLY Task')
        self.__set_flag_taskrunning(1)
        self.CurrentTask = taskinfor
        if taskinfor.end_time and taskinfor.end_time != "None":
            self.__Stop_Schedule.every().days.at(taskinfor.end_time).until(taskinfor.until).do(self.__cancel_task,taskinfor.start_date,0).tag(f'{taskinfor.ID}',f'{taskinfor.label}')

    def __weekly_task(self,taskinfor):
        days_mapping = {
            'mon': self.__Start_Schedule.every().monday,
            'tue': self.__Start_Schedule.every().tuesday,
            'wed': self.__Start_Schedule.every().wednesday,
            'thu': self.__Start_Schedule.every().thursday,
            'fri': self.__Start_Schedule.every().friday,
            'sat': self.__Start_Schedule.every().saturday,
            'sun': self.__Start_Schedule.every().sunday
        }
        print("WEEKLY TASK")
        print(taskinfor.days)
        for day in taskinfor.days:
            if day in days_mapping:
                days_mapping[day.lower()].at(taskinfor.start_time).until(taskinfor.until).do(self.__task,taskinfor).tag(f'{taskinfor.ID}',f'{taskinfor.label}')

    def weekly_task(self,taskinfor):
        # TO DO
        new_ID = self.__task_db.add_task(taskinfor)
        taskinfor.ID = new_ID
        self.ListTask.append(taskinfor)
        self.saveTask(1)
        self.__weekly_task(taskinfor)
        print(self.__Start_Schedule.get_jobs())

    def __daily_task(self,taskinfor):

        if self.__get_flag_taskrunning():
            print(f"Task id: {taskinfor.ID} has been BLOCKED")
            return False
        if(datetime.now() < taskinfor.start_date):
            print("NOT RUN NOW")
            return False
        if taskinfor.duration:
            if (abs(datetime.now() - taskinfor.start_date).days) % taskinfor.duration != 0:
                return False
            
        if datetime.strptime(taskinfor.end_time, "%H:%M").time() > datetime.strptime(taskinfor.start_time, "%H:%M").time():
            if datetime.now().time() >= datetime.strptime(taskinfor.end_time, "%H:%M".time()):
                print(f"DELETE TASK: {taskinfor.ID}")
                return False
        else:
            pass

        myvideolist = self.get_link_video(taskinfor.video_name)
        self.CurrentVideo = myvideolist
        self.__my_obs.set_input_playlist(myvideolist)
        print('Daily_task')
        self.__set_flag_taskrunning(1)
        self.CurrentTask = taskinfor
        if taskinfor.end_time and taskinfor.end_time != "None":
            self.__Stop_Schedule.every().days.at(taskinfor.end_time).until(taskinfor.until).do(self.__cancel_task,taskinfor.start_date,0).tag(f'{taskinfor.ID}',f'{taskinfor.label}')



    def daily_task(self,taskinfor):
        new_ID = self.__task_db.add_task(taskinfor)
        taskinfor.ID = new_ID
        self.ListTask.append(taskinfor)
        self.saveTask(1)
        self.__Start_Schedule.every().days.at(taskinfor.start_time).until(taskinfor.until).do(self.__daily_task, taskinfor).tag(f'{taskinfor.ID}',f'{taskinfor.label}')
        print(self.__Start_Schedule.get_jobs())


    def __onetime_task(self,taskinfor):
        if self.__get_flag_taskrunning():
            print(f"Task id: {taskinfor.ID} has been BLOCKED")
            return False
        if((datetime.now() - taskinfor.start_date).days > 0):
            print(f"DELETE TASK: {taskinfor.ID}")
            return schedule.CancelJob
        if((datetime.now() - taskinfor.start_date).days < 0):
            print("NOT RUN NOW")
            return False
        
        if datetime.strptime(taskinfor.end_time, "%H:%M").time() > datetime.strptime(taskinfor.start_time, "%H:%M").time():
            if datetime.now().time() >= datetime.strptime(taskinfor.end_time, "%H:%M").time():
                print(f"DELETE TASK 2: {taskinfor.ID}")
                return schedule.CancelJob
        else:
            pass

        myvideolist = self.get_link_video(taskinfor.video_name)
        self.CurrentVideo = myvideolist
        self.__my_obs.set_input_playlist(myvideolist)
        print('onetime_task')
        self.__set_flag_taskrunning(1)
        self.CurrentTask = taskinfor
        if taskinfor.end_time and taskinfor.end_time != "None":
            self.__Stop_Schedule.every().days.at(taskinfor.end_time).do(self.__cancel_task,taskinfor.start_date,taskinfor.duration).tag(f'{taskinfor.ID}',f'{taskinfor.label}')
        return schedule.CancelJob
    
    def onetime_task(self,taskinfor):
        new_ID = self.__task_db.add_task(taskinfor)
        taskinfor.ID = new_ID
        self.ListTask.append(taskinfor)
        self.__Start_Schedule.every().days.at(taskinfor.start_time).do(self.__onetime_task,taskinfor).tag(f'{taskinfor.ID}',f'{taskinfor.label}')
        print(self.__Start_Schedule.get_jobs())
        self.saveTask(1)

    
    def delete_task(self,id = 0, label = 0):
        flag = 0
        if id == "all":
            self.__Start_Schedule.clear()
            self.__Stop_Schedule.clear()
            self.__task_db.delete_all_tasks()
            self.ListTask.clear()
            print(schedule.get_jobs())
            return True
        elif id:
            if self.__removeTask_byid(int(id)):
                self.__task_db.delete_task(ID=id)
                self.__Start_Schedule.clear(id)
                self.__Stop_Schedule.clear(id)
                print(self.__Start_Schedule.get_jobs())
                print(self.__Stop_Schedule.get_jobs())
                flag = 1

        if label:
            if self.__removeTask_bylabel(label=label):
                self.__task_db.delete_task(label=label)
                self.__Start_Schedule.clear(label)
                self.__Stop_Schedule.clear(label)
                print(self.__Start_Schedule.get_jobs())
                print(self.__Stop_Schedule.get_jobs())
                flag = 1

        return flag
        
    def __job(self):
        print("#######################################")
        print('Start SCHEDULER')
        print(self.__Start_Schedule.get_jobs())
        print('Stop SCHEDULER')
        print(self.__Stop_Schedule.get_jobs())
        print("#######################################")


    def get_current_task(self):
        return self.CurrentTask

    def get_schedule(self):
        return self.ListTask
    
    def get_stream_key(self):
        stream_key = self.__my_obs.get_stream_service_settings().stream_service_settings.get("key")
        return stream_key
    
    def set_stream_key(self,streamkey):

        self.StreamKey = streamkey
        if self.__my_obs.check_stream_is_active():
            self.__my_obs.stop_stream()
        time.sleep(1)
    

        self.__my_obs.set_stream_service_key_server(streamkey=self.StreamKey,server=self.StreamServer)
        self.__set_flag_streamkey(1)

        if not self.__my_obs.check_stream_is_active():
            self.__my_obs.start_stream()

    def __run(self):
        while True:
            if not self.__get_flag_live() and not self.__get_flag_taskrunning():
                self.__Start_Schedule.run_pending()

            self.__Stop_Schedule.run_pending()
            time.sleep(1)

    def run(self):
        self.__Stop_Schedule.every(10).seconds.do(self.__job)
        schedule_thread = threading.Thread(target=self.__run)
        schedule_thread.start()

def test():
    my_scheduler = StreamScheduler(FileLog="log_thread1.txt",VideoPath="d:/FINAL PROJECT/SERVER/video/",Database='task_infor.db',DataTable="thread1",OBSPass="123456",OBSPort=4444,StreamKey="live_1039732177_vlmsO93WolB9ky2gidCbIfnEBMnXEk",StreamLink = "https://www.twitch.tv/gutsssssssss9")
    my_scheduler.run()

if __name__ == "__main__":
    test()
