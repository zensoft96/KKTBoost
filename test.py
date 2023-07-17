import kktfunc.kktfunctions as kkt


with kkt.Kassa() as kassa:
    try:
        print(kassa)
        print(kassa.checkdm('04603731175229CgQXbjYAAAA2X9F'))
        print(kassa.closeShift(None))
    except Exception as kktErr:
        print(kktErr)
