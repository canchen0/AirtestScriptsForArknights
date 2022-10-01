# -*- encoding=utf8 -*-
__author__ = "Administrator"

from airtest.core.api import *
import json

auto_setup(__file__)





# ----- 脚本运行模式 -----
# 肉鸽类型（仅单选） 支持：'傀影' '水月'
storyType = '水月'
# 当前使用机型（仅单选） 支持：'mumu1440x810' 'Mate40Pro异形屏0'
# mobileType = 'Mate40Pro异形屏0'
mobileType = 'mumu1440x810'
# 备选干员（可多选）支持以下几种('书山', '山', '皮山', '时装笔', '羽毛笔',) 注意：由于元组的特殊性，建议在每个干员名字后面都加一个逗号，避免只放一个干员名字的时候出现错误
useAgents = ('书山', '山', '皮山', '时装笔', '羽毛笔',)
# 是否开启关卡快速匹配模式，如果经常出现关卡匹配错误的情况，则把此项设置为False，这会提升关卡匹配的准确性，但会导致进入关卡前匹配关卡的时间变得很长
fastMatchStrategy = True
# 是否只进行助战招募，如果有大佬好友，且前面这些干员自己都没有或者都练度不够的情况下可以设置为True，这样就能直接进行助战招募而不会招募自己的干员
onlyAssist = False


# ----- 通用的一些操作 -----
# 竖屏时的高 x轴
try:
    height = G.DEVICE.display_info['height']
except:
    height = 1440
# 竖屏时的宽 y轴
try:
    width = G.DEVICE.display_info['width']
except:
    width = 810
# 计算出屏幕中心点 (x, y)
screenCenter = (height / 2, width / 2)

# 1秒内尝试点击一个图片，没有找到图片就不点击
def tryTouch(img):
    try:
        touch(wait(img,timeout=1))
    except:
        pass

# 从右向左滑动屏幕，使屏幕右侧的内容可以显示出来
def swipe2Right(startPosition):
    swipe(startPosition, vector=[-0.2,0])

# 如果目标图片存在，就一直点击该图片，直到该图片消失
def keepTouchIfExist(img):
    position = exists(img)
    while position:
        touch(position)
        sleep(1.5)
        position = exists(img)

# ----- 基础类型 -----
# -- 干员类型模板 --
# 基础干员模板
class Agent:
    '基础干员-只是一个模板啦-不要直接使用ta'

    # 构造函数
    # 干员名称, 招募界面角色标识图, 助战招募界面角色标识图, 立绘标识图, 进队标识图, 进队候选标识图, 选用的技能的标识图, 等待费用的时间(正常情况约0.5秒回1费), 干员在等待上场时的标识, 释放技能时的技能图标
    def __init__(self, agentName, enlistMark, borrowMark, portrait, inTeam, touch2Team, selectSkillMark, wait4Cost, wait4EnterMark, skillMark4Release):
        self.agentName = agentName
        self.enlistMark = enlistMark
        self.borrowMark = borrowMark
        self.portrait = portrait
        self.inTeam = inTeam
        self.touch2Team = touch2Team
        self.selectSkillMark = selectSkillMark
        self.wait4Cost = wait4Cost
        self.wait4EnterMark = wait4EnterMark
        self.skillMark4Release = skillMark4Release

    # 获取干员名称
    def getName(self):
        return self.agentName

    # 是否可以招募
    def canEnlist(self):
        return exists(self.enlistMark)
    
    # 是否可以助战招募
    def canBorrow(self):
        return exists(self.borrowMark)

    # 响应招募
    def answer(self):
        touch(self.enlistMark)
        sleep(1.0)
        touch(Template(r"tpl1654876633543.png", record_pos=(0.42, 0.204), resolution=(2376, 1152)))
        sleep(3.0)
    
    # 结束立绘展示，如果当前干员的立绘一直检测失败，则表示可能招错了人，需要进行纠正
    def showDown(self):
        showDownCheckCount = 0
        # 判断画面是否在那个招到了干员的立绘画面
        while not exists(self.portrait):
            if showDownCheckCount >= 10:
                return False
            sleep(1.0)
            showDownCheckCount = showDownCheckCount + 1
        # 点击立绘进入下一步
        touch(self.portrait)
        sleep(1.0)
        return True
        
    # 是否已经在队伍中
    def isInTeam(self):
        return exists(self.inTeam)
    
    # 变更技能
    def changeSkill(self, skillMenuPosition):
        if self.selectSkillMark is None:
            return
        if not exists(self.selectSkillMark):
            swipe(skillMenuPosition, vector=[0, 0.3])
        touch(self.selectSkillMark)
        sleep(0.5)

    # 加入队伍准备上场
    def joinTheTeam(self, skillMenuPosition):
        touch(self.touch2Team)
        sleep(0.5)
        self.changeSkill(skillMenuPosition)
        touch(Template(r"tpl1653448656197.png", record_pos=(0.42, 0.204), resolution=(2376, 1152)))

    # 干员上场作战
    def enter(self, targetPositions):
        if self.wait4Cost:
            sleep(self.wait4Cost)
        # 如果没有识别到待上场的干员的坐标，则循环多次检测
        positionInTeam = exists(self.wait4EnterMark)
        while not positionInTeam:
            sleep(0.5)
            positionInTeam = exists(self.wait4EnterMark)
        # 下次更新需要在此处加一个干员上场失败的判断，判断的方式是检测场上是否存在干员的小人
        swipe(positionInTeam, targetPositions['干员上场位置'], duration = 1.5)
        sleep(0.5)
        swipe(targetPositions['干员上场位置'], targetPositions['干员朝向位置'], duration = 0.5)

    # 基础干员默认不需要开技能
    def releaseSkill(self, agentPosition):
        return

