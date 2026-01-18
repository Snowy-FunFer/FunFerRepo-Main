""" Python 3.13.5
这是一个用turtle库绘制爱心的程序。

"""

import math
import turtle

turtle.setup(1000, 650, 100, 100)
turtle.hideturtle()

turtle.pensize(10)
deltaColor = 0.02  # 颜色增量
colorRange = [0.3, 0.98]  # 颜色范围

red = colorRange[1]
blue = colorRange[0]
redUp = False
blueUp = True



def updateColor():
    global red, blue
    global redUp, blueUp

    turtle.pencolor(red, 0.01, blue)

    if redUp:
        red += deltaColor
        if red >= colorRange[1]:
            redUp = False
    else:
        red -= deltaColor
        if red <= colorRange[0]:
            redUp = True

    if blueUp:
        blue += deltaColor
        if blue >= colorRange[1]:
            blueUp = False
    else:
        blue -= deltaColor
        if blue <= colorRange[0]:
            blueUp = True


def draw(f, r):
    turtle.pu()
    for i in r:
        updateColor()
        turtle.goto(i, f(i))
        turtle.pd()


r = 50


def f(x):
    return (r ** 2 - (abs(x) - r) ** 2) ** 0.5


def g(x):
    return r * math.asin((abs(x) - r) / r) - math.pi * r / 2


draw(f, [i - 100 for i in range(201)])

draw(g, [i - 100 for i in range(201)])

turtle.done()
