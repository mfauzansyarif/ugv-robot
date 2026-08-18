import serial
import time
import os
# from dotenv import load_dotenv

# Load the .env file
# load_dotenv()

# const
serialPort = '/dev/ttyACM0'
# Read values from the .env file
# mVert1 = float(os.getenv('mVert1'))
# mVert2 = float(os.getenv('mVert2'))
# bVert = float(os.getenv('bVert'))
# mHori1 = float(os.getenv('mHori1'))
# mHori2 = float(os.getenv('mHori2'))
# bHori = float(os.getenv('bHori'))

mVert1 = 2.694879023302476
mVert2 = 1.1455831934909497
bVert = -73.36566910656754
mHori1 = 2.447221740538158
mHori2 = -2.2315937758949502
bHori = -69.7511885011599


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
    checksum = calculate_checksum_pantilt(payload)
    
    # Add FF at the start and append the checksum at the end
    message = [0xFF] + payload + [checksum]
    
    # Send the message
    ser.write(bytes(message))
    # print(f"Sent: {' '.join(format(b, '02X') for b in message)}")

def calc_angle(m1, m2, b, encoder_data):
    angle = m1 * encoder_data[0] + m2 * encoder_data[1] / 100 + b
    return angle

# Function to calculate checksum by summing bytes, omitting FF
def calculate_checksum_pantilt(data):
    checksum = 0
    for byte in data:
        if byte != 0xFF:  # Omit FF
            checksum += byte
    return checksum & 0xFF  # Truncate to 8 bits

def post_rotate_angle(direction, ser):
    if direction not in ["elevation", "azimuth"]:
        print("Invalid direction.")
        return None

    try:
        if direction == "elevation":
            payload = [0x00, 0x00, 0x53, 0x00, 0x00]  # Example vertical payload
        elif direction == "azimuth":
            payload = [0x00, 0x00, 0x51, 0x00, 0x00]  # Example horizontal payload

        # Send the command
        send_payload(ser, payload)

        # Read the response (expecting 7 bytes)
        response = ser.read(7)

        if len(response) == 7:
            start_byte = response[0]
            response_payload = list(response[1:6])  # Extract 5 bytes of payload
            response_checksum = response[6]  # Extract checksum

            # Calculate checksum for the response payload
            calculated_checksum = calculate_checksum_pantilt(response_payload)

            print(f"Response payload: {' '.join(format(b, '02X') for b in response_payload)}")

            if calculated_checksum == response_checksum:
                print("Checksum valid.")
                return response_payload  # Return the valid payload
            else:
                # Log checksum mismatch but continue
                print(f"Checksum mismatch: expected {calculated_checksum}, got {response_checksum}")
                return None  # Return None to indicate failure but continue

        else:
            print("Invalid response length.")
            return None  # Return None if the response length is invalid

    except Exception as e:
        print(f"Error in post_rotate_angle: {e}")
        return None  # Return None in case of any other error but continue

def rotate_left():
    ser = open_serial(serialPort)
    
    try:
        # Rotate left command
        payload_1 = [0x00, 0x00, 0x04, 0x3F, 0x00]
        send_payload(ser, payload_1)

        # Sleep for 1 second
        time.sleep(1)

        # Send stop command
        payload_2 = [0x00, 0x00, 0x00, 0x00, 0x00]
        send_payload(ser, payload_2)

        # Sleep for 1 second
        time.sleep(1)

        # Get response for azimuth
        response_payload = post_rotate_angle("azimuth", ser)

        if response_payload is not None:
            encoder_data = response_payload[3:6]
            angle = movement_angle("azimuth", encoder_data)
            return angle
        else:
            print("Error receiving azimuth response, skipping angle calculation.")
            return '0'

    except Exception as e:
        print(f"Error in rotate_left: {e}")

    # Close the serial port
    close_serial(ser)