# 上场后需要开技能的干员
class NeedOpenSkillAgent(Agent):
    '上场后需要手动开一次技能的干员'

    # 重写开技能的逻辑
    def releaseSkill(self, agentPosition):
        sleep_time = 0
        while not exists(Template(r"tpl1653728387510.png", record_pos=(-0.169, -0.135), resolution=(2376, 1152))):
            # 等待技能时间最长不超过3分钟，否则退出技能释放判定，避免干员在开技能之前就挂掉后导致脚本卡住
            if sleep_time >= 180:
                return
            sleep(1)
            sleep_time = sleep_time + 1
        touch(agentPosition)
        sleep(1)
        touch(self.skillMark4Release)

# -- 关卡攻略类型模板 --
# 基础关卡攻略模板
class Strategy:
    '基础攻略-只是一个模板啦-不要直接使用ta'

    targetType = '基础'

    # 构造函数
    # 攻略对应关卡名称, 攻略对应关卡标识图
    def __init__(self, targetName, targetMark):
        self.targetName = targetName
        self.targetMark = targetMark

    # 判断是否是对应关卡的攻略
    def itsMyTime(self):
        return exists(self.targetMark)
    
    # 这个攻略对应的关卡的类型
    def getTargetType(self):
        return Strategy.targetType

    # 攻略对应的关卡名称
    def getTargetName(self):
        return self.targetName

    # 攻略关卡
    # 参与攻略的干员, 基础性坐标信息, 关卡特定坐标信息
    def challenge(self, agent, basePositions, targetPositions):
        print('我只是个空白的攻略，不知道该干啥，要不我假装给你唱首歌吧，ヾ(´〇｀)ﾉ♪♪♪')
        sleep(120)
        return False
    
    # 是否是最后的关底攻略
    def isLastTargetStrategy(self):
        return False

# 战斗关卡攻略模板
class BattleStrategy(Strategy):
    '战斗类型关卡的攻略'

    targetType = '战斗'

    # 这个攻略对应的关卡的类型
    def getTargetType(self):
        return BattleStrategy.targetType

    # 攻略关卡
    # 参与攻略的干员, 基础性坐标信息, 关卡特定坐标信息
    def challenge(self, agent, basePositions, targetPositions):
        touch(Template(r"tpl1653800722713.png", record_pos=(0.415, 0.08), resolution=(2376, 1152)))
        sleep(1.0)
        touch(Template(r"tpl1641988492692.png", record_pos=(0.322, 0.242), resolution=(1440, 810)))
        while not exists(Template(r"tpl1646226625337.png", threshold=0.9000000000000001, record_pos=(0.044, -0.258), resolution=(1440, 810))):
            sleep(1)  
        sleep(2)
        touch(Template(r"tpl1646126432694.png", threshold=0.9000000000000001, record_pos=(0.362, -0.25), resolution=(1440, 810)))
        sleep(0.5)
        agent.enter(targetPositions)
        agent.releaseSkill(targetPositions['干员站场位置'])
        sleep(75)
        success = self.battleResult()
        if success:
            self.processPass(basePositions)
        else:
            self.processFail()
        return success

    # 获取挑战结果
    def battleResult(self):
        # 检查过关标记
        while not exists(Template(r"tpl1641989217172.png", record_pos=(-0.366, 0.15), resolution=(1440, 810))):
            # 检查失败标记
            if exists(Template(r"tpl1653546770088.png", record_pos=(-0.096, -0.028), resolution=(2376, 1152))):
                sleep(1)
                # 二次确认
                if exists(Template(r"tpl1653546770088.png", record_pos=(-0.096, -0.028), resolution=(2376, 1152))):
                    return False
            sleep(4.0)
        return True

    # 处理挑战成功后的战斗结算
    def processPass(self, basePositions):
        sleep(4.0)
        # 识别到了点击一下
        while exists(Template(r"tpl1641989217172.png", record_pos=(-0.366, 0.15), resolution=(1440, 810))):
            touch(screenCenter)
            sleep(1)
        sleep(1.0)
        
        
        while exists(Template(r"tpl1653115016616.png", record_pos=(-0.354, 0.015), resolution=(2242, 1080))):
            touch(basePositions['关卡奖励列表的第一个接受按钮'])
            sleep(1.5)
        while exists(Template(r"tpl1653449660653.png", record_pos=(-0.395, 0.12), resolution=(2376, 1152))):
            touch(basePositions['关卡奖励列表的第一个接受按钮'])
            sleep(1.5)
        # 判断是否进入到剧目
        keepTouchIfExist(Template(r"tpl1658591469967.png", record_pos=(-0.001, 0.23), resolution=(1440, 810)))
        # 不小心进到干员选择界面时，退出干员选择界面
        while exists(Template(r"tpl1658588032413.png", record_pos=(0.405, 0.246), resolution=(1440, 810))):
            sleep(1)
            abandonRecruitment()
        keepTouchIfExist(Template(r"tpl1658591561918.png", record_pos=(-0.001, 0.056), resolution=(1440, 810)))
        while not exists(Template(r"tpl1641989331329.png", record_pos=(0.296, 0.07), resolution=(1440, 810))):#判断有没有这个图片
            swipe2Right(basePositions['右滑屏幕起始点'])#判断没有，就自右往左滑动屏幕，移到右边，移完回去继续判断图片
        else:
            touch(Template(r"tpl1641989331329.png", record_pos=(0.296, 0.07), resolution=(1440, 810)))#判断到了就点它
        sleep(0.5)
        touch(Template(r"tpl1641989346223.png", record_pos=(0.339, 0.147), resolution=(1440, 810)))
        sleep(1.5)
    
    # 处理挑战失败的情况
    def processFail(self):
        touch(Template(r"tpl1653546790468.png", record_pos=(-0.001, 0.162), resolution=(2376, 1152)))

