from time import sleep
from flask import Flask, flash, redirect, request, render_template
import kktfunc.kktfunctions as kkt
from sql.sqlfunc import *
from libfptr10 import IFptr
import json
from kktfunc.cashier import Cashier #Кассира из json в объект
from collections import deque

app = Flask(__name__)
jobs = deque([])

def returnedjson(success=True, descr=''):
    return json.dumps({'success': success,
                       'descr':descr}, ensure_ascii=False)

@app.route("/")
def hello():
    if request.method == 'POST':
        return request.form
    elif request.method == 'GET':
        return render_template('index.html')
    else:
        return True

@app.route("/props", methods=['POST', 'GET'])
def props():
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        while jobs.count(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        initedkkt = kkt.initKKT(None)
        if initedkkt.get('succes'):
            driver = initedkkt.get('driver')
            kkt_props = kkt.kktproperties(driver)
            driver.close()
            return render_template("props.html", allprops = kkt_props)
        else:
            flash(f'Ошибка инициализации драйвера {initedkkt.get("descr")}')
    else:
        return 'Error method'

#Проверка кода маркировки json
@app.route("/checkmark", methods=['POST'])
def checkmark():
    if request.content_type == 'application/json':
        markCode = request.json.get('code')
        #Проверяем есть ли что-то в очереди, если есть тогда добавляем задание, должны вернуть wait и UUID
        if jobs.count(jobs) > 0:
            return('ККТ в работе. Повторите попытку позже.')
        else:
            if markCode is not None:
                jobs.appendleft({'jobname':'checkmark'})
                initedkkt = kkt.initKKT(None)
                if initedkkt.get('succes'):
                    driver = initedkkt.get('driver')
                    result = kkt.checkdm(driver, markCode)
                    driver.close()
                    jobs.pop()
                    return result
                else:
                    return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')
            else:
                return 'Не правильный запрос'    

@app.route("/settings", methods=['POST','GET'])
def settings():
    settingsdict = {}
    if request.method == 'POST':
        for i in request.form:
            current_settings = Settings.get_or_none(Settings.setting == i)
            if type(current_settings) == type(None):
                current_settings = Settings(setting = i, settingvalue = request.form[i])
                current_settings.save()
            else:
                current_settings.setting = i
                current_settings.settingvalue = request.form[i]
                current_settings.save()
            
            settingsdict[current_settings.setting] = current_settings.settingvalue
        return render_template('settings.html', disabled = 'disabled', 
                               model=settingsdict.get('LIBFPTR_SETTING_MODEL'),
                                   port = settingsdict.get('LIBFPTR_SETTING_PORT'), 
                                   com = settingsdict.get('LIBFPTR_SETTING_COM_FILE'), 
                                   baud = settingsdict.get('LIBFPTR_SETTING_BAUDRATE'))
    elif request.method == 'GET':
        while jobs.count(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        current_settings = Settings.select().dicts()
        cashier = ''
        if len(current_settings) > 0:
            for current_setting in current_settings:
                if current_setting.get('setting') == 'LIBFPTR_SETTING_MODEL':
                    LIBFPTR_SETTING_MODEL = current_setting['settingvalue']
                elif current_setting.get('setting') == 'LIBFPTR_SETTING_PORT':
                    LIBFPTR_SETTING_PORT = current_setting['settingvalue']
                elif current_setting.get('setting') == 'LIBFPTR_SETTING_COM_FILE':
                    LIBFPTR_SETTING_COM_FILE = current_setting['settingvalue']
                elif current_setting.get('setting') == 'LIBFPTR_SETTING_BAUDRATE':
                    LIBFPTR_SETTING_BAUDRATE = current_setting['settingvalue']
                elif current_setting.get('setting') == 'cashier':
                    cashier = current_setting['settingvalue']        
                else:
                    print('Настройка которой не ждали')
                
            return render_template('settings.html', disabled = 'disabled', model=LIBFPTR_SETTING_MODEL,
                                   port = LIBFPTR_SETTING_PORT, com = LIBFPTR_SETTING_COM_FILE, 
                                   baud = LIBFPTR_SETTING_BAUDRATE, cashier = cashier)
        else:
            return render_template('settings.html', disabled = 'disabled')
    else:
        return True
    
@app.route("/saveCashier", methods=['POST','GET'])
def saveCashier():   
    settingsdict = {}
    if request.method == 'POST':
        for i in request.form:
            current_settings = Settings.get_or_none(Settings.setting == i)
            if type(current_settings) == type(None):
                current_settings = Settings(setting = i, settingvalue = request.form[i])
                current_settings.save()
            else:
                current_settings.setting = i
                current_settings.settingvalue = request.form[i]
                current_settings.save()
            settingsdict[current_settings.setting] = current_settings.settingvalue
        return render_template('settings.html', cashier=settingsdict.get('cashier'))
    else:
        return True

@app.route("/check", methods=['POST'])
def checkstatus():
    if request.content_type == 'application/x-www-form-urlencoded':
        settings = kkt.setkktsettingsfromform(request.form)
        initedkkt = kkt.initKKT(settings)
        return render_template('settings.html', model=settings.get('LIBFPTR_SETTING_MODEL'),
                                   port = settings.get('LIBFPTR_SETTING_PORT'), 
                                   com = settings.get('LIBFPTR_SETTING_COM_FILE'), 
                                   baud = settings.get('LIBFPTR_SETTING_BAUDRATE'), 
                                   tested = initedkkt.get('succes'), 
                                   error = initedkkt.get('descr'))
        
@app.route("/openShift", methods=['POST'])
def openShift():
    if request.content_type == 'application/x-www-form-urlencoded':
        while jobs.count(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        initedkkt = kkt.initKKT(None)
        if initedkkt.get('succes'):
            driver = initedkkt.get('driver')
            shiftresult = kkt.openShift(None, driver)
            if shiftresult.get('succes'):
                driver.close()
                flash('Успешно открыта')
                return render_template('index.html')
            else:
                errorstring = f'Ошибка при открытии смены {shiftresult.get("descr")}'
                driver.close()
                flash(errorstring)
                return render_template('index.html')
    else:
        if jobs.count(jobs) > 0:
            return('ККТ в работе. Повторите попытку позже.')
        else:
            jobs.appendleft({'jobname':'openshift'})
            inpjson = request.json
            initedkkt = kkt.initKKT(None)
            if initedkkt.get('succes'):
                driver = initedkkt.get('driver')
                shiftresult = kkt.openShift(inpjson, driver)
                if shiftresult.get('succes'):
                    jobs.pop()
                    driver.close()
                    return returnedjson(True, '')
                else:
                    errorstring = f'Ошибка при открытии смены {shiftresult.get("descr")}'
                    jobs.pop()
                    driver.close()
                    return returnedjson(True, errorstring)

@app.route("/closeShift", methods=['POST'])
def closeShift():
    if request.content_type == 'application/x-www-form-urlencoded':
        while jobs.count(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        initedkkt = kkt.initKKT(None)
        if initedkkt.get('succes'):
            driver = initedkkt.get('driver')
            if driver.isOpened():
                result = kkt.closeShift(None, driver)
                if result.get('succes'):
                    driver.close()
                    flash('Успешно закрыта')
                    return render_template('index.html')
                else:
                    driver.close()
                    flash(f'Ошибка закрытия {result.get("descr")}')
                    return render_template('index.html')
            else:
                driver.close()
                flash("Смена уже закрыта")
                return render_template('index.html')
        else:
            flash(f'Ошибка инициализации драйвера {initedkkt.get("descr")}')
            return render_template('index.html')
    else:
        if jobs.count(jobs) > 0:
            return('ККТ в работе. Повторите попытку позже.')
        else:
            jobs.appendleft({'jobname':'closeshift'})
            inpjson = request.json
            initedkkt = kkt.initKKT(None)
            if initedkkt.get('succes'):
                driver = initedkkt.get('driver')
                if driver.isOpened():
                    result = kkt.closeShift(inpjson, driver)
                    if result.get('succes'):
                        jobs.pop()
                        driver.close()
                        return returnedjson(True, '')
                    else:
                        jobs.pop()
                        driver.close()
                        return returnedjson(False, result.get('descr'))
                else:
                    jobs.pop()
                    driver.close()
                    return returnedjson(True, 'Смена закрыта')
            else:
                return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')

@app.route("/receipt", methods=['POST'])
def receipt():
    import traceback
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        try:
            checkType = request.json['checkType']
            electronnically = request.json['electronnically']
            sno = int(request.json['sno'])
            cashsum = float(request.json['cashsum'])
            goods = request.json['goods']
            cashier = request.json['cashier']
            taxsum = float(request.json['taxsum'])
            cashelesssum = float(request.json['cashelesssum'])
            if checkType.upper().find('CORR') != -1:
                corrType = request.json["correctionType"]
                corrBaseDate = request.json["correctionBaseDate"]
                corrBaseNum = request.json["correctionBaseNumber"]
        except ValueError:
            error_value = str(traceback.format_exc())
            split_error = error_value.split('\n')
            where_str = split_error[2].split('[\'')[1].replace('\'])', '')
            what_str = split_error[4]
            return f'В параметре {where_str} пришли неверные данные. Ошибка: {what_str} '
        except:
            return 'Не все параметры пришли'
        if jobs.count(jobs) > 0:
            return ('ККТ в работе. Повторите попытку позже.')
        jobs.appendleft({'jobname':'receipt'})
        driver = initedkkt.get('driver')
        if checkType.upper().find('CORR') != -1:
            receiptResult = kkt.receipt(fptr=driver, checkType=checkType, 
                                    cashier={'cashierName': cashier[0]['cashierName'],
                                            'INN': cashier[0]['INN']},
                                    electronnically=electronnically, sno=sno, cashsum=cashsum, 
                                    goods=goods,cashelesssum=cashelesssum, taxsum=taxsum, 
                                    corrType = corrType, corrBaseDate = corrBaseDate, corrBaseNum = corrBaseNum)
        else:
            receiptResult = kkt.receipt(fptr=driver, checkType=checkType, 
                                    cashier={'cashierName': cashier[0]['cashierName'],
                                            'INN': cashier[0]['INN']},
                                    electronnically=electronnically,
                                    sno=sno, cashsum=cashsum, goods=goods,cashelesssum=cashelesssum,
                                    taxsum=taxsum)
        jobs.pop()
        return receiptResult
    else:
        return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')

@app.route("/statusShift", methods=['POST'])
def statusShift():
    while jobs.count(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
    jobs.appendleft({'jobname':'statusshift'})
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        driver = initedkkt.get('driver')
        shiftStatus = kkt.checkShift(driver)
        shiftStatus['shiftNumber']  = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
        shiftStatus['receiptNumber'] = driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
        driver.close()
        jobs.pop()
        #Удалить сам драйвер, чтобы были простые значения перед JSON
        shiftStatus.pop('driver')
        return json.dumps(shiftStatus, ensure_ascii=False)
    else:
        return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')

if __name__ == "__main__":
    sqlsettings = Settings()
    sqlsettings.create_table(safe=True)
    app.secret_key = 'hjaskjdhkjasdhjahdkhakjdhqwkhJHHKHY*(Y*Y*(*Y))'
    app.run(debug=False, port=5000, host="0.0.0.0")
    