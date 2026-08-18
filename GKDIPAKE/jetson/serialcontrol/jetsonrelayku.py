import serial
import threading, sys
import time
from pantilt_actions import rotate_up, rotate_down, rotate_left, rotate_right, stopmovement, power_load
from lrf_actions import alignment_light, read_range

# Update these to the correct ports on your machine
#PORT1 = '/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_DU0D4UER-if00-port0'
PORT1 = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0'
PORT2 = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0'
PORT3 = '/dev/serial/by-id/usb-WCH.CN_USB_Quad_Serial_BC6228ABCD-if00'  # pantilt

BAUD_RATE = 57600
value = 0  # Initial value for the counter
kontrol = 0  # Initial control value


latest_command = {"rotate": None, "lrf": None}
exit_event = threading.Event()  # Event to signal thread failure

def update_latest_command(command_type, value):
    """Update the latest command to execute."""
    global latest_command
    latest_command[command_type] = value

def execute_latest_command():
    """ Continuously execute the latest command. """
    try:
        while not exit_event.is_set():
            # Retrieve rotate and lrf commands, ensuring they're treated as strings
            rotate = str(latest_command["rotate"])  # Ensure it's a string
            lrf = str(latest_command["lrf"])  # Ensure it's a string

            # Handle rotate commands
            if rotate == '1':
                charnya = rotate_up()
                # print(charnya)
                send_message_with_data(PORT1, charnya)
                # print('sukses')
            elif rotate == '2':
                charnya = rotate_right()
                # print(charnya)
                send_message_with_data(PORT1, charnya)
            elif rotate == '3':
                charnya = rotate_down()
                # print(charnya)
                send_message_with_data(PORT1, charnya)
            elif rotate == '4':
                charnya = rotate_left()
                # print(charnya)
                send_message_with_data(PORT1, charnya)
            elif rotate == '0':
                stopmovement()
                

            # Handle LRF commands
            #if lrf == '1':
                #alignment_light("on")
                #jarak=read_range()
                #send_message_with_data(PORT1, jarak)
            if lrf == '0':
                # alignment_light("off")
                #jarak = read_range()
                exit_event.set()
                #send_message_with_data(PORT1, jarak)

            elif lrf == '3':
                read_range()

            time.sleep(0.1)  # Small delay to avoid hogging CPU
    except Exception as e:
        print(f"Error in execute_latest_command: {e}")
        # Instead of exiting, we just log the error and continue execution.
        continue_execution = True  # You can set this flag if you want to try again or handle retries.
        if continue_execution:
            pass  # Continue execution on error, you could optionally log this or alert the user.



def pantilt_cons(data, ser):
    """Update the latest commands based on incoming data."""
    if len(data) < 1:  # Check if data is empty or too short
        print("Error: Received invalid data for pantilt_cons")
        return  # Exit the function early if data is invalid

    rotate = data[0]  # Access the first element (rotate)
    lrf = data[4]  # Access the third element (lrf)
    # print(lrf + '=================')
    update_latest_command("rotate", rotate)
    update_latest_command("lrf", lrf)

def receive_and_forward_message(ser1, ser2, ser3):
    """ Continuously read data from ser1 and forward it to ser2. """
    try:
        while not exit_event.is_set():
            if ser1.in_waiting > 0:  # Check if data is available to read
                received = ser1.readline().decode('utf-8', errors='replace').strip()
                print(f"Received on {ser1.port}: {received}")
                
                # Skip empty messages or malformed data
                if not received or len(received.split()) < 6:  # If data is empty or doesn't have enough parts
                    print(f"Skipping invalid data: {received}")
                    continue
                
                # Split the received data into a list of parts
                pecah_string = received.split(' ')
                
                # Parse the necessary parts for pantilt and control
                pantilt = " ".join(pecah_string[6:])  # Assuming the pantilt info starts from index 6
                kontrol = " ".join(pecah_string[:6])  # Control message is the first 6 elements

                # Forward the received data to the pantilt controller and the control system
                pantilt_cons(pantilt, ser3)
                kontrol = kontrol + ' ' + pecah_string[11]  # Add any other needed data to 'kontrol'
                ser2.write((kontrol + "\n").encode())
                print(f"Forwarded to {ser2.port}: {kontrol}")
    except serial.SerialException as e:
        print(f"Error in receiving or forwarding data: {e}")
        exit_event.set()  # Set the event to signal failure

def send_message_with_data(serialnya, data_string):
    """ Send a dynamic message with the provided data string to ser2. """
    try:
        ser2 = serial.Serial(PORT1, BAUD_RATE, timeout=1, rtscts=True)
        # Send the message with the provided data string to ser2
        ser2.write((data_string + "\n").encode())
        print(f"Sent to {ser2.port}: {data_string}")

    except serial.SerialException as e:
        print(f"Error sending data: {e}")
        exit_event.set()  # Set the event to signal failure

def main():
    try:
        # Open all the serial ports
        ser1 = serial.Serial(PORT1, BAUD_RATE, timeout=1, rtscts=True)
        ser2 = serial.Serial(PORT2, BAUD_RATE, timeout=1, rtscts=True)
        ser3 = serial.Serial(PORT3, BAUD_RATE, timeout=1, rtscts=True)
        # ser1.dtr = False
        # ser2.dtr = False
        # ser3.dtr = False
        time.sleep(10)  # Wait for the connection to establish
        print(f"Connected to {PORT1}, {PORT2}, and {PORT3} at {BAUD_RATE} baud.")


        power_load("on")
        # Start the threads
        # send_thread = threading.Thread(target=send_message_with_data, args=(ser1,))
        forward_thread = threading.Thread(target=receive_and_forward_message, args=(ser1, ser2, ser3))
        control_thread = threading.Thread(target=execute_latest_command, daemon=True)

        # send_thread.start()
        forward_thread.start()
        control_thread.start()

        # Wait for any failure in threads (exit_event will be set if any thread fails)
        while not exit_event.is_set():
            time.sleep(0.1)  # Monitor the exit event

        print("A thread failed, exiting...")

    except serial.SerialException as e:
        print(f"Could not open serial ports: {e}")
        exit_event.set()  # Set the event to signal failure
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully.")
        exit_event.set()  # Set the event to signal failure
    finally:
        # Ensure both serial ports are closed on exit
        # power_load("off")
        for ser in [ser1, ser2, ser3]:
            if ser.is_open:
                ser.close()
                print(f"Serial port {ser.port} closed.")

if __name__ == "__main__":
    main()
