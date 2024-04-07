from datetime import datetime, timedelta

def calculate_time_difference(datetime1, datetime2):
    difference = abs(datetime2 - datetime1).days
    a = difference - 1
    return a

# Tạo các đối tượng datetime
datetime1 = datetime(2024, 4, 1, 10, 30)  # 10:30 AM ngày 1 tháng 4 năm 2024
datetime2 = datetime(2024, 4, 4, 12, 45)  # 12:45 PM ngày 4 tháng 4 năm 2024

# Tính toán khoảng cách thời gian giữa hai thời điểm
time_difference = calculate_time_difference(datetime1, datetime2)
print(datetime1)
print("Khoảng cách thời gian:", time_difference)
