# import kktfunc.kktfunctions as kkt
from libfptr10 import IFptr

def returnDict(success: bool, errorDesc: str, fptr: IFptr):
    return {'succes':success, 'descr':errorDesc, 'driver': fptr}


def checkdm(fptr, KM_):
    fptr.cancelMarkingCodeValidation()
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, '014494550435306821QXYXSALGLMYQQ\u001D91EE06\u001D92YWCXbmK6SN8vvwoxZFk7WAY9WoJNMGGr6Cgtiuja04c=')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, KM_)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, 'ЗАЛУПА')
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 1)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, 1.000)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
    # fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_FRACTIONAL_QUANTITY, '1/2')
    fptr.beginMarkingCodeValidation()

    while True:
        fptr.getMarkingCodeValidationStatus()
        if fptr.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
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

def getkktsettings():
    # current_settings = Settings.select().dicts()
    # settingdict = {}
    # if len(current_settings) > 0:
    #     for current_setting in current_settings:
    #         CURRENT_SETTING = IFptr.__getattribute__(IFptr, current_setting.get('setting'))
    #         if CURRENT_SETTING != 'ComFile':
    #             CURRENT_SETTING_VALUE = IFptr.__getattribute__(IFptr, current_setting.get('settingvalue'))
    #         else:
    #             CURRENT_SETTING_VALUE = current_setting.get('settingvalue')
    #         settingdict[CURRENT_SETTING] = CURRENT_SETTING_VALUE
    #     return settingdict
    # else:
    default_settings = {
    IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_11F,
    IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
    IFptr.LIBFPTR_SETTING_COM_FILE: "COM6",
    IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200}
    return default_settings

def initKKT():
    fptr = IFptr("")
    # if not settings:
    settings = getkktsettings()
    fptr.setSettings(settings)
    fptr.open()
    if fptr.isOpened():
        return returnDict(True,'', fptr)
    else:
        return returnDict(False, fptr.errorDescription(), None)
    
initedkkt = initKKT()
if initedkkt.get('succes'):
    driver = initedkkt.get('driver')
    res = checkdm(driver, '04640225422148bj0MQ-RAAAAbkm6')
    print(res)

else:
   print(f'Ошибка инициализации драйвера {initedkkt.get("descr")}')