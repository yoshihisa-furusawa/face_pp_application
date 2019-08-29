import sys
sys.dont_write_bytecode = True

import cv2
from PIL import Image
from PIL import ImageTk
import threading
import tkinter as tk
import numpy as np
import time

import os

class GUI(object):
    def __init__(self, window_h, window_w, window_x_cood, window_y_cood, movie_h, movie_w, out_writer):
        self.movie_flag = True
        self.get_movie = False
        self.cap = cv2.VideoCapture(0)
        self.window_h = window_h
        self.window_w = window_w
        self.window_x_cood = window_x_cood
        self.window_y_cood = window_y_cood
        self.movie_h = movie_h
        self.movie_w = movie_w
        self.out_writer = out_writer
        self.movie_start = True
        self.elapsed_time = 0

        # 画面が更新される速度(ms単位で指定する必要がある)と動画のフレームレートを調整する
        self.video_adjust_rate = int((1./self.cap.get(cv2.CAP_PROP_FPS))*1000)

    def button_start(self):
        self.get_movie = True
        thread = threading.Thread(target=self.on_image, args=())
        thread.start()

        thread_time = threading.Thread(target=self.get_movie_time, args=())
        thread_time.start()

    def on_image(self):
        image = Image.open("/" + os.path.join(*os.path.abspath(__file__).split("/")[:-1]) + "/on_image.jpg")
        image = ImageTk.PhotoImage(image.resize((50, 50)))
        self.panel = tk.Label(image=image)
        self.panel.image = image
        self.panel.place(x=25+150, y=100)

    def get_movie_time(self):
        s = round(self.elapsed_time, 1)
        h = (round(self.elapsed_time, 1)//360)
        m = (round(self.elapsed_time, 1)//60)

        def int_to_string(a, zfill_value=2):
            return int(a).__str__().zfill(zfill_value)
        s, h, m = int_to_string(s), int_to_string(h), int_to_string(m)
        self.root.title('{}:{}:{}'.format(h, m, s))
        self.root.after(50, self.get_movie_time)

    def button_end(self):
        thread = threading.Thread(target=self.destroy, args=())
        thread.start()

    def destroy(self):
        self.out_writer.release()
        self.panel.quit()
        self.root.quit()
        quit()

    def videoLoop(self, mirror=True):
        _, frame = self.cap.read()
        frame = cv2.resize(frame, (self.window_w, self.window_h))

        if self.get_movie:
            if self.movie_start:
                self.start_time = time.time()
                self.movie_start = False
            self.elapsed_time = time.time() - self.start_time

            frame_resize = cv2.resize(frame, (self.movie_w, self.movie_h))
            if mirror:
                frame_resize = frame_resize[:, ::-1]
            self.out_writer.write(frame_resize)

        if mirror:
            frame = frame[:,::-1, ::-1]
        else:
            frame = frame[:, :, ::-1]

        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(frame)
        self.panel = tk.Label(image=frame)
        self.panel.image = frame
        self.panel.place(x=250, y=0)
        self.panel.after(50, self.videoLoop)

    def __call__(self, window_w=None, window_h=None, window_x_cood=None, window_y_cood=None):
        for name in ["window_w", "window_h", "window_x_cood", "window_y_cood"]:
            if eval(name) is not None:
                setattr(self, name, eval(name))

        self.root = tk.Tk()
        self.root.geometry("{}x{}+{}+{}".format(self.window_w + 400, self.window_h + 100, self.window_x_cood, self.window_y_cood))
        thread = threading.Thread(target=self.videoLoop, args=())
        thread.start()

        button1 = tk.Button(self.root, text="Record", bg="#fff", font=("",50), command=self.button_start)
        button1.place(x=25, y=100, width=150, height=50)

        button2 = tk.Button(self.root, text="Stop", bg="#fff", font=("",50), command=self.button_end)
        button2.place(x=25, y=200, width=150, height=50)
        self.root.mainloop()

if __name__ == '__main__':
    window_h, window_w, movie_h, movie_w = 600, 600, 400, 400
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('/Users/furusawa_yoshihisa/Desktop/output.mp4', fourcc, cap.get(cv2.CAP_PROP_FPS), (movie_w, movie_h))

    GUI(window_h, window_w, movie_h, movie_w, out)()
