import sqlite3

class TaskDatabase:
    def __init__(self, db_name, table_name="tasks"):
        self.db_name = db_name
        self.table_name = table_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.table_name} (
                              ID INTEGER PRIMARY KEY,
                              label TEXT,
                              days TEXT,
                              video_name TEXT,
                              duration INTEGER,
                              start_date TEXT,
                              until TEXT,
                              start_time TEXT,
                              end_time TEXT,
                              typetask TEXT
                              )''')
        self.conn.commit()

    def add_task(self, task_info):
        self.cursor.execute("INSERT INTO tasks ( label, days, video_name, duration, start_date, until, start_time, end_time, type_task) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            ( task_info.label, ','.join(task_info.days), ','.join(task_info.video_name), task_info.duration, task_info.start_date, task_info.until, task_info.start_time, task_info.end_time, task_info.typetask))
        self.conn.commit()
        last_row_id = self.cursor.lastrowid
        print(f"The ID of the last inserted row is: {last_row_id}")
        return last_row_id

    def delete_task(self, ID=None, label=None):
        if ID is not None and ID != 0:
            self.cursor.execute("DELETE FROM tasks WHERE ID=?", (ID,))
            self.conn.commit()
            print(f"Deleted task with ID {ID}.")
        elif label is not None:
            self.cursor.execute("DELETE FROM tasks WHERE label=?", (label,))
            self.conn.commit()
            print(f"Deleted task with label {label}.")
        else:
            print("No task deleted. Please provide either ID or label.")

    def close_connection(self):
        self.conn.close()

    def get_last_id(self):
        last_row_id = self.cursor.lastrowid
        print(f"The ID of the last inserted row is: {last_row_id}")
        return last_row_id
    
    def delete_all_tasks(self):
        self.cursor.execute("DELETE FROM tasks")
        self.conn.commit()
        print("Deleted all tasks.")

def main():
    # Sử dụng lớp TaskDatabase để tạo cơ sở dữ liệu và thêm dữ liệu
    task_db = TaskDatabase('task_infor.db',"aa")

    # task1 = TaskInformation(1, 'Study', 'Monday, Wednesday, Friday', 'Math', 60, '2024-04-15', '2024-05-15', '08:00', '09:00', 'Regular')
    # # task2 = TaskInformation(2, 'Exercise', 'Tuesday, Thursday', 'Yoga', 30, '2024-04-15', '2024-05-15', '07:00', '07:30', 'Regular')

    # task_db.add_task(task1)
    task_db.delete_task(label="Study")
    # task_db.add_task(task2)

    # Đóng kết nối
    task_db.close_connection()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise