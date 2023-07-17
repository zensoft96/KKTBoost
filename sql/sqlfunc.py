from peewee import *

db = SqliteDatabase('settings.db')

class Settings(Model):
    setting = TextField(unique=True, help_text='Имя настройки', db_column='setting')
    settingvalue = TextField(unique=True, help_text='Значение настройки', db_column='settingvalue')
        
    class Meta:
        database = db
        db_table = 'settings'
        
class FiskalOrders(Model):
    fpd = IntegerField()
    sum = FloatField()
    
    class Meta:
        database = db
        db_table = 'fiskal_orders'

class Doned_jobs(Model):
    jobid = UUIDField(unique=True, help_text='Имя задачи', db_column='jobid')
    resulttext = TextField(unique=False, help_text='Результат', db_column='result')
    recieved = BooleanField(unique=False, help_text='Получено в 1С',db_column='recieved')
    
    class Meta:
        database = db
        db_table = 'jobresults'