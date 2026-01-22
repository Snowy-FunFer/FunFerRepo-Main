""" Python 3.13.5
这是一个可把视频转成文字视频的程序。(当然图片也行)
将要处理的视频丢进/in/目录并运行程序，
你会看见/out/目录中出现了处理后的视频。
处理结果的宽高和是否彩色以及文字尺寸等属性可在最后一行代码中设置。

"""

import os
import colorama
from tqdm import tqdm
import cv2
import numpy as np
chars = "丶一二三十口日目田由甲申电男男"  # " .'`^\",:;~+_*!|/\\?=()[]%&#$@@"

charPics = [cv2.imread("./res/%d.png" % (i if i < 14 else 13)) for i in range(15)]

# 通过rgb获取灰度值
def get_brightness_by_rgb(r, g, b):
    # 非线性算法
    return 0.547 * ((r / 255) ** 2.2 + (1.5 * g / 255) ** 2.2 + (0.6 * b / 255) ** 2.2) ** 0.455
    # 线性算法
    # return (0.299 * root + 0.587 * g + 0.114 * b) / 255

colorama.init()

# 获取带颜色样式的字符串
def colorful_pixel(string, r=255, g=255, b=255):
    return '\033[38;2;%d;%d;%dm%s\033[0m' % (r, g, b, str(string))

# 通过rgb获取对应的灰度字符
def pixel_to_char(r, g, b, is_colorful):
    brightness = get_brightness_by_rgb(r, g, b)
    index = int(brightness * (len(chars) - 1))
    return colorful_pixel(chars[index], r, g, b) if is_colorful else chars[index]

# 通过rgb获取对应的灰度字符图片
def pixel_to_charPic(r, g, b):
    brightness = get_brightness_by_rgb(r, g, b)
    index = int(brightness * (len(chars) - 1))
    return charPics[index]

# 获取某一区块的rgb平均值
def get_average_rgb(pic_, res_w, res_h, x, y):
    r = np.mean(pic_[(y * res_h): (y * res_h + res_h), (x * res_w): (x * res_w + res_w), 0])
    g = np.mean(pic_[(y * res_h): (y * res_h + res_h), (x * res_w): (x * res_w + res_w), 1])
    b = np.mean(pic_[(y * res_h): (y * res_h + res_h), (x * res_w): (x * res_w + res_w), 2])
    return r, g, b

# 把图片转换成字符串
def transform_pic_to_str(pic_, is_colorful=False, res_w=8, res_h=None):
    pic_ = pic_[:, :, ::-1]
    if not res_h:
        res_h = 2 * res_w
    h, w, _ = pic_.shape
    h_ = h // res_h
    w_ = w // res_w

    pre_ret = [[None for j in range(w_)] for i in range(h_)]
    for x in range(w_):
        for y in range(h_):
            pre_ret[y][x] = pixel_to_char(*get_average_rgb(pic_, res_w, res_h, x, y), is_colorful)

    return "\n".join(["".join(i) for i in pre_ret])

# 把图片转换成字符串图片
def transform_pic_to_charPic(pic_, is_colorful=False, res_w=8, res_h=None):
    if not res_h:
        res_h = 2 * res_w
    h, w, _ = pic_.shape
    h_ = h // res_h
    w_ = w // res_w

    pre_ret = np.zeros((h_ * 29, w_ * 29, 3)).astype(np.uint8)
    for x in range(w_):
        for y in range(h_):
            r, g, b = get_average_rgb(pic_, res_w, res_h, x, y)
            p = np.zeros((28, 28, 3))
            p[:, :, 0] = r
            p[:, :, 1] = g
            p[:, :, 2] = b
            pre_ret[(y * 29): (y * 29 + 28), (x * 29): (x * 29 + 28), :] = (p / 255 * pixel_to_charPic(r, g, b)).astype(np.uint8) if is_colorful else pixel_to_charPic(r, g, b)

    return pre_ret

# 清屏
cls = lambda: os.system("cls")

# 展示图片
def show(p, t=1000):
    cv2.imshow("picture", p)
    cv2.waitKey(t)

# 修改图片尺寸
def resize(p, tar1, tar2=None):
    if type(tar1) == int:
        if not tar2:
            x, y = p.shape[1], p.shape[0]
            tar2 = round(tar1 * y / x)
        return cv2.resize(p, (tar1, tar2))
    else:
        if not tar2:
            tar2 = tar1
        return cv2.resize(p, (0, 0), fx=tar1, fy=tar2)

# 将视频字符化
def transform_video_to_charVideo(path, out_path, tar1, tar2=None, is_colorful=False, res_w=8, res_h=None):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    samp = None
    out = None
    with tqdm(total=cap.get(cv2.CAP_PROP_FRAME_COUNT), desc='Process', leave=True, ncols=100, unit='B', unit_scale=True) as pbar:
        while cap.isOpened():
            pbar.update(1)
            ret, frame = cap.read()
            if ret:
                out_frame = resize(transform_pic_to_charPic(frame, is_colorful, res_w, res_h), tar1, tar2)
                if not samp:
                    samp = out_frame.shape
                    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'XVID'), fps, samp[:2][::-1])
                out.write(out_frame)
            else:
                cap.release()
                out.release()


if __name__ == "__main__":
    for f in list(os.walk("./in"))[0][2]:
        # 参数说明：输入文件路径，输出文件路径，输出的宽度倍数(像素)，输出的高度倍数(像素)，是否彩色，单个文字宽度，单个文字高度
        transform_video_to_charVideo("./in/" + f, "./out/ret_" + f, 0.8, 0.8, False, 24, 24)
