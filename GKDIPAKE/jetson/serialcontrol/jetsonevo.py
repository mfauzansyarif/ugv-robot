import serial
import threading
import time

# Define the ports and baud rate
PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2']  # Update as needed
BAUD_RATE = 57600

def send_data(ser):
    """Continuously send user-inputted data over the serial port."""
    try:
        while True:
            data = input("Enter a message to send: ")
            data += '\n'
            ser.write(data.encode())
            print(f"Sent: {data.strip()}")
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

def receive_data(ser):
    """Continuously read and print data received from the serial port."""
    try:
        while True:
            if ser.in_waiting > 0:
                received = ser.readline().decode('utf-8', errors='replace').strip()
                print(f"Received: {received}")
    except serial.SerialException as e:
        print(f"Error receiving data: {e}")

def main():
    serial_ports = []  # List to store successfully opened ports

    # Try to open each port
    for port in PORTS:
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=1)
            serial_ports.append(ser)
            print(f"Connected to {port} at {BAUD_RATE} baud.")
        except serial.SerialException as e:
            print(f"Failed to open {port}: {e}")

    # Exit if no ports were opened
    if not serial_ports:
        print("No serial ports available. Exiting.")
        return

    try:
        # Start threads for each serial port
        for ser in serial_ports:
            threading.Thread(target=send_data, args=(ser,), daemon=True).start()
            threading.Thread(target=receive_data, args=(ser,), daemon=True).start()

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting gracefully.")
    finally:
        # Close all serial ports
        for ser in serial_ports:
            if ser.is_open:
                ser.close()
                print(f"Closed port {ser.port}")

if __name__ == "__main__":
    main()
