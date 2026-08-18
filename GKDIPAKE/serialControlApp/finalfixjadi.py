import serial
import threading
import tkinter as tk
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
import time

# Serial ports and baudrate configuration
baudrate = 57600

# Global references to serial ports
ser1 = None
ser2 = None

def relay_data(serial_in, serial_out, terminal_text):
    """
    Relay data from serial_in to serial_out and display in the terminal.
    """
    while True:
        try:
            if serial_in.in_waiting > 0:
                data = serial_in.read(serial_in.in_waiting)  # Read all available data
                decoded_data = data.decode('utf-8').strip()  # Strip unwanted characters
                terminal_text.insert(tk.END, f"Relayed Data: {decoded_data}\n")
                terminal_text.yview(tk.END)  # Auto-scroll to the latest message
                serial_out.write(data)  # Write to the other port
        except Exception as e:
            terminal_text.insert(tk.END, f"Error in relaying data: {e}\n")
            terminal_text.yview(tk.END)

def read_from_serial(serial_port, data_display):
    """
    Read data from serial port line-by-line, decode, and display on the terminal.
    """
    while True:
        try:
            if serial_port.in_waiting > 0:
                # Read one line at a time
                data = serial_port.readline()  # Read until newline or timeout
                if data:
                    decoded_data = data.decode('utf-8').strip()  # Remove unwanted 'b' and \r\n
                    data_display.insert(tk.END, f"Received: {decoded_data}\n")
                    data_display.yview(tk.END)  # Auto-scroll
                    parse_and_display_data(decoded_data)
        except Exception as e:
            data_display.insert(tk.END, f"Error reading from {serial_port.portstr}: {e}\n")
            data_display.yview(tk.END)

def parse_and_display_data(data):
    """
    Parse the space-separated data and display its meaning.
    """
    try:
        # Split the data by spaces
        parts = data.split()
        if len(parts) == 13:  # Ensure we have exactly 13 parts
            mode = parts[0]
            throttle = int(parts[1])
            down = int(parts[2])
            up = int(parts[3])
            motor_correction = int(parts[4])
            motor_correction_value = int(parts[5])

            # Display the parsed information in the label
            parsed_text = (
                f"Mode: {mode}\n"
                f"Throttle: {throttle}\n"
                f"Down: {down}\n"
                f"Up: {up}\n"
                f"Motor Correction: {motor_correction}\n"
                f"Motor Correction Value: {motor_correction_value}"
            )
            parsed_label.config(text=parsed_text)
        else:
            parsed_label.config(text="Invalid data format")
    except Exception as e:
        parsed_label.config(text=f"Error parsing data: {e}")

def open_serial_ports():
    global ser1, ser2
    try:
        # Open the selected serial ports
        ser1 = serial.Serial(port1_var.get(), baudrate, timeout=1, rtscts=True)
        ser2 = serial.Serial(port2_var.get(), baudrate, timeout=1, rtscts=False)

        terminal_text.insert(tk.END, f"Opened ports: {port1_var.get()} and {port2_var.get()}\n")
        terminal_text.yview(tk.END)

        # Disable Open Ports button and enable Stop button
        open_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

        # Start threads to relay data and read from COM4
        threading.Thread(target=relay_data, args=(ser1, ser2, terminal_text), daemon=True).start()
        threading.Thread(target=read_from_serial, args=(ser2, data_display), daemon=True).start()
    except Exception as e:
        terminal_text.insert(tk.END, f"Error opening serial ports: {e}\n")
        terminal_text.yview(tk.END)

def stop_operations():
    global ser1, ser2
    try:
        if ser1 and ser1.is_open:
            ser1.close()
        if ser2 and ser2.is_open:
            ser2.close()
        terminal_text.insert(tk.END, "Closed serial ports.\n")
        terminal_text.yview(tk.END)

        # Enable Open Ports button and disable Stop button
        open_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)

        # Stop the video capture
        app.stop_video()
    except Exception as e:
        terminal_text.insert(tk.END, f"Error stopping operations: {e}\n")
        terminal_text.yview(tk.END)

# Video capture class
class MyVideoCapture:
    def __init__(self, video_source=0) -> None:
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def release(self):
        if self.vid.isOpened():
            self.vid.release()

# Camera app class
class CameraApp:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.title(window_title)
        self.video_source = video_source

        # open video source
        self.vid = MyVideoCapture(self.video_source)

        # create a canvas that can fit the above video
        self.canvas = tk.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.pack(side=tk.RIGHT)

        # after it is called once, the update method will be automatically called every delay ms
        self.delay = 15
        self.update()

    def update(self):
        ret, frame = self.vid.get_frame()
        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def stop_video(self):
        self.vid.release()

# Tkinter GUI setup
root = tk.Tk()
root.title("Serial Relay and Camera Feed")

# Frame for Serial Communication on the left
frame_ports = ttk.Frame(root)
frame_ports.pack(side=tk.LEFT, padx=10, pady=10)

# COM Port selection for Send
frame_send = ttk.Frame(frame_ports)
frame_send.pack(pady=5)

ttk.Label(frame_send, text="COM Port 1 (Send):").grid(row=0, column=0, padx=5, pady=5)
port1_var = tk.StringVar()
port1_combobox = ttk.Combobox(frame_send, textvariable=port1_var, values=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'], state="readonly")
port1_combobox.set('COM3')
port1_combobox.grid(row=0, column=1, padx=5, pady=5)

# COM Port selection for Receive
frame_receive = ttk.Frame(frame_ports)
frame_receive.pack(pady=5)

ttk.Label(frame_receive, text="COM Port 2 (Receive):").grid(row=0, column=0, padx=5, pady=5)
port2_var = tk.StringVar()
port2_combobox = ttk.Combobox(frame_receive, textvariable=port2_var, values=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9'], state="readonly")
port2_combobox.set('COM4')
port2_combobox.grid(row=0, column=1, padx=5, pady=5)

# Data Terminal
frame_terminal = ttk.Frame(frame_ports)
frame_terminal.pack(pady=5)

terminal_text = tk.Text(frame_terminal, height=10, width=50, wrap=tk.WORD)
terminal_text.pack()

# Data Meaning
frame_parsed = ttk.Frame(frame_ports)
frame_parsed.pack(pady=5)

parsed_label = ttk.Label(frame_parsed, text="Data Meaning will appear here.", justify=tk.LEFT)
parsed_label.pack()

# Data Received to Device
frame_data = ttk.Frame(frame_ports)
frame_data.pack(pady=5)

data_display = tk.Text(frame_data, height=5, width=50, wrap=tk.WORD, bg="lightgray")
data_display.pack()

# Start/Stop Button
start_stop_frame = ttk.Frame(frame_ports)
start_stop_frame.pack(pady=10)

open_button = ttk.Button(start_stop_frame, text="Start", command=open_serial_ports)
open_button.grid(row=0, column=0, padx=5)

stop_button = ttk.Button(start_stop_frame, text="Stop", command=stop_operations, state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=5)

# Start the video feed
app = CameraApp(root, "Camera", 3)

# Exit Button
ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

root.mainloop()
