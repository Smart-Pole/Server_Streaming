import json
import threading
import schedule

class TaskInformation:
    def __init__(self, ID , label , days, video_name,duration,start_date,until, start_time, end_time ,typetask ):
        self.ID = ID
        self.label = label
        self.video_name = video_name
        self.duration = duration
        self.start_date = start_date
        self.until = until
        self.start_time  = start_time
        self.end_time = end_time
        self.typetask = typetask
        self.days = days
        self.mutex = threading.Lock()
        self.mutex_setstreamkey = threading.Lock()
        self.mutex_taskrunning = threading.Lock()
        


    def __str__(self):
            return f"ID: {self.ID}, Video Name: {', '.join(self.video_name)}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
    
def test():
     pass
if __name__ == "__main__":
    test()