# 事件关卡攻略模板
class EventStrategy(Strategy):
    '事件类型关卡攻略'

    targetType = '事件'

    # 这个攻略对应的关卡的类型
    def getTargetType(self):
        return EventStrategy.targetType

    # 攻略关卡
    # 参与攻略的干员, 基础性坐标信息, 关卡特定坐标信息
    def challenge(self, agent, basePositions, targetPositions):
        touch(Template(r"tpl1641987478502.png", record_pos=(0.395, 0.096), resolution=(1440, 810)))
        sleep(4.0)
        touch(screenCenter)
        sleep(3.0)
        # 这里是针对不期而遇里有三个选项的情况进行确认。
        if exists(Template(r"tpl1642038786944.png", record_pos=(0.435, 0.071), resolution=(1440, 810))):
            touch(Template(r"tpl1642038786944.png", record_pos=(0.435, 0.071), resolution=(1440, 810)))
        else:
            touch(targetPositions['能点到一个或两个选项中最下面的选项的位置'])
        sleep(2.0)
        tryTouch(Template(r"tpl1646274575137.png", threshold=0.9000000000000001, record_pos=(0.435, 0.205), resolution=(1440, 810)))
        sleep(4.0)
        touch(Template(r"tpl1641987578489.png", record_pos=(0.0, 0.232), resolution=(1440, 810)))
        sleep(3.0)
        return True

# 商店关卡攻略模板
class StoreStrategy(Strategy):
    '商店类型关卡攻略'

    targetType = '商店'

    # 这个攻略对应的关卡的类型
    def getTargetType(self):
        return StoreStrategy.targetType

    # 攻略关卡
    # 参与攻略的干员, 基础性坐标信息, 关卡特定坐标信息
    def challenge(self, agent, basePositions, targetPositions):
        sleep(1.0)
        touch(Template(r"tpl1653121619235.png", record_pos=(0.414, 0.082), resolution=(2242, 1080)))
        sleep(1.0)
        # 不可以投资时直接离开
        if not self.bankingSystemExist() or self.accountFull():
