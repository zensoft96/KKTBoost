from ast import If
import json
from logging import raiseExceptions
from itsdangerous import base64_decode
#from kktfunc.initkkt import initkkt
from libfptr10 import IFptr
from sql.sqlfunc import *
from time import time

def returnDict(success: bool, errorDesc: str, fptr: IFptr):
    """Возвращает словарь с параметрами выполнения функции

    Args:
        success (bool): Успешна ли прошла операция
        errorDesc (str): Описание ошибки
        fptr (IFptr): Экземпляр класса IFptr, драйвер ККТ

    Returns:
        dict : Словарь с аргументами
    """    
    return {'succes':success, 'descr':errorDesc, 'driver': fptr}

def fnmKeys():
    pass

def checkTypeClass(checkType):
    checkTypes = {
        "SELL":IFptr.LIBFPTR_RT_SELL,
        "SELLRETURN": IFptr.LIBFPTR_RT_SELL_RETURN,
        "SELLCORR": IFptr.LIBFPTR_RT_SELL_CORRECTION,
        "SELLRETURNCORR": IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION,
        "BUY":IFptr.LIBFPTR_RT_BUY,
        "BUYRETURN":IFptr.LIBFPTR_RT_BUY_RETURN,
        "BUYCORR": IFptr.LIBFPTR_RT_BUY_CORRECTION,
        "BUYRETURNCORR": IFptr.LIBFPTR_RT_BUY_RETURN_CORRECTION
    }
    return checkTypes.get(checkType)

def snoClass(sno):
    snoDict = {
        0:IFptr.LIBFPTR_TT_OSN,
        1:IFptr.LIBFPTR_TT_USN_INCOME,
        2:IFptr.LIBFPTR_TT_USN_INCOME_OUTCOME,
        3:IFptr.LIBFPTR_TT_ESN,
        4:IFptr.LIBFPTR_TT_PATENT
            }
    return snoDict[sno]


def tax(strtax:str):
    taxes = {'NO':IFptr.LIBFPTR_TAX_NO,
             '0': IFptr.LIBFPTR_TAX_VAT0,
             '10': IFptr.LIBFPTR_TAX_VAT10,
             '110': IFptr.LIBFPTR_TAX_VAT110,
             '118': IFptr.LIBFPTR_TAX_VAT118,
             '120': IFptr.LIBFPTR_TAX_VAT120,
             'NO': IFptr.LIBFPTR_TAX_NO,
             '18': IFptr.LIBFPTR_TAX_VAT18,
             '20': IFptr.LIBFPTR_TAX_VAT20}
    return taxes.get(strtax)

