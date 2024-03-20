from flask import Flask
import threading
import time
import schedule

app = Flask(__name__)
def job():
    print('Hello world')



def schedule_thread():

    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/hello')
def hello():
    schedule.every(5).seconds.do(job).tag('hourly-tasks', 'friend')
    return "Hello, world from Flask!"

@app.route('/get_all_schedule')
def get_all_schedule():
    print (schedule.get_jobs())
    return "Hello, world from Flask!"

@app.route('/delete_task/<task_id>')
def delete_task(task_id):
    schedule.clear(task_id)
    return f'DELETE {task_id}'

if __name__ == '__main__':
    # Tạo một luồng cho schedule
    schedule_thread = threading.Thread(target=schedule_thread)
    schedule_thread.start()

    # Chạy Flask trong chính luồng chính
    app.run(debug=True)