#         if not self.bankingSystemExist():
            self.exitStore()
            return True
        self.openBankingSystem()
        self.ready2Investment()
        for i in range(5):
            if self.bankingSystemError() or self.accountFullNeedStopInvestment():
                break
            self.determineInvestment()
        self.closeBankingSystem()
        self.exitStore()
        return True

    # 存在投资系统入口
    def bankingSystemExist(self):
        return exists(Template(r"tpl1641989654147.png", threshold=0.9000000000000001, record_pos=(-0.105, -0.19), resolution=(1440, 810)))
    
    # 打开投资系统
    def openBankingSystem(self):
        touch(Template(r"tpl1641989721200.png", threshold=0.9000000000000001, record_pos=(-0.103, -0.19), resolution=(1440, 810)))
        sleep(0.5)
    
    # 准备投资
    def ready2Investment(self):
        touch(Template(r"tpl1641989745261.png", record_pos=(-0.074, -0.037), resolution=(1440, 810)))
        sleep(0.5)

    # 进行投资
    def determineInvestment(self):
        touch(Template(r"tpl1653449867881.png", record_pos=(0.222, 0.086), resolution=(2376, 1152)), times=40)

    # 投资账户已满
    def accountFull(self):
        return exists(Template(r"tpl1654878339979.png", record_pos=(-0.074, -0.069), resolution=(2376, 1152)))
    
    # 投资账户已满，停止投资
    def accountFullNeedStopInvestment(self):
        return exists(Template(r"tpl1653811751848.png", record_pos=(0.222, 0.004), resolution=(2376, 1152)))
    
    # 投资系统崩溃
    def bankingSystemError(self):
        return exists(Template(r"tpl1641989989616.png", threshold=0.9000000000000001, record_pos=(0.113, -0.04), resolution=(1440, 810)))

    # 关闭投资系统
    def closeBankingSystem(self):
        tryTouch(Template(r"tpl1649060484359.png", threshold=0.9000000000000001, record_pos=(-0.013, 0.104), resolution=(1440, 810)))
        sleep(2.0)
        tryTouch(Template(r"tpl1649060484359.png", threshold=0.9000000000000001, record_pos=(-0.013, 0.104), resolution=(1440, 810)))
        sleep(1.0)

    # 退出商店
    def exitStore(self):
        tryTouch(Template(r"tpl1649060580969.png", threshold=0.9000000000000001, record_pos=(0.452, 0.145), resolution=(1440, 810)))
        tryTouch(Template(r"tpl1649060602062.png", threshold=0.9000000000000001, record_pos=(0.426, 0.145), resolution=(1440, 810)))
        sleep(5.0)
    
    # 是否是最后的关底攻略
    def isLastTargetStrategy(self):
        return True


# ----- 刷取过程的一些关键步骤 -----

# 确认进行探索
def confirmExploration(basePositions):
    touch(Template(r"tpl1646224294375.png", threshold=0.9000000000000001, record_pos=(0.405, 0.191), resolution=(1440, 810)))
    sleep(1.5)

# 进入古堡前的准备
def prepareEnterCastle(agents, basePositions):
    # 灾厄难度会提供初始藏品
    acceptInitCollection()
    chooseHow2Explore(basePositions)
    agent = chooseSaberAgent(agents, basePositions['右滑屏幕起始点'])
    # 没有招募到干员时，直接退出
    if not agent:
        return False
    notEnlistOtherAgents()
    return agent

# 接受初始藏品
def acceptInitCollection():
    tryTouch(Template(r"tpl1653448196391.png", record_pos=(-0.002, 0.189), resolution=(2376, 1152)))
    sleep(1.5)

# 选择探索策略
def chooseHow2Explore(basePositions):
    while not exists(Template(r"tpl1641990883595.png", threshold=0.9000000000000001, record_pos=(0.203, 0.063), resolution=(1440, 810))):
        #精二高级的山比较稳定过关，所以选了这个分队'''
        swipe2Right(basePositions['右滑屏幕起始点'])
    else:
        while exists(Template(r"tpl1641990883595.png", threshold=0.9000000000000001, record_pos=(0.203, 0.063), resolution=(1440, 810))):
            tryTouch(Template(r"tpl1641990883595.png", threshold=0.9000000000000001, record_pos=(0.203, 0.063), resolution=(1440, 810)))
            #有需要的就把这两个突击战术分队的图片换成自己想要的分队吧，用左侧Airtest辅助窗里的功能就可以截图生成自己的代码了。'''
            sleep(1.0)
            tryTouch(Template(r"tpl1641991004571.png", record_pos=(0.287, 0.182), resolution=(1440, 810)))
            sleep(1.0)
    sleep(1.0)
    touch(Template(r"tpl1641991034647.png", threshold=0.9000000000000001, record_pos=(0.11, 0.062), resolution=(1440, 810)))
    sleep(1.0)
    touch(Template(r"tpl1641991004571.png", record_pos=(0.287, 0.182), resolution=(1440, 810)))
    sleep(2.0)

# 选择进行探索的近卫干员
def chooseSaberAgent(agents, swipeAgentListStartPosition):
    #点击近卫招募券
    touch(Template(r"tpl1653112240088.png", record_pos=(-0.175, 0.012), resolution=(2242, 1080)))
    sleep(1.0)
    # 自己没有干员的情况下，直接进行助战招募
    if onlyAssist:
        agent = tryEnlistAgentFromMogul(agents, swipeAgentListStartPosition)
    # 自己有干员的情况下
    else:
        agent = tryEnlistAgent(agents, swipeAgentListStartPosition)
        if not agent:
            agent = tryEnlistAgentFromMogul(agents, swipeAgentListStartPosition)
    return agent

# 从期望的干员中挑选一个可以实际招募到的干员
def tryEnlistAgent(agents, swipeAgentListStartPosition):
    # 最多滑动10次
    for i in range(10):
        for agent in agents:
            if not agent.canEnlist():
                continue
            agent.answer()
            isShowDown = agent.showDown()
            # 立绘检测失败可能是招错了干员，判断错招的干员是否在支持列表中
            if not isShowDown:
                for reCheckAgent in agents:
                    isShowDown = reCheckAgent.showDown()
                    if isShowDown:
                        agent = reCheckAgent
                    continue
            # 不在支持列表中，直接返回招募失败，重开一局
            if not isShowDown:
                touch(screenCenter)
                sleep(1)
                return False
            return agent
        # 滑动界面，继续检查能否找到目标干员
        swipe2Right(swipeAgentListStartPosition)

