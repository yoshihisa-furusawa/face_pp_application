import sys
sys.dont_write_bytecode = True

from PIL import Image
from PIL import ImageTk
import threading
import tkinter as tk
import numpy as np
import time
import pandas as pd
import yaml

import os
from gui_to_movie import GUI
import glob

class Logging(object):
    def __init__(self, image_list):
        self.select_number = 0
        self.image_list = image_list

    def return_image_path(self):
        return self.image_list[self.select_number]

    def record(self, output_path, label, label_value):
        if self.select_number == 0:
            open(output_path, "w").close()
            data = pd.DataFrame([], index=["label", "label_value"])
        else:
            with open(output_path, "r+") as f:
                data = pd.read_csv(f, usecols=self.use_culms)

        data[self.return_image_path().split("/")[-1]] = [label, label_value]
        self.use_culms = data.columns.tolist()
        self.use_culms = sorted(self.use_culms, key=lambda x : x.split(".")[0])
        data[self.use_culms].to_csv(output_path)

class Botton(object):
    def __init__(self, label, label_value, output_path, log):
        self.label = label
        self.label_value = label_value
        self.output_path = output_path
        self.log = log

    def button(self):
        thread = threading.Thread(target=self.anotetion, args=())
        thread.start()

    def anotetion(self):
        self.log.record(self.output_path, self.label, self.label_value)
        self.log.select_number += 1

    def __call__(self, root, botton_cood):
        button = tk.Button(root, text=self.label, bg="#fff", font=("",20), command=self.button)
        x, y, width, height = botton_cood
        button.place(x=x, y=y, width=width, height=height)

class Anotation(object):
    def __init__(self, output_path, input_image_path, config_path=None, anotation_random=True):
        print(config_path)
        with open(config_path, "r") as f:
            self.config = yaml.load(f)

        if anotation_random:
            np.random.seed(1)
            image_list = np.array(glob.glob(os.path.join(*[input_image_path, "*"])))
            shuffle_index = np.random.permutation(len(image_list))
            self.image_list = image_list[shuffle_index].tolist()
        else:
            self.image_list = sorted(glob.glob(os.path.join(*[input_image_path, "*"])))

        self.log = Logging(self.image_list)

        for i, (key, value) in enumerate(self.config.items()):
            botton = Botton(label=key,
                            label_value=value,
                            output_path=output_path,
                            log=self.log)
            setattr(self, "button_{}".format(i), botton)

    def video_anotation(self):
        if self.log.select_number < len(self.image_list):
            work_ratio = '{}/{}'.format(self.log.select_number + 1, len(self.image_list))
            self.root.title(work_ratio + " "*5 + "|" + " "*5 + self.log.return_image_path().split("/")[-1])
            frame = Image.open(self.log.return_image_path()).resize((350, 350))
            frame = ImageTk.PhotoImage(frame)

            self.panel = tk.Label(image=frame)
            self.panel.image = frame
            self.panel.place(x=250, y=25)
            self.panel.after(50, self.video_anotation)

        else:
            self.anotation_break()

    def anotation_break(self):
        thread = threading.Thread(target=self.destroy, args=())
        thread.start()

    def destroy(self):
        self.panel.quit()
        self.root.quit()
        exit()

    def __call__(self):
        self.root = tk.Tk()
        self.root.geometry("{}x{}".format(900, 600))
        thread = threading.Thread(target=self.video_anotation, args=())
        thread.start()

        row_number = 5
        for row in range(len(self.config.items())):
            cood = (160*(row % row_number - 1) + 200, 100*(row//row_number+1) + 300, 150, 80)
            getattr(self, "button_{}".format(row))(root=self.root, botton_cood=cood)

        self.root.mainloop()

if __name__ == '__main__':
    args = sys.argv

    if len(args) == 4:
        Anotation(output_path=args[1],
                  input_image_path=args[2],
                  config_path=args[3],
                  anotation_random=True)()
    else:
        print("length of args is {}".format(len(args)))
        exit()
