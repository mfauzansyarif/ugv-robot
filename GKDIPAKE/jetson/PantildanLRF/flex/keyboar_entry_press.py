import keyboard
from pantilt_actions2 import rotate_up, rotate_down, rotate_left, rotate_right, read_angle, power_load, stopmovement
from lrf_actions import read_range, alignment_light
import time

# Track the last rotation key pressed
last_key_pressed = None

def main():
    global last_key_pressed

    print("Press 'i', ',', 'j', 'l', 'k', 's', 'w', '1', '0' for respective actions.")
    print("Hold the key to keep the action active.")
    print("Type 'q' to quit.")

    while True:
        key_pressed = False  # Flag to track if a movement key is pressed

        if keyboard.is_pressed('i'):
            rotate_up()
            last_key_pressed = 'i'
            key_pressed = True
        elif keyboard.is_pressed(','):
            rotate_down()
            last_key_pressed = ','
            key_pressed = True
        elif keyboard.is_pressed('j'):
            rotate_left()
            last_key_pressed = 'j'
            key_pressed = True
        elif keyboard.is_pressed('l'):
            rotate_right()
            last_key_pressed = 'l'
            key_pressed = True
        elif keyboard.is_pressed('k'):
            read_angle()
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
            stopmovement()
            last_key_pressed = None  # Reset last key pressed

        # Sleep a bit to prevent high CPU usage
        time.sleep(0.1)

if __name__ == "__main__":
    main()