# 尝试从大佬那儿借一个干员
def tryEnlistAgentFromMogul(agents, swipeAgentListStartPosition):
    touch(Template(r"tpl1653815759246.png", record_pos=(0.395, -0.212), resolution=(2376, 1152)))
    sleep(2)
    # 最多刷新10次
    for i in range(10):
        for agent in agents:
            # 两次循环处理干员的助战按钮在屏幕外的情况
            for j in range(2):
                # 尝试读取想要借用的助战干员所在位置
                agentPosition = agent.canBorrow()
                if not agentPosition:
                    break
                touch(agentPosition)
                # 判断是否进入到招募助战页
                if exists(Template(r"tpl1658585243605.png", record_pos=(0.156, 0.124), resolution=(1440, 810))):
                    # 点击招募助战按钮
                    touch(Template(r"tpl1658585243605.png", record_pos=(0.156, 0.124), resolution=(1440, 810)))
                    sleep(2)
                    isShowDown = agent.showDown()
                    # 立绘检测失败可能是招错了干员，判断错招的干员是否在支持列表中
                    if not isShowDown:
                        for reCheckAgent in agents:
                            isShowDown = reCheckAgent.showDown()
                            if isShowDown:
                                agent = reCheckAgent
                            continue
                    # 不在支持列表中，直接返回招募失败，重开一局
                    if not isShowDown:
                        touch(screenCenter)
                        sleep(1)
                        return False
                    return agent
                # 如果不使用continue进入下一轮循环，会导致swipe2Right被认为是k这个循环内的代码（很奇怪为啥会这样），而被不合时宜的执行
                else:
                    continue
                
                # 没点到助战按钮，说明按钮在屏幕外边
                swipe2Right(swipeAgentListStartPosition)
                continue
            continue
        while not exists(Template(r"tpl1658585376428.png", record_pos=(0.437, -0.257), resolution=(1440, 810))):
            sleep(1)
        touch(Template(r"tpl1658585376428.png", record_pos=(0.437, -0.257), resolution=(1440, 810)))
        
# 不招募其他干员
def notEnlistOtherAgents():
    for i in range(2):  
        touch(Template(r"tpl1646060523902.png", threshold=0.9000000000000001, record_pos=(-0.001, 0.145), resolution=(1440, 810)))
        sleep(1)
        abandonRecruitment()

# 放弃招募
def abandonRecruitment():
    touch(Template(r"tpl1646271295365.png", threshold=0.9000000000000001, record_pos=(0.277, 0.247), resolution=(1440, 810)))
    sleep(0.5)
    touch(Template(r"tpl1646271313530.png", threshold=0.9000000000000001, record_pos=(0.157, 0.106), resolution=(1440, 810)))
    sleep(1.0)
        
# 确认进入古堡
def confirmEnterCastle():
    touch(Template(r"tpl1641991718574.png", record_pos=(0.441, -0.006), resolution=(1440, 810)))
    sleep(5.0)

# 编队
def organizeIntoTeams(agent, basePositions):
    touch(Template(r"tpl1653795040229.png", record_pos=(0.384, 0.204), resolution=(2376, 1152)))
    sleep(1)
    if not agent.isInTeam():
        touch(basePositions['第一个加人入队按钮'])
        sleep(0.5)
        agent.joinTheTeam(basePositions['待入队干员技能选择栏坐标'])
    while exists(Template(r"tpl1653796258656.png", record_pos=(-0.455, -0.21), resolution=(2376, 1152))):
        touch(Template(r"tpl1653796258656.png", record_pos=(-0.455, -0.21), resolution=(2376, 1152)))
        sleep(1)

# 选择要攻略的关卡
def chooseLevel(levelButtonPositions):
    for position in levelButtonPositions:
        touch(position)

# 查找闯关攻略
def findStrategy():
    # 由于airtest的图片识别偶尔抽风，所以增加二次确认
    reCheckList = []
    for strategy in strategies:
        if not strategy.itsMyTime():
            continue
        if fastMatchStrategy:
            return strategy
        reCheckList.append(strategy)
    if len(reCheckList) == 1:
        return reCheckList[0]
    for strategy in reCheckList:
        if not strategy.itsMyTime():
            continue
        return strategy

# 尝试攻略关卡
def tryChallenge(strategy, agent, mobilePositionConfig):
    targetPositions = None
    targetType = strategy.getTargetType()
    if targetType == BattleStrategy.targetType:
        targetPositions = mobilePositionConfig[strategy.getTargetName()]
    elif targetType == EventStrategy.targetType:
        targetPositions = mobilePositionConfig[EventStrategy.targetType]
    return strategy.challenge(agent, mobilePositionConfig['基础位置配置'], targetPositions)

