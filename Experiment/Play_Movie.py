import sys
sys.dont_write_bytecode = True

import cv2
import matplotlib.pylab as plt
import numpy as np
import yaml
import os
import datetime
from gui_to_movie import GUI
import time


class make_dataset(object):
    """
    動画を撮影して，画像を切りはりしてくるためのクラス
    """
    def __init__(self, path_to_config, base_output_dir="./results/", USE_GUI=True):
        """
        path_to_config (str) : configファイルまでのパス
        base_output_di (str) : 実行した結果を出力するパス，ここで指定したディレクトリ下に保存される
        """
        self.path_to_config = path_to_config
        self.base_output_dir = base_output_dir
        self.USE_GUI = USE_GUI

        with open(self.path_to_config, "r") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)

    def get_movie_config(self):
        '''
        Function:
            動画の細々とした設定をconfigファイルから取り出す関数
        '''

        if self.config["output_video_style"] is None:
            self.config["output_video_style"] = ".mp4"

        if self.config["output_video_style"] == ".mp4":
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        elif self.config["output_video_style"] == ".avi":
            fourcc = cv2.VideoWriter_fourcc(*'XVID')

        else:
            print("Please seach and select the format following page")
            print("http://www.fourcc.org/codecs.php")
            exit()

        width = int(self.config["get_movie_shape"][1])
        height = int(self.config["get_movie_shape"][0])

        window_x_cood = self.config["window_coodinate"][0]
        window_y_cood = self.config["window_coodinate"][1]

        if self.config["output_movie_name"] is None:
            self.config["output_movie_name"] = self.now

        cap = cv2.VideoCapture(0)

        return fourcc, cap, width, height, window_x_cood, window_y_cood

    def make_movie_gui(self):
        fourcc, cap, width, height, window_x_cood, window_y_cood = self.get_movie_config()
        self.output_path_movie = os.path.join(*[self.output_path, self.config["output_movie_name"] + self.config["output_video_style"]])
        window_w, window_h = self.config["window_size"]
        out_writer = cv2.VideoWriter(self.output_path_movie, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))
        self.gui = GUI(window_h=window_h,
                        window_w=window_w,
                        window_x_cood=window_x_cood,
                        window_y_cood= window_y_cood,
                        movie_h=height,
                        movie_w=width,
                        out_writer=out_writer)
        self.gui()
        self._cap_del(cap, out_writer)

    def _cap_del(self, cap, out):
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    def make_movie(self):
        """
        Function:
            動画をパソコン付属のカメラから撮影するための関数
        """
        fourcc, cap, width, height, window_x_cood, window_y_cood = self.get_movie_config()

        self.output_path_movie = os.path.join(*[self.output_path, self.config["output_movie_name"] + self.config["output_video_style"]])
        out = cv2.VideoWriter(self.output_path_movie, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))
        movie_title = 'If you want to stop, please press the "q" command in key borad.'

        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame[:, ::-1], (width, height))
                out.write(frame)
                cv2.imshow(movie_title, frame)
                cv2.moveWindow(movie_title, window_x_cood, window_y_cood)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break

        self._cap_del(cap, out)

    def movie_to_images(self, image_output_path=None):
        """
        Function:
            動画から画像を切ってくるための関数
        """

        cap = cv2.VideoCapture(self.output_path_movie)

        if not self.USE_GUI:
            fps = cap.get(cv2.CAP_PROP_FPS)
        else:
            fps = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / (self).gui.elapsed_time + 1e-15))

        if self.config["choise_unit"] in ["frame", "s", "m"]:
            minite = 60*fps if self.config["choise_unit"] == "m" else 1
            second = fps if self.config["choise_unit"] == "s" else 1
            pass_frame_number = self.config["pass_rate"] * minite * second
        else:
            print("{} is not difined. please choise in ['frame', 's', 'm']".format(self.config["pass_rate"]))

        if image_output_path is None:
            self.image_output_path = os.path.join(*[self.output_path, self.config["image_dir_name"]])
        else:
            self.image_output_path = image_output_path
        os.makedirs(self.image_output_path, exist_ok=True)
        counts = 0
        zfill_num = 7

        width = int(self.config["get_image_shape"][1])
        height = int(self.config["get_image_shape"][0])

        print("Start cutting movie to images")
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret:
                counts += 1
                if int(counts % pass_frame_number) == 0:
                    image_name = int(counts // pass_frame_number).__str__().zfill(zfill_num) + self.config["image_style"]
                    cv2.imwrite(os.path.join(*[self.image_output_path, image_name]), cv2.resize(frame, (width, height)))
            else:
                break

        print("End")

    def set_config(self):
        """
        Function:
            comfingファイルに書かれた設定によって適当にディレクトリを作る関数
        Args:
            path_to_config (dict) : path to config file
                                    If you want to get keys in this dict, you see yaml file directly, please.
        Returns:
            output_path (str) : path to output results
        """

        self.now = datetime.datetime.now().strftime("%m%d_%H%M")
        if self.config["output_movie_dir_name"] is not None:
            now = self.now + "_" + self.config["output_movie_dir_name"]
        self.config["do_time_info"] = now
        self.output_path = os.path.join(*[self.base_output_dir, now])
        os.makedirs(self.output_path, exist_ok=True)

        with open(os.path.join(*[self.output_path, self.path_to_config.split("/")[-1]]), "w") as f:
            yaml.dump(self.config, f)

    def __call__(self):
        self.set_config()

        if self.USE_GUI:
            self.make_movie_gui()
        else:
            self.make_movie()

        self.movie_to_images()

if __name__ == '__main__':
    args = sys.argv

    if len(args) == 3:
        dataset = make_dataset(path_to_config= args[1],
                               base_output_dir= args[2],
                               USE_GUI=True)()
    else:
        print("length of args is {}, not 3".format(len(args)))
        exit()
