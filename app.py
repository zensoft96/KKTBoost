from time import sleep
from warnings import catch_warnings
from flask import Flask, flash, request, render_template, Response, redirect, url_for
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

def jobs_in_thread(queuejobs: deque):
    """Для выполнения в потоке
    Args:
        queuejobs (Deque): Очередь задач
    """    
    while True:
        if len(queuejobs) > 0:
            # Возьмем первый элемент, попробуем обработать и поставим в конец
            print('Есть задача')
            firstjob = queuejobs.popleft()
            jobname = firstjob.get('jobname')
            jobparameters = firstjob.get('parameters')
            jobid = firstjob.get('jobid')
            jobrotate = firstjob.get('jobrotate')
            nowjob = jf.Job(jobname=jobname, jobid=jobid, jobparameters=jobparameters, jobrotate=jobrotate)
            if nowjob.jobrotate < 30:
                try:
                    result = nowjob.completeTask()
                    if not result:
                        queuejobs.append(nowjob.task_to_dict())
                    else:
                        resultjob = Doned_jobs.insert(jobid=jobid, resulttext=result, recieved=False)
                        resultjob.execute()
                except:
                    pass
            #Иначе пусть пропадает из очереди в небытие попробовал 30 раз
            
                

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
        response = app.response_class(response='Метод не поддерживается',
                                      status=405, content_type='application/json')
        return response

@app.route('/jobresult/<job_id>', methods=['GET'])
def getjob(job_id:str):
    currentJob = Doned_jobs.get_or_none(Doned_jobs.job_id == job_id)
    if currentJob is None:
        response = app.response_class(response=json.dumps({
                                        'result': False,
                                        'error':'Нет задачи с UID {job_id}'
                                        }, ensure_ascii=False),
                    status = 204, 
                    content_type='application/json'
                                      )
        return response
    else:
        currentJob.recieved = True
        currentJob.save()
        response = app.response_class(
            response=json.dumps({
                           'result': True,
                           'error': '',
                           'parameters': currentJob.result_text
                           },ensure_ascii=False), 
            status= 200, 
            content_type='application/json'
        )
        return response
        

