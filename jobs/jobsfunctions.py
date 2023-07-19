from uuid import uuid4
import kktfunc.kktfunctions as kkt


class Job:
    """Работа в очереди
    """
    def __init__(self, jobname:str, jobparameters:dict, jobid:uuid4, jobrotate:int) -> None:
        """_Работа в очереди_

        Args:
            jobname (str): Наименование работы checkmark(ПроверкаКМ), openShift(ОткрСмены), closeShift, receipt(Чек)
            jobparameters (dict): Параметры задачи, принятные в запросе и требуемые для функции обработки
            jobid (uuid4): UUID4 - Угикальные номер задачи, по которому ее можно будет запросить
            jobrotate (int):  Сколько раз задача попыталась выполниться
        """
        self.jobname = jobname
        self.jobparameters = jobparameters
        self.jobid = jobid
        if jobrotate is None:
            self.jobrotate = 0
        else:
            self.jobrotate = jobrotate
        
    def __str__(self) -> str:
        return f'Name: {self.jobname}, ID: {self.jobid}, Parameters: {self.jobparameters}, Rotate: {self.jobrotate}'
    
    def completeTask(self):
        try:
            with kkt.Kassa() as kassa:
                match self.jobname:
                    case 'checkmark': #Проверка кода маркировки
                        taskresult = kassa.checkdm(DM_code=self.jobparameters.get('markCode'))
                    case 'openShift': #Открытие смены
                        taskresult = kassa.openShift(cashier=None)
                    case 'closeShift': #Закрытие смены
                        taskresult = kassa.closeShift(cashier=None)
                    case 'receipt': #Чек
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
        except:
            self.jobrotate += 1
            return None
            
    
    def task_to_dict(self):
        retdict = {}
        retdict['jobname'] = self.jobname
        retdict['parameters'] = self.jobparameters
        retdict['jobid'] = self.jobid
        retdict['jobrotate'] = self.jobrotate
        return retdict