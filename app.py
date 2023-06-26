from flask import Flask
from flask import request
import kktfunc.kktfunctions as kkt
from libfptr10 import IFptr
import json
from kktfunc.cashier import Cashier #Кассира из json в объект

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/check", methods=['POST'])
def checkstatus():
    kkt = kkt.initkkt(None)
    if kkt.isinstance(IFptr):
        pass
    else: #Возвращаем ошибку инциализации
        return kkt
        

@app.route("/openShift", methods=['POST'])
def openShift(cashier):
    kkt = kkt.initkkt(None)
    if kkt.isinstance(IFptr):
        if kkt.isOpened():
            return "error shift opened"
        else:
            pass
    else: #Возвращаем ошибку инциализации
        return kkt

@app.route("/closeShift", methods=['POST'])
def closeShift(cashier):
    kkt = kkt.initkkt(None)
    if kkt.isinstance(IFptr):
        pass
    else: #Возвращаем ошибку инциализации
        return kkt

@app.route("/receipt", methods=['POST'])
def receipt(receiptData):
    kkt = kkt.initkkt(None)
    if kkt.isinstance(IFptr):
        pass
    else: #Возвращаем ошибку инциализации
        return kkt


if __name__ == "__main__":
    app.run(debug=True, port=5000)
    