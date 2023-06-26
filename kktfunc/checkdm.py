from libfptr10 import IFptr

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