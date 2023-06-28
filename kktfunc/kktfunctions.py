import json
from logging import raiseExceptions
#from kktfunc.initkkt import initkkt
from libfptr10 import IFptr
from sql.sqlfunc import *

def returnDict(success: bool, errorDesc: str, fptr: IFptr):
    return {'succes':success, 'descr':errorDesc, 'driver': fptr}

#Проверка кода маркировки
def checkdm(fptr):
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '014494550435306821QXYXSALGLMYQQ\u001D91EE06\u001D92YWCXbmK6SN8vvwoxZFk7WAY8WoJNMGGr6Cgtiuja04c=')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 2)
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, 1.000)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_FRACTIONAL_QUANTITY, '1/2')
    fptr.beginMarkingCodeValidation()
    while True:
        fptr.getMarkingCodeValidationStatus()
        if fptr.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
            break
    validationResult = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)

#Инициализация ККТ 
def initKKT(settings: dict[str, any]):
    fptr = IFptr("")
    if not settings:
        settings = getkktsettings()
    fptr.setSettings(settings)
    fptr.open()
    if fptr.isOpened():
        return returnDict(True,'', fptr)
    else:
        return returnDict(False, fptr.errorDescription(), None)

# Установка кассира
def setcashier(cashier: json, fptr: IFptr):
    fptr.setParam(1021, "Кассир Иванов И.")
    fptr.setParam(1203, "123456789047")
    fptr.operatorLogin()
    if fptr.errorCode() == 0:
        return returnDict(True, '', None)
    else:    
        return returnDict(False, fptr.errorDescription(), None)

#Открытие смены
def openShift(cashier: json, fptr: IFptr):
    if cashier:
        setcashier(cashier, fptr)
    else: #TODO кассир не пришел, надо взять из БД
        setcashier(cashier, fptr)
    #fptr = initKKT(None)
    #if fptr.isinstance(IFptr):
    fptr.openShift()
    if fptr.errorCode() == 0:
        return returnDict(True, '', None)
    else:
        return returnDict(False, fptr.errorDescription(), None)
    
#Закрытие смены
def closeShift(cashier: json, fptr: IFptr):
    if cashier:
        setcashier(cashier, fptr)
    else: #TODO кассир не пришел, надо взять из БД
        setcashier(cashier, fptr)
    #fptr = initKKT(None)
    #if fptr.isinstance(IFptr):
    if fptr.isOpened():
        fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
        fptr.report()
        if fptr.errorCode() == 0:
            return returnDict(True, '', None)
        else:
            return returnDict(False, fptr.errorDescription(), None)
    else:
        return returnDict(False, fptr.errorDescription())

#Получить настройки ККТ
def getkktsettings():
    current_settings = Settings.select().dicts()
    settingdict = {}
    if len(current_settings) > 0:
        for current_setting in current_settings:
            CURRENT_SETTING = IFptr.__getattribute__(IFptr, current_setting.get('setting'))
            if CURRENT_SETTING != 'ComFile':
                CURRENT_SETTING_VALUE = IFptr.__getattribute__(IFptr, current_setting.get('settingvalue'))
            else:
                CURRENT_SETTING_VALUE = current_setting.get('settingvalue')
            settingdict[CURRENT_SETTING] = CURRENT_SETTING_VALUE
        return settingdict
    else:
        default_settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_11F,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
        IFptr.LIBFPTR_SETTING_COM_FILE: "COM5",
        IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200}
        return default_settings

# Настройки с формы в словарь в аттрибутах класса
def setkktsettingsfromform(formsettings):
    settingsdict = {}
    for current_setting in formsettings:
        settingsdict[IFptr.__getattribute__(IFptr,current_setting)] = IFptr.__getattribute__(IFptr,formsettings[current_setting])
    return settingsdict

#Текущее состояние смены
def checkShift(fptr: IFptr):
    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
    fptr.queryData()
    shiftState = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
    if shiftState == IFptr.LIBFPTR_SS_CLOSED:
        return returnDict(True, 'СменаЗакрыта', fptr)
    elif shiftState == IFptr.LIBFPTR_SS_EXPIRED:
        return returnDict(True, 'Смена истекла', fptr)
    elif shiftState == IFptr.LIBFPTR_SS_OPENED:
        return returnDict(True, 'Смена закрыта', fptr)
    else:
        return returnDict(False, f'Исключительная, не вернулось состояние {fptr.errorDescription()}', fptr)

if __name__ == '__main__':
    print('Not for start')