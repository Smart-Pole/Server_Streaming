import json
from datetime import datetime, time, timedelta

class TaskInformation:
    def __init__(self, ID , label , days , video_name , duration , start_date , until , start_time , end_time , typetask, input_type = "video"):
        self.ID = ID
        self.label = label
        self.video_name = video_name
        self.duration = duration
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        self.until = datetime.strptime(until, "%Y-%m-%d %H:%M:%S")
        self.start_time  = start_time
        self.end_time = end_time
        self.typetask = typetask
        self.days = days
        self.input_type = input_type
        


    def __str__(self):
            return f"ID: {self.ID}, Video Name: {', '.join(self.video_name)}"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
    
def test():
     pass

if __name__ == "__main__":
    test()
