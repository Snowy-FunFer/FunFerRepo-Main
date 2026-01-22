""" Python 3.13.5
这是一款名为《军工战争》的游戏。

"""

import tkinter as tk
import threading
from time import sleep
from json import load
import keyboard  # 第三方库，用于接受键盘输入

"""
(启动游戏时 有概率启动失败)
操作说明:
先手: 上下左右:wasd  进入商店/确定:f  退出商店/铲除:g  下一回合:h
后手: 上下左右:箭头  进入商店/确定:,  退出商店/铲除:.  下一回合:/
"""

# 读取预设信息
with open("./settings.json", "r") as f:
    EnumData = load(f)

class Enum:  # 枚举值
    initial_money = EnumData.get("initial_money", 1000)
    natural_efficiency = EnumData.get("natural_efficiency", 100)
    initial_castle = EnumData.get("initial_castle", [  # 初始堡垒
        [1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], [7, 0], [8, 0],
        [1, 1], [1, 2], [1, 3], [1, 4], [1, 5],
        [8, 1], [8, 2], [8, 3], [8, 4], [8, 5],
        [2, 5], [3, 5], [4, 5], [5, 5], [6, 5], [7, 5]
    ])
    block = EnumData.get("block", {  # 方块 (耗资, 耐久, 特有属性)
        "brick": [
            (40, 20),
            (100, 50),
            (200, 100),
            (400, 200),
            (1000, 500)
        ],
        "factory": [  # 特有属性: 生产效率
            (200, 50, 100),
            (400, 100, 200),
            (700, 200, 300),
            (1500, 500, 500)
        ],
        "attacker": [  # 特有属性: 炮弹质量
            (150, 50, 10),
            (300, 100, 30),
            (600, 200, 50),
            (1400, 500, 100),
            (2600, 600, -1)
        ],
        "engine": [  # 特有属性: *(供弹量, 最大初始射速)
            (50, 50, 1, 4),
            (100, 80, 2, 7),
            (300, 160, 2, 10),
            (600, 300, 3, 5)
        ]
    })
    description = EnumData.get("description", {
        "brick": [
            "耐久%d的砖，木头做的" % (block["brick"][0][1]),
            "耐久%d的砖，石头做的" % (block["brick"][1][1]),
            "耐久%d的砖，铁块做的" % (block["brick"][2][1]),
            "耐久%d的砖，金块做的" % (block["brick"][3][1]),
            "耐久%d的砖，钻石做的" % (block["brick"][4][1])
        ],
        "factory": [
            "小型工厂，每个回合生产价值%d资金" % (block["factory"][0][2]),
            "中型工厂，每个回合生产价值%d资金" % (block["factory"][1][2]),
            "大型工厂，每个回合生产价值%d资金" % (block["factory"][2][2]),
            "超大型工厂，每个回合生产价值%d资金" % (block["factory"][3][2])
        ],
        "attacker": [
            "小型炮台，发射%d质量的炮弹 (建造初回合无法投入使用，炮弹伤害=撞击速度*质量)" % (block["attacker"][0][2]),
            "中型炮台，发射%d质量的炮弹 (建造初回合无法投入使用，炮弹伤害=撞击速度*质量)" % (block["attacker"][1][2]),
            "大型炮台，发射%d质量的炮弹 (建造初回合无法投入使用，炮弹伤害=撞击速度*质量)" % (block["attacker"][2][2]),
            "超大型炮台，发射%d质量的炮弹 (建造初回合无法投入使用，炮弹伤害=撞击速度*质量)" % (block["attacker"][3][2]),
            "特殊炮台，发射的炮弹能直接炸毁3x3的区域 (建造初回合无法投入使用)"
        ],
        "engine": [
            "小型引擎，每个回合为周围4格炮台提供%d发炮弹，最大初射速度为%d" % (block["engine"][0][2], block["engine"][0][3]),
            "中型引擎，每个回合为周围4格炮台提供%d发炮弹，最大初射速度为%d" % (block["engine"][1][2], block["engine"][1][3]),
            "大型引擎，每个回合为周围4格炮台提供%d发炮弹，最大初射速度为%d" % (block["engine"][2][2], block["engine"][2][3]),
            "特殊引擎，每个回合为周围4格炮台提供%d发炮弹，最大初射速度为%d，无视重力作用" % (block["engine"][3][2], block["engine"][3][3])
        ]
    })
    party_state = {  # 状态 (0: 此回合未轮到该玩家, 1: 战场移动, 2: 商店移动, 3: 炮台移动, 4: 准备铲除)
        "unavailable": 0,
        "move": 1,
        "shop": 2,
        "attack": 3,
        "clear": 4
    }

