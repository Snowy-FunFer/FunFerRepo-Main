""" Python 3.13.5
这是一个对散点进行二次拟合的程序。
运行程序后先输入需对多少个散点进行拟合，
然后在坐标系上点击任意位置放置散点。
当散点全被放置完毕后，
你会看到一条最佳拟合抛物线

"""

# 二次拟合
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
        if n >= 3:
            break
        else:
            print(" 散点个数应大于等于3！")
    except ValueError:
        print(" 请输入实数！")

# 点集
points = plt.ginput(n)

# 分量列表
x = np.array(list(dict([*points]).keys()))
y = np.array(list(dict([*points]).values()))
# 定义计算n次平均数的函数
def mean(l, n):
    return sum([i ** n for i in l]) / len(l)

# 拟合系数方程矩阵 及其逆矩阵
A = np.array([
    [mean(x, 2), mean(x, 1), 1],
    [mean(x, 3), mean(x, 2), mean(x, 1)],
    [mean(x, 4), mean(x, 3), mean(x, 2)]
])
A_i = np.linalg.inv(A)
# 计算拟合系数
value_victor = np.array([mean(y, 1), mean(y * x, 1), mean(y * (x ** 2), 1)])
theta = A_i.dot(value_victor)

# 定义二次拟合曲线函数
X = np.linspace(-10, 10, 500)
Y = theta[0] * (X ** 2) + theta[1] * X + theta[2]

# 画散点图
for p in points:
    plt.scatter(p[0], p[1], color="b")

# 画曲线图
plt.plot(X, Y)

# 设置范围
plt.xlim(min(x) - 0.3, max(x) + 0.3)
plt.ylim(min(y) - 0.3, max(y) + 0.3)

plt.show()

os.system("pause")
