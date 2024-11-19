import json
import sqlite3
import schedule
import time
from datetime import datetime
import threading
from mqtt import MyMQTTClient

# Lớp quản lý database SQLite
class DatabaseManager:
    def __init__(self, db_name="sensor_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pole_id INTEGER,
                temperature REAL,
                humidity REAL,
                lux REAL,
                noise REAL,
                air_pressure REAL,
                pm2_5 REAL,
                pm10 REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_data(self, pole_id, temperature, humidity, lux, noise, air_pressure, pm2_5, pm10):
        """Lưu dữ liệu cảm biến vào database, bao gồm pole_id."""
        self.cursor.execute('''
            INSERT INTO sensor_data (pole_id, temperature, humidity, lux, noise, air_pressure, pm2_5, pm10)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pole_id, temperature, humidity, lux, noise, air_pressure, pm2_5, pm10))
        self.conn.commit()

    def get_latest_n_data_by_pole(self, pole_id, n=10):
        """Lấy n bản ghi gần nhất từ bảng sensor_data theo pole_id. Nếu n = 0 thì lấy tất cả dữ liệu theo pole_id."""
        if n == 0:
            # Lấy tất cả dữ liệu theo pole_id
            self.cursor.execute('SELECT * FROM sensor_data WHERE pole_id = ? ORDER BY id DESC', (pole_id,))
        else:
            # Lấy n bản ghi gần nhất theo pole_id
            self.cursor.execute('SELECT * FROM sensor_data WHERE pole_id = ? ORDER BY id DESC LIMIT ?', (pole_id, n))
        
        results = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "pole_id": row[1],
                "temperature": row[2],
                "humidity": row[3],
                "lux": row[4],
                "noise": row[5],
                "air_pressure": row[6],
                "pm2_5": row[7],
                "pm10": row[8],
                "timestamp": row[9]
            }
            for row in results
        ]
    
    def get_all_pole_ids(self):
        """Lấy tất cả các pole_id có trong cơ sở dữ liệu."""
        self.cursor.execute('SELECT DISTINCT pole_id FROM sensor_data')
        pole_ids = [row[0] for row in self.cursor.fetchall()]
        return pole_ids
    
    def close(self):
        """Đóng kết nối database."""
        self.conn.close()

class IntergrateHandler:
# Lớp quản lý thu thập dữ liệu cảm biến
    def __init__(self, topic , max_entries=20):
        self.topic = topic
        self.db_manager = DatabaseManager()  # Sử dụng DatabaseManager để lưu và lấy dữ liệu
        self.avg_data = {}   # Dữ liệu chứa giá trị trung bình cho mỗi ID
        self.hourly_avg_data = {}  # Mảng chứa giá trị trung bình mỗi giờ
        self.max_entries = max_entries  # Giới hạn số lượng phần tử trong hourly_avg_data
        self.lock = threading.Lock()
        # Khởi tạo với 20 giá trị trung bình gần nhất từ database
        self.load_hourly_avg_data_from_db()


        # Tạo và bắt đầu thread để chạy schedule
        self.schedule_thread = threading.Thread(target=self.run_schedule)
        self.schedule_thread.daemon = True  # Đảm bảo thread này kết thúc khi chương trình chính kết thúc
        self.schedule_thread.start()

    def load_hourly_avg_data_from_db(self):
        """Tải 20 giá trị trung bình gần nhất từ database và lưu vào hourly_avg_data, lọc theo pole_id."""
        # Lấy tất cả các pole_id từ cơ sở dữ liệu
        pole_ids = self.db_manager.get_all_pole_ids()

        # Lặp qua từng pole_id và tải dữ liệu
        for pole_id in pole_ids:
            # Lấy 20 bản ghi gần nhất cho mỗi pole_id
            data_from_db = self.db_manager.get_latest_n_data_by_pole(n=self.max_entries, pole_id=pole_id)
            
            # Tạo array cho pole_id nếu chưa có
            if pole_id not in self.hourly_avg_data:
                self.hourly_avg_data[pole_id] = []

            for record in data_from_db:
                if record['pole_id'] == pole_id:  # Lọc theo pole_id
                    # Thêm dữ liệu vào mảng của pole_id trong hourly_avg_data
                    self.hourly_avg_data[pole_id].append({
                        "timestamp": record['timestamp'],
                        "avg_data": {
                            "temperature": record['temperature'],
                            "humidity": record['humidity'],
                            "lux": record['lux'],
                            "noise": record['noise'],
                            "air_pressure": record['air_pressure'],
                            "pm2_5": record['pm2_5'],
                            "pm10": record['pm10']
                        }
                    })

        #print(f"Loaded data into hourly_avg_data for {len(self.hourly_avg_data)} pole_ids.")


    def process_message(self, feed_id, payload):
        """Xử lý dữ liệu JSON và tính toán giá trị trung bình, nhóm theo ID."""
        try:
            if feed_id != self.topic:
                return

            data = json.loads(payload)

            # Lấy dữ liệu từ payload
            pole_id = data.get("ID")
            temperature = data.get("temp")
            humidity = data.get("humi")
            lux = data.get("lux")
            # lux = 20
            noise = data.get("noise")
            air_pressure = data.get("atm")
            pm2_5 = data.get("pm2.5")
            pm10 = data.get("pm10")

            # Kiểm tra nếu dữ liệu hợp lệ
            if all(value is not None for value in [temperature, humidity, lux, noise, air_pressure, pm2_5, pm10]):
                # Tính giá trị trung bình cho ID này và lưu vào avg_data
                with self.lock:
                    self.calculate_average(pole_id, temperature, humidity, lux, noise, air_pressure, pm2_5, pm10)

                #print(f"Data processed and average updated for feed_id {feed_id}: {data}")
            else:
                #print("Missing some sensor data in the payload.")
                pass

        except json.JSONDecodeError:
            print("Failed to decode JSON payload MQTT.")
            

    def calculate_average(self, pole_id, temperature, humidity, lux, noise, air_pressure, pm2_5, pm10):
        """Tính toán giá trị trung bình của các cảm biến cho một pole_id cụ thể theo công thức mới."""
        # Nếu không có giá trị cũ (lần đầu tiên), sử dụng giá trị mới trực tiếp
        avg_temperature = round((self.avg_data.get(pole_id, {}).get('temperature', temperature) * 2 + temperature) / 3, 2)
        avg_humidity = round((self.avg_data.get(pole_id, {}).get('humidity', humidity) * 2 + humidity) / 3, 2)
        avg_lux = round((self.avg_data.get(pole_id, {}).get('lux', lux) * 2 + lux) / 3, 2)
        avg_noise = round((self.avg_data.get(pole_id, {}).get('noise', noise) * 2 + noise) / 3, 2)
        avg_air_pressure = round((self.avg_data.get(pole_id, {}).get('air_pressure', air_pressure) * 2 + air_pressure) / 3, 2)
        avg_pm2_5 = round((self.avg_data.get(pole_id, {}).get('pm2_5', pm2_5) * 2 + pm2_5) / 3, 2)
        avg_pm10 = round((self.avg_data.get(pole_id, {}).get('pm10', pm10) * 2 + pm10) / 3, 2)


        # Cập nhật avg_data với giá trị trung bình mới
        self.avg_data[pole_id] = {
            "temperature": avg_temperature,
            "humidity": avg_humidity,
            "lux": avg_lux,
            "noise": avg_noise,
            "air_pressure": avg_air_pressure,
            "pm2_5": avg_pm2_5,
            "pm10": avg_pm10
        }

        #print(f"Updated average data for pole_id {pole_id}: {self.avg_data[pole_id]}")


    def save_hourly_data_to_db(self):
        """Lưu giá trị trung bình vào hourly_avg_data mỗi giờ và lưu vào database."""
        current_time = datetime.now()
        #print("test")
        with self.lock:
            # Lưu vào hourly_avg_data cho mỗi pole_id riêng biệt
            for pole_id, avg_values in self.avg_data.items():
                # Lưu vào cơ sở dữ liệu
                self.db_manager.save_data(pole_id, avg_values['temperature'], avg_values['humidity'], avg_values['lux'],
                                        avg_values['noise'], avg_values['air_pressure'], avg_values['pm2_5'], avg_values['pm10'])

                # Lưu vào hourly_avg_data của pole_id
                if pole_id not in self.hourly_avg_data:
                    self.hourly_avg_data[pole_id] = []  # Khởi tạo mảng nếu pole_id chưa có

                # Lưu giá trị trung bình vào mảng của pole_id
                self.hourly_avg_data[pole_id].append({
                    "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "avg_data": avg_values  # Lưu dữ liệu trung bình cho pole_id này
                })

                # Nếu mảng hourly_avg_data của pole_id có quá 20 giá trị, xóa giá trị cũ nhất
                if len(self.hourly_avg_data[pole_id]) > self.max_entries:
                    self.hourly_avg_data[pole_id].pop(0)  # Loại bỏ phần tử đầu tiên (giá trị cũ nhất)

            #print(f"Hourly average data saved at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def get_hourly_avg_data(self):
        """Trả về danh sách dữ liệu trung bình theo giờ."""
        return self.hourly_avg_data

    def get_avg_data(self):
        """Trả về dữ liệu trung bình hiện tại cho tất cả các feed_id."""
        return self.avg_data
    
    def get_combined_data_by_pole_id(self, pole_id):
        current_time = datetime.now()
        """Trả về 10 giá trị gần nhất từ hourly_avg_data và 1 giá trị từ avg_data cho một pole_id."""
        combined_data = []

        # Lấy 1 giá trị từ avg_data cho pole_id
        if pole_id in self.avg_data:
            avg_data = {
                "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),  # Bạn có thể thay thế timestamp nếu muốn
                "avg_data": self.avg_data[pole_id]
            }
            combined_data.append(avg_data)

        # Lấy 10 giá trị gần nhất từ hourly_avg_data (nếu có)
        if pole_id in self.hourly_avg_data:
            # Lấy 10 giá trị gần nhất (nếu có ít hơn 10 thì lấy tất cả)
            latest_hourly_data = self.hourly_avg_data[pole_id][-10:]
            combined_data.extend(latest_hourly_data)
            
        if not combined_data:
            #print(f"No data found for pole_id {pole_id}.")
            pass
        
        return combined_data
    
    def run_schedule(self):
        """Chạy lịch trình để lưu dữ liệu hàng giờ mà không làm gián đoạn chương trình chính."""
        schedule.every(30).minutes.do(self.save_hourly_data_to_db)  # Lưu mỗi 30 giây
        while True:
            n = schedule.idle_seconds()
            if n is None:
                # no more jobs
                break
            elif n > 0:
                # sleep exactly the right amount of time
                time.sleep(n)
            schedule.run_pending()
# Main program
if __name__ == "__main__":
    # Thiết lập database
    test = IntergrateHandler("fan")    
    AIO_USERNAME = "GutD"
    AIO_KEY = "aio_bGuw63ehyU54faTrMmITodLTDQoa"
    AIO_FEED_ID = ["fan"]

    mqtt_client = MyMQTTClient(AIO_USERNAME, AIO_KEY, AIO_FEED_ID)
    mqtt_client.start()
    mqtt_client.processMessage = test.process_message
    while True:
        #print(test.get_combined_data_by_pole_id(1))
        time.sleep(10)

