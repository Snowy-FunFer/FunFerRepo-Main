""" Python 3.13.5
这是win10屏幕控制的辅助工具。
里面集成了许多常用的功能。
需要时可直接导入你的脚本文件并调用。

"""

import cv2
import numpy as np
import pyautogui
import pynput
import time
import datetime
import threading
from pathlib import Path

class ScreenHelper(object):
	""" 屏幕控制助手类，便于屏幕操作自动化
	Attributes:
		width(int): 屏幕宽（像素）
		height(int): 屏幕高（像素）
		mouse(object): 鼠标控制器对象
		keyboard(object): 键盘控制器对象
		res_dir_path(Path): 用于储存捕获资源文件的目录。默认为当前目录
		special_keys(dict): 特殊键字典
	"""
	# 键盘上的特殊键
	special_keys = {key: getattr(pynput.keyboard.Key, key) for key in [
		# 左右两边的shift/ctrl/alt键
		*[f"{b}_{p}" for p in ('l', 'r') for b in ("shift", "ctrl", "alt")],
		# F1 ~ F12
		*[f"f{i}" for i in range(1, 13)],
		# 杂项
		"up", "down", "left", "right",
		"space", "caps_lock", "delete",
		"esc", "enter", "tab"
	]}

	def __init__(self, res_dir_path: Path | str="."):
		self.width, self.height = pyautogui.size()
		self.mouse = pynput.mouse.Controller()
		self.keyboard = pynput.keyboard.Controller()
		self.res_dir_path = Path(res_dir_path).mkdir(parents=True, exist_ok=True)

	def click(self, *button: str | int, num: int=1, interval: float=0, blocking: bool=False) -> "ScreenHelper":
		""" 鼠标按钮点击控制
		Args:
			*button(str | int): 鼠标按钮序列。可选: "left"(0), "middle"(1), "right"(2)。默认为"left"
			num(int): 大于0表示点击次数；为-1表示按下；为0表示松开。默认为1
			interval(float): num大于0时连点的间隔时间（秒）。默认为0
			blocking(bool): 是否阻塞线程。默认为False
		Returns:
			self: 便于链式调用
		"""
		if len(button) == 1:
			button = button[0]
		else:
			def f():
				for i, b in enumerate(button):
					if i > 0:
						time.sleep(interval)
					self.click(b, num=num, interval=interval, blocking=True)
			if blocking:
				f()
			else:
				threading.Thread(target=f).start()
			return self
		btn = getattr(pynput.mouse.Button, ["left", "middle", "right"][button] if type(button) == int else button)
		if num > 0:
			if interval > 0:
				def precise_click():
					for i in range(num):
						if i > 0:
							time.sleep(interval)
						self.mouse.press(btn)
						self.mouse.release(btn)
				if blocking:
					precise_click()
				else:
					threading.Thread(target=precise_click).start()
			else:
				self.mouse.click(btn, num)
		elif num == 0:
			self.mouse.release(btn)
		elif num == -1:
			self.mouse.press(btn)
		return self
	
	def move(self, pos: list | tuple | np.ndarray, duration: float=0.0, blocking: bool=True) -> list | tuple | np.ndarray:
		""" 移动鼠标指针
		Args:
			pos(list | tuple| np.ndarray): 终点坐标
			duration(float, optional): 移动到终点所花的时间。默认为0.0
			blocking(bool, optional): 是否阻塞线程。默认为True
		Returns:
			pos(list | tuple| np.ndarray): 返回终点坐标
		"""
		if duration:
			def f():
				pyautogui.moveTo(*pos, duration)
			if blocking:
				f()
			else:
				threading.Thread(target=f).start()
		else:
			self.mouse.position = tuple(pos)
		return pos
	
	def scroll(self, units: int=1) -> "ScreenHelper":
		""" 滚动鼠标滚轮
		Args:
			units(int, optional): 向上滚动的单位数。该单位对应像素数不确定；为正表示向上滚动（新内容从底部刷新）。默认为1
		Returns:
			self: 便于链式调用
		"""
		pyautogui.scroll(units)
		return self
	
	def type(self, *key: str, num: int=1, interval: float=0, blocking=False) -> "ScreenHelper":
		""" 键盘按钮点击控制
		Args:
			*key(str): 键名称序列
			num(int): 大于0表示点击次数；为-1表示按下；为0表示松开。默认为1
			interval(float): num大于0时连点的间隔时间（秒）。默认为0
			blocking(bool): 是否阻塞线程。默认为False
		Returns:
			self: 便于链式调用
		"""
		if len(key) == 1:
			key = key[0]
		else:
			def f():
				for i, k in enumerate(key):
					if i > 0:
						time.sleep(interval)
					self.type(k, num=num, interval=interval, blocking=True)
			if blocking:
				f()
			else:
				threading.Thread(target=f).start()
			return self
		key = self.special_keys.get(key, key)
		if num > 0:
			if interval > 0:
				def precise_type():
					for i in range(num):
						if i > 0:
							time.sleep(interval)
						self.keyboard.type(key)
				if blocking:
					precise_type()
				else:
					threading.Thread(target=precise_type).start()
			else:
				for i in range(num):
					self.keyboard.type(key)
		elif num == 0:
			self.keyboard.release(key)
		elif num == -1:
			self.keyboard.press(key)
		return self



	def save_screen(self, file_name: Path | str=None, file_dir: Path | str=None) -> None:
		""" 截取当前屏幕图片并保存
		Args:
			file_name(Path | str, optional): 保存的文件名，为None则以时间点作为名字。默认为None
			file_dir(Path | str, optional): 保存文件所在的目录，为None则保存至默认资源目录。默认为None
		"""
		if not file_name:
			file_name = f"Screenshot{datetime.now().isoformat()}.png"
		pyautogui.screenshot().save((self.res_dir_path if file_dir else Path(file_dir).mkdir(parents=True, exist_ok=True)) / file_name)

	def match_img(self, template_name: Path | str, template_dir: Path | str=None, img_path: Path | str | np.ndarray=None, n: int=1, threshold: float=0.5, fail_protect_num: int=0, fail_protect_duration: float=1.0) -> list:
		""" 全等匹配图片并返回符合条件的中心坐标列表
		Args:
			template_name(Path | str): 模板图片文件名（或相对于template_dir的路径）
			template_dir(Path | str, optional): 模板图片文件所在目录，为None则用默认资源目录。默认为None
			img_path(Path | str, optional): 源图片文件路径，为None则用当前屏幕截图。默认为None
			n(int, optional): 匹配数量。默认为1
			threshold(float, optional): 模糊度阈值（0.0～1.0），n=0时尽可能多的匹配，但匹配结果相似度应大于该阈值。默认为0.75
			fail_protect_num(int, optional): 匹配失败后的重复次数，仅对屏幕截图有效；此参数会阻塞线程。默认为0
			fail_protect_duration(float, optional): 匹配失败重复的间隔；此参数会阻塞线程。默认为1.0
		Returns:
			ret(list): 所有匹配结果中心坐标组成的列表
				[(x: int, y: int), ...] (匹配结果数量不多于n)
		"""
		if n > 0:
			is_screen = not bool(img_path)
			img_path = cv2.cvtColor(np.asarray(pyautogui.screenshot()), cv2.COLOR_BGR2GRAY) if is_screen else img_path if is_screen or type(img_path) == np.ndarray else cv2.imread(img_path, 0)
			template = cv2.imread((Path(template_dir).mkdir(parents=True, exist_ok=True) if template_dir else self.res_dir_path) / Path(template_name), 0)
			res = cv2.matchTemplate(img_path, template, cv2.TM_CCOEFF_NORMED)
			""" cv2.matchTemplate最后一个参数可选择：（若修改，则需一并修改阈值相关算法）
				cv2.TM_SQDIFF 平方差匹配：越小越相似
				cv2.TM_CCORR 相关匹配：越大越相似
				cv2.TM_CCORR_NORMED 归一化相关匹配：越大越相似（0.0～1.0）
				cv2.TM_CCOEFF 相关系数匹配：考虑均值，更稳定（-1：反色相似；0：不相似；1：相似）
			"""
			max_similarity = np.max(res)
			if max_similarity >= threshold:
				raw_ret = np.array(np.where(res == max_similarity)[::-1])
				ret = list(zip(*(raw_ret + np.array([[template.shape[1] // 2], [template.shape[0] // 2]]))))
				for p in raw_ret.T:
					img_path[p[0] : p[0] + template.shape[1], p[1] : p[1] + template.shape[0]] = 0
				return ret + self.match_img(template_name, template_dir, img_path, n - 1, threshold, fail_protect_num, fail_protect_duration)
			else:
				if is_screen:
					if fail_protect_num:
						if fail_protect_duration:
							time.sleep(fail_protect_duration)
							return self.match_img(template_name, template_dir, None, n, threshold, fail_protect_num - 1, fail_protect_duration)
						else:
							return []
					else:
						return []
				else:
					return []
		else:
			return []


