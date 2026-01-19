""" Python 3.13.5
这是更好的线性拟合演示程序。
传统的线性拟合是优化拟合直线与散点的竖直距离方差。
经过@Snowy-FunFer的改进，
更好的线性拟合则是优化拟合直线与散点的距离方差，
从而使拟合直线更加拟合散点。
运行程序后先输入需对多少个散点进行拟合，
然后在坐标系上点击任意位置放置散点。
当散点全被放置完毕后，
你会看到两条拟合直线。
实线那条是更好的线性拟合结果，
而虚线那条是传统的线性拟合结果。

"""

# 更好的线性拟合
import os
import numpy as np
import matplotlib.pyplot as plt

plt.figure(figsize=(6, 6))
plt.grid()

plt.xlim(-1.5, 1.5)
plt.ylim(-1.5, 1.5)

# 点的数量
while 1:
    try:
        n = int(input("请输入散点个数: "))
        if n >= 2:
            break
        else:
            print(" 散点个数应大于等于2！")
    except ValueError:
        print(" 请输入实数！")

# 点集
points = plt.ginput(n)

# 分量列表
x = np.array(list(dict([*points]).keys()))
y = np.array(list(dict([*points]).values()))
# 定义平均数函数
def mean(l):
    return sum(l) / len(l)

# 计算拟合系数（精确算法）
e = (mean(x ** 2) - mean(y ** 2) + mean(y) ** 2 - mean(x) ** 2) / (mean(x * y) - mean(x) * mean(y))
k = (e - (e ** 2 + 4) ** 0.5) / 2
b = - mean(y) - mean(x) * k

# 定义拟合直线函数
X = np.linspace(-10, 10, 500)
Y1 = -k * X - b

# 简单算法
b_hat = (mean(x * y) - mean(x) * mean(y)) / (mean(x ** 2) - mean(x) ** 2)
a_hat = mean(y) - b_hat * mean(x)

Y2 = a_hat + b_hat * X

# 画散点图
for p in points:
    plt.scatter(p[0], p[1], color="b")

# 画直线图
plt.plot(X, Y1)
plt.plot(X, Y2, "--")

# 设置范围
plt.xlim(min(x) - 0.3, max(x) + 0.3)
plt.ylim(min(y) - 0.3, max(y) + 0.3)

plt.show()

os.system("pause")
