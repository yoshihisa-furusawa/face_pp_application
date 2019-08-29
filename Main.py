import sys
import cv2
import os

sys.dont_write_bytecode = True
for _path in ["./Analyze/", "./Experiment/", "./utils/"]:
    sys.path.append(_path)

from Play_Movie import make_dataset
from Analyze import Analyze
from Anotation import Anotation

if __name__ == '__main__':
    # Experiment
    dataset = make_dataset(path_to_config= "./Experiment/config_camera.yaml", base_output_dir="./results/")
    dataset()

    # Anotation中の時間が勿体無いので，AnotationとAnalyzeを並行処理する．
    # Anotation
    output_path = dataset.output_path + "/Anotation.csv"
    input_image_path = dataset.image_output_path
    config_path = "./Experiment/config_anotation.yaml"
    do_text_1 = "pythonw ./Experiment/anotation.py {} {} {}".format(output_path,
                                                                    input_image_path,
                                                                    config_path)

    # Analyze
    path_to_analyze_config = "./Analyze/config_analyze.yaml"
    target_file = None
    path_to_image = dataset.output_path
    do_text_2 = "pythonw ./Analyze/Analyze.py {} {} {}".format(path_to_analyze_config,
                                                                target_file,
                                                                path_to_image)
    # 並行処理
    os.system(do_text_1 + "&" + do_text_2 + "&")
