from pantilt_actions import rotate_up, rotate_down, rotate_left, rotate_right, read_angle, power_load
from lrf_actions import read_range, alignment_light

def main():
    print("Press 'i', ',', 'j', 'l', 'k', 's', '1', '0' for respective actions.")
    print("Type 'q' to quit.")
    
    while True:
        user_input = input("Enter command: ").strip()  # Reads input from the user

        if user_input == 'i':
            rotate_up()
        elif user_input == ',':
            rotate_down()
        elif user_input == 'j':
            rotate_left()
        elif user_input == 'l':
            rotate_right()
        elif user_input == 'k':
            read_angle()
        elif user_input == 's':
            read_range()
        elif user_input == 'w':
            alignment_light("on")
        elif user_input == '1':
            power_load("on")
        elif user_input == '0':
            power_load("off")
        elif user_input == 'q':
            print("Exiting...")
            break
        else:
            print("Unknown command, please try again.")

if __name__ == "__main__":
    main()