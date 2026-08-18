import serial
import struct

# serialPort = '/dev/tty.usbmodemBC6228ABCD1'
serialPort = '/dev/ttyACM0'

def open_serial(port, baudrate=9600, timeout=1):
    """Opens the serial port with the given parameters."""
    ser = serial.Serial(
        port=port,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=timeout  # Set a read timeout of 1 second
    )
    return ser

def close_serial(ser):
    """Closes the serial port."""
    if ser.is_open:
        ser.close()

# Function to send payload with checksum
def send_payload(ser, payload):
    # Calculate checksum
    checksum = calculate_checksum_LRF(payload)

    # append the checksum at the end
    payload.append(checksum)
    message = bytes(payload)

    # Send the message
    ser.write(message)
    print(f"Sent: {' '.join(format(b, '02X') for b in message)}")

def calculate_checksum_LRF(data):
    """
    Calculate the checksum by summing all bytes
    and XOR it with 50h
    """

    hex_bytes = data
    checksum = sum(hex_bytes) % 256   
    final_checksum = checksum ^ 0x50
    return final_checksum

def hex_to_float_little_endian(hex_bytes):
    
    # Unpack the bytes using IEEE 754 float format (little endian)
    value = struct.unpack('<f', hex_bytes)[0]
    
    return value

def extract_range_1_data(hex_data):
    # Check if the data starts with the identifier '59 CC'
    if hex_data[:2] == bytes([0x59, 0xCC]):

        # Calculate the data checksum excluding the tail data checksum itself
        calculated_checksum = calculate_checksum_LRF(hex_data[:-1])

        # Extract checksum from the last byte
        received_checksum = hex_data[21]

        # Compare checksum and calculated checksum
        if received_checksum == calculated_checksum:
            # Extract Range 1 data (4 bytes)
            range_1_hex = hex_data[2:6]

            # Convert the Range 1 hex to a float value in meters
            range_1_meters = hex_to_float_little_endian(range_1_hex)
            if range_1_meters >= 1:
                return range_1_meters
            else:
                return range_1_meters
        else:
            print(f"Checksum mismatch. Received: {received_checksum}, Calculated: {calculated_checksum}")
            return 0
    else:
        return 0


def read_range():
    ser = open_serial(serialPort)
    payload = [0xCC, 0x10, 0x00, 0x00]
    send_payload(ser, payload)

    # Read response from the serial port
    response = ser.read(22)

    ### -- test call only:
    hex_string = ''.join(f'{x:02X}' for x in response[2:6])
    print(f"{hex_string}")
    ### ---

    close_serial(ser)




    # Extract and convert Range 1 data to meters
    range_1_meters = extract_range_1_data(response)
    print(f"Range 1 in meters: {range_1_meters}")

def alignment_light(switch):
    if switch == "on":
        payload = [0xC5, 0x02]
        ser = open_serial(serialPort)
        send_payload(ser, payload)
        close_serial(ser)
    elif switch == "off":
        payload = [0xC5, 0x00]
        ser = open_serial(serialPort)
        send_payload(ser, payload)
        close_serial(ser)
    return 0