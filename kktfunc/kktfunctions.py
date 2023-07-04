import json
from logging import raiseExceptions
#from kktfunc.initkkt import initkkt
from libfptr10 import IFptr
from sql.sqlfunc import *
from time import time

def returnDict(success: bool, errorDesc: str, fptr: IFptr):
    return {'succes':success, 'descr':errorDesc, 'driver': fptr}

# Возврат типа чека, либо чек закрыт
def receipt_type(LIBFPTR_PARAM_RECEIPT_TYPE: IFptr.LIBFPTR_PARAM_RECEIPT_TYPE):
    states = {IFptr.LIBFPTR_RT_CLOSED : "чек закрыт",
    IFptr.LIBFPTR_RT_SELL : "чек прихода",
    IFptr.LIBFPTR_RT_SELL_RETURN : "чек возврата прихода",
    IFptr.LIBFPTR_RT_SELL_CORRECTION : "чек коррекции прихода",
    IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION : "чек коррекции возврата прихода",
    IFptr.LIBFPTR_RT_BUY : "чек расхода",
    IFptr.LIBFPTR_RT_BUY_RETURN : "чек возврата расхода",
    IFptr.LIBFPTR_RT_BUY_CORRECTION : "чек коррекции расхода",
    IFptr.LIBFPTR_RT_BUY_RETURN_CORRECTION : "чек коррекции возврата расхода"}
    try:
        result = states[LIBFPTR_PARAM_RECEIPT_TYPE]
        return result
    except:
        return 'Не получено состояние типа открытого чека' 

#Возврат типа документа
def document_type(LIBFPTR_PARAM_DOCUMENT_TYPE: IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE):
    states = {IFptr.LIBFPTR_DT_CLOSED : "документ закрыт",
    IFptr.LIBFPTR_DT_RECEIPT_SELL : "чек прихода",
    IFptr.LIBFPTR_DT_RECEIPT_SELL_RETURN : "чек возврата прихода",
    IFptr.LIBFPTR_DT_RECEIPT_BUY : "чек расхода",
    IFptr.LIBFPTR_DT_RECEIPT_BUY_RETURN : "чек возврата расхода",
    IFptr.LIBFPTR_DT_OPEN_SHIFT : "документ открытия смены",
    IFptr.LIBFPTR_DT_CLOSE_SHIFT : "документ закрытия смены",
    IFptr.LIBFPTR_DT_REGISTRATION : "документ пере/регистрации",
    IFptr.LIBFPTR_DT_CLOSE_ARCHIVE : "документ закрытия архива ФН",
    IFptr.LIBFPTR_DT_OFD_EXCHANGE_STATUS : "отчёт о состоянии расчётов",
    IFptr.LIBFPTR_DT_RECEIPT_SELL_CORRECTION : "чек коррекции прихода",
    IFptr.LIBFPTR_DT_RECEIPT_BUY_CORRECTION : "чек коррекции расхода",
    IFptr.LIBFPTR_DT_RECEIPT_SELL_RETURN_CORRECTION : "чек коррекции возврата прихода",
    IFptr.LIBFPTR_DT_RECEIPT_BUY_RETURN_CORRECTION : "чек коррекции возврата расхода",
    IFptr.LIBFPTR_DT_DOCUMENT_SERVICE : "сервисный документ",
    IFptr.LIBFPTR_DT_DOCUMENT_COPY : "копия документа"}
    try:
        result = states[LIBFPTR_PARAM_DOCUMENT_TYPE]
        return result
    except:
        return 'Не получено состояние открытого документа'

#Настройки(свойства ККТ)
def kktproperties(fptr: IFptr):
    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
    fptr.queryData()
    dict_to_return = {}
    #Номер кассира
    dict_to_return['operatorID']      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID)
    #Номер ККТ в магазине
    dict_to_return['logicalNumber']   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER)
    #Состояние смены
    dict_to_return['shiftClosed']= fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_CLOSED
    dict_to_return['shiftOpened'] = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_OPENED
    dict_to_return['shiftExpired'] = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_EXPIRED
    #Модель
    dict_to_return['model']           = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
    #Режим ККТ
    dict_to_return['mode']            = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODE)
    #Подрежим ККТ
    dict_to_return['submode']         = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE)
    #Номер чека
    dict_to_return['receiptNumber']   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
    #Номер документа
    dict_to_return['documentNumber']  = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
    #Номер смены
    dict_to_return['shiftNumber']     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
    #Тип открытого чека
    dict_to_return['receiptType']     = receipt_type(fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE))
    #Тип открытого документа
    dict_to_return['documentType']    = document_type(fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE))
    #ККТ Зарегистрирована
    dict_to_return['isFiscalDevice']          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FISCAL)
    #ФН Фискализован
    dict_to_return['isFiscalFN']              = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_FISCAL)
    #ФН Присутствует
    dict_to_return['isFNPresent']             = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_PRESENT)
    #ФН НЕ Правильный
    dict_to_return['isInvalidFN']             = fptr.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN)
    #Бумага присутствует
    dict_to_return['isPaperPresent']          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT)
    #Бумага заканчивается
    dict_to_return['isPaperNearEnd']          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END)
    #Крышка открыта
    dict_to_return['isCoverOpened']           = fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED)
    #Потеряно соединение с печатным механизмом
    dict_to_return['isPrinterConnectionLost'] = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_CONNECTION_LOST)
    #Невосстановимая ошибка печатного механизма
    dict_to_return['isPrinterError']          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_ERROR)
    #Перегрев ККТ
    dict_to_return['isPrinterOverheat']       = fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_OVERHEAT)
    #ККТ Заблокирована из-за ошибок
    dict_to_return['isDeviceBlocked']         = fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED)
    #Дата Время на кассе
    dict_to_return['dateTime'] = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
    #Серийный номер ККТ
    dict_to_return['serialNumber']    = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
    #Имя модели ККТ
    dict_to_return['modelName']       = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
    #Номер прошивки ККТ
    dict_to_return['firmwareVersion'] = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
    return dict_to_return
    
