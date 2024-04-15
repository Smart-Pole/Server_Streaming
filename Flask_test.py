from datetime import datetime, time, timedelta
start_date = "2024-12-12"
now = datetime.now()
start_time = now.strftime("%H:%M")
end_time = "11:00"
# Chuyển đổi start_date từ chuỗi thành đối tượng datetime
if not start_date:
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
else:
    start_date = datetime.strptime(start_date, "%Y-%m-%d")

# Kiểm tra và xử lý start_time
if not end_time:
    end_time = time(0, 0)  # Nếu không có start_time, mặc định là 00:00
else:
    end_time = datetime.strptime(end_time, "%H:%M")

# Gộp start_date và start_time thành một đối tượng datetime
if end_time.time() <= start_time.time():
    print("hello")
    start_datetime = datetime.combine(start_date.date() + timedelta(days=1), end_time.time())
# start_datetime = datetime.combine(start_date.date(), end_time.time())
print(start_datetime)
