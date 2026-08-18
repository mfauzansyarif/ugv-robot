import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
import time

class App:
    def __init__(self, window, window_title, video_source=0) -> None:
        self.window = window
        self.window.title(window_title)
        self.video_source = video_source

        # open video source 
        self.vid = MyVideoCapture(self.video_source)

        # create a canvas that can fit the above video
        self.canvas = tk.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        # after it is called once, the update method will be automatically called every delay ms
        self.delay = 15
        self.update()

        self.window.mainloop()


    def update(self):
        ret, frame = self.vid.get_frame()
        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

class MyVideoCapture:
    def __init__(self, video_source=0) -> None:
        #self.vid = cv2.VideoCapture(video_source, cv2.CAP_GSTREAMER)
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
        
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

#App(tk.Tk(), "Camera", "videotestsrc ! appsink")
App(tk.Tk(), "Camera", 3)