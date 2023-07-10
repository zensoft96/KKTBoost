from flask import Flask, flash, redirect, request, render_template
import kktfunc.kktfunctions as kkt
from sql.sqlfunc import *
from libfptr10 import IFptr
import json
from kktfunc.cashier import Cashier #Кассира из json в объект

app = Flask(__name__)

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
        if markCode is not None:
            initedkkt = kkt.initKKT(None)
            if initedkkt.get('succes'):
                driver = initedkkt.get('driver')
                #TODO Функция не принимает сейчас сам код, только экземпляр драйвера, надо поправить
                result = kkt.checkdm(driver, markCode)
                driver.close()
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
        current_settings = Settings.select().dicts()
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
                else:
                    print('Настройка которой не ждали')
                
            return render_template('settings.html', disabled = 'disabled', model=LIBFPTR_SETTING_MODEL,
                                   port = LIBFPTR_SETTING_PORT, com = LIBFPTR_SETTING_COM_FILE, baud = LIBFPTR_SETTING_BAUDRATE)
        else:
            return render_template('settings.html', disabled = 'disabled')
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
        inpjson = request.json
        initedkkt = kkt.initKKT(None)
        if initedkkt.get('succes'):
            driver = initedkkt.get('driver')
            shiftresult = kkt.openShift(inpjson, driver)
            if shiftresult.get('succes'):
                driver.close()
                return returnedjson(True, '')
            else:
                errorstring = f'Ошибка при открытии смены {shiftresult.get("descr")}'
                driver.close()
                return returnedjson(True, errorstring)



@app.route("/closeShift", methods=['POST'])
def closeShift():
    if request.content_type == 'application/x-www-form-urlencoded':
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
        inpjson = request.json
        initedkkt = kkt.initKKT(None)
        if initedkkt.get('succes'):
            driver = initedkkt.get('driver')
            if driver.isOpened():
                result = kkt.closeShift(inpjson, driver)
                if result.get('succes'):
                    driver.close()
                    return returnedjson(True, '')
                else:
                    driver.close()
                    return returnedjson(False, result.get('descr'))
            else:
                driver.close()
                return returnedjson(True, 'Смена закрыта')
        else:
            return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')
            
        
@app.route("/receipt", methods=['POST'])
def receipt():
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        try:
            checkType = request.json['checkType']
            electronnically = request.json['electronnically']
            sno = request.json['sno']
            cashsum = request.json['cashsum']
            goods = request.json['goods']
            cashier = request.json['cashier']
            cashelesssum = request.json['cashelesssum']
            taxsum = request.json['taxsum']
        except:
            return 'Не все параметры пришли'
        
        driver = initedkkt.get('driver')
        receiptResult = kkt.receipt(fptr=driver, checkType=checkType, 
                                    cashier={'cashierName': cashier[0]['cashierName'],
                                             'INN': cashier[0]['INN']},
                                    electronnically=electronnically,
                                    sno=sno, cashsum=cashsum, goods=goods,cashelesssum=cashelesssum,
                                    taxsum=taxsum)
        return(receiptResult)        
    else:
        return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')

@app.route("/statusShift", methods=['POST'])
def statusShift():
    initedkkt = kkt.initKKT(None)
    if initedkkt.get('succes'):
        driver = initedkkt.get('driver')
        shiftStatus = kkt.checkShift(driver)
        print(shiftStatus.get('descr'))
        
    else:
        return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')

if __name__ == "__main__":
    sqlsettings = Settings()
    sqlsettings.create_table(safe=True)
    app.secret_key = 'hjaskjdhkjasdhjahdkhakjdhqwkhJHHKHY*(Y*Y*(*Y))'
    app.run(debug=False, port=5000, host="0.0.0.0")
    