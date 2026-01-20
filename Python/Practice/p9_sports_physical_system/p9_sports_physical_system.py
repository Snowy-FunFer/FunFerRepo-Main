""" Python 3.13.5
这是一个二维运动学系统模拟程序。
参数写在SportsPhysicalSystem类的构造函数中，
包括：初位矢、初速度、加速度场、普朗克时间、显示范围。
由于是离散化物理系统，
模拟结果会有微小偏差。

"""

import numpy as np
import matplotlib.pyplot as plt

class SportsPhysicalSystem(object):
    def __init__(self, x=(0, 0), v=(0, 0), a=lambda x, v, t: np.array([0, 0]), dt=0.035, view=(-5, 5, -5, 5)):
        self.is_render = True
        self.fig = plt.figure(figsize=(7, 7))
        self.ax = self.fig.subplots()
        self.view = view
        self.reset_all(x, v, a, dt)

    # 开始运行
    def start(self, t_=1):
        while self.t <= t_:
            self.render()
            self.refresh()
            self.t += self.dt

    # 重设所有参数
    def reset_all(self, x=(0, 0), v=(0, 0), a=lambda x, v, t: np.array([0, 0]), dt=0.035):
        self.initial = (x, v, a, dt)
        self.t = 0
        self.x = np.array(x)
        self.v = np.array(v)
        self.a = a
        self.dt = dt

    # 回到初始参数状态
    def reset(self):
        self.t = 0
        self.x, self.v, self.a, self.dt = self.initial

    # 流逝一个dt时间（不渲染）
    def refresh(self):
        self.v = self.a(self.x, self.v, self.t) * self.dt + self.v
        self.x = self.v * self.dt + self.x

    # 设置当前时间
    def set_t(self, t):
        self.t = t

    # 设置视野区域
    def set_view(self, view=(-5, 5, -5, 5)):
        self.view = view

    # 设置是否渲染
    def set_is_render(self, b):
        self.is_render = b

    # 渲染图像
    def render(self):
        plt.grid()
        plt.xlim(self.view[:2])
        plt.ylim(self.view[2:])
        plt.xlabel("t = %.2f" % self.t)
        self.ax.scatter(*self.x)
        plt.pause(0.001)
        self.ax.cla()

x0 = (0.8, 0)
v0 = (0, 9)
GM = 40
def a(x, v, t):
    return -GM / np.sqrt(x.dot(x)) ** 3 * x

SPS = SportsPhysicalSystem(x=x0, v=v0, a=a, view=(-5, 5, -5, 5))
SPS.start(3600)