def receipt(fptr:IFptr, checkType:str, cashier:dict, electronnically:bool, sno: int, goods:list, cashsum:float, 
            cashelesssum: float, taxsum:float):
    """Формирование чека состоит из следующих операций:
    открытие чека и передача реквизитов чека;
    регистрация позиций, печать нефискальных данных (текст, штрихкоды, изображения);
    регистрация итога (необязательный пункт - если регистрацию итога не провести, он автоматически рассчитается из суммы всех позиций);
    регистрация налогов на чек (необязательный пункт - налоги могут быть подтянуты из позиций и суммированы);
    регистрация оплат;
    закрытие чека;
    проверка состояния чека.
    
    Args:
        checkType (str): Тип чека, ждем аргументы SELL - чек продажи, SELLRETURN - чек возврата, SELLCORR - чек коррекции,
        SELLRETURNCORR - чек кореекции возврата, BUY - чек расхода(покупки), BUYCORR - Чек коррекции расхода, 
        BUYRETURNCORR - Чек коррекции возврата расхода, BUYRETURN - Чек возврата расхода(покупки),
        cashier (dict): Кассир, словарь, {cashierName: Иванов А.А., INN: ИННКассира}
        fptr (IFptr): Текущий драйвер ККТ
        electronnically (bool): Печатать чек электронно(не на бумаге)
        sno (int): Система налогообложения, 0 - Общая, 1 - УСН Доход, 2 - УСН Доход-Расход, 3 - ЕНВД, 4 - ЕСХН, 5 - Патент
        goods (list): Список с товарами(словарь)
        cashsum (float): Сумма оплаты наличными
        cashelesssum (float): Сумма оплаты безналичными
        taxsum (float): Сумма налога чека
    """    
    # fptr.cancelMarkingCodeValidation()
    for good in goods:
        checkdm(fptr, good['markingcode'])
    
    sumerrors = "" #Для сбора промежуточных ошибок
    fptr.setParam(1021, cashier['cashierName'])
    fptr.setParam(1203, cashier['INN'])
    fptr.operatorLogin()
    
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, checkTypeClass(checkType=checkType))
    #Печатать электронный чек
    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, electronnically)
    #Налогообложение
    fptr.setParam(1055, snoClass(sno=sno))
    fptr.openReceipt()
    if fptr.errorCode() > 0:
        sumerrors += f'\n {fptr.errorDescription()}'
    
    #Регистрация позиции с кодом маркировки сделать столько итераций сколько товаров
    #Соглашение, жду в словаре name - Имя товара, price - цена, quantity - количество
    # tax - Налоговая ставка, sum - Сумма, markingCode - Код маркировки(массив байт в base64)
    for good in goods:
        fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, good['name'])
        fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, good['price'])
        fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, good['quantity'])
        goodtax = tax(good['tax'])
        if goodtax is None:
            return f'Не пришла налоговая ставка для {good["name"]}'
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, goodtax)
        fptr.setParam(1212, good['ppr']) #Признак предмета расчета
        """30 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки
            31 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, имеющем код маркировки
            32 о реализуемом товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки, за исключением подакцизного товара
            33 о реализуемом товаре, подлежащем маркировке средством идентификации, имеющем код маркировки, за исключением подакцизного товара
        """
        fptr.setParam(1214, good['psr']) #Признак способа расчета
        
        # fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, 200.02)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, good['markingcode'])
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_WAIT_FOR_VALIDATION_RESULT, True)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT))
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)

	
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, good['markingcode'])
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_WAIT_FOR_VALIDATION_RESULT, True)
        
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
        validationResult = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, validationResult)
        
        fptr.registration()
    
    if cashelesssum > 0:
        fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
        fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashelesssum)
        fptr.payment()
    elif cashsum > 0:
        fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
        fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashsum)
        fptr.payment()
    else: return 'Нет сумм чека'
    
    
    fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, goodtax)
    fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, taxsum)
    fptr.receiptTax()
    if fptr.errorCode() > 0:
        sumerrors += f'\n {fptr.errorDescription()}'

    fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, 10.00)
    fptr.receiptTotal()
    #Закрытие полность оплаченного чека
    fptr.closeReceipt()
    if fptr.errorCode() > 0:
        sumerrors += f'\n {fptr.errorDescription()}'
    
    # Тут или после проверки? Очистка кодов из таблицы.
    fptr.clearMarkingCodeValidationResult()
    while fptr.checkDocumentClosed() < 0:
        # Не удалось проверить состояние документа. Вывести пользователю текст ошибки, попросить устранить неполадку и повторить запрос
        errorDesc = fptr.errorDescription()
        errorCode = fptr.errorCode()
        fptr.close()
        return f'Не удалось проверить состояние документа {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'
    
    if not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
        # Документ не закрылся. Требуется его отменить (если это чек) и сформировать заново
        fptr.cancelReceipt()
        errorDesc = fptr.errorDescription()
        errorCode = fptr.errorCode()
        fptr.close()
        return f'Не удалось закрыть документ {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'

    if not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
    # Можно сразу вызвать метод допечатывания документа, он завершится с ошибкой, если это невозможно
        while fptr.continuePrint() < 0:
            # Если не удалось допечатать документ - показать пользователю ошибку и попробовать еще раз.            
            errorDesc = fptr.errorDescription()
            errorCode = fptr.errorCode()
            fptr.close()
            return f'Не удалось напечатать документ (Ошибка {errorDesc}). Устраните неполадку и повторите. Промежуточные ошибки {sumerrors}'
    #Все проверки пройдены, чек есть, запрашиваем параметры
    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
    fptr.fnQueryData()
    if fptr.errorCode() == 0:
        resultDict = {'documentNumber' : fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
        'receiptType' : fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
        'receiptSum' : fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
        'fiscalSign' : fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN),
        'dateTime' : fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)}
        return resultDict
    else:
        return f'Проблема запроса ФПД чека {fptr.errorDescription()}'


