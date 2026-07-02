import serial
import time

# Set up serial communication
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

while True:
    # Simulated sensor and actuator data
    sensor1_value = 25  # Replace with actual sensor 1 value
    sensor2_value = 75  # Replace with actual sensor 2 value
    actuator_command = 1  # Replace with actual actuator command

    # Create a formatted string
    data = f"{sensor1_value},{sensor2_value},{actuator_command}\n"
    
    # Send data over UART
    ser.write(data.encode('utf-8'))
    print(f"Sent: {data.strip()}")  # Print sent data for debugging

    # Wait for feedback from the STM32H7
    feedback = ser.readline().decode('utf-8').strip()
    if feedback:
        print(f"Received feedback: {feedback}")  # Print feedback for debugging

    time.sleep(1)  # Send data every second
