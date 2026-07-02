import serial
import threading
import time

# Update this to the correct port on your Windows machine (e.g., 'COM3')
PORT = 'COM3'  # Replace with the actual COM port
BAUD_RATE = 57600

def send_fixed_message(ser):
    """ Continuously send a fixed message over the serial port for testing. """
    try:
        while True:
            data = "Hello\n"  # Fixed message for testing
            ser.write(data.encode())  # Send data as bytes
            print(f"Sent: {data.strip()}")
            time.sleep(1)  # Send the message every 1 second
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

def receive_message(ser):
    """ Continuously read and display data received from the serial port. """
    try:
        while True:
            if ser.in_waiting > 0:  # Check if data is available to read
                received = ser.readline().decode('utf-8', errors='replace').strip()
                print(f"Received: {received}")
    except serial.SerialException as e:
        print(f"Error receiving data: {e}")

def main():
    try:
        # Open the serial port
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for the connection to establish
        print(f"Connected to {PORT} at {BAUD_RATE} baud.")

        # Start threads for sending and receiving fixed messages
        send_thread = threading.Thread(target=send_fixed_message, args=(ser,))
        receive_thread = threading.Thread(target=receive_message, args=(ser,))

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
