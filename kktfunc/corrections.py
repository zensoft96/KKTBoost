"""Для чеков коррекции на дату 05.12.2023 работает, и передает все реквизиты НО! Такском выдает такую балду, объяснить что это не хочет.
0031:

Кассовый чек коррекции

ФЛК 528: Значение "0.00" реквизита "сумма НДС чека по ставке 10%" (тег 31.1103) отличается от значения "" суммы реквизитов "сумма НДС за предмет расчета" (тег 31.1059[*].1200) предметов расчета по ставке 10% более, чем на 1 рубль

ФЛК 529: Значение "0.00" реквизита "сумма НДС чека по расч. ставке 20/120" (тег 31.1106) отличается от значения "" суммы реквизитов "сумма НДС за предмет расчета" (тег 31.1059[*].1200) предметов расчета по ставке 20/120 более, чем на 1 рубль

ФЛК 530: Значение "0.00" реквизита "сумма НДС чека по расч. ставке 10/110" (тег 31.1107) отличается от значения "" суммы реквизитов "сумма НДС за предмет расчета" (тег 31.1059[*].1200) предметов расчета по ставке 10/110 более, чем на 1 рубль

ФЛК 531: Значение "0.00" реквизита "сумма расчета по чеку с НДС по ставке 0%" (тег 31.1104) отличается от значения "" суммы реквизитов "сумма НДС за предмет расчета" (тег 31.1059[*].1200) предметов расчета по ставке 0% более, чем на 1 рубль

ФЛК 532: Значение "0.00" реквизита "сумма расчета по чеку без НДС" (тег 31.1105) отличается от значения "" суммы реквизитов "сумма НДС за предмет расчета" (тег 31.1059[*].1200) предметов расчета по ставке NoNds более, чем на 1 рубль
"""
def receiptCorrectionSELL(self, checkType:str, cashier:dict, electronnically:bool, sno: int, goods:list, cashsum:float, 
            cashelesssum: float, prepaidsum: float, #taxsum:float, 
            corrType: int = 0, corrBaseDate: str = '0001.01.01', corrBaseNum: str = '0', docsum: int = 0, clientmail:str = None, fiskalSighn: int = 0):
        driver = self.driver
        # #Печатать электронный чек не работает почему то с коррекцией
        # driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, electronnically)
        driver.setParam(1178, datetime.strptime(corrBaseDate, '%Y-%m-%dT%H:%M:%S'))
        driver.setParam(1179, "1")
        driver.utilFormTlv()

        correctionInfo = driver.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
    
        # LIBFPTR_RT_CLOSED - чек закрыт;
        # LIBFPTR_RT_SELL - чек прихода;
        # LIBFPTR_RT_SELL_RETURN - чек возврата прихода;
        # LIBFPTR_RT_SELL_CORRECTION - чек коррекции прихода;
        # LIBFPTR_RT_SELL_RETURN_CORRECTION - чек коррекции возврата прихода;
        # LIBFPTR_RT_BUY - чек расхода;
        # LIBFPTR_RT_BUY_RETURN - чек возврата расхода;
        # LIBFPTR_RT_BUY_CORRECTION - чек коррекции расхода;
        # LIBFPTR_RT_BUY_RETURN_CORRECTION - чек коррекции возврата расхода.
        if checkType.find('LIBFPTR_RT_SELL_RETURN_CORRECTION') != -1:
            driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION)
        elif checkType.find('LIBFPTR_RT_SELL_CORRECTION') != -1:
            driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_CORRECTION)
        #driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_CORRECTION)
        driver.setParam(1173, 0)
        driver.setParam(1174, correctionInfo)
        #driver.setParam(1055, self.snoClass(sno=sno))
        driver.setParam(1055, 0) #ОСН
        for good in goods:
            if good.get('markingcode') is not None:
                self.checkdm(good['markingcode'])
        sumerrors = "" #Для сбора промежуточных ошибок  
        driver.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, electronnically)
        driver.setParam(1192, str(fiskalSighn))
        driver.openReceipt()
        if driver.errorCode() > 0:
             sumerrors += f'\n {driver.errorDescription()}'
        if fiskalSighn == 0:
            return {
                'success': False,
                'errorDesc': f'Не указан фискальный признак {driver.errorDescription()}'}
        for good in goods:
            driver.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, good['name'])
            driver.setParam(IFptr.LIBFPTR_PARAM_PRICE, good['price'])
            driver.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, good['quantity'])
            goodtax = self.tax(good['tax'])
            if goodtax is None:
                sumerrors += f'\n Не пришла налоговая ставка для {good["name"]}'
            else:
                driver.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, goodtax)
            #GIV 29.11.2023 TEST
            #driver.setParam(IFptr.LIBFPTR_PARAM_USE_ONLY_TAX_TYPE, True)
            #driver.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, good['price'] * good['quantity'] * 20 /120)
            driver.setParam(1212, good['ppr']) 
            #Признак предмета расчета
            """30 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки
                31 о реализуемом подакцизном товаре, подлежащем маркировке средством идентификации, имеющем код маркировки
                32 о реализуемом товаре, подлежащем маркировке средством идентификации, не имеющем кода маркировки, за исключением подакцизного товара
                33 о реализуемом товаре, подлежащем маркировке средством идентификации, имеющем код маркировки, за исключением подакцизного товара
            """
            driver.setParam(2108, 0)
            # Мера количества предмета расчета https://www.consultant.ru/document/cons_doc_LAW_362322/0060b1f1924347c03afbc57a8d4af63888f81c6c/
            driver.setParam(1214, good['psr']) #Признак способа расчета
            
            if good.get('markingcode') is not None:
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, good['markingcode'])
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_WAIT_FOR_VALIDATION_RESULT, True)
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
                validationResult = driver.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
                driver.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, validationResult)
            
            driver.registration() # Регистрация позиции
        if prepaidsum > 0:
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_PREPAID)
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, prepaidsum)
            #driver.payment()
        elif cashelesssum > 0:
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashelesssum)
            #driver.payment()
        elif cashsum > 0:
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
            driver.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, cashsum)
            #driver.payment()
        else: return 'Нет сумм чека'    
        driver.payment() # Регистрация оплаты
        driver.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT20)
        driver.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, round(docsum * 20 / 120, 2))
        driver.receiptTax() # Регистрация налога на чек
        if driver.errorCode() > 0:
            sumerrors += f'\n {driver.errorDescription()}'
        driver.setParam(IFptr.LIBFPTR_PARAM_SUM, docsum)
        driver.receiptTotal() # Регистрация итога чека
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
            return {
                'success': False, 
                'errorDesc':f'Не удалось проверить состояние документа {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'
                }
        
        if not driver.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
            # Документ не закрылся. Требуется его отменить (если это чек) и сформировать заново
            driver.cancelReceipt()
            errorDesc = driver.errorDescription()
            errorCode = driver.errorCode()
            driver.close()
            return {
                'success': False,
                'errorDesc': f'Не удалось закрыть документ {errorDesc} код ошибки {errorCode}. Промежуточные ошибки {sumerrors}'
            }

        if not driver.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
        # Можно сразу вызвать метод допечатывания документа, он завершится с ошибкой, если это невозможно
            while driver.continuePrint() < 0:
                # Если не удалось допечатать документ - показать пользователю ошибку и попробовать еще раз.            
                errorDesc = driver.errorDescription()
                errorCode = driver.errorCode()
                driver.close()
                return {
                    'sucess': False,
                    'errorDesc': f'Не удалось напечатать документ (Ошибка {errorDesc}). Устраните неполадку и повторите. Промежуточные ошибки {sumerrors}'
                }
                
        #Все проверки пройдены, чек есть, запрашиваем параметры
        driver.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
        driver.fnQueryData()
        if driver.errorCode() == 0:
            resultDict = {
                        'success': True,
                        'documentNumber' : driver.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
                        'receiptType' : driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
                        'fiscalSign' : driver.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN),
                        }
            driver.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
            driver.queryData()
            resultDict['receiptSum'] = driver.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM)
            resultDict['dateTime'] = str(driver.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME))
            resultDict['receiptNumber'] = driver.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
            driver.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
            driver.queryData()
            resultDict['shiftNumber']  = driver.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            return resultDict
        else:
            return {
                'success': False,
                'errorDesc': f'Проблема запроса ФПД чека {driver.errorDescription()}'}
        
