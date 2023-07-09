from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome, ChromeOptions
from threading import Timer
from email.mime.text import MIMEText
from email.header import Header
import time
import re
import os
import warnings
import time
import requests
import json

warnings.filterwarnings("ignore")
url = "https://zjuam.zju.edu.cn/cas/login?service=http://jwbinfosys.zju.edu.cn/default2.aspx"
uname = ""
upwd = ""
cnt = 2
curCnt = 0
isLoggedin = False
isTempLog = False
isAutoUpdate = True
isAutoDing = False
isReady = False
isShowUp = False
localtime = ""
upInt = 30
uWebHook = ""

opt = ChromeOptions()
opt.headless = True ##########
opt.add_argument('log-level=3')
web = webdriver.Chrome(options=opt)
web.get(url)

dataList = {}
dataList['serial'] = []
dataList['name'] = []
dataList['score'] = []
dataList['credit'] = []
dataList['grdpnt'] = []
newScoreIndex = []
season = {'1':'秋冬','2':'春夏'}

def getScoreFromSite():
    global newScoreIndex
    global web
    orginScoreIndex = dataList["serial"].copy()
    newScoreIndex.clear()
    isFirst = True
    web.find_element(By.ID, 'Button2').click()
    table = web.find_element(By.ID, "DataGrid1")
    rows = table.find_elements(By.TAG_NAME ,"tr")
    dataList['serial'].clear()
    dataList['name'].clear()
    dataList['score'].clear()
    dataList['credit'].clear()
    dataList['grdpnt'].clear()
    for row in rows:
        if isFirst:
            isFirst = False
            continue
        cells = row.find_elements(By.TAG_NAME ,"td")
        if cells[2].text == "弃修":
            continue
        if  orginScoreIndex.count(cells[0].text) == 0:
            newScoreIndex.append(cells[0].text)
        dataList['serial'].append(cells[0].text)
        dataList['name'].append(cells[1].text)
        dataList['score'].append(int(cells[2].text))
        dataList['credit'].append(float(cells[3].text))
        dataList['grdpnt'].append(float(cells[4].text))
    
def saveScoreToFile():
    global localtime
    fileSav = open('scinfos.sav', mode='w')
    fileSav.write(str(getTotalNum('all'))+"\n")
    fileSav.write(localtime+"\n")
    for num in range(0, len(dataList["serial"])):
        fileSav.write(dataList['serial'][num] + ' ')
        fileSav.write(dataList['name'][num] + ' ')
        fileSav.write(str(dataList['score'][num]) + ' ')
        fileSav.write(str(dataList['credit'][num]) + ' ')
        fileSav.write(str(dataList['grdpnt'][num]))
        fileSav.write('\n')
    fileSav.close()

def loadScoreFromFile():
    global curCnt
    fileSav = open('scinfos.sav', mode='r')
    curCnt = int(fileSav.readline())
    global localtime
    localtime = fileSav.readline().strip('\n')
    dataList['serial'].clear()
    dataList['name'].clear()
    dataList['score'].clear()
    dataList['credit'].clear()
    dataList['grdpnt'].clear()
    for line in fileSav.readlines():
        splt = line.split( )
        dataList['serial'].append(splt[0])
        dataList['name'].append(splt[1])
        dataList['score'].append(int(splt[2]))
        dataList['credit'].append(float(splt[3]))
        dataList['grdpnt'].append(float(splt[4]))
    fileSav.close()
    
def getTotalNum(sem):
    totalNum = 0
    for num in range(0, len(dataList["serial"])):
        if dataList['serial'][num][1:12] == sem or dataList['serial'][num][1:10] == sem or sem == 'all':
            totalNum += 1
    return totalNum
 
def getTotalCredit(sem):
    totalCredit = 0.00
    for num in range(0, len(dataList["serial"])):
        if dataList['serial'][num][1:12] == sem or dataList['serial'][num][1:10] == sem or sem == 'all':
            totalCredit += dataList['credit'][num]
    return totalCredit
 
def getGPA(sem):
    totalWeighedGp = 0.00
    for num in range(0, len(dataList["serial"])):
        if dataList['serial'][num][1:12] == sem or dataList['serial'][num][1:10] == sem or sem == 'all':
           totalWeighedGp += (dataList['credit'][num] * dataList['grdpnt'][num])
    return totalWeighedGp / getTotalCredit(sem)

def putBorder(color, type):
    if(type==1):
        print("\033[1;"+str(color)+"m┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\033[0m")
    elif type == 2 :
        print("\033[1;"+str(color)+"m┃\033[0m")
    else:
        print("\033[1;"+str(color)+"m┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\033[0m")

