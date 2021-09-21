from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic.response import *
import asyncio
import json
import os

app = Sanic("RemoteRestServer")



@app.route("/IM/TextSearch/query", methods=["POST"])
async def TS(request):
    
    text = request.json['text']
    method = request.json['method']
    os.chdir('Search/')
    try:
        with open("result.json","w") as f:
            f.write("")
        
        cmd = f"python search.py --o=\"result.json\" --input=\"{text}\" --method=\"{method}\" "
        os.system(cmd)
        with open("result.json","r",encoding="utf-8") as f:
            resultJson = f.read()
        result=json.loads(resultJson)
        retD=[]
        for i in range(len(result)):
            ID = result[i]['resultID']
            with open(f"data/{ID}.txt","r",encoding="utf-8") as f:
                resultText = f.read()
            retD.append({})
            retD[i]['text'] = resultText
            retD[i]['quality'] = result[i]['Accuracy']
        os.chdir('..')
        
        ret={
            "state":"success",
            "info":"Nothing",
            "data":retD
            }
        return response.json(ret)
    except Exception as e:
        print(e)
        os.chdir('..')
        ret = {
            "state": "failed",
            "info": "内部错误",
            "data": {}
        }
        return response.json(ret)


@app.route("/IM/VoiceSearch/query/<method>", methods=["POST"])
async def TS(request,method):

    print("method:",method)
    VB = request.files['file'][0].body
    VN = request.files['file'][0].name
    suffix = VN.split('.')[-1]
    print("file:",VN)

    assert suffix == "wav" or suffix == "WAV" ,"只能接受wav或者WAV文件"

    try:
        os.chdir('Search/')
        with open("WebVoice.wav","wb") as f:
            f.write(VB)
        
        cmd = f"python VoiceSearch.py --source=\"WebVoice.wav\" --target=\"result.json\" --method=\"{method}\""
        with open("result.json", "w") as f:
            f.write("")
        os.system(cmd)

        #cmd = f"python search.py --o=\"result.json\" --input=\"{text}\" --method=\"{method}\" "
        #os.system(cmd)
        with open("result.json", "r", encoding="utf-8") as f:
            resultJson = f.read()
        result = json.loads(resultJson)
        retD = []
        for i in range(len(result)):
            ID = result[i]['resultID']
            with open(f"data/{ID}.txt", "r", encoding="utf-8") as f:
                resultText = f.read()
            retD.append({})
            retD[i]['text'] = resultText
            retD[i]['quality'] = result[i]['Accuracy']
            retD[i]['url'] = f"/IM/file/voice/{ID}.mp3"
        os.chdir('..')

        ret = {
            "state": "success",
            "info": "Nothing",
            "data": retD
        }
        return response.json(ret)
    except Exception as e:
        print(e)
        os.chdir('..')
        ret = {
            "state": "failed",
            "info": "内部错误",
            "data": {}
        }
        return response.json(ret)


@app.route("/IM/TextExtract/query", methods=["POST"])
async def TE(request):

    text = request.json['text']
    os.chdir('Extract/')
    try:
        with open("数据/WebText.txt","w",encoding="utf-8") as f:
            f.write(text)
        
        cmd = f"python TextInfoExtract.py --all --specificdoc=\"WebText\" "
        os.system(cmd)
        with open("提取结果/信息/WebText.txt", "r", encoding="utf-8") as f:
            resultText = f.read()
        with open("提取结果/信息/结果指标.txt", "r", encoding="utf-8") as f:
            otherText = f.read()
        

        retD = [{}]
        retD[0]['text'] = resultText+"\n"+otherText
        retD[0]['imageURL'] = "/IM/file/image/WebText.jpg"

        os.chdir('..')

        ret = {
            "state": "success",
            "info": "Nothing",
            "data": retD
        }
        return response.json(ret)
    except Exception as e:
        print(e)
        os.chdir('..')
        ret = {
            "state": "failed",
            "info": "内部错误",
            "data": {}
        }
        return response.json(ret)


@app.route("/IM/VoiceExtract/query", methods=["POST"])
async def TS(request):


    VB = request.files['file'][0].body
    VN = request.files['file'][0].name
    suffix = VN.split('.')[-1]
    print("file:", VN)

    assert suffix == "wav" or suffix == "WAV", "只能接受wav或者WAV文件"

    try:
        os.chdir('Extract/')
        with open("WebVoice.wav", "wb") as f:
            f.write(VB)

        cmd = f"python VoiceInfoExtract.py --source=\"WebVoice.wav\" --target=\"result.txt\" "
        with open("result.txt", "w") as f:
            f.write("")
        os.system(cmd)

        #cmd = f"python search.py --o=\"result.json\" --input=\"{text}\" --method=\"{method}\" "
        #os.system(cmd)
        with open("result.txt", "r", encoding="utf-8") as f:
            resultText = f.read()

        retD = [{}]

        retD[0]['text'] = resultText
        retD[0]['imageURL'] = "/IM/file/image/TempText.jpg"
        os.chdir('..')

        ret = {
            "state": "success",
            "info": "Nothing",
            "data": retD
        }
        return response.json(ret)
    except Exception as e:
        print(e)
        os.chdir('..')
        ret = {
            "state": "failed",
            "info": "内部错误",
            "data": {}
        }
        return response.json(ret)



@app.route("/IM/file/image/<filename>", methods=["GET"])
def handle_requestT(request, filename):
    return response.file(f"Extract/提取结果/关系网络/{filename}")


@app.route("/IM/file/voice/<filename>", methods=["GET"])
def handle_requestV(request, filename):
    return response.file(f"Search/voiceData/{filename}")




@app.route('/', methods=["GET"])
def handle_request(request):
    global webbase
    #print(filename)
    return response.file('Web/index.html')


@app.route('/_assets/<filename>', methods=["GET"])
def handle_request(request, filename):
    global webbase
    return response.file("Web/_assets/"+filename)

'''
@app.route('/_assets/index.6c2099c3.js')
def handle_request(request):
    print(1)
    return response.file('D:/VueJS/compiler/dist/_assets/index.6c2099c3.js')


@app.route('/_assets/style.18ac1221.css')
def handle_request(request):
    return response.file('D:/VueJS/compiler/dist/_assets/style.18ac1221.css')
'''

if __name__ == "__main__":
    os.chdir('Extract')
    #os.system("python VoiceInfoExtract.py --source=\"../csdnb.wav\" --target=\"../result.txt\"")
    os.chdir('..')
    app.run(host="0.0.0.0", port=8000)



