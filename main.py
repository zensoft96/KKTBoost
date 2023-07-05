from kktfunc.initkkt import initkkt
from libfptr10 import IFptr
fptr = initkkt
#ggg

print(fptr.version())
settings = {
    IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_11F,
    IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
    IFptr.LIBFPTR_SETTING_COM_FILE: "COM5",
    IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200
}
fptr.setSettings(settings)
print(fptr.getSettings())
fptr.open()
print(fptr.isOpened())

fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
fptr.queryData()
operatorID      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID)
logicalNumber   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER)
shiftState      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
model           = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
mode            = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODE)
submode         = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE)
receiptNumber   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
documentNumber  = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
shiftNumber     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
receiptType     = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
documentType    = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE)
lineLength      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH)
lineLengthPix   = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX)
dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
serialNumber    = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
modelName       = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
firmwareVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)

fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
fptr.queryData()
state       = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
number      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)

fptr.setParam(1021, "Кассир Иванов И.")
fptr.setParam(1203, "123456789047")
fptr.operatorLogin()

fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
fptr.report()
if not fptr.errorCode() == 0:
    print(fptr.errorDescription())
    fptr.close

closedDoc = fptr.checkDocumentClosed()

fptr.openShift()
closedDoc = fptr.checkDocumentClosed()

fptr.close()