def putScoreInfo(sem):
    i = 0
    for num in range(0, len(dataList["serial"])):
        if dataList['serial'][num][1:12] == sem or dataList['serial'][num][1:10] == sem or sem == 'all' or (sem == "new" and newScoreIndex.count(dataList['serial'][num]) == 1):
            if(dataList['grdpnt'][num]<1.5):
                color = 31
            elif dataList['grdpnt'][num]<3.9:
                color = 33
            else:
                color = 32
            putBorder(color,1)
            print(("\033[1;"+str(color)+"m \033[0m 课程："+dataList['name'][num]).ljust(30, ' '))
            print("\033[1;"+str(color)+"m \033[0m 学期：" + dataList['serial'][num][1:10] + ' '+season[dataList['serial'][num][11]]+"学期")
            print("\033[1;"+str(color)+"m \033[0m 成绩：" + str(dataList['score'][num]) + " 学分：" + str(dataList['credit'][num]))
            print("\033[1;"+str(color)+"m \033[0m 绩点：" + "\033[4;37m" + str(dataList['grdpnt'][num]) + "\033[0m")
            putBorder(color,3)
            if sem == "new":
                send_msg = []
                send_msg.append("#### 成绩通知 \n")
                send_msg.append(">课程 **"+dataList['name'][num]+"** 已出分.\n")
                send_msg.append(">- 分数："+str(dataList['score'][num])+"\n")
                send_msg.append(">- 绩点："+str(dataList['grdpnt'][num]))
                if isAutoDing: 
                    sendNote("".join(send_msg))
            i = 1
    if i == 0 and not sem == "new":
        print("未找到符合条件的成绩项.")

def putScoreInfoByGP(bound, egl):
     i = 0
     for num in range(0, len(dataList["serial"])):
        gp = dataList['grdpnt'][num]
        if (egl==0 and gp == bound)or(egl==1 and gp > bound)or(egl==2 and gp < bound)or(egl==3 and not (dataList['name'][num].find(bound) == -1)):
            if(dataList['grdpnt'][num]<1.5):
                color = 31
            elif dataList['grdpnt'][num]<3.9:
                color = 33
            else:
                color = 32
            putBorder(color,1)
            print("\033[1;"+str(color)+"m┃\033[0m 课程："+dataList['name'][num])
            print("\033[1;"+str(color)+"m┃\033[0m 学期：" + dataList['serial'][num][1:10] + ' '+season[dataList['serial'][num][11]]+"学期")
            print("\033[1;"+str(color)+"m┃\033[0m 成绩：" + str(dataList['score'][num]) + " 学分：" + str(dataList['credit'][num]))
            print("\033[1;"+str(color)+"m┃\033[0m 绩点：" + "\033[4;37m" + str(dataList['grdpnt'][num]) + "\033[0m")
            putBorder(color,3)
            i = 1
     if i == 0:
        print("未找到符合条件的成绩项.")

def putSemInfo(sem):
    print("\033[1;34m┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\033[0m")
    if len(sem) == 9:
        print("  ＞" + sem[0:9] + " 学年")
    elif len(sem) == 11:
        print("  ＞" + sem[0:9] + " " + season[sem[10]]+"学期")
    else:
        print("  ＞所有课程")
    
    print("  修读课程数：\033[1;37m"+ str(getTotalNum(sem))+"\033[0m")
    print("  修读总学分：\033[1;37m"+ str(getTotalCredit(sem))+"\033[0m")
    print("  学期均绩：\033[1;37m"+ str(getGPA(sem))+"\033[0m")
    print("\033[1;34m┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\033[0m")

def refreshSc():
    global localtime
    global curCnt
    global web
    print("\033[5;37m正在下载...\033[0m")
    getScoreFromSite()
    localtime = time.asctime( time.localtime(time.time()) )
    saveScoreToFile()
    _ = os.system('cls')
    print("\033[1;32m分数已更新,更新成绩 "+str(getTotalNum('all') - curCnt)+" 门.\033[0m\n")
    if not len(newScoreIndex) == 0:
        print("以下为新出的成绩：") 
    putScoreInfo("new")
    curCnt = getTotalNum('all')