# 退出本轮探索
def exitExploration(basePositions):
    while not exists(Template(r"tpl1653449983336.png", record_pos=(-0.472, -0.211), resolution=(2376, 1152))):
        sleep(1)
    touch(Template(r"tpl1653449983336.png", record_pos=(-0.472, -0.211), resolution=(2376, 1152)))
    while not exists(Template(r"tpl1641990570636.png", record_pos=(0.412, -0.018), resolution=(1440, 810))):
        touch(screenCenter)
        sleep(1.0)
    keepTouchIfExist(Template(r"tpl1641990570636.png", record_pos=(0.412, -0.018), resolution=(1440, 810)))
    while not exists(Template(r"tpl1641990587770.png", record_pos=(0.159, 0.106), resolution=(1440, 810))):
        sleep(1.0)
    touch(Template(r"tpl1641990587770.png", record_pos=(0.159, 0.106), resolution=(1440, 810)))

# 结算探索收益
def settlementExplorationIncome():
    sleep(3.0)
    while not exists(Template(r"tpl1653122893867.png", record_pos=(0.461, -0.001), resolution=(2242, 1080))):
        sleep(1)
    tryTouch(Template(r"tpl1653122893867.png", record_pos=(0.461, -0.001), resolution=(2242, 1080)))
    sleep(6.0)
    while not exists(Template(r"tpl1653122941343.png", record_pos=(0.02, 0.192), resolution=(2242, 1080))):
        tryTouch(Template(r"tpl1653122893867.png", record_pos=(0.461, -0.001), resolution=(2242, 1080)))
        sleep(6.0)
    while exists(Template(r"tpl1654246321136.png", record_pos=(-0.0, 0.186), resolution=(2376, 1152))):
        tryTouch(Template(r"tpl1654246321136.png", record_pos=(-0.0, 0.186), resolution=(2376, 1152)))
        sleep(1.0)
    sleep(3.0)
    while exists(Template(r"tpl1646104849842.png", threshold=0.9000000000000001, record_pos=(0.001, -0.204), resolution=(1440, 810))):
        tryTouch(Template(r"tpl1646104849842.png", threshold=0.9000000000000001, record_pos=(0.001, -0.204), resolution=(1440, 810)))
        sleep(1.0)
    sleep(1.0)
    while exists(Template(r"tpl1653450900687.png", record_pos=(0.423, 0.158), resolution=(2376, 1152))):
        sleep(60)
    while not exists(Template(r"tpl1646224294375.png", threshold=0.9000000000000001, record_pos=(0.405, 0.191), resolution=(1440, 810))):
        touch(screenCenter)
        sleep(1)

# ----- 脚本运行配置 -----

# 当前脚本支持的手机设备的坐标配置信息集
supportMobilePositionConfigs = {
    'Mate40Pro异形屏0': {
        '基础位置配置': {
            '右滑屏幕起始点': (1150,500),
            '关卡奖励列表的第一个接受按钮': (255,860),
            '第一个加人入队按钮': (535,260),
            '待入队干员技能选择栏坐标': (250,830)
        },
        '关卡按钮的可能位置':[
            (800,530),
            (1525,420),
            (1525,630),
            (1525,530),
            (1525,315),
            (1525,735),
            (1525,210),
            (1525,835),
        ],
        '礼炮小队': {
            '干员上场位置': (990,570),
            '干员朝向位置': (1160,550),
            '干员站场位置': (830,520)
        },
        '与虫为伴': {
            '干员上场位置': (1130,600),
            '干员朝向位置': (930,600),
            '干员站场位置': (985,590)
        },
        '意外': {
            '干员上场位置': (1314,540),
            '干员朝向位置': (1140,540),
            '干员站场位置': (1185,525)
        },
        '驯兽小屋': {
            '干员上场位置': (1820,580),
            '干员朝向位置': (2100,580),
            '干员站场位置': (1700,600)
        },
        '死斗': {
            '干员上场位置': (865,835),
            '干员朝向位置': (865,450),
            '干员站场位置': (620,835)
        },
        '事件': {
            '能点到一个或两个选项中最下面的选项的位置': (1900,620),
        }
    },
    'mumu1440x810': {
        '通用配置':{
            '基础位置配置': {
                '右滑屏幕起始点': (670,500),
                '关卡奖励列表的第一个接受按钮': (185,620),
                '第一个加人入队按钮': (250,190),
                '待入队干员技能选择栏坐标': (200,600)
            },
            '事件': {
                '能点到一个或两个选项中最下面的选项的位置': (1190,460),
            },
        },
        '非通用配置': {
            '傀影':{
                '关卡按钮的可能位置':[
                    (440,370),
                    (880,290),
                    (880,440),
                    (880,370),
                    (880,210),
                    (880,510),
                    (880,140),
                    (880,590),
                ],
                '礼炮小队': {
                    '干员上场位置': (575,386),
                    '干员朝向位置': (1380,400),
                    '干员站场位置': (455,364)
                },
                '与虫为伴': {
                    '干员上场位置': (667,432),
                    '干员朝向位置': (380,400),
                    '干员站场位置': (575,411)
                },
                '意外': {
                    '干员上场位置': (806,370),
                    '干员朝向位置': (380,400),
                    '干员站场位置': (715,363)
                },
                '驯兽小屋': {
                    '干员上场位置': (1180,400),
                    '干员朝向位置': (1400,400),
                    '干员站场位置': (1100,410)
                },
                '死斗': {
                    '干员上场位置': (480,600),
                    '干员朝向位置': (480,200),
                    '干员站场位置': (305,600)
                },
            },
            '水月': {
                '关卡按钮的可能位置':[
                    (540,370),
                    (980,290),
                    (980,300),
                    (980,300),
                    (980,365),
                    (980,365),
                    (980,365),
                    (980,365),
                ],
                '射手部队': {
                    '干员上场位置': (1148,328),
                    '干员朝向位置': (941,341),
                    '干员站场位置': (1070,357)
                },
                '虫群横行': {
                    '干员上场位置': (1171,425),
                    '干员朝向位置': (938,445),
                    '干员站场位置': (1089,460)
                },
                '共生': {
                    '干员上场位置': (820,448),
                    '干员朝向位置': (806,262),
                    '干员站场位置': (718,456)
                },
                '蓄水池': {
                    '干员上场位置': (1077,501),
                    '干员朝向位置': (836,521),
                    '干员站场位置': (998,541)
                },
            }
        }
    }
}

