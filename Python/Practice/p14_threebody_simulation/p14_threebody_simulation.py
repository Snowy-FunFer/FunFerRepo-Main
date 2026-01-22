""" Python 3.13.5
这是一个三体运动的模拟程序。
运行此程序后你会看到空间中三个质点因受万有引力而漂浮不定。
相关物理参数可在以下代码中调整。

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# 物理参数
G = 100  # 万有引力常量
dt = 0.003  # 时间步长

# 初始条件
init_x = [  # 初位置
    [1, 0, 0],
    [0, 0, 0],
    [0, 0, 1]
]
init_v = [  # 初速度
    [0, 10, 0],
    [0, 0, 10],
    [0, -10, 0]
]
mass = [1, 1, 1]  # 质量（不考虑相对论效应）


# 创建图形和3D轴
fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

# 设置坐标轴范围和标签
ax.set_xlim([-1.5, 1.5])
ax.set_ylim([-1.5, 1.5])
ax.set_zlim([-1.5, 1.5])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Three-Body Simulation with Trails')
ax.grid(True)

# 设置等比例缩放
ax.set_box_aspect([1, 1, 1])

# 加速度计算函数
def accelerate(x):
    dx0 = x[0] - x[1]
    dx1 = x[1] - x[2]
    dx2 = x[2] - x[0]
    temp0 = dx0 / (dx0.dot(dx0) + 1e-10) ** 1.5
    temp1 = dx1 / (dx1.dot(dx1) + 1e-10) ** 1.5
    temp2 = dx2 / (dx2.dot(dx2) + 1e-10) ** 1.5
    a0 = temp2 * mass[2] - temp0 * mass[1]
    a1 = temp0 * mass[0] - temp1 * mass[2]
    a2 = temp1 * mass[1] - temp2 * mass[0]
    return np.array([a0, a1, a2])

# 初始化质点位置和速度
vertices = np.array(init_x)
vertices_v = np.array(init_v)

# 创建轨迹存储结构
max_trail_points = 200  # 最大轨迹点数
trail_data = [[], [], []]  # 三个质点的轨迹点
colors = ['red', 'green', 'blue']

# 创建主质点
points = ax.scatter(
    vertices[:, 0],
    vertices[:, 1],
    vertices[:, 2],
    s=150,
    c=colors,
    marker='o',
    edgecolors='black',
    zorder=10  # 确保主点在最上层
)

# 创建轨迹散点图
trail_scatters = []
for i in range(3):
    sc = ax.scatter([], [], [], s=30, c=colors[i], alpha=0.3, marker='.')
    trail_scatters.append(sc)

# 动画更新函数
def update(frame):
    global vertices, vertices_v, trail_data

    # 计算加速度
    a = G * accelerate(vertices)

    # 更新速度
    vertices_v = vertices_v + a * dt

    # 更新位置
    vertices = vertices + vertices_v * dt

    # 更新主质点位置
    points._offsets3d = (vertices[:, 0], vertices[:, 1], vertices[:, 2])

    # 更新轨迹
    for i in range(3):
        # 添加新位置到轨迹
        trail_data[i].append(vertices[i].copy())

        # 限制轨迹长度
        if len(trail_data[i]) > max_trail_points:
            trail_data[i].pop(0)

        # 更新轨迹散点图
        if trail_data[i]:
            trail_points = np.array(trail_data[i])
            trail_scatters[i]._offsets3d = (
                trail_points[:, 0],
                trail_points[:, 1],
                trail_points[:, 2]
            )

    # 调整视角中心
    center = np.mean(vertices, axis=0)
    view_range = 1.5  # 增大视野范围
    ax.set_xlim([center[0] - view_range, center[0] + view_range])
    ax.set_ylim([center[1] - view_range, center[1] + view_range])
    ax.set_zlim([center[2] - view_range, center[2] + view_range])

    # 缓慢旋转视角
    ax.view_init(elev=25, azim=frame * 0.2)

    # 返回所有需要更新的对象
    return [points] + trail_scatters

# 创建动画
ani = FuncAnimation(
    fig,
    update,
    frames=np.arange(0, 1e6, 1),  # 帧数
    interval=10,  # 帧间隔(ms)
    blit=False
)

plt.tight_layout()
plt.show()
