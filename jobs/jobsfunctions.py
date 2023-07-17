import kktfunc.kktfunctions as kkt


class Job:
    def __init__(self, jobname, jobparameters, jobid) -> None:
        self.jobname = jobname
        self.jobparameters = jobparameters
        self.jobid = jobid
        
    def __str__(self) -> str:
        return f'Name: {self.jobname}, ID: {self.jobid}, Parameters: {self.jobparameters}'
    
    def completeTask(self):
        with kkt.Kassa() as kassa:
            match self.jobname:
                case 'checkmark': #Проверка кода маркировки
                    taskresult = kassa.checkdm(DM_code=self.jobparameters.get('markCode'))
                case 'openShift': #Открытие смены
                    taskresult = kassa.openShift(cashier=None)
                case 'closeShift': #Закрытие смены
                    taskresult = kassa.closeShift(cashier=None)
                case 'receipt': #Чек
                    #TODO бахнуть тоже в класс
                    taskresult = kkt.receipt(fptr=None, checkType=self.jobparameters.get('checkType'), 
                                cashier=self.jobparameters.get('cashier'),
                                electronnically=self.jobparameters.get('electronnically'),
                                sno=self.jobparameters.get('sno'),
                                goods=self.jobparameters.get('goods'), 
                                cashsum=self.jobparameters.get('cashsum'),
                                cashelesssum=self.jobparameters.get('cashelesssum'),
                                taxsum=self.jobparameters.get('taxsum'),
                                corrBaseDate=self.jobparameters.get('corrBaseDate'),
                                corrBaseNum=self.jobparameters.get('corrBaseNum'))
            return taskresult
    
    def task_to_dict(self):
        retdict = {}
        retdict['jobname'] = self.jobname
        retdict['jobparameters'] = self.jobparameters
        retdict['jobid'] = self.jobid
        return retdict