# 当前脚本支持的干员的列表
# 格式：
# 干员名称: 干员信息
# 干员信息格式：干员名称, 招募界面角色标识图, 助战招募界面角色标识图, 立绘标识图, 进队标识图, 进队候选标识图, 选用的技能的标识图, 等待费用的时间(正常情况约0.5秒回1费), 干员在等待上场时的标识, 释放技能时的技能图标
scriptSupportAgents = {
    '书山': NeedOpenSkillAgent(
        '山', Template(r"tpl1662650693135.png", record_pos=(-0.149, -0.052), resolution=(2376, 1152)), Template(r"tpl1662650775079.png", record_pos=(0.152, 0.001), resolution=(2376, 1152)), Template(r"tpl1662650799826.png", record_pos=(0.061, -0.114), resolution=(2376, 1152)), Template(r"tpl1662650914025.png", record_pos=(-0.261, -0.125), resolution=(2376, 1152)), Template(r"tpl1662650888953.png", record_pos=(-0.149, -0.144), resolution=(2376, 1152)), Template(r"tpl1653448639620.png", record_pos=(-0.464, 0.141), resolution=(2376, 1152)), 0, Template(r"tpl1662650952970.png", record_pos=(0.463, 0.191), resolution=(2376, 1152)), Template(r"tpl1653804899756.png", record_pos=(0.121, 0.025), resolution=(2376, 1152))
    ),
    '皮山': NeedOpenSkillAgent(
        '山', Template(r"tpl1654876740282.png", record_pos=(-0.149, 0.035), resolution=(2376, 1152)), Template(r"tpl1654877639494.png", record_pos=(-0.013, 0.009), resolution=(2376, 1152)), Template(r"tpl1654876084914.png", record_pos=(-0.106, 0.002), resolution=(2376, 1152)), Template(r"tpl1653114218333.png", record_pos=(-0.249, -0.124), resolution=(2242, 1080)), Template(r"tpl1649332188667.png", record_pos=(0.457, 0.237), resolution=(1440, 810)), Template(r"tpl1653448639620.png", record_pos=(-0.464, 0.141), resolution=(2376, 1152)), 0, Template(r"tpl1653810245161.png", record_pos=(-0.225, 0.193), resolution=(2376, 1152)), Template(r"tpl1653804899756.png", record_pos=(0.121, 0.025), resolution=(2376, 1152))
    ),
    '山': NeedOpenSkillAgent(
        '山', Template(r"tpl1654877593706.png", record_pos=(-0.15, 0.034), resolution=(2376, 1152)), Template(r"tpl1654877617731.png", record_pos=(-0.206, 0.003), resolution=(2376, 1152)), Template(r"tpl1654180427509.png", record_pos=(0.028, -0.119), resolution=(2376, 1152)), Template(r"tpl1654180517936.png", record_pos=(-0.257, -0.116), resolution=(2376, 1152)), Template(r"tpl1654180552783.png", record_pos=(-0.147, -0.143), resolution=(2376, 1152)), Template(r"tpl1653448639620.png", record_pos=(-0.464, 0.141), resolution=(2376, 1152)), 0, Template(r"tpl1654180691569.png", record_pos=(0.466, 0.196), resolution=(2376, 1152)), Template(r"tpl1653804899756.png", record_pos=(0.121, 0.025), resolution=(2376, 1152))
    ),
    '羽毛笔': Agent(
        '羽毛笔', Template(r"tpl1654876856644.png", record_pos=(0.354, 0.126), resolution=(2376, 1152)), Template(r"tpl1654881100153.png", record_pos=(0.33, 0.0), resolution=(2376, 1152)), Template(r"tpl1653668752866.png", record_pos=(-0.023, 0.127), resolution=(2376, 1152)), Template(r"tpl1653727095461.png", record_pos=(-0.26, -0.117), resolution=(2376, 1152)), Template(r"tpl1653668896069.png", record_pos=(-0.118, -0.138), resolution=(2376, 1152)), None, 5, Template(r"tpl1653810270867.png", record_pos=(0.083, 0.194), resolution=(2376, 1152)), None
    ),
    '时装笔': Agent(
        '羽毛笔', Template(r"tpl1661003927437.png", record_pos=(0.053, -0.138), resolution=(2376, 1152)), Template(r"tpl1661003987591.png", record_pos=(0.252, 0.01), resolution=(2376, 1152)), Template(r"tpl1661004047547.png", record_pos=(0.06, -0.081), resolution=(2376, 1152)), Template(r"tpl1661004130364.png", record_pos=(-0.266, -0.121), resolution=(2376, 1152)), Template(r"tpl1661004105685.png", record_pos=(-0.113, -0.142), resolution=(2376, 1152)), None, 5, Template(r"tpl1661004174372.png", record_pos=(0.463, 0.192), resolution=(2376, 1152)), None
    )
}

