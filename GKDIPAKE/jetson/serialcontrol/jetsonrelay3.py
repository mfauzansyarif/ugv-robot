#!usr/bin/python3.8
import serial
import threading
import time
from pantilt_actions import rotate_up, rotate_down, rotate_left, rotate_right, read_angle, power_load, open_serial, stopmovement
from lrf_actions import read_range, alignment_light

# Update these to the correct ports on your machine
PORT1 = '/dev/ttyUSB0'  # Source port
PORT2 = '/dev/ttyUSB1'  # micro
PORT3 = '/dev/ttyACM0'  # pantilt
BAUD_RATE = 57600
import threading

# Global variables to store the latest command threads
motion_thread = None
alignment_thread = None

def execute_in_thread(target_func, *args):
    """Helper function to execute a function in a separate thread."""
    global motion_thread, alignment_thread
    
    thread = threading.Thread(target=target_func, args=args)
    thread.start()
    return thread

def pantilt_cons(data, ser):
    global motion_thread, alignment_thread

    # Parse motion command
    rotate = data[0]
    if rotate == '1':
        if motion_thread and motion_thread.is_alive():
            motion_thread.join(0.1)  # Cancel the previous thread
        motion_thread = execute_in_thread(rotate_up)
    elif rotate == '2':
        if motion_thread and motion_thread.is_alive():
            motion_thread.join(0.1)
        motion_thread = execute_in_thread(rotate_right)
    elif rotate == '3':
        if motion_thread and motion_thread.is_alive():
            motion_thread.join(0.1)
        motion_thread = execute_in_thread(rotate_down)
    elif rotate == '4':
        if motion_thread and motion_thread.is_alive():
            motion_thread.join(0.1)
        motion_thread = execute_in_thread(rotate_left)
    else:
        if motion_thread and motion_thread.is_alive():
            motion_thread.join(0.1)
        motion_thread = execute_in_thread(stopmovement)

    # Parse laser rangefinder command
    lrf = data[2]
    if lrf == '1':
        if alignment_thread and alignment_thread.is_alive():
            alignment_thread.join(0.1)
        alignment_thread = execute_in_thread(alignment_light, "on")
    elif lrf == '2':
        if alignment_thread and alignment_thread.is_alive():
            alignment_thread.join(0.1)
        alignment_thread = execute_in_thread(alignment_light, "off")
    elif lrf == '3':
        if alignment_thread and alignment_thread.is_alive():
            alignment_thread.join(0.1)
        alignment_thread = execute_in_thread(read_range)

    # Parse camera commands (implement these similarly if needed)
    zoomplus = data[4]
    zoommin = data[6]
    focusplus = data[8]
    focusmin = data[10]


def send_fixed_message(ser):
    """ Continuously send a fixed message over the serial port for testing. """
    try:
        while True:
            global value
            global kontrol
            value += 1
            data = "Ini dari jetson " + str(value) + " " + str(kontrol)  # Fixed message for testing
            ser.write(data.encode())  # Send data as bytes
            print(f"Sent on {ser.port}: {data.strip()}")
            time.sleep(10)  # Send the message every 1 second
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

def receive_and_forward_message(ser1, ser2, ser3):
    """ Continuously reaad data from ser1 and forward it to ser2. """
    try:
        ser=open_serial(PORT3)
        while True:
            if ser1.in_waiting > 0:  # Check if data is available to read
                received = ser1.readline().decode('utf-8', errors='replace').strip()
                print(f"Received on {ser1.port}: {received}")
                pecah_string = received.split(' ')
                # print(pecah_string)
                
                global kontrol
                pantilt = " ".join(pecah_string[6:])
                # Forward the received data to the second serial port
                print(f"Forwarded to {ser3.port}: {pantilt}")
                pantilt_cons(pantilt,ser)
                # print(pantilt)

                kontrol = " ".join(pecah_string[:6])
                kontrol = kontrol + ' ' + pecah_string[11]
                #pecah sinyal kontrol ke motor dan pantilt
                ser2.write((kontrol + "\n").encode())
                print(f"Forwarded to {ser2.port}: {kontrol}")

    except serial.SerialException as e:
        print(f"Error in receiving or forwarding data: {e}")

def main():
    try:
        # Open both serial ports
        ser1 = serial.Serial(PORT1, BAUD_RATE, timeout=1)
        ser2 = serial.Serial(PORT2, BAUD_RATE, timeout=1)
        ser3 = serial.Serial(PORT3, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for the connection to establish
        print(f"Connected to {PORT1} and {PORT2} at {BAUD_RATE} baud.")
        global value
        value = 0
        global kontrol
        kontrol = 0
        # Start a thread to send fixed messages on ser1
        send_thread = threading.Thread(target=send_fixed_message, args=(ser1,))
        
        # Start a thread to receive messages on ser1 and forward them to ser2
        forward_thread = threading.Thread(target=receive_and_forward_message, args=(ser1, ser2, ser3))

        send_thread.start()
        forward_thread.start()

        # Wait for both threads to complete
        send_thread.join()
        forward_thread.join()

    except serial.SerialException as e:
        print(f"Could not open serial ports: {e}")
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully.")
    finally:
        # Ensure both serial ports are closed on exit
        for ser in [ser1, ser2, ser3]:
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print(f"Serial port {ser.port} closed.")

if __name__ == "__main__":
    main()
