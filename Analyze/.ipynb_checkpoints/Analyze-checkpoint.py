import numpy as np
import sys
sys.dont_write_bytecode = True

import requests
try:
    sys.path.append("./utils/")
    from facepp import API, File
except:
    sys.path.append("../utils/")
    from facepp import API, File

import ImagePro
import glob
import yaml
import os

from progressbar import ProgressBar #progressbar2をインストール
import base64
import time
import json


class Analyze(object):
    def __init__(self, path_to_analyze_config, output_dir_name="analyzed_result", wait_time=None):
        self.path_to_analyze_config = path_to_analyze_config
        with open(self.path_to_analyze_config, "r") as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)
        self.output_dir_name = output_dir_name
        
        self.wait_time = wait_time #自然数で指定する必要がある．

        if self.config["output_json_name"] is None:
            self.output_json_name = "output"
        else:
            self.output_json_name = self.config["output_json_name"]

        self.api = API(API_KEY=self.config["API_KEY"],
                       API_SECRET=self.config["API_SECRET"])

        del self.config["API_KEY"], self.config["API_SECRET"]

    def get_dataset(self, serch_config_name="config_camera.yaml", path_to_image=None):
        if path_to_image is None:
            path_to_image = self.config["target_dir_name"]

        if serch_config_name in os.listdir(path_to_image):
            self.abs_path = os.path.abspath(path_to_image)
            path_to_camera_config = os.path.join(*[self.abs_path, serch_config_name])
            with open(path_to_camera_config, "r") as f:
                self.config_camera = yaml.load(f, Loader=yaml.SafeLoader)
            self.path_to_image = os.path.join(*[self.abs_path, self.config_camera["image_dir_name"]])
        else:
            print("'{}' do not have Image dirctory, ex) {}".format(path_to_image, os.path.join(*[path_to_image, "Images/"])))
            exit()

        path_list = glob.glob(os.path.join(*[self.path_to_image, "*{}".format(self.config_camera['image_style'])]))
        path_list = sorted(path_list, key=lambda x: int(x.split("/")[-1].split(".")[0]))
        output_dir_path = os.path.join(*[self.abs_path, self.output_dir_name])
        os.makedirs(output_dir_path, exist_ok=True)

        with open(os.path.join(*[output_dir_path, self.path_to_analyze_config.split("/")[-1]]), "w") as f:
            yaml.dump(self.config, f)
        return path_list

    def choise_function(self, encode_image, api_kind):
        if api_kind == "Detect":
            return self.api.detect(image_base64=encode_image, return_attributes=",".join(self.config["Attribute_Detect"]))
        elif api_kind == "Dence":
            return self.api.face.thousandlandmark(image_base64=encode_image, return_landmark="all")

    def detect(self, path_list, api_kind):
        print("-"*10 + api_kind + "-"*10)
        output_list = []
        p_bar = ProgressBar(maxval=len(path_list))
        for i, each_file in enumerate(path_list):
            p_bar.update(i)
            encode_img = self.img_to_bese64(each_file)
            output = self.choise_function(encode_image=encode_img, api_kind=api_kind)
            output["image_path"] = each_file
            output_list.append(output)
            if (api_kind == "Dence") and (self.wait_time is not None):
                import time
                time.sleep(int(self.wait_time)) #実行制限の関係から，ここの値を調整する必要がある．
        api_output_path = os.path.join(*[self.abs_path, self.output_dir_name, api_kind])
        self.save_output(api_output_path, output_list)

    def compere(self, path_list, target_file=None):
        if target_file is None:
            print("target_file is None, pleasse give any path to image file")
            exit()

        print("-"*10 + "Get Compere" + "-"*10)
        p_bar = ProgressBar(maxval=len(path_list))
        output_list = []
        if target_file is None:
            target_file = self.config["target_file"]
        target_img = self.img_to_bese64(target_file)
        for i, each_file in enumerate(path_list):
            p_bar.update(i)
            if each_file != target_file:
                each_img = self.img_to_bese64(each_file)
                output = self.api.compare(image_base64_1=target_img, image_base64_2=each_img)
                output["image_path"] = each_img
                output_list.append(output)
        api_output_path = os.path.join(*[self.abs_path, self.output_dir_name, "Compere"])
        self.save_output(api_output_path, output_list, name=target_file.split("/")[-1].split(".")[0])

    def save_output(self, path, output_list, name=None):
        os.makedirs(path, exist_ok=True)
        if name is None:
            with open(os.path.join(*[path, self.output_json_name + ".json"]), "w") as f:
                json.dump(output_list, f)
        else:
            with open(os.path.join(*[path, name + ".json"]), "w") as f:
                json.dump(output_list, f)

    def img_to_bese64(self, target_file):
        with open(target_file, 'rb') as f:
                data = f.read()
        return base64.b64encode(data)

    def __call__(self, target_file=None, path_to_image=None):
        path_list = self.get_dataset(path_to_image=path_to_image)

        if self.config["USE_API_Detect"]:
            self.detect(path_list, api_kind="Detect")

        if self.config["USE_API_Compare"]:
            self.compere(path_list, target_file)

        if self.config["USE_API_Dense_Facial_Landmarks"]:
            self.detect(path_list, "Dence")

        sys.exit()
        