@app.route("/props", methods=['POST', 'GET'])
def props():
    if request.method == 'POST':
        #TODO Возвращать в дальнейшем в драйвер эти свойства(когда напишу)
        pass
    elif request.method == 'GET':
        while len(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        try:
            with kkt.Kassa() as kassa:
                kkt_props = kassa.kktproperties()
                return render_template("props.html", allprops = kkt_props)
        except Exception as ErrMessage:
                if isinstance(ErrMessage,type(kkt.KassaCriticalError())):
                    flash(f'Ошибка инициализации драйвера {ErrMessage.args[0]}')
                    response = app.response_class(response=f'Ошибка инициализации драйвера. {ErrMessage.args[0]}',
                                                 status=203)
                    return response
                elif isinstance(ErrMessage,type(kkt.KassaBusyError())):
                    flash(f'Касса занята, дождитесь выполнения задачи и обновите страницу {ErrMessage.args[0]}')
                    response = app.response_class(response=f'Касса занята, дождитесь выполнения задачи и обновите страницу. {ErrMessage.args[0]}',
                                                 status=203)
                    return response
    else:
        response = app.response_class(response='Метод не поддерживается.',
                                                 status=405)
        return response

# @app.errorhandler(500)
# def internal_server_error(e):
#     return str(e.original_exception)


#Проверка кода маркировки json
@app.route("/checkmark", methods=['POST'])
def checkmark():
    if request.content_type == 'application/json':
        markCode = request.json.get('code')
        try:
            if markCode is not None:
                with kkt.Kassa() as kassa:
                        markresult = kassa.checkdm(markCode)
                        response = app.response_class(response=json.dumps({'codeStatus':markresult},ensure_ascii=False),
                                                      status=200,
                                                      content_type='application/json')
                        return response
            else:
                return 'Ждем кода маркировки для проверки'
        except Exception as ErrMessage:
                    if isinstance(ErrMessage,type(kkt.KassaCriticalError())):
                        response = app.response_class(response=f'Ошибка инициализации ККТ {ErrMessage.args[0]}',
                                                      status=500,
                                                      content_type='application/json'
                                                      )
                        return response
                    elif isinstance(ErrMessage,type(kkt.KassaBusyError())):
                        jobid = str(uuid.uuid4())
                        jobs.append({'jobname':'checkmark', 'jobid': jobid, 'parameters':{'markCode':markCode}})
                        response = app.response_class(response=f'Ошибка при выполнении запроса {ErrMessage}. Номер задачи в очереди {jobid}',
                                                      status=503, content_type='application/json')
                        return response
        
        
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
        response = app.response_class(response='Метод не поддерживается.',
                                                 status=405)
        return response
    
@app.route("/saveCashier", methods=['POST','GET'])
def saveCashier():   
    if request.method == 'POST':
        cashier = request.form.get('cashier')
        if cashier is not None:
            current_setting = Settings.get_or_none(Settings.setting == 'cashier')
            if current_setting is None:
                current_setting = Settings(setting = 'cashier', settingvalue = cashier)
                current_setting.save()
            else:
                current_setting.setting = 'cashier'
                current_setting.settingvalue = cashier
                current_setting.save()
        return redirect(url_for('settings'), 301)
    else:
        response = app.response_class(response='Метод не поддерживается.',
                                                 status=405)
        return response

@app.route("/check", methods=['POST'])
def checkstatus():
    if request.content_type == 'application/x-www-form-urlencoded':
        try:    
            kassa = kkt.Kassa()
            initedkkt = kassa.initkkt(kwargs=request.form)
        except Exception as error:
            flash(str(error))
            settings = initedkkt.get('parameters')
            return render_template('settings.html', model=settings.get('LIBFPTR_SETTING_MODEL'),
                                   port = settings.get('LIBFPTR_SETTING_PORT'), 
                                   com = settings.get('LIBFPTR_SETTING_COM_FILE'), 
                                   baud = settings.get('LIBFPTR_SETTING_BAUDRATE'), 
                                   tested = initedkkt.get('succes'), 
                                   error = initedkkt.get('errordesc'))
        if initedkkt.get('success'):
            flash('Выполнено успешно')
            settings = initedkkt.get('parameters')
            return render_template('settings.html', model=settings.get('LIBFPTR_SETTING_MODEL'),
                                   port = settings.get('LIBFPTR_SETTING_PORT'), 
                                   com = settings.get('LIBFPTR_SETTING_COM_FILE'), 
                                   baud = settings.get('LIBFPTR_SETTING_BAUDRATE'), 
                                   tested = initedkkt.get('succes'), 
                                   error = initedkkt.get('errordesc'))
        else:
            flash(f"Возникли ошибки {initedkkt.get('errordesc')}")
            settings = initedkkt.get('parameters')
            return render_template('settings.html', model=settings.get('LIBFPTR_SETTING_MODEL'),
                                   port = settings.get('LIBFPTR_SETTING_PORT'), 
                                   com = settings.get('LIBFPTR_SETTING_COM_FILE'), 
                                   baud = settings.get('LIBFPTR_SETTING_BAUDRATE'), 
                                   tested = initedkkt.get('succes'), 
                                   error = initedkkt.get('errordesc'))
        
@app.route("/openShift", methods=['POST'])
def openShift():
    if request.content_type == 'application/x-www-form-urlencoded':
        while len(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        try:
            with kkt.Kassa() as kassa:
                    shiftresult = kassa.openShift(None)
                    if shiftresult.get('success'):
                        flash('Смена успешно открыта')
                        return render_template('index.html')
                    else:
                        flash(f'Ошибка при открытии смены. {shiftresult.get("errordesc")}')
                        return render_template('index.html')
        except Exception as ErrMessage:
                    errorStr = f'Ошибка при октрытии смены на ККТ {ErrMessage.args[0]}'
                    flash(errorStr)
                    return render_template('index.html')
    else:
        try:
            with kkt.Kassa() as kassa:        
                cashier = request.json.get('cashier')
                shiftresult = kassa.openShift(cashier=cashier)
                returnedJson = json.dumps(shiftresult, ensure_ascii=False)
                if shiftresult.get('success'):
                    rc = 200
                else:
                    rc = 201
                response = app.response_class(response=returnedJson, status=rc, content_type='application/json')                
                return response
                
        except Exception as ErrMessage:
            response = app.response_class(response=f'Ошибка при выполнении запроса {ErrMessage}.',
                                            status=503, content_type='application/json')
            return response

@app.route("/closeShift", methods=['POST'])
def closeShift():
    if request.content_type == 'application/x-www-form-urlencoded':
        while len(jobs) > 0:
            #Ждем обработки очереди
            sleep(5)
        try:
            with kkt.Kassa() as kassa:
                shiftresult = kassa.closeShift(None)
                if shiftresult.get('success'):
                    flash('Смена успешно Закрыта')
                    return render_template('index.html')
                else:
                    flash(f'Ошибка при закрытии смены. {shiftresult.get("errordesc")}')
                    return render_template('index.html')
        except Exception as ErrMessage:
                    errorStr = f'Ошибка при закрытии смены на ККТ. {ErrMessage.args[0]}'
                    flash(errorStr)
                    return render_template('index.html')
    else:
        try:
            with kkt.Kassa() as kassa:        
                cashier = request.json.get('cashier')
                shiftresult = kassa.closeShift(cashier=cashier)
                returnedJson = json.dumps(shiftresult, ensure_ascii=False)
                if shiftresult.get('success'):
                    rc = 200
                else:
                    rc = 201
                response = app.response_class(response=returnedJson, status=rc, content_type='application/json')                
                return response
                
        except Exception as ErrMessage:
            response = app.response_class(response=f'Ошибка при выполнении запроса {ErrMessage}.',
                                            status=503, content_type='application/json')
            return response

@app.route("/receipt", methods=['POST'])
def receipt():
    import traceback
    try:
        checkType = request.json['checkType']
        electronnically = request.json['electronnically']
        sno = int(request.json['sno'])
        cashsum = float(request.json['cashsum'])
        goods = request.json['goods']
        cashier = request.json['cashier']
        # taxsum = float(request.json['taxsum'])
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
        return Response({f'В параметре {where_str} пришли неверные данные. Ошибка: {what_str} ', 415, {'Content-Type': 'application/json'}})
    except:
        return Response('Не все параметры пришли', 415, {'Content-Type': 'application/json'})

    try:
        with kkt.Kassa() as kassa:
            if checkType.upper().find('CORR') != -1:
                    receiptResult = kassa.receipt(checkType=checkType, 
                                cashier=cashier,
                                electronnically=electronnically, sno=sno, cashsum=cashsum, 
                                goods=goods,cashelesssum=cashelesssum, #taxsum=taxsum, 
                                corrType = corrType, corrBaseDate = corrBaseDate, corrBaseNum = corrBaseNum)
            else:
                receiptResult = kassa.receipt(checkType=checkType, 
                                        cashier=cashier,
                                        electronnically=electronnically,
                                        sno=sno, cashsum=cashsum, goods=goods,cashelesssum=cashelesssum)
                                        #taxsum=taxsum)
                                        
            if receiptResult.get('success'):
                response = app.response_class(
                    response=json.dumps(receiptResult, ensure_ascii=False),
                    status=200, content_type='application/json')
            else:
                response = app.response_class(
                    response=json.dumps(receiptResult, ensure_ascii=False),
                    status=500, content_type='application/json')
    except Exception as ErrMessage:
                    if isinstance(ErrMessage,type(kkt.KassaCriticalError())):
                        response = app.response_class(response=f'Ошибка инициализации ККТ {ErrMessage.args[0]}',
                                                      status=500,
                                                      content_type='application/json'
                                                      )
                        return response
                    elif isinstance(ErrMessage,type(kkt.KassaBusyError())):
                        if checkType.upper().find('CORR') != -1:
                            jobid = str(uuid.uuid4())
                            dictJob = {
                                'jobname': 'receipt',
                                'jobid': jobid,
                                'jobrotate': 0,
                                'parameters':{
                                    'checkType': checkType,
                                    'electronnically': electronnically,
                                    'cashier': cashier,
                                    'sno': sno,
                                    'cashsum': cashsum,
                                    'goods': goods,
                                    'cashelesssum': cashelesssum,
                                    'corrType': corrType, 
                                    'corrBaseDate': corrBaseDate, 
                                    'corrBaseNum': corrBaseNum
                                    }
                            }
                            jobs.append(dictJob)
                            jobsDict = {'success':False, 
                                        'error':f'Ошибка при выполнении запроса {ErrMessage}.', 
                                        'jobid':jobid}
                            respJson = json.dumps(jobsDict, ensure_ascii=False)
                            response = app.response_class(response=respJson,
                                                        status=503, 
                                                        content_type='application/json')
                            return response
                        else:
                            jobid = str(uuid.uuid4())
                            dictJob = {
                                'jobname': 'receipt',
                                'jobid': jobid,
                                'jobrotate': 0,
                                'parameters':{
                                    'checkType': checkType, 
                                    'cashier': cashier,
                                    'electronnically': electronnically,
                                    'sno': sno, 
                                    'cashsum':cashsum, 
                                    'goods': goods,
                                    'cashelesssum': cashelesssum
                                    }
                            }
                            jobs.append(dictJob)
                            jobsDict = {'success':False, 
                                        'error':f'Ошибка при выполнении запроса {ErrMessage}.', 
                                        'jobid':jobid}
                            respJson = json.dumps(jobsDict, ensure_ascii=False)
                            response = app.response_class(response=respJson,
                                                        status=503, 
                                                        content_type='application/json')
                            return response


@app.route("/statusShift", methods=['POST'])
def statusShift():
    try:
        with kkt.Kassa() as kassa:
            shiftResult = kassa.checkShift()
            if shiftResult is not None:
                retCode = 0 
                if shiftResult.get('Expired'):
                    retCode = 3
                elif shiftResult.get('Opened') and not shiftResult.get('Expired'):
                    retCode = 2
                elif shiftResult.get('Closed'):
                    retCode = 1
                returnDict = {}
                returnDict['success'] = True
                returnDict['shiftStatus'] = retCode
                returnDict['shiftNumber'] = shiftResult.get('shiftNumber')
                returnDict['receiptNumber'] = shiftResult.get('receiptNumber')
                retJson = json.dumps(returnDict, ensure_ascii=False)
                response = app.response_class(response=retJson, status=200, content_type='application/json')
                return response
            else:
                returnDict = {}
                returnDict['success'] = False
                retJson = json.dumps(returnDict)
                response = app.response_class(response=retJson, status=503, content_type='application/json')
                return response
    except Exception as ErrMessage:
            response = app.response_class(response=f'Ошибка при выполнении запроса {ErrMessage}.',
                                            status=503, content_type='application/json')
            return response    


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
    