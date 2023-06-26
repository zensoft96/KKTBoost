from logging import raiseExceptions
from libfptr10 import IFptr

def initkkt():
    fptr = IFptr("")
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_11F,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
        IFptr.LIBFPTR_SETTING_COM_FILE: "COM5",
        IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200
    }

    fptr.setSettings(settings)
    fptr.open()
    if fptr.isOpened():
        return fptr
    else:
        raiseExceptions(fptr.errorDescription())
