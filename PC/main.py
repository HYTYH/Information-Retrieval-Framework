import re
import os
import time
import argparse
import json
from bs4 import BeautifulSoup
from urllib import request
import lxml

def washHtml(path):
    soup=BeautifulSoup(open(path,'r',encoding='utf-8'),features="lxml")
    saveType=['title','p','h1','h2','h3','h4','h5']
    result=""
    wrong=[]
    for child in soup.descendants:
        if(child.name in saveType):
            '''
            if(child.string!=None):
                result=result+child.string
                '''
            if(child.text!=None):
                if(child.name in ['p']):
                    result=result+'    '
                elif (child.name in ['title']):
                    result=result+'标题:'
                result=result+child.text
            else:      
                wrong.append(child)
            if(child.name in ['p','title']):
                result=result+'\n'
    
    return result,wrong

def saveFile(file,result):
    f=open(file,'w',encoding='utf-8')
    f.write(result)
    f.close()
    
def getFileFromInternet(webId,cookie):
    baseURL='http://my.bupt.edu.cn/xnxw_content.jsp?urltype=news.NewsContentUrl&wbtreeid=1269&wbnewsid='
    headers={
        'Cookie':cookie
        }        
    req = request.Request(baseURL+str(webId),headers=headers)
    try:
        with request.urlopen(req) as f:
            result=f.read().decode('utf-8')
        if(result!=None):
            return result
        else:
            print("wrong in webget:",webID)
            return "wrong"
    except:
        print("http wrong")
        return "wrong"
    
    
    
parser = argparse.ArgumentParser()
parser.add_argument('--total', type=int, default=120, help='爬取的文章数量')
parser.add_argument('--startId', type=int, default=90297, help='文章开始的ID号，北邮信息门户新闻2021.5.26日这个号最大是90297，爬取会对这个号递减')
args = parser.parse_args()

with open("settings.json","r") as f:
    settings = json.load(f)

cookie = settings['cookie']
startId = args.startId
total = args.total
i=1
idIter=0
print("Current cookie : ",cookie)
assert cookie!="","cookie不能为空,需要在settings.json中填写"
while(i<=total):
    print("Now:",i)
    result=getFileFromInternet(startId-idIter,cookie)
    if(result=="wrong"):
        idIter+=1
        time.sleep(0.1) #稍微暂停一下
        continue
    
    #right
    saveFile("input/"+str(i)+".html",result)
    result_after,wrongList=washHtml("input/"+str(i)+".html")
    if(len(result_after)>210):
        saveFile("output/"+str(i)+".txt",result_after)  
        idIter+=1
        i+=1
    else:
        idIter+=1
        
    time.sleep(0.1) #稍微暂停一下
    


#final:idIter=220,i=161
    