def rotate_right():
    ser = open_serial(serialPort)
    
    try:
        # Rotate right command
        payload_1 = [0x00, 0x00, 0x02, 0x3F, 0x00]
        send_payload(ser, payload_1)

        # Sleep for 1 second
        time.sleep(1)

        # Send stop command
        payload_2 = [0x00, 0x00, 0x00, 0x00, 0x00]
        send_payload(ser, payload_2)

        # Sleep for 1 second
        time.sleep(1)

        # Get response for azimuth
        response_payload = post_rotate_angle("azimuth", ser)

        if response_payload is not None:
            encoder_data = response_payload[3:6]
            angle = movement_angle("azimuth", encoder_data)
            return angle
        else:
            print("Error receiving azimuth response, skipping angle calculation.")
            return '0'

    except Exception as e:
        print(f"Error in rotate_right: {e}")

    # Close the serial port
    close_serial(ser)

def rotate_up():
    ser = open_serial(serialPort)
    
    try:
        # Rotate up command
        payload_1 = [0x00, 0x00, 0x08, 0x00, 0x3F]
        send_payload(ser, payload_1)

        # Sleep for 1 second
        time.sleep(1)

        # Send stop command
        payload_2 = [0x00, 0x00, 0x00, 0x00, 0x00]
        send_payload(ser, payload_2)

        # Sleep for 1 second
        time.sleep(1)

        # Get response for elevation
        response_payload = post_rotate_angle("elevation", ser)

        if response_payload is not None:
            encoder_data = response_payload[3:6]
            angle = movement_angle("elevation", encoder_data)
            return angle
        else:
            print("Error receiving elevation response, skipping angle calculation.")
            return '0'

    except Exception as e:
        print(f"Error in rotate_up: {e}")

    # Close the serial port
    close_serial(ser)

def rotate_down():
    ser = open_serial(serialPort)
    
    try:
        # Rotate down command
        payload_1 = [0x00, 0x00, 0x10, 0x00, 0x3F]
        send_payload(ser, payload_1)

        # Sleep for 1 second
        time.sleep(1)

        # Send stop command
        payload_2 = [0x00, 0x00, 0x00, 0x00, 0x00]
        send_payload(ser, payload_2)

        # Sleep for 1 second
        time.sleep(1)

        # Get response for elevation
        response_payload = post_rotate_angle("elevation", ser)

        if response_payload is not None:
            encoder_data = response_payload[3:6]
            angle = movement_angle("elevation", encoder_data)
            return angle
        else:
            print("Error receiving elevation response, skipping angle calculation.")
            return '0'

    except Exception as e:
        print(f"Error in rotate_down: {e}")

    # Close the serial port
    close_serial(ser)

def movement_angle(direction, encoder_data):
    # init value and no calculation result value
    angle = 0
    sudut = 0
    try:
        if direction == "elevation":
            angle = calc_angle(mVert1, mVert2, bVert, encoder_data)
            sudut = "elevasi " + str(angle)
            # print(f"elev: {angle}")
            return sudut
        if direction == "azimuth":
            angle = calc_angle(mHori1, mHori2, bHori, encoder_data)
            print(f"azim: {angle}")
            sudut = "azimuth " + str(angle)
            return sudut
    except Exception as e:
        return sudut

def read_angle():
    ser = open_serial(serialPort)

    response_payload = post_rotate_angle("elevation", ser)
    encoder_data = response_payload[3:6] if response_payload else []
    movement_angle("elevation", encoder_data)

    response_payload = post_rotate_angle("azimuth", ser)
    encoder_data = response_payload[3:6] if response_payload else []
    movement_angle("azimuth", encoder_data)

    # Close the serial port
    close_serial(ser)

def stopmovement():
    ser = open_serial(serialPort)
    # Send stop command: 00 00 00 00 00
    payload_2 = [0x00, 0x00, 0x00, 0x00, 0x00]
    send_payload(ser, payload_2)

def power_load(switch):
    if switch == "on":
        ser = open_serial(serialPort)
        
        # Power on the load part of pantilt's slip ring
        payload = [0x00, 0x00, 0x09, 0x00, 0x02]
        send_payload(ser, payload)
        # close_serial(ser)

    elif switch == "off":
        ser = open_serial(serialPort)
        
        # Power off the load part of pantilt's slip ring
        payload = [0x00, 0x00, 0x0B, 0x00, 0x02]
        send_payload(ser, payload)
        close_serial(ser)
