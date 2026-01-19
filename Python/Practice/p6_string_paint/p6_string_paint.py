""" Python 3.13.5
线织画。

"""

import os
import cv2
import time
import numpy as np

# # #   切 忌 直 接 关 闭 程 序 ！！！
# 在输出目录中创建stop文件以停止计算， 切 忌 直 接 关 闭 程 序 ！！！
# 在输出目录中创建stop文件以停止计算， 切 忌 直 接 关 闭 程 序 ！！！
# 在输出目录中创建stop文件以停止计算， 切 忌 直 接 关 闭 程 序 ！！！

# 启动类
class StringPaint(object):
    # 输入图片边长像素为w，共n个钉子，输出目录为res，输入图片名称(不含后缀)为target，输出图片名称(不含后缀)为result，图片必须是正方形的

    # 在输出目录中创建stop文件以停止计算， 切 忌 直 接 关 闭 程 序 ！！！

    def __init__(self, w=200, n=100, res="./res/", target="sample1", result="sample2"):
        self.w = w  # 边长w的正方形
        self.n = n  # 共n个钉子
        self.s = n * (n - 1) / 2  # 共s条绳子
        self.r = w / 2 * 0.999  # 钉子圈半径为r
        # 初始化 对象
        self.res = res  # 输出目录路径
        X, Y = np.array(np.meshgrid(np.arange(0, w, 1), np.arange(0, w, 1))) - self.w / 2 + 0.5
        self.circle_blank = ((X ** 2 + Y ** 2 - self.r ** 2) <= 0).astype(dtype=np.uint8)  # 圆盘内为1，外为0的矩阵
        self.P = self.circle().T  # 钉子坐标 数组


        # 有记录
        if os.path.exists(res + "paint.txt"):
            with open(res + "init_data.txt", "root") as f:
                init_data = f.read().split("\n")
            init_global_i = eval(init_data[0])  # 全过程 钉子编号记录
            init_record = eval(init_data[1])  # 记录已连接的绳子
            paint = self.start(res + target + ".png", init_global_i[-1], self.read_out_txt("paint"), init_record, init_global_i)
        else:  # 无记录
            paint = self.start(res + target + ".png")
        cv2.imwrite(res + result + ".png", (255 * (1 - paint)).astype(dtype=np.uint8))  # 输出图像
        self.show_img(paint, True, True)


    # 正式启动！！目标图片路径为path，从编号origin的钉子开始，init_开头参数为初始记录
    def start(self, path, origin=0, init_paint=None, init_record=None, init_global_i=None):
        img = (1 - cv2.imread(path, cv2.IMREAD_GRAYSCALE) / 255) * self.circle_blank
        if init_paint is None:
            paint = np.zeros(shape=(self.w, self.w))
        else:
            paint = init_paint
        if init_record is None:  # 记录已连接的绳子
            record = []
        else:
            record = init_record
        if init_global_i is None:  # 全过程 钉子编号记录
            global_i = []
        else:
            global_i = init_global_i
        global_D = self.w ** 2  # 全过程 方差记录
        timer = time.time()
        while 1:  # 开始计算(画画) (贪婪算法)
            D = {}  # 记录方差
            for i in range(self.n):
                if i != origin and {i, origin} not in record:
                    ret = self.line(self.P[i], self.P[origin]) + paint
                    ret = (ret <= 1) * (ret - 1) + 1
                    D[i] = np.sum((img - ret) ** 2)
            v = list(D.values())
            final_D = min(v)
            final_i = list(D.keys())[v.index(final_D)]
            if final_D > global_D:
                break
            ret = self.line(self.P[final_i], self.P[origin]) + paint
            paint = (ret <= 1) * (ret - 1) + 1
            record.append({final_i, origin})
            origin = final_i
            global_D = final_D
            global_i.append(final_i)

            if os.path.exists(self.res + "stop"):
                self.write_in_txt("paint", paint)
                with open(self.res + "init_data.txt", "w") as f:
                    f.write(str(global_i) + "\n" + str(record))
                print("当前总连接钉子数: " + str(len(global_i)))
                self.show_img(paint, True, True)
                exit()

            # _timer = time.time()
            # print(round(_timer - timer, 2))
            # timer = _timer  # 计时方法

        self.write_in_txt("paint", paint)
        with open(self.res + "init_data.txt", "w") as f:
            f.write(str(global_i) + "\n" + str(record))

        self.write_in_txt("final_paint", paint)
        with open(self.res + "final_init_data.txt", "w") as f:
            f.write(str(global_i) + "\n" + str(record))

        print("总连接钉子数: " + str(len(global_i)))
        return paint


    # 计算钉子坐标数组
    def circle(self):
        theta = np.linspace(0, 2 * np.pi, self.n + 1)[:-1]  # 均分周角n等份
        return self.w / 2 + self.r * np.array([np.cos(theta), np.sin(theta)])  # 钉子坐标 数组

    # 正方形的边长为w，p0与p1为两个点，线宽为2d，纯黑色宽为2u，线的不透明度为alpha，开启0-1数据输出为is_float
    def line(self, p0, p1, w=500, d=1, u=0.3, alpha=0.05, is_float=True):
        w = self.w  # 强制化定义
        # 计算
        X = np.arange(0, w, 1)
        Y = np.arange(0, w, 1)
        X, Y = np.meshgrid(X, Y)
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dis = np.sqrt(dx ** 2 + dy ** 2)
        A = dy / dis
        B = -dx / dis
        C = (p1[0] * p0[1] - p0[0] * p1[1]) / dis
        # Z为两点所确定直线的图像矩阵
        Z = (d - np.abs(A * X + B * Y + C)) / (d - u)
        Z = (Z > 0) * Z
        Z = alpha * (Z + (Z > 1) * (1 - Z)) * self.circle_blank
        if is_float:  # 0-1数据
            return Z
        else:  # 0-255数据
            return np.round(255 * Z).astype(dtype=np.uint8)

    # 开启反色为is_antic，开启0-1颜色值为is_float
    def show_img(self, img, is_antic=False, is_float=True, size=(600, 600)):
        cv2.namedWindow("image", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        if is_antic and is_float:
            img = np.round(255 * (1 - img))
        elif not is_antic and is_float:
            img = np.round(255 * img)
        elif is_antic and not is_float:
            img = 255 - img
        cv2.imshow("image", img.astype(dtype=np.uint8))
        cv2.resizeWindow("image", *size)  # 图像大小
        cv2.waitKey()
        cv2.destroyAllWindows()

    # 写入数据进txt文件，文件放在桌面，文件名称为name(不加后缀)，写入数据为data(二维矩阵)
    def write_in_txt(self, name, data: np.ndarray):
        with open(self.res + name + ".txt", "w") as f:
            f.write("\n".join(["\t".join([str(i) for i in d]) for d in data]))

    # 读出数据于txt文件，文件放在桌面，文件名称为name(不加后缀)，返回值为浮点型数组
    def read_out_txt(self, name) -> np.ndarray:
        with open(self.res + name + ".txt", "root") as f:
            return np.array([[float(i) for i in data.split("\t")] for data in f.read().split("\n")])

# 启动！！
sp = StringPaint()


"""  # 线织画实际所需绳长估计

# 估计实际所需绳长(cm)，实际圆盘半径为r(cm)，钉子数为n，最终数据列表为data_list
def estimate_length(root, n, data_list):
    a = [0] + data_list[:-1]
    dirs = 0
    for _file, j in zip(a, data_list):
        dirs += 2 * root * np.sin(np.abs(_file - j) / n * np.pi)
    return dirs

ret = estimate_length(19, 236,
                [126, 234, 120, 223, 115, 218, 116, 222, 114, 224, 130, 2, 125, 229, 123, 231, 126, 235, 119, 230, 122, 232, 127, 227, 123, 5, 125, 234, 128, 226, 114, 216, 110, 213, 108, 214, 107, 209, 108, 219, 117, 232, 139, 235, 127, 5, 130, 8, 133, 6, 124, 235, 145, 0, 147, 1, 122, 0, 141, 233, 127, 9, 129, 235, 137, 230, 125, 1, 120, 233, 131, 222, 132, 12, 135, 15, 132, 6, 129, 226, 133, 225, 130, 13, 136, 229, 115, 220, 112, 213, 111, 7, 123, 0, 149, 1, 117, 218, 109, 210, 104, 205, 100, 206, 103, 213, 109, 221, 111, 215, 126, 10, 163, 9, 132, 235, 140, 24, 142, 232, 134, 16, 131, 3, 151, 0, 119, 221, 130, 1, 148, 0, 125, 6, 155, 5, 113, 227, 124, 3, 121, 224, 134, 14, 129, 233, 138, 24, 141, 234, 144, 6, 122, 5, 109, 9, 160, 7, 158, 3, 128, 235, 135, 227, 132, 229, 139, 27, 143, 231, 124, 217, 116, 2, 110, 4, 114, 212, 112, 223, 110, 217, 128, 230, 138, 15, 128, 10, 135, 20, 140, 1, 111, 8, 109, 208, 105, 214, 125, 10, 162, 6, 146, 234, 117, 222, 127, 1, 119, 208, 99, 201, 88, 195, 92, 199, 81, 195, 93, 197, 95, 203, 101, 201, 85, 204, 98, 220, 134, 21, 138, 28, 142, 233, 118, 217, 121, 232, 143, 31, 145, 4, 109, 6, 154, 0, 131, 18, 139, 24, 136, 11, 168, 9, 165, 5, 112, 1, 138, 226, 115, 12, 148, 37, 147, 233, 133, 17, 118, 203, 103, 228, 120, 212, 124, 4, 116, 15, 150, 235, 141, 31, 138, 19, 178, 58, 175, 61, 179, 57, 172, 16, 153, 5, 115, 221, 128, 218, 92, 211, 90, 210, 123, 234, 142, 23, 122, 220, 116, 3, 156, 2, 159, 8, 112, 12, 127, 216, 123, 228, 113, 6, 111, 10, 108, 2, 122, 209, 97, 199, 80, 186, 71, 192, 75, 191, 86, 189, 73, 163, 4, 154, 15, 146, 38, 149, 7, 157, 1, 126, 22, 121, 211, 117, 235, 133, 224, 115, 16, 137, 27, 144, 231, 137, 228, 101, 204, 83, 187, 69, 183, 25, 135, 13, 173, 59, 159, 32, 128, 0, 106, 215, 91, 198, 114, 230, 101, 17, 151, 20, 136, 233, 149, 11, 166, 46, 153, 8, 169, 51, 176, 60, 157, 9, 110, 13, 148, 19, 119, 202, 34, 134, 27, 186, 78, 198, 76, 185, 28, 129, 220, 118, 204, 41, 151, 4, 166, 79, 1, 113, 219, 132, 33, 195, 82, 176, 20, 118, 210, 87, 178, 64, 161, 10, 164, 227, 140, 15, 175, 63, 180, 18, 130, 226, 161, 36, 200, 117, 228, 60, 230, 63, 161, 2, 111, 207, 45, 167, 9, 92, 194, 77, 167, 21, 141, 29, 145, 12, 96, 223, 157, 16, 171, 11, 151, 46, 140, 32, 129, 229, 64, 177, 19, 154, 235, 113, 10, 91, 202, 98, 194, 34, 147, 17, 112, 227, 105, 2, 75, 182, 67, 162, 226, 120, 203, 33, 131, 22, 133, 29, 189, 26, 153, 220, 97, 205, 39, 197, 114, 225, 136, 18, 156, 53, 212, 115, 215, 43, 165, 71, 235, 155, 25, 123, 207, 89, 5, 108, 222, 63, 184, 84, 4, 160, 76, 1, 152, 219, 99, 16, 179, 70, 0, 140, 228, 57, 181, 55, 224, 158, 54, 182, 12, 137, 44, 208, 122, 29, 207, 47, 223, 58, 147, 41, 213, 117, 205, 31, 126, 4, 78, 169, 6, 86, 197, 73, 181, 94, 193, 74, 164, 6, 107, 194, 25, 137, 47, 210, 93, 188, 31, 146, 43, 218, 114, 17, 139, 224, 52, 145, 213, 52, 229, 102, 19, 170, 80, 175, 89, 212, 126, 225, 51, 220, 130, 26, 187, 66, 170, 53, 143, 211, 54, 222, 65, 181, 15, 148, 216, 115, 195, 24, 191, 67, 232, 102, 207, 84, 7, 161, 75, 198, 37, 131, 235, 73, 184, 29, 160, 225, 103, 20, 143, 5, 87, 174, 10, 152, 27, 125, 23, 111, 196, 40, 153, 65, 227, 165, 68, 178, 56, 231, 145, 39, 216, 129, 35, 201, 114, 227, 98, 189, 25, 132, 17, 178, 88, 173, 11, 97, 222, 155, 14, 95, 180, 66, 233, 156, 9, 176, 50, 226, 141, 47, 150, 217, 112, 3, 110, 220, 62, 231, 108, 208, 116, 206, 30, 153, 20, 169, 88, 4, 74, 234, 135, 21, 190, 87, 196, 79, 230, 171, 52, 144, 42, 220, 108, 11, 86, 175, 79, 192, 85, 177, 96, 225, 46, 212, 116, 200, 38, 217, 149, 60, 222, 135, 42, 150, 21, 104, 14, 172, 91, 219, 135, 229, 168, 81, 7, 87, 185, 18, 109, 229, 50, 209, 124, 30, 147, 215, 121, 204, 32, 144, 54, 232, 59, 169, 80, 205, 119, 199, 37, 220, 113, 213, 44, 134, 8, 180, 25, 176, 46, 172, 70, 196, 23, 184, 67, 156, 222, 66, 162, 5, 73, 195, 114, 0, 153, 74, 228, 164, 3, 107, 222, 50, 149, 12, 111, 218, 61, 160, 81, 164, 41, 215, 55, 143, 36, 218, 120, 235, 163, 227, 45, 152, 3, 177, 89, 173, 52, 140, 49, 230, 57, 224, 53, 233, 143, 48, 206, 106, 5, 77, 174, 8, 158, 71, 179, 51, 146, 25, 190, 83, 9, 94, 172, 90, 12, 183, 64, 188, 27, 178, 2, 150, 28, 208, 114, 193, 82, 159, 6, 72, 167, 228, 139, 206, 123, 1, 69, 155, 19, 191, 92, 171, 95, 210, 27, 111, 18, 192, 115, 222, 110, 210, 49, 234, 77, 197, 22, 101, 185, 61, 223, 59, 213, 87, 202, 113, 196, 91, 3, 161, 11, 186, 32, 148, 39, 136, 202, 31, 182, 79, 205, 84, 12, 129, 225, 41, 230, 127, 26, 213, 43, 138, 35, 158, 77, 183, 98, 7, 71, 229, 169, 92, 180, 235, 146, 61, 229, 44, 198, 21, 102, 221, 67, 186, 91, 11, 192, 130, 214, 42, 202, 100, 23, 190, 72, 164, 69, 196, 132, 40, 231, 55, 155, 221, 112, 209, 141, 56, 214, 112, 0, 59, 174, 83, 158, 62, 176, 4, 111, 216, 40, 226, 49, 178, 0, 104, 215, 24, 208, 83, 13, 165, 47, 235, 159, 224, 100, 200, 118, 201, 45, 174, 156, 75, 227, 36, 232, 39, 133, 221, 92, 174, 231, 118, 193, 109, 20, 199, 134, 228, 63, 145, 175, 151, 218, 63, 189, 114, 219, 60, 234, 35, 146, 214, 17, 89, 14, 82, 163, 175, 189, 166, 70, 8, 110, 107, 211, 113, 204, 96, 113, 93, 10, 233, 23, 17, 13, 144, 212, 94, 123, 80, 165, 171, 159, 184, 179, 149, 22, 141]
                )
print(ret)

"""
