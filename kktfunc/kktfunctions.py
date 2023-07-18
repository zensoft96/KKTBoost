
import json
from sys import exception
from app import settings
from libfptr10 import IFptr
from sql.sqlfunc import *
from time import time

class KassaBusyError(Exception):
    """Ошибка, касса сейчас в работе, нужно повторить задачу"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class KassaCriticalError(Exception):
    """Критичная ошибка ККТ, надо принимать действия(отмена задачи)"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Kassa():
    
    __busy = False
        
    def __init__(self) -> None:
        self.settings = self.getkktsettings()
            
    # def __del__(self):
    #     print('Закрытие ресурса')

    #Получить настройки ККТ
    def getkktsettings(self):
        current_settings = Settings.select().dicts()
        settingdict = {}
        if len(current_settings) > 0:
            for current_setting in current_settings:
                try:
                    CURRENT_SETTING = IFptr.__getattribute__(IFptr, current_setting.get('setting'))
                except:
                    CURRENT_SETTING = current_setting.get('setting')
                if CURRENT_SETTING != 'ComFile' and CURRENT_SETTING != 'cashier':
                    CURRENT_SETTING_VALUE = IFptr.__getattribute__(IFptr, current_setting.get('settingvalue'))
                else:
                    CURRENT_SETTING_VALUE = current_setting.get('settingvalue')
                settingdict[CURRENT_SETTING] = CURRENT_SETTING_VALUE
            return settingdict
        else:
            raise KassaCriticalError(f'Нет настроек ККТ в базе, зайдите в web и выполните начальную настройку кассы')
        
    #Текущее состояние смены
    def checkShift(self):
        driver = self.driver
        driver.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        driver.queryData()
        shiftState = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
        shiftDict = {}
        shiftDict['Closed'] = shiftState == IFptr.LIBFPTR_SS_CLOSED
        shiftDict['Expired'] = shiftState == IFptr.LIBFPTR_SS_EXPIRED
        shiftDict['Opened'] = shiftState == IFptr.LIBFPTR_SS_OPENED
        return shiftDict
    
    def receipt(self, checkType:str, cashier:dict, electronnically:bool, sno: int, goods:list, cashsum:float, 
            cashelesssum: float, #taxsum:float, 
            corrType: int = 0, corrBaseDate: str = '0001.01.01', corrBaseNum: str = '0'):
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
            Если чек коррекции: 
            corrType (int): Тип коррекции (0 - самостоятельно, 1 - по предписанию)
            corrBaseDate (str): Дата совершения корректируемого расчета	в формате yyyy.mm.dd
            corrBaseNum (str): Номер предписания налогового органа

        """    
    # fptr.cancelMarkingCodeValidation()
        driver = self.driver
        for good in goods:
            self.checkdm(good['markingcode'])
        
        sumerrors = "" #Для сбора промежуточных ошибок
        self.setcashier(cashier=cashier)
        # driver.setParam(1021, cashier['cashierName'])
        # driver.setParam(1203, cashier['INN'])
        # driver.operatorLogin()
        
        driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, checkTypeClass(checkType=checkType))
        #Печатать электронный чек
        driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, electronnically)
        #Налогообложение
        driver.setParam(1055, snoClass(sno=sno))

        if checkType.upper().find('CORR') != -1:
            driver.setParam(1178, corrBaseDate)
            driver.setParam(1179, corrBaseNum)
            driver.utilFormTlv() #формируется основание для коррекции на основании реквизитов 1178 и 1179
            correctionInfo = driver.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)

            driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_CORRECTION)
            driver.setParam(1173, corrType)
            driver.setParam(1174, correctionInfo)

        driver.openReceipt()
        if driver.errorCode() > 0:
            sumerrors += f'\n {driver.errorDescription()}'
        
        #Регистрация позиции с кодом маркировки сделать столько итераций сколько товаров
        #Соглашение, жду в словаре name - Имя товара, price - цена, quantity - количество
        # tax - Налоговая ставка, sum - Сумма, markingCode - Код маркировки(массив байт в base64)
        for good in goods:
            driver.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, good['name'])
            driver.setParam(IFptr.LIBFPTR_PARAM_PRICE, good['price'])
            driver.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, good['quantity'])
            goodtax = tax(good['tax'])
            if goodtax is None:
                return f'Не пришла налоговая ставка для {good["name"]}'
            driver.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, goodtax)
            driver.setParam(1212, good['ppr']) 
            #Признак предмета расчета
            """30 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки
                31 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, имеющем код маркировки
                32 о реализуемом товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки, за исключением подакцизного товара
                33 о реализуемом товаре, подлежащем маркировке средством идентификации, имеющем код маркировки, за исключением подакцизного товара
            """
            driver.setParam(1214, good['psr']) #Признак способа расчета
            
            # fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, 200.02)
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, good['markingcode'])
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_WAIT_FOR_VALIDATION_RESULT, True)
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT))
            # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)

        
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, good['markingcode'])
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_WAIT_FOR_VALIDATION_RESULT, True)
            
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
            validationResult = driver.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
            driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, validationResult)
            
            driver.registration()
        
        if cashelesssum > 0:
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashelesssum)
            driver.payment()
        elif cashsum > 0:
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashsum)
            driver.payment()
        else: return 'Нет сумм чека'
        
        
        driver.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, goodtax)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, taxsum)
        driver.receiptTax()
        if driver.errorCode() > 0:
            sumerrors += f'\n {driver.errorDescription()}'

        driver.setParam(IFptr.LIBFPTR_PARAM_SUM, 10.00)
        driver.receiptTotal()
        #Закрытие полность оплаченного чека
        driver.closeReceipt()
        if driver.errorCode() > 0:
            sumerrors += f'\n {driver.errorDescription()}'
        
        # Тут или после проверки? Очистка кодов из таблицы.
        driver.clearMarkingCodeValidationResult()
        while driver.checkDocumentClosed() < 0:
            # Не удалось проверить состояние документа. Вывести пользователю текст ошибки, попросить устранить неполадку и повторить запрос
            errorDesc = driver.errorDescription()
            errorCode = driver.errorCode()
            driver.close()
            return f'Не удалось проверить состояние документа {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'
        
        if not driver.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
            # Документ не закрылся. Требуется его отменить (если это чек) и сформировать заново
            driver.cancelReceipt()
            errorDesc = driver.errorDescription()
            errorCode = driver.errorCode()
            driver.close()
            return f'Не удалось закрыть документ {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'

        if not driver.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
        # Можно сразу вызвать метод допечатывания документа, он завершится с ошибкой, если это невозможно
            while driver.continuePrint() < 0:
                # Если не удалось допечатать документ - показать пользователю ошибку и попробовать еще раз.            
                errorDesc = driver.errorDescription()
                errorCode = driver.errorCode()
                driver.close()
                return f'Не удалось напечатать документ (Ошибка {errorDesc}). Устраните неполадку и повторите. Промежуточные ошибки {sumerrors}'
        #Все проверки пройдены, чек есть, запрашиваем параметры
        driver.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
        driver.fnQueryData()
        if driver.errorCode() == 0:
            resultDict = {'documentNumber' : driver.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            'receiptType' : driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
            'receiptSum' : driver.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
            'fiscalSign' : driver.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN),
            'dateTime' : driver.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME),
            'shiftNumber': driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            'receiptNumber': driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)}
            return resultDict
        else:
            return f'Проблема запроса ФПД чека {driver.errorDescription()}'
        
        #Настройки(свойства ККТ)
    def kktproperties(self):
        driver = self.driver
        driver.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        driver.queryData()
        dict_to_return = {}
        #Номер кассира
        dict_to_return['operatorID']      = driver.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID)
        #Номер ККТ в магазине
        dict_to_return['logicalNumber']   = driver.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER)
        #Состояние смены
        dict_to_return['shiftClosed']= driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_CLOSED
        dict_to_return['shiftOpened'] = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_OPENED
        dict_to_return['shiftExpired'] = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE) == IFptr.LIBFPTR_SS_EXPIRED
        #Модель
        dict_to_return['model']           = driver.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
        #Режим ККТ
        dict_to_return['mode']            = driver.getParamInt(IFptr.LIBFPTR_PARAM_MODE)
        #Подрежим ККТ
        dict_to_return['submode']         = driver.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE)
        #Номер чека
        dict_to_return['receiptNumber']   = driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
        #Номер документа
        dict_to_return['documentNumber']  = driver.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        #Номер смены
        dict_to_return['shiftNumber']     = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
        #Тип открытого чека
        dict_to_return['receiptType']     = receipt_type(driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE))
        #Тип открытого документа
        dict_to_return['documentType']    = document_type(driver.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE))
        #ККТ Зарегистрирована
        dict_to_return['isFiscalDevice']          = driver.getParamBool(IFptr.LIBFPTR_PARAM_FISCAL)
        #ФН Фискализован
        dict_to_return['isFiscalFN']              = driver.getParamBool(IFptr.LIBFPTR_PARAM_FN_FISCAL)
        #ФН Присутствует
        dict_to_return['isFNPresent']             = driver.getParamBool(IFptr.LIBFPTR_PARAM_FN_PRESENT)
        #ФН НЕ Правильный
        dict_to_return['isInvalidFN']             = driver.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN)
        #Бумага присутствует
        dict_to_return['isPaperPresent']          = driver.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT)
        #Бумага заканчивается
        dict_to_return['isPaperNearEnd']          = driver.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END)
        #Крышка открыта
        dict_to_return['isCoverOpened']           = driver.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED)
        #Потеряно соединение с печатным механизмом
        dict_to_return['isPrinterConnectionLost'] = driver.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_CONNECTION_LOST)
        #Невосстановимая ошибка печатного механизма
        dict_to_return['isPrinterError']          = driver.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_ERROR)
        #Перегрев ККТ
        dict_to_return['isPrinterOverheat']       = driver.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_OVERHEAT)
        #ККТ Заблокирована из-за ошибок
        dict_to_return['isDeviceBlocked']         = driver.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED)
        #Дата Время на кассе
        dict_to_return['dateTime'] = driver.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        #Серийный номер ККТ
        dict_to_return['serialNumber']    = driver.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        #Имя модели ККТ
        dict_to_return['modelName']       = driver.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
        #Номер прошивки ККТ
        dict_to_return['firmwareVersion'] = driver.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        return dict_to_return
        
    def close(self):
        Kassa().__unsetBusy()
        self.driver.close()
        
        
    #Открытие смены
    def openShift(self, cashier: json):
        driver = self.driver
        try:
            self.setcashier(cashier)
        except Exception as SetCashierError:
            return self.creturnDict(False, {}, SetCashierError)
        driver.openShift()
        if driver.errorCode() == 0:
            return self.creturnDict(True,{},None)
        else:
            return self.creturnDict(False,{}, f'Ошибка при открытии смены {driver.errorDescription()}')
            
        
    #Закрытие смены
    def closeShift(self, cashier: json):
        driver = self.driver
        try:
            self.setcashier(cashier)
        except Exception as SetCashierError:
            return self.creturnDict(False, {}, SetCashierError)
        if driver.isOpened():
            driver.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
            driver.report()
            if driver.errorCode() == 0:
                return self.creturnDict(True, {}, None)
            else:
                return self.creturnDict(False,{}, f'{driver.errorDescription()}')
        else:
            return self.creturnDict(False,{}, f'Ошибка проверки обр к драйверу {driver.errorDescription()}')
    
    def returnTextValidationResult (self, result):
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
    def checkdm(self, DM_code):
        driver = self.driver
        start_time = time()
        driver.cancelMarkingCodeValidation()

        driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '014494550435306821QXYXSALGLMYQQ\u001D91EE06\u001D92YWCXbmK6SN8vvwoxZFk7WAY9WoJNMGGr6Cgtiuja04c=')
        driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, DM_code)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, 'ЗАЛУПА')
        driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, 1.000)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
        driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
        # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_FRACTIONAL_QUANTITY, '1/2')
        driver.beginMarkingCodeValidation()

        while True:
            current_time = time()
            driver.getMarkingCodeValidationStatus()
            if driver.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
                break
            if int(current_time - start_time) >= 7:
                break
        validationResult = driver.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
        # isRequestSent = fptr.getParamBool(IFptr.LIBFPTR_PARAM_IS_REQUEST_SENT)
        # error = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR)
        # errorDescription = fptr.getParamString(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_ERROR_DESCRIPTION)
        # info = fptr.getParamInt(2109)
        # processingResult = fptr.getParamInt(2005)
        # processingCode = fptr.getParamInt(2105)
        driver.acceptMarkingCode()
        result = driver.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
        return(returnTextValidationResult(str(result)))
        
        
     # Установка кассира
    def setcashier(self, cashier: json):
        driver = self.driver
        if cashier is None:
            sqlsettings = Settings()
            cashierName = sqlsettings.get_or_none(Settings.setting == 'cashier')
            if cashierName is not None:
                driver.setParam(1021, cashierName.settingvalue)
                return self
            else:
                raise exception(f'Касир не получен в запросе, кассир по умолчанию не установлен')            
        else:
            driver.setParam(1021, cashier.get("cashierName"))
            #driver.setParam(1203, "665811557830")
            driver.operatorLogin()
            if driver.errorCode() == 0:
                return returnDict(True, '', None)
            else:    
                raise exception(f'Проблема при установке кассира {driver.errorDescription()}')
                # return returnDict(False, fptr.errorDescription(), None)
        
    def settings():
        pass
    
    
    def creturnDict(self, success=False, parameters={}, errordesc=None):
        """Возврат словаря
        
        Args:
            success (bool): Успех выполнения
            parameters (Dict): Словарь параметров выполнения
            errordesc (str): Описание ошибки . Defaults to None.

        Returns:
            Dict: Словарь с передаваемыми значениями
        """        
        retDict = {'success':success,
                   'errordesc': '',
                   'parameters':parameters}
        if errordesc is not None:
            retDict['errordesc'] = errordesc
        return retDict
    
    def __str__(self):
        return f'ДрайверККТ инициализирован: {self.driver.isOpened()}'
        
    def __enter__(self):
        if not Kassa().__busy:
            fptr = IFptr("")
            fptr.setSettings(self.settings)
            fptr.open()
            if fptr.isOpened():
                #Удачно соединились, драйвер есть
                Kassa().__setBusy()
                self.driver = fptr
                return self
            else:
                #Неудачно соединились, вернуть exit
                raise KassaCriticalError(f'Проблема инициализации драйвера возможно ККТ выключена')
        else:
            raise KassaBusyError(f'Касса сейчас занята')
    
    def __exit__(self, exc_type, exc_value, traceback):
        #Убираем флаг занято
        Kassa().__unsetBusy()
        #Выключаем работу с драйвером
        self.driver.close()
        #Возвращаем ответ
        if exc_type is not None:
            return self.creturnDict(False, f'Зафиксировано исключение {exc_value}, тип исключения {exc_type}')
        else:
            return self.creturnDict(success=True)
        
        
    @classmethod
    def __setBusy(cls):
        cls.__busy = True
    
    @classmethod
    def __unsetBusy(cls):
        cls.__busy = False
        

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
            cashelesssum: float, #taxsum:float, 
            corrType: int = 0, corrBaseDate: str = '0001.01.01', corrBaseNum: str = '0'):
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
        Если чек коррекции: 
        corrType (int): Тип коррекции (0 - самостоятельно, 1 - по предписанию)
        corrBaseDate (str): Дата совершения корректируемого расчета	в формате yyyy.mm.dd
        corrBaseNum (str): Номер предписания налогового органа

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

    if checkType.upper().find('CORR') != -1:
        fptr.setParam(1178, corrBaseDate)
        fptr.setParam(1179, corrBaseNum)
        fptr.utilFormTlv() #формируется основание для коррекции на основании реквизитов 1178 и 1179
        correctionInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)

        fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_CORRECTION)
        fptr.setParam(1173, corrType)
        fptr.setParam(1174, correctionInfo)

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
    # fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, taxsum)
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
        'dateTime' : fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME),
        'shiftNumber': fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
        'receiptNumber': fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)}
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

#TODO Инициализация ККТ Очень подумать за переносить или нет в класс
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
    else: #TODO кассир не пришел, надо взять из БД, Реализовано в классе
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
    else: #TODO кассир не пришел, надо взять из БД, Реализовано в классе
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
            try:
                CURRENT_SETTING = IFptr.__getattribute__(IFptr, current_setting.get('setting'))
            except:
                CURRENT_SETTING = current_setting.get('setting')
            if CURRENT_SETTING != 'ComFile' and CURRENT_SETTING != 'cashier':
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