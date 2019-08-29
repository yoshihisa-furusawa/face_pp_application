import cv2
from PIL import Image
from PIL import ImageTk
import threading
import tkinter as tk
import numpy as np
import sys
import time

import os

class GUI(object):
    def __init__(self, window_h, window_w, movie_h, movie_w, out_writer):
        self.movie_flag = True
        self.get_movie = False
        self.cap = cv2.VideoCapture(0)
        self.window_h = window_h
        self.window_w = window_w
        self.movie_h = movie_h
        self.movie_w = movie_w
        self.out_writer = out_writer
        
    def button_start(self):
        self.get_movie = True
        self.start_time = time.time()
        thread = threading.Thread(target=self.on_image, args=())     
        thread.start()
            
        thread_time = threading.Thread(target=self.get_movie_time, args=())
        thread_time.start()
            
    def on_image(self):
        image = Image.open("/" + os.path.join(*os.path.abspath(__file__).split("/")[:-1]) + "/on_image.jpg").resize((50, 50))
        image = ImageTk.PhotoImage(image)
        self.panel = tk.Label(image=image)
        self.panel.image = image
        self.panel.place(x=25+150, y=100)
        
    def get_movie_time(self):
        elapsed_time = time.time() - self.start_time
        s = int(elapsed_time).__str__().zfill(2)
        h = (int(elapsed_time)//360).__str__().zfill(2)
        m = (int(elapsed_time)//60).__str__().zfill(2)
        
        self.root.title('{}:{}:{}'.format(h, m, s))
        self.root.after(50, self.get_movie_time)

    def button_end(self):
        thread = threading.Thread(target=self.destroy, args=())
        thread.start()

    def destroy(self):
        self.out_writer.release()
        self.panel.quit()
        self.root.quit()
        exit()
        
    def videoLoop(self):
        _, frame = self.cap.read()
        frame = cv2.resize(frame, (self.window_w, self.window_h))
        
        if self.get_movie:
            frame_resize = cv2.resize(frame, (self.movie_w, self.movie_h))
            self.out_writer.write(frame_resize[:, ::-1])
            
        frame = frame[:,::-1, ::-1]
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(frame)
        self.panel = tk.Label(image=frame)
        self.panel.image = frame
        self.panel.place(x=250, y=0)
        self.panel.after(50, self.videoLoop)

    def __call__(self):
        self.root = tk.Tk()
        
        self.root.geometry("{}x{}".format(self.window_w + 400, self.window_h + 100))
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