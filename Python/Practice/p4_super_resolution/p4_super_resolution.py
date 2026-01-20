""" Python 3.11.0
这是一个给图片做超分辨率的程序，
使用的是EDSR模型。
该程序将会把in文件夹的内容处理成高分辨率图片，
输出在out文件夹中。
分辨率倍数可在最后一行super_resolution函数的第二个参数中修改。

"""

import cv2  # pip install opencv-contrib-python==4.8.1.78
import numpy as np  # pip install numpy==1.24.3
import os
import math
import requests
from tqdm import tqdm
from pathlib import Path

def download_models():
    models = {
        'EDSR_x2.pb': 'https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x2.pb',
        'EDSR_x3.pb': 'https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x3.pb',
        'EDSR_x4.pb': 'https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb'
    }

    # 创建模型文件夹
    model_dir = Path('./opencv_models')
    model_dir.mkdir(exist_ok=True)

    for model_name, url in models.items():
        model_path = model_dir / model_name

        if not model_path.exists():
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open(model_path, 'wb') as f, tqdm(
                    desc=model_name,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    pbar.update(size)
            print(f"模型 {model_name} 下载完成！")
        else:
            print(f"模型 {model_name} 已存在，跳过下载")

def super_resolution(input_image, scale):
    height, width = input_image.shape[:2]
    num = round(np.log(scale) / np.log(3)) if scale in [3, 9, 27, 81, 243, 729] else math.ceil(np.log(scale) / np.log(3))
    ret = input_image
    for i in range(num):
        ret = super_resolution_unit(ret)
    ret = cv2.resize(ret, (round(width * scale), round(height * scale)))
    return ret

# 使用EDSR模型
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel('./opencv_models/EDSR_x3.pb')
sr.setModel('edsr', 3)

def super_resolution_unit(input_image):
    model_func = sr.upsample
    scale = 3  # 每次处理的放大倍数
    unit = 300  # 每次处理的图象块大小

    # 图象分块处理，以防止内存溢出
    height, width = input_image.shape[:2]
    ret_img = np.zeros((height * scale, width * scale, 3), dtype=np.uint8)

    horizontal_chunk_num = width // unit
    horizontal_chunk_remainder = width % unit
    vertical_chunk_num = height // unit
    vertical_chunk_remainder = height % unit

    for i in range(horizontal_chunk_num):
        for j in range(vertical_chunk_num):
            ret_img[
                j * unit * scale : (j + 1) * unit * scale,
                i * unit * scale : (i + 1) * unit * scale,
                :
            ] = model_func(input_image[
                j * unit : (j + 1) * unit,
                i * unit : (i + 1) * unit
            ])

    HCNU = horizontal_chunk_num * unit
    HCNU_HCR = HCNU + horizontal_chunk_remainder
    HCNUS = HCNU * scale
    HCNUS_HCRS = HCNU_HCR * scale

    VCNU = vertical_chunk_num * unit
    VCNU_VCR = VCNU + vertical_chunk_remainder
    VCNUS = VCNU * scale
    VCNUS_VCRS = VCNU_VCR * scale

    if horizontal_chunk_remainder > 0:
        for j in range(vertical_chunk_num):
            ret_img[
                j * unit * scale : (j + 1) * unit * scale,
                HCNUS : HCNUS_HCRS,
                :
            ] = model_func(input_image[
                j * unit : (j + 1) * unit,
                HCNU : HCNU_HCR
            ])

    if vertical_chunk_remainder > 0:
        for i in range(horizontal_chunk_num):
            ret_img[
                VCNUS : VCNUS_VCRS,
                i * unit * scale : (i + 1) * unit * scale,
                :
            ] = sr.upsample(input_image[
                VCNU : VCNU_VCR,
                i * unit : (i + 1) * unit
            ])

    if horizontal_chunk_remainder > 0 and vertical_chunk_remainder > 0:
        ret_img[
            VCNUS : VCNUS_VCRS,
            HCNUS : HCNUS_HCRS,
            :
        ] = sr.upsample(input_image[
            VCNU : VCNU_VCR,
            HCNU : HCNU_HCR
        ])

    return ret_img

if __name__ == "__main__":
    # download_models()  # 下载模型

    for f in list(os.walk("./in"))[0][2]:
        src_img = cv2.imread("./in/" + f)
        cv2.imwrite("./out/ret_" + f, super_resolution(src_img, 3))