# 待选关卡攻略列表
strategies = (
    StoreStrategy('商店', Template(r"tpl1642255403039.png", threshold=0.9000000000000001, record_pos=(0.247, -0.144), resolution=(1440, 810))),
    BattleStrategy('与虫为伴', Template(r"tpl1653738179917.png", record_pos=(0.29, -0.112), resolution=(2376, 1152))),

    BattleStrategy('意外', Template(r"tpl1653668846937.png", record_pos=(0.269, -0.112), resolution=(2376, 1152))),
    BattleStrategy('礼炮小队', Template(r"tpl1653641521012.png", record_pos=(0.26, -0.133), resolution=(2376, 1152))),
    BattleStrategy('驯兽小屋', Template(r"tpl1653641068701.png", record_pos=(0.259, -0.134), resolution=(2376, 1152))),
    BattleStrategy('死斗', Template(r"tpl1655520829193.png", record_pos=(0.269, -0.111), resolution=(2376, 1152))),

    EventStrategy('不期而遇', Template(r"tpl1642143362809.png", threshold=0.9000000000000001, record_pos=(0.247, -0.144), resolution=(1440, 810))),
    EventStrategy('幕间余兴', Template(r"tpl1642172966906.png", threshold=0.9000000000000001, record_pos=(0.247, -0.145), resolution=(1440, 810)))
)

if __name__ == "__main__":
    # 初始配置
    mobilePositionConfig = supportMobilePositionConfigs[mobileType]
    agents = []
    for agentName in useAgents:
        agent = scriptSupportAgents[agentName]
        agents.append(agent)
        
    # 调试助战
#     tryEnlistAgentFromMogul(agents, mobilePositionConfig['基础位置配置']['右滑屏幕起始点'])
    
    # 死循环，持续挑战不停歇
    while(True):
        # 确认进行探索
        confirmExploration(mobilePositionConfig['基础位置配置'])
        # 进入古堡前的准备，选出一位探索古堡的勇士干员
        warrior = prepareEnterCastle(agents, mobilePositionConfig['基础位置配置'])
        # 如果干员招募失败，则退出重开一局
        if not warrior:
            # 退出本轮探索
            exitExploration(mobilePositionConfig['基础位置配置'])
            # 结束本轮探索并结算本轮探索收益
            settlementExplorationIncome()
            continue
        # 准备完成，确认进入古堡
        confirmEnterCastle()
        # 将勇士加入探索编队
        organizeIntoTeams(warrior, mobilePositionConfig['基础位置配置'])
        success = False
        # 不断挑战本轮探索内的关卡, 直到关底或者攻略关卡失败
        while(True):
            # 点击选中本次挑战关卡
            chooseLevel(mobilePositionConfig['关卡按钮的可能位置'])
            # 查找关卡攻略
            strategy = findStrategy()
            if strategy is not None:
                print('匹配到的关卡：' + strategy.targetName)
            else:
                print('关卡匹配失败！退出本轮探索')
                success = True
                break
            # 攻略关卡
            success = tryChallenge(strategy, warrior, mobilePositionConfig)
            # 是否挑战失败或已经挑战到关底
            if not success or strategy.isLastTargetStrategy():
                break
        if success:
            # 退出本轮探索
            exitExploration(mobilePositionConfig['基础位置配置'])
        # 结束本轮探索并结算本轮探索收益
        settlementExplorationIncome()




