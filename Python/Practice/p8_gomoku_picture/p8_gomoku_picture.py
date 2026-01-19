""" Python 3.13.5
这是一个可把图片转成五子棋图案的程序。
将要处理的图片丢进/in/目录并运行程序，
你会看见/out/目录中出现了处理后的图片。
处理结果的宽高和是否允许灰棋以及灰度阈值等属性可在最后一行代码中设置。

"""

import os
import cv2
import numpy as np

# 可能会有RuntimeWarning，但不要紧 (无视它)

# 把图片转成五子棋图案
def summon_gomoku_picture(height, width, path_or_obj="./res/sample.jpg", is_double_color=True, white_edge=150, gray_edge=(90, 175), res_path="./res"):
	# 图片加载
	unit = cv2.imread(res_path + "/unit.jpg")  # 网格单元图片
	length = len(unit)  # 网格单元图片边长
	black = cv2.copyMakeBorder(cv2.resize(cv2.imread(res_path + "/black.jpg"), (length, length)), 0, (height - 1) * length, 0, (width - 1) * length, borderType=cv2.BORDER_WRAP)  # 黑棋
	white = cv2.copyMakeBorder(cv2.resize(cv2.imread(res_path + "/white.jpg"), (length, length)), 0, (height - 1) * length, 0, (width - 1) * length, borderType=cv2.BORDER_WRAP)  # 白棋
	gray = cv2.copyMakeBorder(cv2.resize(cv2.imread(res_path + "/gray.jpg"), (length, length)), 0, (height - 1) * length, 0, (width - 1) * length, borderType=cv2.BORDER_WRAP)  # 灰棋
	grid = cv2.copyMakeBorder(unit, 0, max(height, width) * length, 0, max(height, width) * length, borderType=cv2.BORDER_WRAP)  # 网格图片
	picture = cv2.copyMakeBorder(unit, 0, height * length, 0, width * length, borderType=cv2.BORDER_WRAP)  # 图像部分
	chessman = np.zeros(np.array(picture.shape) - np.array([length, length, 0]))  # 棋子部分
	bg_top = cv2.imread(res_path + "/bg_top.jpg")  # 背景图片 上
	bg_bottom = cv2.imread(res_path + "/bg_bottom.jpg")  # 背景图片 下
	bg_left = cv2.imread(res_path + "/bg_left.jpg")  # 背景图片 左
	bg_right = cv2.imread(res_path + "/bg_right.jpg")  # 背景图片 右

	# 灰度图转换
	if type(path_or_obj) == str:
		img = cv2.cvtColor(cv2.imread(path_or_obj), cv2.COLOR_BGR2GRAY)
	else:
		img = cv2.cvtColor(path_or_obj, cv2.COLOR_BGR2GRAY)

	# 处理
	h_num = img.shape[0] % height  # 高度需补充样本量
	w_num = img.shape[1] % width  # 宽度需补充样本量

	rule1 = [  # 增量填充规则
		(img.shape[0] // height * np.ones((1, height)) + np.append(np.ones((1, h_num)), np.zeros((1, height - h_num))))[0].astype(dtype=np.int16),
		(img.shape[1] // width * np.ones((1, width)) + np.append(np.ones((1, w_num)), np.zeros((1, width - w_num))))[0].astype(dtype=np.int16)
	]
	rule2 = [np.empty((1, height))[0], np.empty((1, width))[0]]  # 位置填充规则
	# 位置填充规则 处理
	for i in range(height):
		s = 0
		for j in range(i):
			s += rule1[0][j]
		rule2[0][i] = s
	for i in range(width):
		s = 0
		for j in range(i):
			s += rule1[1][j]
		rule2[1][i] = s
	rule2[0] = rule2[0].astype(dtype=np.int16)
	rule2[1] = rule2[1].astype(dtype=np.int16)

	# 像素化
	ret = np.empty((height, width)).astype(dtype=np.int16)
	for i in range(height):
		for j in range(width):
			ret[i, j] = round(
				np.average(img[rule2[0][i]:rule2[0][i] + rule1[0][i] + 1, rule2[1][j]:rule2[1][j] + rule1[1][j] + 1]))

	if is_double_color:  # 双色
		edge = white_edge  # 阈值
		ret = np.ones(ret.shape) * (ret >= edge)  # 0黑 1白

		# 处理
		temp = cv2.resize(ret, chessman.shape[:2][::-1], interpolation=cv2.INTER_AREA)
		chessman = cv2.merge([temp, temp, temp])
		chessman = white * chessman + black * (1 - chessman)
		picture[int(length / 2):int(length / 2) + chessman.shape[0], int(length / 2):int(length / 2) + chessman.shape[1]] = chessman

	else:  # 三色
		edge1 = gray_edge[0]  # 阈值1
		edge2 = gray_edge[1]  # 阈值2
		ret = 0.5 * np.ones(ret.shape) * (ret >= edge1) + 0.5 * np.ones(ret.shape) * (ret >= edge2)  # 0黑 0.5灰 1白

		# 处理
		temp = cv2.resize(ret, chessman.shape[:2][::-1], interpolation=cv2.INTER_AREA)
		chessman = cv2.merge([temp, temp, temp])
		chessman = white * (chessman == 1) + gray * (chessman == 0.5) + black * (chessman == 0)
		picture[int(length / 2):int(length / 2) + chessman.shape[0], int(length / 2):int(length / 2) + chessman.shape[1]] = chessman

	# 将图像部分贴到棋盘网格上
	if height % 2 == width % 2:
		if height >= width:
			grid[:, length * int((height - width) / 2):length * int((height - width) / 2 + width + 1)] = picture
		else:
			grid[length * int((width - height) / 2):length * int((width - height) / 2 + height + 1), :] = picture
	else:
		if height >= width:
			grid[:, length * int((height - width - 1) / 2):length * int((height - width - 1) / 2 + width + 1)] = picture
		else:
			grid[length * int((width - height - 1) / 2):length * int((width - height - 1) / 2 + height + 1), :] = picture

	# 计算
	l = round(grid.shape[0] / bg_left.shape[0] * bg_left.shape[1])
	r = round(grid.shape[0] / bg_right.shape[0] * bg_right.shape[1])
	w = l + r + grid.shape[1]
	t = round(w / bg_top.shape[1] * bg_top.shape[0])
	b = round(w / bg_bottom.shape[1] * bg_bottom.shape[0])
	h = t + b + grid.shape[0]
	# 输出图像
	ret = np.zeros((h, w, 3))
	# 背景框
	bg_top = cv2.resize(bg_top, (w, t))
	bg_bottom = cv2.resize(bg_bottom, (w, b))
	bg_left = cv2.resize(bg_left, (l, grid.shape[0]))
	bg_right = cv2.resize(bg_right, (r, grid.shape[0]))

	ret[0:t, :] = bg_top
	ret[h - b:, :] = bg_bottom
	ret[t:h - b, 0:l] = bg_left
	ret[t:h - b, w - r:] = bg_right
	ret[t:h - b, l:w - r] = grid

	return ret.astype(dtype=np.int16)

if __name__ == "__main__":
	for f in list(os.walk("./in"))[0][2]:
		# 参数: 高, 宽, 输入文件, 是否只有两种颜色, 灰度阈值（宽高以棋子为单位）
		cv2.imwrite("./out/ret_" + f, summon_gomoku_picture(30, 46, "./in/" + f, False, gray_edge=(90, 175)))