class Detect_api_json_to_csv(object):
    def __init__(self, path_to_json, output_path=None, output_dir_name="result_by_image"):
        with open(path_to_json, "r") as f:
            self.data = json.load(f)
            
        if output_path is None:
            self.output_file_path = os.path.join(*[*path_to_json.split("/")[:-1], output_dir_name])
        else:
            self.output_file_path = os.path.join(*[output_path, output_dir_name])
        
    def detect_face_attribute(self, data, output_path_each_face, index_name="output"):
        gender_category = data["attributes"].keys()
        for attribute_key in gender_category:
            df = pd.DataFrame([], index=[index_name])
            for key_name, value_score in data["attributes"][attribute_key].items():

                if hasattr(value_score, "keys"):
                    for key_name_each, value_score_each in data["attributes"][attribute_key][key_name].items():
                        df[key_name_each] = [value_score_each]
                else:
                    df[key_name] = [value_score]

            output_file_name = os.path.join(*[output_path_each_face, attribute_key + ".csv"])
            df.to_csv(output_file_name)
            
    def detect_face_rectange(self, data, output_path_each_face, index_name="cood"):
        df = pd.DataFrame([], index=[index_name])
        for b_box_info_name, value in data["face_rectangle"].items():
            df[b_box_info_name] = value
        output_file_name = os.path.join(*[output_path_each_face, "face_rectangle.csv"])
        df.to_csv(output_file_name)
    
    def __call__(self, output_dir=None):
        if output_dir is not None:
            self.output_file_path = output_dir
            
        for each_data in self.data:
            image_number = each_data["image_path"].split("/")[-1].split(".")[0]
            each_output_path = os.path.join(*[self.output_file_path, image_number])
            for face_number, each_face_data in enumerate(each_data["faces"]):
                
                # 顔ごとにディレクトリを作る, 1つしか写っていない場合は"0"のディレクトリが作られる
                output_path_each_face = os.path.join(*[each_output_path, str(face_number)])
                os.makedirs(output_path_each_face, exist_ok=True)
                
                self.detect_face_attribute(data=each_face_data,
                                           output_path_each_face=output_path_each_face,
                                           index_name="output")
                
                self.detect_face_rectange(data=each_face_data,
                                          output_path_each_face=output_path_each_face)
                

