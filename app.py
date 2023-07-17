from time import sleep
from typing import Deque
from flask import Flask, flash, request, render_template
import kktfunc.kktfunctions as kkt
from sql.sqlfunc import *
import json, uuid
from collections import deque
from threading import Thread
import jobs.jobsfunctions as jf

app = Flask(__name__)
jobs = deque([], maxlen=50)
#Для теста задач, потом удалить нахуй
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229CgQXbjYAAAA2X9F'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229eqX4A3kAAAA0tKf'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229A4K4mtFAAAAhv8Z'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229\';r2lV"AAAAX3Id'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229ZGI+v3\'AAAAVYr8'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229r9GcX%nAAAAbIHi'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229KXAQhhFAAAAjt0m'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229!ZNntFnAAAAs++F'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229YeLyE/CAAAAG1UU'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229LEEMJiiAAAAs+ds'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229C4S*skFAAAATeNR'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'046037311752292msEGEpAAAAYng0'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229,LFRB2:AAAA5/L+'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229REr2!>SAAAA+TVy'
# }})
# jobs.append({'jobname':'checkmark', 
#              'jobid': uuid.uuid4,
#              'parameters':{
#     'markCode':'04603731175229uGTEsgbAAAA0BEu'
# }})

def jobs_in_thread(queuejobs: Deque):
    """Для выполнения в потоке
    Args:
        queuejobs (Deque): Очередь задач
    """    
    while True:
        if len(queuejobs) > 0:
            # Возьмем первый элемент, попробуем обработать и поставим в конец
            firstjob = queuejobs.popleft()
            jobname = firstjob.get('jobname')
            jobparameters = firstjob.get('parameters')
            jobid = firstjob.get('id')
            nowjob = jf.Job(jobname=jobname, jobid=jobid, jobparameters=jobparameters)
            result = nowjob.completeTask()
            if not result:
                queuejobs.append(nowjob.task_to_dict)
            else:
                resultjob = Doned_jobs.insert(job_id=jobid, result_text='', recieved=False)
                resultjob.execute()
                

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

@app.route('/jobresult/<job_id>', methods=['GET'])
def getjob(job_id:str):
    currentJob = Doned_jobs.get_or_none(Doned_jobs.job_id == job_id)
    if currentJob is None:
        return json.dumps({
            'result': False,
            'error':'Нет задачи с UID {job_id}'
            }, ensure_ascii=False)
    else:
        currentJob.recieved = True
        currentJob.save()
        return json.dumps({
                           'result': True,
                           'error': '',
                           'parameters': currentJob.result_text
                           },ensure_ascii=False)
        

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
#FIXME Отсюда дичь, пока не исправишь передавать нельзя
@app.route("/checkmark", methods=['POST'])
def checkmark():
    if request.content_type == 'application/json':
        markCode = request.json.get('code')
        if markCode is not None:
            with kkt.Kassa() as kassa:
                try:                    
                    markresult = kassa.checkdm(markCode)
                    return markresult
                except Exception as ErrMessage:
                    jobid = uuid.uuid4
                    jobs.append({'jobname':'checkmark', 'jobid': jobid, 'parameters':{'markCode':markCode}})
                    return f'Ошибка при выполнении запроса {ErrMessage}. Номер задачи в очереди {jobid}'
        else:
            return 'Ждем кода маркировки для проверки'
        # if jobs.count(jobs) > 0:
        #     return('ККТ в работе. Повторите попытку позже.')
        # else:
        #     if markCode is not None:
        #         jobs.appendleft({'jobname':'checkmark', 
        #                          'jobid':uuid.uuid4, 'parameters':{
        #                          'markCode': markCode}
        #                          })
        #         initedkkt = kkt.initKKT(None)
        #         if initedkkt.get('succes'):
        #             driver = initedkkt.get('driver')
        #             result = kkt.checkdm(driver, markCode)
        #             driver.close()
        #             jobs.popleft()
        #             return result
        #         else:
        #             return returnedjson(False, f'Ошибка инициализации драйвера {initedkkt.get("descr")}')
        #     else:
        #         return 'Не правильный запрос'    

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
    sql_doned_jobs = Doned_jobs()
    sql_doned_jobs.create_table(safe=True)
    jobthread = Thread(target=jobs_in_thread, args=(jobs,))
    jobthread.start()
    #jobthread.join()
    app.secret_key = 'hjaskjdhkjasdhjahdkhakjdhqwkhJHHKHY*(Y*Y*(*Y))'
    app.run(debug=False, port=5000, host="0.0.0.0")
    