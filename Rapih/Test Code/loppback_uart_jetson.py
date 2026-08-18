import serial
import time

PORT = "/dev/ttyTHS1"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

test_data = b"Hello UART Loopback!"

print(f"Testing loopback on {PORT}")
print(f"Sending: {test_data}")

ser.write(test_data)
time.sleep(0.1)
received = ser.read(len(test_data))

print(f"Received: {received}")

if received == test_data:
    print("✅ LOOPBACK SUCCESS — data match!")
else:
    print("❌ LOOPBACK FAILED — data mismatch")

ser.close()