import serial
import threading
import time
import string

# Update this to the correct port on your machine
PORT = '/dev/ttyUSB1'  # or '/dev/ttyACM0'
BAUD_RATE = 57600

def send_data(ser):
    """ Continuously send user-inputted data over the serial port. """
    try:
        while True:
            data = input("Enter a message to send: ")
            ser.write(data.encode())  # Send data as bytes
            print(f"Sent: {data}")
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

def receive_data(ser):
    """ Continuously read and print data received from the serial port. """
    try:
        while True:
            if ser.in_waiting > 0:  # Check if data is waiting to be read
                # Decode received data with error handling
                received = ser.readline().decode('utf-8', errors='replace').strip()
                # Filter to display only printable characters
                printable_data = ''.join(filter(lambda x: x in string.printable, received))
                print(f"Received: {printable_data}")
    except serial.SerialException as e:
        print(f"Error receiving data: {e}")

def main():
    try:
        # Attempt to open the serial port
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1, dsrdtr=False, rtscts=False)
        time.sleep(2)  # Wait for the connection to establish
        print(f"Connected to {PORT} at {BAUD_RATE} baud.")

        # Start threads for sending and receiving
        send_thread = threading.Thread(target=send_data, args=(ser,))
        receive_thread = threading.Thread(target=receive_data, args=(ser,))

        send_thread.start()
        receive_thread.start()

        # Wait for both threads to complete
        send_thread.join()
        receive_thread.join()

    except serial.SerialException as e:
        print(f"Could not open serial port {PORT}: {e}")
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully.")
    finally:
        # Ensure the serial port is closed on exit
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
