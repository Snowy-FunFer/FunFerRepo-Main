import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from matplotlib.animation import FuncAnimation

fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

ax.set_xlim([-2.3, 2.3])
ax.set_ylim([-2.3, 2.3])
ax.set_zlim([-2.3, 2.3])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.grid(True)

ax.set_box_aspect([1, 1, 1])

# 空间中连接两点的线段
def line(p1, p2, color='C0'):
    return ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color=color)[0]

cube0 = np.matrix([
    [-1, -1, -1, -1, 1, 1, 1, 1],
    [-1, -1, 1, 1, -1, -1, 1, 1],
    [-1, 1, -1, 1, -1, 1, -1, 1]
])

class Cube(object):
    def __init__(self, points_matrix, color='C0'):
        self.color = color
        self.data = points_matrix
        self.points = None
        self.lines = None
        self.draw()
    def update(self, points_matrix):
        self.data = points_matrix
        self.points.remove()
        for l in self.lines:
            l.remove()
        self.draw()
    def draw(self):
        self.points = ax.scatter(*self.data, color=self.color)
        self.lines = [
            line(self.data[:, 0], self.data[:, 1], self.color),
            line(self.data[:, 0], self.data[:, 2], self.color),
            line(self.data[:, 0], self.data[:, 4], self.color),
            line(self.data[:, 1], self.data[:, 3], self.color),
            line(self.data[:, 1], self.data[:, 5], self.color),
            line(self.data[:, 2], self.data[:, 3], self.color),
            line(self.data[:, 2], self.data[:, 6], self.color),
            line(self.data[:, 3], self.data[:, 7], self.color),
            line(self.data[:, 4], self.data[:, 5], self.color),
            line(self.data[:, 4], self.data[:, 6], self.color),
            line(self.data[:, 5], self.data[:, 7], self.color),
            line(self.data[:, 6], self.data[:, 7], self.color),
        ]


cube1 = cube0
cube2 = cube0 * np.sqrt(3) / 2
cube3 = cube0 * 0.75
obj1 = Cube(cube1, 'black')
obj2 = Cube(cube2, 'grey')
obj3 = Cube(cube3, 'purple')

# 将z轴转向向量(1, 1, 1)方向的线性变换
A = expm(np.atan(np.sqrt(2)) / np.sqrt(2) * np.array([
    [0, 0, 1],
    [0, 0, 1],
    [-1, -1, 0]
]))
# 绕z轴旋转的旋转矩阵
B = lambda theta: np.matrix([
    [np.cos(theta), -np.sin(theta), 0],
    [np.sin(theta), np.cos(theta), 0],
    [0, 0, 1]
])

def update(frame):
    t = frame / 40 * 1.5
    # 缓慢旋转视角
    ax.view_init(elev=25, azim=frame * 0.2)

    offset = 0.75 * np.sin(4 * t) * np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1]
    ])
    obj3.update(offset + B(t) @ A @ A @ B(t) @ A @ B(t) @ cube3)
    obj2.update(offset + B(t) @ A @ A @ B(t) @ cube2)
    obj1.update(offset + B(t) @ A @ cube1)

    return []

ani = FuncAnimation(
    fig,
    update,
    frames=np.arange(0, 1e6, 1),  # 帧数
    interval=25,  # 帧间隔(ms)。此时一秒有40帧(semi-tick)
)

plt.tight_layout()
plt.show()