def receipt_type(LIBFPTR_PARAM_RECEIPT_TYPE: IFptr.LIBFPTR_PARAM_RECEIPT_TYPE):
    """ Возврат типа чека, либо чек закрыт

    Args:
        LIBFPTR_PARAM_RECEIPT_TYPE (IFptr.LIBFPTR_PARAM_RECEIPT_TYPE): Тип чека

    Returns:
        str : Человекопонятный текст
    """    
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

def returnTextValidationResult (result):
    text_results = {
        '0' : "Проверка КП КМ не выполнена, статус товара ОИСМ не проверен [М]",
        '1' : "Проверка КП КМ выполнена в ФН с отрицательным результатом, статус товара ОИСМ не проверен [М-]",
        '3' : "Проверка КП КМ выполнена с положительным результатом, статус товара ОИСМ не проверен [М]",
        '16' : "Проверка КП КМ не выполнена, статус товара ОИСМ не проверен (ККТ функционирует в автономном режиме) [М]",
        '17' : "Проверка КП КМ выполнена в ФН с отрицательным результатом, статус товара ОИСМ не проверен (ККТ функционирует в автономном режиме) [М-]",
        '19' : "Проверка КП КМ выполнена в ФН с положительным результатом, статус товара ОИСМ не проверен (ККТ функционирует в автономном режиме) [М]",
        '5' : "Проверка КП КМ выполнена с отрицательным результатом, статус товара у ОИСМ некорректен [М-]",
        '7' : "Проверка КП КМ выполнена с положительным результатом, статус товара у ОИСМ некорректен [М-]",
        '15' : "Проверка КП КМ выполнена с положительным результатом, статус товара у ОИСМ корректен [М+]"

    }
    try:
        result = text_results[result]
        return result
    except:
        return 'Не получен статус проверки'
    
#Проверка кода маркировки
def checkdm(fptr, DM_code):
    start_time = time()
    fptr.cancelMarkingCodeValidation()

    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '014494550435306821QXYXSALGLMYQQ\u001D91EE06\u001D92YWCXbmK6SN8vvwoxZFk7WAY9WoJNMGGr6Cgtiuja04c=')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, DM_code)
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
    # isRequestSent = fptr.getParamBool(IFptr.LIBFPTR_PARAM_IS_REQUEST_SENT)
    # error = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR)
    # errorDescription = fptr.getParamString(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR_DESCRIPTION)
    # info = fptr.getParamInt(2109)
    # processingResult = fptr.getParamInt(2005)
    # processingCode = fptr.getParamInt(2105)
    fptr.acceptMarkingCode()
    result = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
    return(returnTextValidationResult(str(result)))

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
    fptr.setParam(1021, "Соколов В.И.")
    fptr.setParam(1203, "665811557830")
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
            if current_setting.get('setting') != 'cashier':
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
        # if IFptr.__getattribute__(IFptr, current_setting)  != 'ComFile':
        #     settingsdict[current_setting] = formsettings[current_setting]
        # else:
        settingsdict[current_setting] = formsettings[current_setting]
            
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