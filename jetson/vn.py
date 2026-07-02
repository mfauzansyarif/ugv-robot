import serial
import time

# Configure the serial connection (adjust parameters as needed)
ser = serial.Serial(
    port='/dev/ttyTHS1',  # Change this to your serial port
    baudrate=115200,      # Check VN-100 documentation for baud rate
    timeout=1
)

def read_vn100_data():
    print("Program Started")
    while True:
        if ser.in_waiting > 0:
            out = ser.read(ser.in_waiting).decode('utf-8')
            data = out.split(',')
            if data[0] == "$VNYMR":
                print(f'[{data[1]}, {data[2]}, {data[3]}]')
            else:
                print(f'Output Type Not Supported: {data[0]}')
                

try:
    read_vn100_data()
except KeyboardInterrupt:
    print("Program interrupted")
finally:
    ser.close()