def kktfatalerrors(fptr: IFptr):
    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_FATAL_STATUS)
    fptr.queryData()
    #Остутствует серийный номер
    noSerialNumber          = fptr.getParamBool(IFptr.LIBFPTR_PARAM_NO_SERIAL_NUMBER)
    #Ошибка часов реального времени
    rtcFault                = fptr.getParamBool(IFptr.LIBFPTR_PARAM_RTC_FAULT)
    #Ошибка настроек
    settingsFault           = fptr.getParamBool(IFptr.LIBFPTR_PARAM_SETTINGS_FAULT)
    #Ошибка счетчиков
    counterFault            = fptr.getParamBool(IFptr.LIBFPTR_PARAM_COUNTERS_FAULT)
    #Ошибка пользовательской памяти
    userMemoryFault         = fptr.getParamBool(IFptr.LIBFPTR_PARAM_USER_MEMORY_FAULT)
    #Ошибка сервисных регистров
    serviceCountersFault    = fptr.getParamBool(IFptr.LIBFPTR_PARAM_SERVICE_COUNTERS_FAULT)
    #Ошибка реквизитов
    attributesFault         = fptr.getParamBool(IFptr.LIBFPTR_PARAM_ATTRIBUTES_FAULT)
    #Фатальная ошибка ФН
    fnFault                 = fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_FAULT)
    #Установлен ФН из другой ККТ
    invalidFN               = fptr.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN)
    #Фатальная аппаратная ошибка
    hardFault               = fptr.getParamBool(IFptr.LIBFPTR_PARAM_HARD_FAULT)
    #Ошибка диспетчера памяти
    memoryManagerFault      = fptr.getParamBool(IFptr.LIBFPTR_PARAM_MEMORY_MANAGER_FAULT)
    #Шаблоны повреждены или отсутствуют
    scriptFault             = fptr.getParamBool(IFptr.LIBFPTR_PARAM_SCRIPTS_FAULT)
    #Требуется перезагрузка
    waitForReboot           = fptr.getParamBool(IFptr.LIBFPTR_PARAM_WAIT_FOR_REBOOT)
    #Ошибка универсальных счётчиков
    universalCountersFault  = fptr.getParamBool(IFptr.LIBFPTR_PARAM_UNIVERSAL_COUNTERS_FAULT)
    #Ошибка таблицы товаров
    commoditiesTableFault   = fptr.getParamBool(IFptr.LIBFPTR_PARAM_COMMODITIES_TABLE_FAULT)

    #Дата и время последней успешной отправки документа в ОФД
    def ofd_last_connection(fptr: IFptr):
        fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_LAST_SENT_OFD_DOCUMENT_DATE_TIME)
        fptr.queryData()

    # Тип переменной datetime - datetime.datetime
    dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
    return dateTime


    
#Проверка кода маркировки
def checkdm(fptr):
    start_time = time()
    fptr.cancelMarkingCodeValidation()

    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '014494550435306821QXYXSALGLMYQQ\u001D91EE06\u001D92YWCXbmK6SN8vvwoxZFk7WAY9WoJNMGGr6Cgtiuja04c=')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '04603731175250\u001DTI4K_aiAAAA\u001D0m3r')
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, 'ЗАЛУПА')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, 1.000)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_FRACTIONAL_QUANTITY, '1/2')
    fptr.beginMarkingCodeValidation()

    while True:
        current_time = time()
        fptr.getMarkingCodeValidationStatus()
        if fptr.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
            break
        if int(current_time - start_time) >= 30:
            break
    validationResult = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
    isRequestSent = fptr.getParamBool(IFptr.LIBFPTR_PARAM_IS_REQUEST_SENT)
    error = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR)
    errorDescription = fptr.getParamString(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR_DESCRIPTION)
    info = fptr.getParamInt(2109)
    processingResult = fptr.getParamInt(2005)
    processingCode = fptr.getParamInt(2105)
    fptr.acceptMarkingCode()
    result = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
    return(validationResult)

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
        if IFptr.__getattribute__(IFptr, current_setting)  != 'ComFile':
            settingsdict[IFptr.__getattribute__(IFptr,current_setting)] = IFptr.__getattribute__(IFptr,formsettings[current_setting])
        else:
            settingsdict[IFptr.__getattribute__(IFptr,current_setting)] = formsettings[current_setting]
            
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