class Dence_api_json_to_csv(object):
    def __init__(self, path_to_json, output_path=None, output_dir_name="result_by_image"):
        with open(path_to_json, "r") as f:
            self.data = json.load(f)
            
        if output_path is None:
            self.output_file_path = os.path.join(*[*path_to_json.split("/")[:-1], output_dir_name])
        else:
            self.output_file_path = os.path.join(*[output_path, output_dir_name])
            
    def make_dence_face_json_to_csv(self, data, output_file_path):
        '''
        Function:
            Faceに関するランドマークをcsvファイルに保存するための関数
        Args:
            data (dics) : jsonファイルから読み込んだ結果．画像一枚に対する出力結果取り出したもの．
                    print(each_data.keys()) # dict_keys(['time_used', 'request_id', 'face', 'image_path'])
            output_file_path (str) : 出力先のパス
        ''' 
        data = copy.deepcopy(data)
        df_eye = pd.DataFrame([], index=["radius", "center_x", "center_y"])
        
        for landmark_key in data["face"]['landmark']:
            if landmark_key in ["left_eye", "right_eye"]:
                radius = data["face"]['landmark'][landmark_key][landmark_key + "_pupil_radius"]
                center = data["face"]['landmark'][landmark_key][landmark_key + "_pupil_center"]
                df_eye[landmark_key] = [radius, center["x"], center["y"]]

                del data["face"]['landmark'][landmark_key][landmark_key + "_pupil_center"]
                del data["face"]['landmark'][landmark_key][landmark_key + "_pupil_radius"]

            self.make_dence_dir(data["face"]['landmark'], output_dir=output_file_path, landmark_key_name=landmark_key, mode="landmark")

        df_eye.to_csv(os.path.join(*[output_file_path, "eye_center_radius.csv"]))
        self.make_dence_dir(data["face"]['face_rectangle'], output_dir=output_file_path, mode="rectangle")
        
    def make_dence_dir(self, each_data, output_dir, landmark_key_name=None, mode="landmark"):
        """
        Function:
            denceの処理を行なった場合に，APIからの各アウトプットをcsvファイルに保存するための関数
        Args:
            each_data (dics) : jsonファイルから読み込んだ結果．画像一枚に対する出力結果取り出したもの
            output_dir (str) : 出力先のパス
            landmark_key_name (str) : landmarkに関するkey
            mode (str) : APIからの各アウトプットの形式が違うので，修正するためにmodeとして入れる．["landmark", "rectangle"]から選択
        """
        os.makedirs(output_dir, exist_ok=True)
        each_data = copy.deepcopy(each_data)
        
        if mode == "landmark":
            df = pd.DataFrame([], index=["x_cood", "y_cood"])
            
            if landmark_key_name == "nose":
                each_data[landmark_key_name]['left_nostril_0'] = each_data[landmark_key_name].pop('left_nostril')
                each_data[landmark_key_name]['right_nostril_0'] = each_data[landmark_key_name].pop('right_nostril')
    
            target_dataset = each_data[landmark_key_name].items()
            target_dataset = sorted(target_dataset, key= lambda x: int(x[0].split("_")[-1]))
            for land_name, cood in target_dataset:
                df[land_name] = [cood["x"], cood["y"]]
            df.to_csv(os.path.join(*[output_dir, landmark_key_name + ".csv"]))

        elif mode == "rectangle":
            df = pd.DataFrame([], index=['width', 'top', 'height', 'left'])
            df["b_box"] = [each_data['width'], each_data['top'], each_data['height'], each_data['left']] 
            df.to_csv(os.path.join(*[output_dir, "rectangle.csv"]))
            
    def __call__(self, output_dir=None):
        
        if output_dir is not None:
            self.output_file_path = output_dir
            
        for each_data in self.data:
            image_number = each_data["image_path"].split("/")[-1].split(".")[0]
            each_output_path = os.path.join(*[self.output_file_path, image_number])
            os.makedirs(each_output_path, exist_ok=True)
            self.make_dence_face_json_to_csv(data=each_data,
                                             output_file_path=each_output_path)
            

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 5:
        quit()

    for _ in range(5 - len(args)):
        args.append(None)

    analyze = Analyze(path_to_analyze_config=args[1], wait_time=args[4])
    analyze(target_file=args[2], path_to_image=args[3])
