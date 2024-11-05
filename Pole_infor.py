import sqlite3
class Pole_Information:
    def __init__(self, ID, location , infor , area ,link,channel):
        self.ID = ID
        self.location = location
        self.infor =  infor
        self.area =  area
        self.link = link
        self.channel = channel

class Pole_manager:
    def __init__(self, db_name = "pole_infor.db", table_name = "pole"):
        
        self.db_name = db_name
        self.table_name = table_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.create_table()

        self.pole_infor = self.get_pole()

    def create_table(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.table_name} (
                              ID INTEGER PRIMARY KEY,
                              location TEXT,
                              information TEXT,
                              area TEXT,
                              link TEXT,
                              channel TEXT 
                              )''')
        self.conn.commit()

    def get_pole(self):
        self.cursor.execute(f"SELECT * FROM {self.table_name}")
        poles_infor = self.cursor.fetchall()
        poles = []
        for pole_infor in poles_infor:
            pole = Pole_Information(*pole_infor)
            poles.append(pole)
        return poles
    
    def close_connection(self):
        self.conn.close()

    def update_area(self, pole_ids, new_area):
        # Update in the database
        for pole_id in pole_ids:
            self.cursor.execute(f"UPDATE {self.table_name} SET area = ? WHERE ID = ?", (new_area, pole_id))
        self.conn.commit()
        
        # Update in self.pole_infor
        for pole in self.pole_infor:
            if pole.ID in pole_ids:
                pole.area = new_area
                    
        print("Area updated successfully.")


    def update_link_by_id(self, pole_ids, new_link,channel):
        # Update in the database
        for pole_id in pole_ids:
            self.cursor.execute(f"UPDATE {self.table_name} SET link = ?, channel = ? WHERE ID = ?", (new_link,channel, pole_id))
        self.conn.commit()
        
        # Update in self.pole_infor
        for pole in self.pole_infor:
            if pole.ID in pole_ids:
                pole.link = new_link
                pole.channel = channel
                    

    def update_link_by_area(self, area, new_link,channel):
        # Update in the database
        self.cursor.execute(f"UPDATE {self.table_name} SET link = ?, channel = ? WHERE area = ?", (new_link, channel,area))
        self.conn.commit()
        
        # Update in self.pole_infor
        for pole in self.pole_infor:
            if pole.area == area:
                pole.link = new_link
                pole.channel = channel

    def get_ids_by_area(self, area):
        # Tạo một danh sách rỗng để lưu trữ ID
        ids = []

        # Lặp qua danh sách pole_infor
        for pole in self.pole_infor:
            # Nếu area của pole trùng với giá trị được cung cấp
            if pole.area == area:
                # Thêm ID của pole vào danh sách
                ids.append(pole.ID)

        # Trả về danh sách các ID có area tương ứng
        return ids

def main():
    # Sử dụng lớp TaskDatabase để tạo cơ sở dữ liệu và thêm dữ liệu
    task_db = Pole_manager('pole_infor.db',"pole")
    print(task_db.get_ids_by_area("HCMUT01"))

    if task_db.pole_infor:
        print("Retrieved Task Information:")
        for task in task_db.pole_infor:
            print(f"ID: {task.ID}")
            print(f"Location: {task.location}")
            print(f"Information: {task.infor}")
            print(f"Area: {task.area}")
            print(f"Link: {task.link}")
            print("\n")

    # Đóng kết nối

    task_db.close_connection()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise