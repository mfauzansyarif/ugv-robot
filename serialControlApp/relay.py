import serial
import threading

# Configure serial ports
port1 = 'COM6'  # COM port for the first device
port2 = 'COM4'  # COM port for the second device

baudrate = 57600  # Adjust as needed for your devices

def relay_data(serial_in, serial_out):
    """
    Relay data from serial_in to serial_out.
    """
    while True:
        try:
            if serial_in.in_waiting > 0:
                data = serial_in.read(serial_in.in_waiting)  # Read all available data
                serial_out.write(data)  # Write to the other port
                print(str(data))
        except Exception as e:
            print(f"Error in relaying data: {e}")
            break

def main():
    try:
        # Open serial ports
        ser1 = serial.Serial(port1, baudrate, timeout=1, rtscts=True)
        ser2 = serial.Serial(port2, baudrate, timeout=1, rtscts=False)

        print(f"Relaying data between {port1} and {port2}")

        # Create threads to relay data in both directions
        thread1 = threading.Thread(target=relay_data, args=(ser1, ser2))
        thread2 = threading.Thread(target=relay_data, args=(ser2, ser1))

        # Start threads
        thread1.start()
        thread2.start()

        # Join threads to keep the main program running
        thread1.join()
        thread2.join()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure ports are closed on exit
        if 'ser1' in locals() and ser1.is_open:
            ser1.close()
        if 'ser2' in locals() and ser2.is_open:
            ser2.close()

if __name__ == "__main__":
    main()