class Game:  # 游戏主类
    class Party:  # 队伍类
        def __init__(self, game, index, aimPos):
            # 游戏实例
            self.game = game
            # 队伍信息
            self.index = index  # 队伍代号
            self.money = 0  # 资金
            self.death = False  # 是否死亡
            self.aimPos = list(aimPos)  # 选择光标 (战场坐标)
            self.shopPos = [0, 0]  # 选择光标 (商店坐标: [方块类型, 等级])
            self.current_attackerPos = [0, 0]  # 当前选中炮台坐标
            self.state = Enum.party_state["unavailable"]  # 玩家状态
            self.factory_efficiency = 0  # 工厂效率

        def set_state(self, tar):  # 设置状态
            self.state = Enum.party_state[tar]
            if tar == "shop":  # 进入商店则显示商店光标
                self.game.ground.setvisible_shopAim(self.index, True)
                self.game.ground.move_shop(self.index)
            else:
                self.game.ground.setvisible_shopAim(self.index, False)
                if self.index == 0:
                    self.game.ground.cv.itemconfig(self.game.ground.descriptionA, text="描述信息")
                elif self.index == 1:
                    self.game.ground.cv.itemconfig(self.game.ground.descriptionB, text="描述信息")
            if tar == "clear":  # 准备清除则高光清除按钮
                if self.index == 0:
                    self.game.ground.cv.itemconfig(self.game.ground.clearA, image=self.game.ground.active_clear)
                elif self.index == 1:
                    self.game.ground.cv.itemconfig(self.game.ground.clearB, image=self.game.ground.active_clear)
            else:
                if self.index == 0:
                    self.game.ground.cv.itemconfig(self.game.ground.clearA, image=self.game.ground.clear)
                elif self.index == 1:
                    self.game.ground.cv.itemconfig(self.game.ground.clearB, image=self.game.ground.clear)
            if tar == "attack":  # 进入炮台
                self.current_attackerPos = [self.aimPos[0], self.aimPos[1]]  # must so do... there is an unknown bug.
            else:
                self.game.ground.cv.coords(self.game.ground.attacker_arrow, 0, 0, 0, 0)

        def become_active(self):  # 轮到操作
            self.set_state("move")
            self.game.ground.show_active_player(self.index)
            if self.index == 0:
                keyboard.wait("h")
            elif self.index == 1:
                keyboard.wait("/")

        def become_negative(self):  # 轮完操作
            self.set_state("unavailable")

        def add_money(self, dm):  # 增加资金
            self.money += dm
            self.game.ground.update_money_data()

        def add_factory_efficiency(self, de):  # 增加工厂效率
            self.factory_efficiency = max(self.factory_efficiency + de, 0)

        def factory(self):  # 让工厂按效率生产并增加资金
            self.add_money(self.factory_efficiency)

    class Ground:  # 游戏场地类
        class Block:  # 方块类
            def __init__(self, ground, belong, blockType, pos):  # blockType = type : level (str)
                self.ground = ground  # 场景对象
                self.pos = pos
                self.img = ground.cv.create_image(*ground.analyze_pos(*pos), image=ground.blank)  # 方块图片
                self.durText = ground.cv.create_text(*ground.analyze_pos(*pos))  # 方块耐久文本
                self.transform(belong, blockType)  # 初始化方块信息
                self.shell_num = 0  # 炮弹数量

            def update_img(self):  # 更新方块图片
                if self.type == "blank":
                    img = self.ground.blank
                    self.ground.cv.itemconfig(self.durText, state="hidden")
                    self.ground.cv.itemconfig(self.img, state="hidden")
                else:
                    self.ground.cv.itemconfig(self.durText, state="normal")
                    self.ground.cv.itemconfig(self.img, state="normal")
                if self.type == "brick":
                    img = self.ground.brick
                elif self.type == "attacker":
                    img = self.ground.attacker[self.level]
                elif self.type == "factory":
                    img = self.ground.factory[self.level]
                elif self.type == "engine":
                    img = self.ground.engine[self.level]
                else:
                    return
                self.ground.cv.itemconfig(self.img, image=img)
                self.ground.cv.itemconfig(self.durText, text=str(self.duration))

            def transform(self, belong, blockType, duration=None):  # 转换为设定方块
                self.belong = belong  # 所属队伍 (空白为None)
                self.type, self.level = blockType.split(":")  # 类型
                self.level = int(self.level)  # 等级
                if duration == None:  # 耐久
                    self.duration = self.ground.get_full_duration(blockType)
                else:
                    self.duration = duration
                if self.type != "attacker":  # 不是炮台，则清空炮弹
                    self.shell_num = 0
                self.update_img()  # 更新贴图

            def update_shell_num(self):  # 更新炮弹数量
                if self.type == "attacker":  # 判断是否为炮台
                    engine_level = self.ground.get_near_highest_engine(*self.pos)
                    if engine_level >= 0:
                        self.shell_num = Enum.block["engine"][engine_level][2]
                    else:
                        self.shell_num = 0

            def broke(self, duration):  # 损坏方块
                self.duration -= duration
                if self.duration <= 0:  # 耐久耗尽，变为空气
                    ret = -self.duration  # 返还炮弹伤害
                    self.ground.destroy_block(self.pos)
                    return ret
                self.update_img()

        class Shell:  # 炮弹类
            def __init__(self, ground):
                self.belong = None
                self.ground = ground
                self.img = self.ground.cv.create_image(0, 0, image=self.ground.shell, state="hidden")  # 炮弹贴图
                self.is_boom = False  # 是否会爆炸
                self.is_straight = False  # 是否直线打击
                self.velocity = [0, 0]  # 速度

            def get_speed(self):  # 获取速率 (欧拉距离)
                return (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** 0.5

            def setvisible(self, is_visible):  # 设置是否显示
                if is_visible:
                    state = "normal"
                else:
                    state = "hidden"
                self.ground.cv.itemconfig(self.img, state=state)

            def shoot(self, mass, velocity, party, is_straight=False):  # 开炮！！！
                self.belong = party.index
                self.is_boom = True if mass < 0 else False  # 炸弹
                self.is_straight = True if is_straight else False  # 直线打击
                self.velocity = velocity
                self.setvisible(True)

                original_pos = party.current_attackerPos  # 源坐标
                while True:
                    target_pos = [original_pos[0] + self.velocity[0], original_pos[1] + self.velocity[1]]
                    original_pos = self.fly(original_pos, mass)
                    if not original_pos:  # 飞行失败 (伤害耗完)
                        self.setvisible(False)
                        break
                    if not self.is_straight:
                        self.velocity[1] -= 1

            def fly(self, from_pos, mass):  # 直线飞行
                cur_pos = None
                for t in range(20):
                    sleep(0.01)
                    dx = self.velocity[0] / 12
                    dy = self.velocity[1] / 12
                    # 撞击方块
                    hit_pos = [round(from_pos[0] + t * dx), round(from_pos[1] + t * dy)]
                    # 撞到边界 (不包括上界)
                    if not (0 <= hit_pos[0] <= 29 and 0 <= hit_pos[1] <= 128):
                        return False
                    if hit_pos[1] <= 29:
                        hit_blockInfo = self.ground.get_block(*hit_pos)
                        if hit_blockInfo["name"] != "blank" and hit_blockInfo["belong"] != self.belong:  # 撞到非空气方块 且 非己方方块
                            if self.is_boom:  # 爆炸
                                blocks = [
                                    self.ground.get_block_obj(hit_pos[0] - 1, hit_pos[1] - 1),
                                    self.ground.get_block_obj(hit_pos[0] - 1, hit_pos[1]),
                                    self.ground.get_block_obj(hit_pos[0] - 1, hit_pos[1] + 1),
                                    self.ground.get_block_obj(hit_pos[0], hit_pos[1] - 1),
                                    self.ground.get_block_obj(hit_pos[0], hit_pos[1]),
                                    self.ground.get_block_obj(hit_pos[0], hit_pos[1] + 1),
                                    self.ground.get_block_obj(hit_pos[0] + 1, hit_pos[1] - 1),
                                    self.ground.get_block_obj(hit_pos[0] + 1, hit_pos[1]),
                                    self.ground.get_block_obj(hit_pos[0] + 1, hit_pos[1] + 1)
                                ]
                                for block in blocks:
                                    if block:
                                        block.broke(99999)
                                return False
                            else:  # 不爆炸
                                damage = self.ground.get_block_obj(*hit_pos).broke(round(self.get_speed() * mass))
                                if not damage:  # 伤害耗尽
                                    return False
                                else:  # 伤害未耗尽
                                    self.velocity = [  # 减慢速度
                                        round(self.velocity[0] / self.get_speed() * damage / mass),
                                        round(self.velocity[1] / self.get_speed() * damage / mass)
                                    ]
                                    if self.get_speed() < 0.3:  # 速度过小
                                        return False
                    # 渲染贴图
                    cur_pos = [from_pos[0] + t * dx, from_pos[1] + t * dy]
                    self.ground.cv.coords(self.img, *self.ground.analyze_pos(*cur_pos))
                return cur_pos

        def __init__(self, game):
            # 游戏主类实例
            self.game = game
            # 注册监听键盘输入
            self.register_listen_to_keyboard()

        def update_money_data(self):  # 更新资金信息
            self.cv.itemconfig(self.partyA_money, text=str(self.game.partyA.money))
            self.cv.itemconfig(self.partyB_money, text=str(self.game.partyB.money))

        def update_round_data(self, r):  # 更新回合信息
            self.cv.itemconfig(self.round_title, text="第"+str(r)+"回合")

        def update_attacker(self):  # 更新所有炮台
            for i in self.blockGround:
                for block in i:
                    block.update_shell_num()

        def update_attacker_arrow(self, party):  # 更新炮台箭头
            self.cv.coords(self.attacker_arrow, *self.analyze_pos(*party.current_attackerPos), *self.analyze_pos(*party.aimPos))

        def analyze_pos(self, x, y):  # 输入: 理论(x, y) 返回: 画板(x', y')
            return 110 + 20 * x, 60 + 20 * (29 - y)

        def is_in_legal_range(self, partyId):  # 判断战场光标是否在合法范围内
            party = self.get_party_by_id(partyId)
            if partyId == 0:
                return party.aimPos[0] <= 12
            elif partyId == 1:
                return party.aimPos[0] >= 17

        def get_near_highest_engine(self, x, y):  # 判断目标位置周围四格是否有引擎，返回最高等级的引擎，没有则为-1
            ret = [-1]
            if self.get_block(x - 1, y)["name"] == "engine":
                ret.append(self.get_block(x - 1, y)["level"])
            elif self.get_block(x + 1, y)["name"] == "engine":
                ret.append(self.get_block(x + 1, y)["level"])
            elif self.get_block(x, y - 1)["name"] == "engine":
                ret.append(self.get_block(x, y - 1)["level"])
            elif self.get_block(x, y + 1)["name"] == "engine":
                ret.append(self.get_block(x, y + 1)["level"])
            return max(ret)

        def get_party_by_id(self, id):
            if id == 0:
                party = self.game.partyA
            elif id == 1:
                party = self.game.partyB
            else:
                party = None
            return party

        def get_blockType_by_shopPos(self, party):  # 获取玩家当前在商店选中的商品
            line, index = party.shopPos
            return list(Enum.block.keys())[line] + ":" + str(index)

        def get_full_duration(self, blockType):  # 获取方块的满耐久值
            name, level = blockType.split(":")
            blockInfo = Enum.block.get(name)
            if blockInfo:
                return blockInfo[int(level)][1]
            else:
                return -1

        def get_price(self, blockType):  # 获取方块的价格
            name, level = blockType.split(":")
            return Enum.block[name][int(level)][0]

        def get_attacker_velocity(self, party):  # 获取炮台初射速矢
            return [party.aimPos[0] - party.current_attackerPos[0], party.aimPos[1] - party.current_attackerPos[1]]

        def get_distance_to_attacker(self, pos, party):  # 获取目标坐标与选定玩家的炮台的距离
            return abs(pos[0] - party.current_attackerPos[0]) + abs(pos[1] - party.current_attackerPos[1])

        def show_active_player(self, index):  # 显示操作方
            if index == 0:
                self.cv.moveto(self.active_player_title, 15, 30)
            elif index == 1:
                self.cv.moveto(self.active_player_title, 715, 30)

        def setvisible_shopAim(self, partyId, state):
            if state:
                state = "normal"
            else:
                state = "hidden"
            if partyId == 0:
                self.cv.itemconfig(self.shopAimA, state=state)
            elif partyId == 1:
                self.cv.itemconfig(self.shopAimB, state=state)

        def register_listen_to_keyboard(self):  # 注册监听键盘输入
            keyboard.add_hotkey("w", self.move_aim, args=(0, "u"))
            keyboard.add_hotkey("a", self.move_aim, args=(0, "l"))
            keyboard.add_hotkey("s", self.move_aim, args=(0, "dirs"))
            keyboard.add_hotkey("d", self.move_aim, args=(0, "root"))
            keyboard.add_hotkey("f", self.click, args=(0,))
            keyboard.add_hotkey("g", self.cancel, args=(0,))
            keyboard.add_hotkey("h", self.finish, args=(0,))
            keyboard.add_hotkey("up", self.move_aim, args=(1, "u"))
            keyboard.add_hotkey("left", self.move_aim, args=(1, "l"))
            keyboard.add_hotkey("down", self.move_aim, args=(1, "dirs"))
            keyboard.add_hotkey("right", self.move_aim, args=(1, "root"))
            keyboard.add_hotkey(",", self.click, args=(1,))
            keyboard.add_hotkey(".", self.cancel, args=(1,))
            keyboard.add_hotkey("/", self.finish, args=(1,))

        def click(self, partyId):  # 选择
            party = self.get_party_by_id(partyId)
            # 判断状态
            if party.state == Enum.party_state["unavailable"]:
                return
            elif party.state == Enum.party_state["move"]:  # 进入商店 / 进入炮台
                blockInfo = self.get_block(*party.aimPos)
                if self.is_in_legal_range(partyId) and blockInfo["name"] == "blank":  # 在合法范围内 且 选中为空白方块 -> 进入商店
                    self.enter_shop(party)
                elif blockInfo["name"] == "attacker" and blockInfo["belong"] == partyId:  # 选中为己方炮台方块 -> 进入炮台
                    self.enter_attacker(party)  # 要判断有无炮弹
            elif party.state == Enum.party_state["shop"]:  # 购买方块
                self.enter_buy(party)  # 要判断资金是否足够
            elif party.state == Enum.party_state["attack"]:  # 发射炮弹
                self.enter_attack(party)
            elif party.state == Enum.party_state["clear"]:  # 确认清除方块
                self.enter_clear(party)

        def cancel(self, partyId):  # 取消选择
            party = self.get_party_by_id(partyId)
            # 判断状态
            if party.state == Enum.party_state["unavailable"]:
                return
            elif party.state == Enum.party_state["move"]:  # 准备清除方块
                self.enter_try_clear(party)  # 要判断是否为空白方块
            elif party.state == Enum.party_state["shop"]:  # 退出商店
                self.exit_shop(party)
            elif party.state == Enum.party_state["attack"]:  # 退出炮台
                self.exit_attack(party)
            elif party.state == Enum.party_state["clear"]:  # 取消清除方块
                self.exit_clear(party)

        def finish(self, partyId):  # 跳过操作
            if partyId == 0:
                self.game.partyA.become_negative()
            elif partyId == 1:
                self.game.partyB.become_negative()

        def enter_shop(self, party):  # 进入商店
            party.set_state("shop")

        def enter_attacker(self, party):  # 进入炮台 要判断有无炮弹
            if self.get_block_obj(*party.aimPos).shell_num > 0:
                party.set_state("attack")

        def enter_buy(self, party):  # 购买方块 要判断资金是否足够
            blockType = self.get_blockType_by_shopPos(party)
            price = self.get_price(blockType)
            if party.money >= price:
                party.add_money(-price)
                self.place_block(*party.aimPos, party.index, blockType)
                party.set_state("move")

        def enter_attack(self, party):  # 发射炮弹
            self.get_block_obj(*party.current_attackerPos).shell_num -= 1
            self.shoot_shell(party)
            party.set_state("move")
            self.game.test_death()

        def enter_clear(self, party):  # 确认清除方块
            party.add_money(self.get_block(*party.aimPos)["duration"] // 2)
            self.destroy_block(party.aimPos)
            party.set_state("move")

        def enter_try_clear(self, party):  # 准备清除方块 要判断是否为空白方块 且 在合法范围内
            if self.is_in_legal_range(party.index) and self.get_block(*party.aimPos)["name"] != "blank":
                party.set_state("clear")

        def exit_shop(self, party):  # 退出商店
            party.set_state("move")

        def exit_attack(self, party):  # 退出炮台
            party.set_state("move")

        def exit_clear(self, party):  # 取消清除方块
            party.set_state("move")

        def move_aim(self, partyId, towards):  # 移动某队伍的选择光标，towards = "u" / "l" / "dirs" / "root"
            party = self.get_party_by_id(partyId)
            if party.state == Enum.party_state["unavailable"] or party.state == Enum.party_state["move"]:  # 战场移动
                if partyId == 0:
                    aim = self.aimA
                elif partyId == 1:
                    aim = self.aimB
                else:
                    return
                if towards == "u":
                    if party.aimPos[1] != 29:
                        self.cv.move(aim, 0, -20)
                        party.aimPos[1] += 1
                elif towards == "l":
                    if party.aimPos[0] != 0:
                        self.cv.move(aim, -20, 0)
                        party.aimPos[0] -= 1
                elif towards == "dirs":
                    if party.aimPos[1] != 0:
                        self.cv.move(aim, 0, 20)
                        party.aimPos[1] -= 1
                elif towards == "root":
                    if party.aimPos[0] != 29:
                        self.cv.move(aim, 20, 0)
                        party.aimPos[0] += 1
            elif party.state == Enum.party_state["shop"]:  # 商店移动
                if towards == "u":
                    if party.shopPos[0] != 0:
                        party.shopPos[0] -= 1
                        party.shopPos[1] = min(len(Enum.block[list(Enum.block.keys())[party.shopPos[0]]]) - 1, party.shopPos[1])
                        self.move_shop(partyId)
                elif towards == "l":
                    if party.shopPos[1] != 0:
                        party.shopPos[1] -= 1
                        self.move_shop(partyId)
                elif towards == "dirs":
                    if party.shopPos[0] != 3:
                        party.shopPos[0] += 1
                        party.shopPos[1] = min(len(Enum.block[list(Enum.block.keys())[party.shopPos[0]]]) - 1, party.shopPos[1])
                        self.move_shop(partyId)
                elif towards == "root":
                    if party.shopPos[1] < len(Enum.block[list(Enum.block.keys())[party.shopPos[0]]]) - 1:
                        party.shopPos[1] += 1
                        self.move_shop(partyId)
            elif party.state == Enum.party_state["attack"]:  # 炮台移动
                speed = Enum.block["engine"][self.get_near_highest_engine(*party.current_attackerPos)][3]
                if partyId == 0:
                    aim = self.aimA
                elif partyId == 1:
                    aim = self.aimB
                else:
                    return
                if towards == "u":
                    if party.aimPos[1] != 29 and self.get_distance_to_attacker((party.aimPos[0], party.aimPos[1] + 1), party) <= speed:
                        self.cv.move(aim, 0, -20)
                        party.aimPos[1] += 1
                        self.update_attacker_arrow(party)
                elif towards == "l":
                    if party.aimPos[0] != 0 and self.get_distance_to_attacker((party.aimPos[0] - 1, party.aimPos[1]), party) <= speed:
                        self.cv.move(aim, -20, 0)
                        party.aimPos[0] -= 1
                        self.update_attacker_arrow(party)
                elif towards == "dirs":
                    if party.aimPos[1] != 0 and self.get_distance_to_attacker((party.aimPos[0], party.aimPos[1] - 1), party) <= speed:
                        self.cv.move(aim, 0, 20)
                        party.aimPos[1] -= 1
                        self.update_attacker_arrow(party)
                elif towards == "root":
                    if party.aimPos[0] != 29 and self.get_distance_to_attacker((party.aimPos[0] + 1, party.aimPos[1]), party) <= speed:
                        self.cv.move(aim, 20, 0)
                        party.aimPos[0] += 1
                        self.update_attacker_arrow(party)

        def move_shop(self, partyId):  # 移动商店光标
            party = self.get_party_by_id(partyId)
            p = party.shopPos
            if partyId == 0:
                # 移动
                if p[0] == 0:  # 5
                    self.cv.itemconfig(self.descriptionA, text=Enum.description["brick"][p[1]])
                    if p[1] <= 1:
                        self.cv.moveto(self.shopAimA, 30 - 11 + p[1] * 40, 200 - 11)
                    else:
                        self.cv.moveto(self.shopAimA, 15 - 11 + (p[1] - 2) * 35, 240 - 11)
                elif p[0] == 1:  # 4
                    self.cv.itemconfig(self.descriptionA, text=Enum.description["factory"][p[1]])
                    self.cv.moveto(self.shopAimA, 30 - 11 + p[1] % 2 * 40, 310 - 11 + p[1] // 2 * 40)
                elif p[0] == 2:  # 5
                    self.cv.itemconfig(self.descriptionA, text=Enum.description["attacker"][p[1]])
                    if p[1] <= 1:
                        self.cv.moveto(self.shopAimA, 30 - 11 + p[1] * 40, 420 - 11)
                    else:
                        self.cv.moveto(self.shopAimA, 15 - 11 + (p[1] - 2) * 35, 460 - 11)
                elif p[0] == 3:  # 4
                    self.cv.itemconfig(self.descriptionA, text=Enum.description["engine"][p[1]])
                    self.cv.moveto(self.shopAimA, 30 - 11 + p[1] % 2 * 40, 530 - 11 + p[1] // 2 * 40)
            elif partyId == 1:
                # 移动
                if p[0] == 0:  # 5
                    self.cv.itemconfig(self.descriptionB, text=Enum.description["brick"][p[1]])
                    if p[1] <= 1:
                        self.cv.moveto(self.shopAimB, 730 - 11 + p[1] * 40, 200 - 11)
                    else:
                        self.cv.moveto(self.shopAimB, 715 - 11 + (p[1] - 2) * 35, 240 - 11)
                elif p[0] == 1:  # 4
                    self.cv.itemconfig(self.descriptionB, text=Enum.description["factory"][p[1]])
                    self.cv.moveto(self.shopAimB, 730 - 11 + p[1] % 2 * 40, 310 - 11 + p[1] // 2 * 40)
                elif p[0] == 2:  # 5
                    self.cv.itemconfig(self.descriptionB, text=Enum.description["attacker"][p[1]])
                    if p[1] <= 1:
                        self.cv.moveto(self.shopAimB, 730 - 11 + p[1] * 40, 420 - 11)
                    else:
                        self.cv.moveto(self.shopAimB, 715 - 11 + (p[1] - 2) * 35, 460 - 11)
                elif p[0] == 3:  # 4
                    self.cv.itemconfig(self.descriptionB, text=Enum.description["engine"][p[1]])
                    self.cv.moveto(self.shopAimB, 730 - 11 + p[1] % 2 * 40, 530 - 11 + p[1] // 2 * 40)

        def shoot_shell(self, party):  # 发射炮弹
            mass = Enum.block["attacker"][self.get_block(*party.current_attackerPos)["level"]][2]
            velocity = self.get_attacker_velocity(party)
            self.shell_obj.shoot(mass, velocity, party, True if self.get_near_highest_engine(*party.current_attackerPos) == 3 else False)

        def place_block(self, x, y, belong, blockType, duration=None):  # 放置方块 (默认耐久None为满耐久)
            self.blockGround[x][y].transform(belong, blockType, duration)
            name, level = blockType.split(":")
            if name == "factory":
                de = Enum.block["factory"][int(level)][2]
                self.get_party_by_id(belong).add_factory_efficiency(de)

        def get_block_obj(self, x, y):  # 获取方块对象
            if 0 <= x <= 29 and 0 <= y <= 29:
                return self.blockGround[x][y]

        def get_block(self, x, y):  # 获取方块 返回字典: {"name": (名称), "level": (等级), "duration": (耐久), "belong": (partyId)}
            if 0 <= x <= 29 and 0 <= y <= 29:
                blockObj = self.blockGround[x][y]
                return {
                    "name": blockObj.type,
                    "level": blockObj.level,
                    "duration": blockObj.duration,
                    "belong": blockObj.belong
                }
            else:
                return {
                    "name": "blank",
                    "level": 0,
                    "duration": -1,
                    "belong": None
                }

        def destroy_block(self, pos):  # 摧毁方块
            blockInfo = self.get_block(*pos)
            if blockInfo["name"] == "factory":
                de = Enum.block["factory"][blockInfo["level"]][2]
                self.get_party_by_id(blockInfo["belong"]).add_factory_efficiency(-de)
            self.place_block(*pos, None, "blank:0")

        def initial(self):  # 开始游戏画面渲染
            self.root = tk.Tk()
            self.root.geometry("800x700+200+50")
            self.root.title("军工战争")
            self.root.resizable(False, False)
            self.cv = tk.Canvas(self.root, width=800, height=700)
            self.cv.pack()

            # 贴图资源
            self.sky = tk.PhotoImage(file="res/sky.png")
            self.clear = tk.PhotoImage(file="res/clear.png")
            self.active_clear = tk.PhotoImage(file="res/active_clear.png")
            self.aim = tk.PhotoImage(file="res/aim.png")
            self.shell = tk.PhotoImage(file="res/shell.png")
            self.blank = None
            self.brick = tk.PhotoImage(file="res/brick.png")
            self.factory = [
                tk.PhotoImage(file="res/factory/0.png"),
                tk.PhotoImage(file="res/factory/1.png"),
                tk.PhotoImage(file="res/factory/2.png"),
                tk.PhotoImage(file="res/factory/3.png")
            ]
            self.attacker = [
                tk.PhotoImage(file="res/attacker/0.png"),
                tk.PhotoImage(file="res/attacker/1.png"),
                tk.PhotoImage(file="res/attacker/2.png"),
                tk.PhotoImage(file="res/attacker/3.png"),
                tk.PhotoImage(file="res/attacker/4.png")
            ]
            self.engine = [
                tk.PhotoImage(file="res/engine/0.png"),
                tk.PhotoImage(file="res/engine/1.png"),
                tk.PhotoImage(file="res/engine/2.png"),
                tk.PhotoImage(file="res/engine/3.png")
            ]

            # 渲染逻辑

            # 回合数
            self.round_title = self.cv.create_text(400, 25, text="第0回合", font=("Arial", 20))

            # 操作方标识
            self.active_player_title = self.cv.create_text(0, 0, text="操作方", fill="red", font=("Arial", 17))

            # 资金信息
            self.partyA_money_title = self.cv.create_text(50, 100, text="资金:")
            self.partyA_money = self.cv.create_text(50, 120, text="0")
            self.partyB_money_title = self.cv.create_text(750, 100, text="资金:")
            self.partyB_money = self.cv.create_text(750, 120, text="0")

            # 商店信息
            self.shopA_brick_title = self.cv.create_text(50, 180, text="砖块商店")
            self.shopA_brick = [
                self.cv.create_image(30, 200, image=self.brick),
                self.cv.create_text(30, 200, text=str(self.get_full_duration("brick:0"))),
                self.cv.create_text(30, 218, text=str(self.get_price("brick:0")), fill="#AACC00"),
                self.cv.create_image(70, 200, image=self.brick),
                self.cv.create_text(70, 200, text=str(self.get_full_duration("brick:1"))),
                self.cv.create_text(70, 218, text=str(self.get_price("brick:1")), fill="#AACC00"),
                self.cv.create_image(15, 240, image=self.brick),
                self.cv.create_text(15, 240, text=str(self.get_full_duration("brick:2"))),
                self.cv.create_text(15, 258, text=str(self.get_price("brick:2")), fill="#AACC00"),
                self.cv.create_image(50, 240, image=self.brick),
                self.cv.create_text(50, 240, text=str(self.get_full_duration("brick:3"))),
                self.cv.create_text(50, 258, text=str(self.get_price("brick:3")), fill="#AACC00"),
                self.cv.create_image(85, 240, image=self.brick),
                self.cv.create_text(85, 240, text=str(self.get_full_duration("brick:4"))),
                self.cv.create_text(85, 258, text=str(self.get_price("brick:4")), fill="#AACC00")
            ]
            self.shopA_factory_title = self.cv.create_text(50, 285, text="工厂商店")
            self.shopA_factory = [
                self.cv.create_image(30, 310, image=self.factory[0]),
                self.cv.create_text(30, 310, text=str(self.get_full_duration("factory:0"))),
                self.cv.create_text(30, 328, text=str(self.get_price("factory:0")), fill="#AACC00"),
                self.cv.create_image(70, 310, image=self.factory[1]),
                self.cv.create_text(70, 310, text=str(self.get_full_duration("factory:1"))),
                self.cv.create_text(70, 328, text=str(self.get_price("factory:1")), fill="#AACC00"),
                self.cv.create_image(30, 350, image=self.factory[2]),
                self.cv.create_text(30, 350, text=str(self.get_full_duration("factory:2"))),
                self.cv.create_text(30, 368, text=str(self.get_price("factory:2")), fill="#AACC00"),
                self.cv.create_image(70, 350, image=self.factory[3]),
                self.cv.create_text(70, 350, text=str(self.get_full_duration("factory:3"))),
                self.cv.create_text(70, 368, text=str(self.get_price("factory:3")), fill="#AACC00")
            ]
            self.shopA_attacker_title = self.cv.create_text(50, 395, text="炮台商店")
            self.shopA_attacker = [
                self.cv.create_image(30, 420, image=self.attacker[0]),
                self.cv.create_text(30, 420, text=str(self.get_full_duration("attacker:0"))),
                self.cv.create_text(30, 438, text=str(self.get_price("attacker:0")), fill="#AACC00"),
                self.cv.create_image(70, 420, image=self.attacker[1]),
                self.cv.create_text(70, 420, text=str(self.get_full_duration("attacker:1"))),
                self.cv.create_text(70, 438, text=str(self.get_price("attacker:1")), fill="#AACC00"),
                self.cv.create_image(15, 460, image=self.attacker[2]),
                self.cv.create_text(15, 460, text=str(self.get_full_duration("attacker:2"))),
                self.cv.create_text(15, 478, text=str(self.get_price("attacker:2")), fill="#AACC00"),
                self.cv.create_image(50, 460, image=self.attacker[3]),
                self.cv.create_text(50, 460, text=str(self.get_full_duration("attacker:3"))),
                self.cv.create_text(50, 478, text=str(self.get_price("attacker:3")), fill="#AACC00"),
                self.cv.create_image(85, 460, image=self.attacker[4]),
                self.cv.create_text(85, 460, text=str(self.get_full_duration("attacker:4"))),
                self.cv.create_text(85, 478, text=str(self.get_price("attacker:4")), fill="#AACC00")
            ]
            self.shopA_engine_title = self.cv.create_text(50, 505, text="引擎商店")
            self.shopA_engine = [
                self.cv.create_image(30, 530, image=self.engine[0]),
                self.cv.create_text(30, 530, text=str(self.get_full_duration("engine:0"))),
                self.cv.create_text(30, 548, text=str(self.get_price("engine:0")), fill="#AACC00"),
                self.cv.create_image(70, 530, image=self.engine[1]),
                self.cv.create_text(70, 530, text=str(self.get_full_duration("engine:1"))),
                self.cv.create_text(70, 548, text=str(self.get_price("engine:1")), fill="#AACC00"),
                self.cv.create_image(30, 570, image=self.engine[2]),
                self.cv.create_text(30, 570, text=str(self.get_full_duration("engine:2"))),
                self.cv.create_text(30, 588, text=str(self.get_price("engine:2")), fill="#AACC00"),
                self.cv.create_image(70, 570, image=self.engine[3]),
                self.cv.create_text(70, 570, text=str(self.get_full_duration("engine:3"))),
                self.cv.create_text(70, 588, text=str(self.get_price("engine:3")), fill="#AACC00")
            ]
            self.shopB_brick_title = self.cv.create_text(750, 180, text="砖块商店")
            self.shopB_brick = [
                self.cv.create_image(730, 200, image=self.brick),
                self.cv.create_text(730, 200, text=str(self.get_full_duration("brick:0"))),
                self.cv.create_text(730, 218, text=str(self.get_price("brick:0")), fill="#AACC00"),
                self.cv.create_image(770, 200, image=self.brick),
                self.cv.create_text(770, 200, text=str(self.get_full_duration("brick:1"))),
                self.cv.create_text(770, 218, text=str(self.get_price("brick:1")), fill="#AACC00"),
                self.cv.create_image(715, 240, image=self.brick),
                self.cv.create_text(715, 240, text=str(self.get_full_duration("brick:2"))),
                self.cv.create_text(715, 258, text=str(self.get_price("brick:2")), fill="#AACC00"),
                self.cv.create_image(750, 240, image=self.brick),
                self.cv.create_text(750, 240, text=str(self.get_full_duration("brick:3"))),
                self.cv.create_text(750, 258, text=str(self.get_price("brick:3")), fill="#AACC00"),
                self.cv.create_image(785, 240, image=self.brick),
                self.cv.create_text(785, 240, text=str(self.get_full_duration("brick:4"))),
                self.cv.create_text(785, 258, text=str(self.get_price("brick:4")), fill="#AACC00")
            ]
            self.shopB_factory_title = self.cv.create_text(750, 285, text="工厂商店")
            self.shopB_factory = [
                self.cv.create_image(730, 310, image=self.factory[0]),
                self.cv.create_text(730, 310, text=str(self.get_full_duration("factory:0"))),
                self.cv.create_text(730, 328, text=str(self.get_price("factory:0")), fill="#AACC00"),
                self.cv.create_image(770, 310, image=self.factory[1]),
                self.cv.create_text(770, 310, text=str(self.get_full_duration("factory:1"))),
                self.cv.create_text(770, 328, text=str(self.get_price("factory:1")), fill="#AACC00"),
                self.cv.create_image(730, 350, image=self.factory[2]),
                self.cv.create_text(730, 350, text=str(self.get_full_duration("factory:2"))),
                self.cv.create_text(730, 368, text=str(self.get_price("factory:2")), fill="#AACC00"),
                self.cv.create_image(770, 350, image=self.factory[3]),
                self.cv.create_text(770, 350, text=str(self.get_full_duration("factory:3"))),
                self.cv.create_text(770, 368, text=str(self.get_price("factory:3")), fill="#AACC00")
            ]
            self.shopB_attacker_title = self.cv.create_text(750, 395, text="炮台商店")
            self.shopB_attacker = [
                self.cv.create_image(730, 420, image=self.attacker[0]),
                self.cv.create_text(730, 420, text=str(self.get_full_duration("attacker:0"))),
                self.cv.create_text(730, 438, text=str(self.get_price("attacker:0")), fill="#AACC00"),
                self.cv.create_image(770, 420, image=self.attacker[1]),
                self.cv.create_text(770, 420, text=str(self.get_full_duration("attacker:1"))),
                self.cv.create_text(770, 438, text=str(self.get_price("attacker:1")), fill="#AACC00"),
                self.cv.create_image(715, 460, image=self.attacker[2]),
                self.cv.create_text(715, 460, text=str(self.get_full_duration("attacker:2"))),
                self.cv.create_text(715, 478, text=str(self.get_price("attacker:2")), fill="#AACC00"),
                self.cv.create_image(750, 460, image=self.attacker[3]),
                self.cv.create_text(750, 460, text=str(self.get_full_duration("attacker:3"))),
                self.cv.create_text(750, 478, text=str(self.get_price("attacker:3")), fill="#AACC00"),
                self.cv.create_image(785, 460, image=self.attacker[4]),
                self.cv.create_text(785, 460, text=str(self.get_full_duration("attacker:4"))),
                self.cv.create_text(785, 478, text=str(self.get_price("attacker:4")), fill="#AACC00")
            ]
            self.shopB_engine_title = self.cv.create_text(750, 505, text="引擎商店")
            self.shopB_engine = [
                self.cv.create_image(730, 530, image=self.engine[0]),
                self.cv.create_text(730, 530, text=str(self.get_full_duration("engine:0"))),
                self.cv.create_text(730, 548, text=str(self.get_price("engine:0")), fill="#AACC00"),
                self.cv.create_image(770, 530, image=self.engine[1]),
                self.cv.create_text(770, 530, text=str(self.get_full_duration("engine:1"))),
                self.cv.create_text(770, 548, text=str(self.get_price("engine:1")), fill="#AACC00"),
                self.cv.create_image(730, 570, image=self.engine[2]),
                self.cv.create_text(730, 570, text=str(self.get_full_duration("engine:2"))),
                self.cv.create_text(730, 588, text=str(self.get_price("engine:2")), fill="#AACC00"),
                self.cv.create_image(770, 570, image=self.engine[3]),
                self.cv.create_text(770, 570, text=str(self.get_full_duration("engine:3"))),
                self.cv.create_text(770, 588, text=str(self.get_price("engine:3")), fill="#AACC00")
            ]

            # 铲除工具
            self.clearA_title = self.cv.create_text(150, 660, text="铲除工具")
            self.clearA = self.cv.create_image(150, 680, image=self.clear)
            self.clearB_title = self.cv.create_text(650, 660, text="铲除工具")
            self.clearB = self.cv.create_image(650, 680, image=self.clear)

            # 商店描述信息
            self.descriptionA = self.cv.create_text(50, 650, text="描述信息", fill="grey", width=95, font=("Arial", 9))
            self.descriptionB = self.cv.create_text(750, 650, text="描述信息", fill="grey", width=95, font=("Arial", 9))

            # 天空图片
            self.skyBg = self.cv.create_image(400, 350, image=self.sky)

            # 方块网坐标系
            self.blockGround = [[self.Block(self, None, "blank:0", (x, y)) for y in range(30)] for x in range(30)]

            # 炮弹
            self.shell_obj = self.Shell(self)

            # 炮台箭头
            self.attacker_arrow = self.cv.create_line(0, 0, 0, 0, arrow="last", width=5, fill="orange")

            # 选择光标 (战场)
            self.aimA = self.cv.create_image(*self.analyze_pos(0, 0), image=self.aim)
            self.aimB = self.cv.create_image(*self.analyze_pos(29, 0), image=self.aim)

            # 选择光标 (商店)
            self.shopAimA = self.cv.create_image(0, 0, image=self.aim, state="hidden")
            self.shopAimB = self.cv.create_image(0, 0, image=self.aim, state="hidden")

            # 胜利图标
            self.winnerA = self.cv.create_text(400, 350, text="左方胜利!", fill="#FF3300", state="hidden", font=("Arial", 80))
            self.winnerB = self.cv.create_text(400, 350, text="右方胜利!", fill="#FF3300", state="hidden", font=("Arial", 80))

            # 运行
            self.root.mainloop()

    def __init__(self):
        self.times = 0
        self.ground = self.Ground(self)
        self.partyA = self.Party(self, 0, (0, 0))
        self.partyB = self.Party(self, 1, (29, 0))

        self.threadPool = []  # 线程池
        self.threadPool.append(threading.Thread(target=self.start_ground))
        self.threadPool[0].start()  # 游戏画面线程
        self.threadPool.append(threading.Thread(target=self.start))
        self.threadPool[1].start()  # 逻辑线程

    def start_ground(self):  # 游戏画面线程
        self.ground.initial()  # 开始渲染

    def start(self):
        sleep(0.2)
        self.partyA.add_money(Enum.initial_money)
        self.partyB.add_money(Enum.initial_money)

        # 自动搭建初始堡垒
        for x, y in Enum.initial_castle:
            self.ground.place_block(x, y, 0, "brick:0")
        for x, y in Enum.initial_castle:
            self.ground.place_block(29 - x, y, 1, "brick:0")

        while 1:
            self.times += 1
            self.ground.update_round_data(self.times)  # 更新回合信息

            self.partyA.become_active()
            self.partyA.add_money(Enum.natural_efficiency)
            self.partyA.factory()

            self.partyB.become_active()
            self.partyB.add_money(Enum.natural_efficiency)
            self.partyB.factory()

            self.ground.update_attacker()  # 更新炮台

    def test_death(self):
        is_live_A = False
        is_live_B = False
        for i in self.ground.blockGround:
            for block in i:
                if block.belong == 0:
                    is_live_A = True
                elif block.belong == 1:
                    is_live_B = True
        if not is_live_A:
            self.over(1)
        elif not is_live_B:
            self.over(0)

    def over(self, winner):
        self.ground.cv.itemconfig(self.ground.winnerA if winner == 0 else self.ground.winnerB, state="normal")
        print("游戏结束! 胜利方: " + "左方" if winner == 0 else "右方")
        sleep(3600)

game = Game()