def showHelp():
    print("\033[1;34m┏━━指令列表━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━┓\033[0m")
    print("  - \033[4;35m/refresh\033[0m         - 从教务系统获取最新成绩信息")
    print("  - \033[4;35m/display\033[0m         - 显示成绩信息")
    print("     - \033[4;36mall\033[0m              - 总成绩")
    print("        - \033[4;33m20XX-20XX-X\033[0m      - 学年/学期")
    print("     - \033[4;36mdetail\033[0m           - 各课程成绩")
    print("        - \033[4;33m(no argument)\033[0m    - 显示全部")
    print("        - \033[4;33m20XX-20XX-X\033[0m      - 学年/学期")
    print("        - \033[4;33mgpe X\033[0m            - 绩点等于X")
    print("        - \033[4;33mgpg X\033[0m            - 绩点高于X")
    print("        - \033[4;33mgpl X\033[0m            - 绩点低于X")
    print("        - \033[4;33mcontain X\033[0m        - 课程名包含X")
    print("  - \033[4;35m/config\033[0m          - 设置")
    print("     - \033[4;36mautoupdt\033[0m         - 自动更新")
    print("        - \033[4;33mswitch\033[0m           - 打开/关闭")
    print("        - \033[4;33minterval X\033[0m       - 将时间间隔设为X(s)")
    print("     - \033[4;36mnotify\033[0m           - 出分提醒")
    print("        - \033[4;33mswitch\033[0m           - 打开/关闭")
    print("        - \033[4;33mwebhook X\033[0m        - 将目标WebHook设为X")
    print("  - \033[4;35m/logout\033[0m          - 清除当前账号/密码信息")
    print("  - \033[4;35m/info\033[0m            - 关于")
    print("  - \033[4;35m/quit\033[0m            - 退出程序")
    print("  > 例如：\033[1;37m/display detail contain 程序\033[0m") 
    print("\033[1;34m┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\033[0m")

def displayUI(isLogged):
    _ = os.system('cls')
    print("\033[1;34m┏━━ZJU成绩管理━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━┓\033[0m")
    if isLogged:
        print("  \033[1;33m"+uname+"\033[0m，欢迎回来！")
        print("  当前学分：\033[1;37m"+str(getTotalCredit("all"))+"\033[0m     当前均绩：\033[1;37m"+str(round(getGPA("all"),3))+"\033[0m")
        tmpStr = ""
        tmpStr2 = ""
        if isAutoUpdate:
            tmpStr = "\033[1;32m已启用\033[0m"
        else:
            tmpStr = "\033[1;31m未启用\033[0m"
        if isAutoDing:
            tmpStr2 = "\033[1;32m已启用\033[0m"
        else:
            tmpStr2 = "\033[1;31m未启用\033[0m"
        if uWebHook == "":
            tmpStr2 = "\033[1;35m未设置WebHook\033[0m"
        print("  上次更新：\033[1;37m"+localtime+"\033[0m")
        print("  自动更新："+tmpStr+"   间隔：\033[1;37m"+str(upInt)+"\033[0m 秒")
        print("  自动提醒："+tmpStr2)
        print("  输入\033[1;37m/help\033[0m查看指令列表")
        
    else:
        print("\033[0;31m  当前未登录\033[0m")
        print("  - \033[4;37m/login\033[0m        - 登录")
    print("\033[1;34m┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\033[0m")

