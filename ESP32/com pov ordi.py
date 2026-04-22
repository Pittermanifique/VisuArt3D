import serial,time
import struct
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(4)

while True:
    
    cmd = int(input("cmd: "))
    ser.write(b"10")
    data = ser.readline().decode('utf-8').strip()
    print(data)
