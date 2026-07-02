import keyboard, time
from pantilt_actions2 import rotate_up, rotate_down, rotate_left, rotate_right, read_angle, power_load, open_serial, stopmovement
from lrf_actions import read_range, alignment_light


def main():
    serialPort = '/dev/ttyACM0'
    ser = open_serial(serialPort)
    
    global last_key_pressed
    last_key_pressed = None

    print("Press 'i', ',', 'j', 'l', 'k', 's', 'w', '1', '0' for respective actions.")
    print("Hold the key to keep the action active.")
    print("Type 'q' to quit.")

    while True:
        key_pressed = False  # Flag to track if a movement key is pressed

        if keyboard.is_pressed('i'):
            rotate_up(ser)
            last_key_pressed = 'i'
            key_pressed = True
        elif keyboard.is_pressed(','):
            rotate_down(ser)
            last_key_pressed = ','
            key_pressed = True
        elif keyboard.is_pressed('j'):
            rotate_left(ser)
            last_key_pressed = 'j'
            key_pressed = True
        elif keyboard.is_pressed('l'):
            rotate_right(ser)
            last_key_pressed = 'l'
            key_pressed = True
        elif keyboard.is_pressed('k'):
            read_angle(ser)
        elif keyboard.is_pressed('s'):
            read_range()
        elif keyboard.is_pressed('w'):
            alignment_light("on")
        elif keyboard.is_pressed('1'):
            power_load("on")
        elif keyboard.is_pressed('0'):
            power_load("off")
        elif keyboard.is_pressed('q'):
            print("Exiting...")
            break

        # Stop movement if no movement key is currently pressed
        if not key_pressed and last_key_pressed in ['i', ',', 'j', 'l']:
            stopmovement(ser)
            last_key_pressed = None  # Reset last key pressed

        # Sleep a bit to prevent high CPU usage
        time.sleep(0.3)
    

    stopmovement(ser)
    time.sleep(1)

    
    read_angle(ser)


if __name__ == "__main__":
    main()