def logIn():
    global uname
    global upwd
    global isLoggedin
    global isTempLog
    global web
    global isAutoDing
    global uWebHook
    fileSav = open('config.sav', mode='r')
    ptmp = fileSav.readline()
    farr = ptmp.split( )
    if(len(farr) == 4):
        isAutoUpdate = (farr[0]=='t')
        upInt = int(farr[1])
        isAutoDing = (farr[2]=='t')
        uWebHook = farr[3]
    elif len(farr) == 3:
        isAutoUpdate = (farr[0]=='t')
        upInt = int(farr[1])
        isAutoDing = False
    else:
        isAutoUpdate = True
        upInt = 30
        isAutoDing = False
    fileSav.close()
    if(not isLoggedin):
        
        print("\033[1;34m请输入账号：\033[0m")
        uname = input()
        _ = os.system('cls')
        print("\033[1;34m请输入密码：\033[0m")
        upwd = input()
        _ = os.system('cls')
        print("\033[5;34m正在登录\033[0m")
        print("...")
        web.find_element(By.XPATH, '//*[@id="username"]').send_keys(uname)
        web.find_element(By.XPATH, '//*[@id="password"]').send_keys(upwd, Keys.ENTER)
        _ = os.system('cls')
        if web.current_url != url:
            web.find_element(By.XPATH, '//*[@id="Button1"]').click()
            web.find_element(By.XPATH, '//*[@id="xsmain_kscj.htm"]').click()
            web.find_element(By.XPATH, '//*[@class="iconcjcx"]/a').click()
            web.switch_to.window(web.window_handles[1])
            web.find_element(By.ID, 'Button2').click()
            print("\033[1;32m登录成功！\033[0m")
            print("\033[1;34m欢迎回来，\033[0m"+uname)
            print("是否记住密码？下次打开时无需登录.(y/n)")
            getAns = input()
            if getAns == "y" or getAns == "Y":
                fileSav = open('unpas.sav', mode='w')
                fileSav.write(uname+" ")
                fileSav.write(upwd)
                fileSav.close()
                isTempLog = False
                _ = os.system('cls')
                print("\033[1;32m已记住密码.\033[0m")
            else:
                _ = os.system('cls')
                print("本次登录为临时登录.")
                isTempLog = True
            
            isLoggedin = True
            fileSav = open('scinfos.sav', mode='r')
            ptmp = fileSav.readline()
            fileSav.close()
            
            if ptmp == "":
                _ = os.system('cls')
                print("\033[5;37m本地尚无成绩信息，将为您自动下载...\033[0m")
                refreshSc()
            else:
                loadScoreFromFile()
        else:
            print("\033[5;31m账号或密码错误.\033[0m")
            web.get(url)
            uname = ''
            upwd = ''
            isLoggedin = False
    else:
        global isReady
        if not isReady:
            print("\033[5;37m自动登录中...\033[0m")
            web.find_element(By.XPATH, '//*[@id="username"]').send_keys(uname)
            web.find_element(By.XPATH, '//*[@id="password"]').send_keys(upwd, Keys.ENTER)
            web.find_element(By.XPATH, '//*[@id="Button1"]').click()
            web.find_element(By.XPATH, '//*[@id="xsmain_kscj.htm"]').click()
            web.find_element(By.XPATH, '//*[@class="iconcjcx"]/a').click()
            web.switch_to.window(web.window_handles[1])
            web.find_element(By.ID, 'Button2').click()
            _ = os.system('cls')

            print("\033[1;32m登录成功！\033[0m")
            print("\033[1;34m欢迎回来，\033[0m"+uname)
            input()
            
            isReady = True
        else:
            print("\033[1;31m您已登录！\033[0m")
    if(isAutoUpdate):
        t = Timer(upInt, autoUpdata)
        t.start()

def logOut():
    global uname
    global upwd
    global isLoggedin
    global isTempLog
    global isAutoDing
    global uWebHook
    global isAutoUpdate
    global web
    if isLoggedin:
        uname = ''
        upwd = ''
        isLoggedin = False
        if not isTempLog:
            fileSav = open('unpas.sav', mode='w')
            fileSav.write("")
            fileSav.close()
        print("\033[0;32m已安全退出.\033[0m")
        print("是否删除本地成绩信息？(y/n)")
        if input() == 'y':
            _ = os.system('cls')
            fileSav = open('scinfos.sav', mode='w')
            fileSav.write("")
            fileSav.close()
            print("\033[0;32m已删除本地信息.\033[0m")
            uWebHook = ""
            isAutoDing = False
            saveConfig()
            isAutoUpdate = False
        else:
            _ = os.system('cls')
            print("\033[0;32m已保留本地信息.\033[0m")
        web.get(url)
    else:
        print("\033[0;31m您当前未登录.\033[0m")

def autoUpdata():
    global t
    getScoreFromSite()
    saveScoreToFile()
    global localtime
    global curCnt
    localtime = time.asctime( time.localtime(time.time()) )
    print("\n\033[4;32m自动更新:\033[0m"+"\033[4;37m"+localtime+"\033[0m \033[1;32m分数已更新,更新成绩 "+str(getTotalNum('all') - curCnt)+" 门.\033[0m")
    if not len(newScoreIndex) == 0:
        print("以下为新出的成绩：") 
    localtime = time.asctime( time.localtime(time.time()) )
    putScoreInfo("new")
    curCnt = getTotalNum('all')
    t = Timer(upInt, autoUpdata)
    if(isAutoUpdate):
        t.start()

def sendNote(text):
    webhook = uWebHook
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    message ={
        "msgtype": "markdown",
        "markdown": {
            "title":"成绩通知",
            "text": text
        },

        "at": {

            "isAtAll": True
        }
    }
    message_json = json.dumps(message)
    info = requests.post(url=webhook,data=message_json,headers=header)

def saveConfig():
    fileSav = open('config.sav', mode='w')
    if(isAutoUpdate):
        fileSav.write("t ")
    else:
        fileSav.write("f ")
    fileSav.write(str(upInt)+" ")
    if(isAutoDing):
        fileSav.write("t ")
    else:
        fileSav.write("f ")
    fileSav.write(uWebHook)

