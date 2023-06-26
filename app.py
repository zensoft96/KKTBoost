from flask import Flask
from flask import request
import kktfunc.kktfunctions as kkt
from libfptr10 import IFptr
import json
from kktfunc.cashier import Cashier #Кассира из json в объект

app = Flask(__name__)


def returnedjson(result:dict):
    json.dumps(result)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/check", methods=['POST'])
def checkstatus():
    kkt = kkt.initK(None)
    if kkt.isinstance(IFptr):
        pass
    else: #Возвращаем ошибку инциализации
        return kkt
        

@app.route("/openShift", methods=['POST'])
def openShift():
    inpjson = request.json
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        driver = initedkkt.get('driver')
        # if driver.LIBFPTR_SS_EXPIRED > 0:
        #     driver.close()
        #     return json.dumps({'error': 'Смена открыта более 24 часов',
        #                        'success': False},ensure_ascii=False)
        # if driver.isOpened():
        #     driver.close()
        #     return json.dumps({'error': 'Смена уже открыта',
        #                        'success': True},ensure_ascii=False)
        shiftresult = kkt.openShift(inpjson, driver)
        if shiftresult.get('succes'):
            return json.dumps({'succes':True,
                               'error':''},ensure_ascii=False)
        else:
            errorstring = f'Ошибка при открытии смены {shiftresult.get("descr")}'
            return json.dumps({'succes': True, 'error': errorstring}, ensure_ascii=False)
    

@app.route("/closeShift", methods=['POST'])
def closeShift():
    inpjson = request.json
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        driver = initedkkt.get('driver')
        if driver.isOpened():
            result = kkt.closeShift(inpjson, driver)
            if result.get('succes'):
                driver.close()
                return json.dumps({'succes': True,
                                   'error':''})
            else:
                driver.close()
                return json.dumps({'succes': False, 'error':result.get('descr')},ensure_ascii=False)
        else:
            driver.close()
            return json.dumps({'succes': False, 'error':'Смена закрыта'}, ensure_ascii=False)

@app.route("/receipt", methods=['POST'])
def receipt(receiptData):
    kkt = kkt.initkkt(None)
    if kkt.isinstance(IFptr):
        pass
    else: #Возвращаем ошибку инциализации
        return kkt


if __name__ == "__main__":
    app.run(debug=False, port=5000)
    