def showInfo():
    _ = os.system('cls')
    print("\033[5;33m██╗     ██╗██╗   ██╗     ██╗██╗  ██╗██╗  ██╗ ██████╗ ██╗  ██╗\033[0m")
    print("\033[5;33m██║     ██║██║   ██║     ██║╚██╗██╔╝██║  ██║██╔═████╗██║  ██║\033[0m")
    print("\033[5;33m██║     ██║██║   ██║     ██║ ╚███╔╝ ███████║██║██╔██║███████║\033[0m")
    print("\033[5;33m██║     ██║██║   ██║██   ██║ ██╔██╗ ╚════██║████╔╝██║╚════██║\033[0m")
    print("\033[5;33m███████╗██║╚██████╔╝╚█████╔╝██╔╝ ██╗     ██║╚██████╔╝     ██║\033[0m")
    print("\033[5;33m╚══════╝╚═╝ ╚═════╝  ╚════╝ ╚═╝  ╚═╝     ╚═╝ ╚═════╝      ╚═╝\033[0m")
    print("\n  ZJU成绩管理系统. V1.0.0     2023.07.05")
    print("\n  作者：3220102363. 浙江大学计算机学院")
    print("\n  Written with Python, all right reserved.\n")

_ = os.system('cls')
###LOAD CONFIG


fileSav = open('unpas.sav', mode='r')
ptmp = fileSav.readline()
farr = ptmp.split( )
if(len(farr) == 2):
    uname = farr[0]
    upwd = farr[1]
    isLoggedin = True
    logIn()
    loadScoreFromFile()
fileSav.close()


command = ""
while command != '/quit':
    displayUI(isLoggedin)
    command = input()
    if command == "":
        continue
    _ = os.system('cls')
    args = command.split( )
    if args[0] == "/refresh":
        refreshSc()
        putSemInfo('all')
    elif args[0] == "/display":
       if len(args) == 1:
           print("\033[0;31m错误:缺少参数.\033[0m")
           input()
           continue
       if args[1] == "all":
          if len(args) == 2:
              putSemInfo('all')
          else:
              putSemInfo(args[2])
       elif args[1] == "detail":
          if len(args) == 2:
              putScoreInfo('all')
          else:
              if args[2] == 'gpe':
                  putScoreInfoByGP(float(args[3]),0)
              elif args[2] == 'gpg':
                  putScoreInfoByGP(float(args[3]),1)
              elif args[2] == 'gpl':
                  putScoreInfoByGP(float(args[3]),2)
              elif args[2] == 'contain':
                  putScoreInfoByGP(args[3],3)
              else:
                  putScoreInfo(args[2])
       else:
           print("\033[0;31m错误:不存在参数：\033[0m"+args[1])
    elif command == '/quit':
        break
    elif command == '/login':
        logIn()
    elif command == '/logout':
        logOut()
    elif command == '/help':
        showHelp()
    elif args[0] == '/config':
        if (len(args) < 3) or ((args[2]=="interval" or args[2]=="webhook") and len(args) < 4):
           print("\033[0;31m错误:缺少参数.\033[0m")
           input()
           continue
        else:
            if args[1] == 'autoupdt':
                if args[2] == "switch":
                    isAutoUpdate = not isAutoUpdate
                    print("\033[1;32m自动更新已设为：\033[0m"+str(isAutoUpdate))
                    saveConfig()
                    if(isAutoUpdate):
                        t = Timer(upInt, autoUpdata)
                        t.start()
                elif args[2] == "interval":
                    if(int(args[3]) < 0):
                        print("\033[1;31m间隔时间不得为负！\033[0m")
                    else:
                        upInt=args[3]
                        saveConfig()
                        print("\033[1;32m自动更新间隔时间已设为：\033[0m"+str(upInt))
            elif args[1] == "notify":
                if args[2] == "switch":
                    if (not uWebHook == ""):
                        isAutoDing = not isAutoDing
                        print("\033[1;32m消息提醒已设为：\033[0m"+str(isAutoDing))
                        saveConfig()
                        if(isAutoDing):
                            sendNote("消息提醒已开启.")
                        else:
                            sendNote("消息提醒已关闭.")
                            t.cancel()
                    else:
                        print("\033[1;31m请先设置WebHook\033[0m")
                    
                elif args[2] == "webhook":
                    uWebHook = args[3]
                    saveConfig()
                    print("\033[1;32m提醒WebHook已设为：\033[0m"+uWebHook)
    elif command == "/info":
        showInfo() 
    else:
        print("\033[1;31m未知指令，输入\033[0m\033[4;37m/help\033[0m\033[1;31m查看指令列表]\033[0m")
    print("\033[5;37m任意键以返回主菜单...\033[0m")
    input()
          
