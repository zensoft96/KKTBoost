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


# class DB():
#     DB_LOCATION = 'zendb.db'
    
#     def __init__(self) -> None:
#         self.error = ''
#         try:
#             self.connection = sqlite3.connect(DB.DB_LOCATION, check_same_thread=False)
#             self.cur = self.connection.cursor()
#         except sqlite3.Error as error_sql:
#             self.error = error_sql
    
#     def __del__(self):
#         self.connection.close()
        
#     def loadsettings(self):
#         result = self.connection.execute("SELECT * FROM settings")
#         return result.fetchall()
    
#     def savesettings(self, setting: tuple):
#         select_query = """SELECT setting, settingvalue FROM settings WHERE setting = ?"""
#         result = self.connection.execute(select_query, (setting[0],))
#         if result.fetchone():
#             try:
#                 self.cur.execute("UPDATE TABLE settings SET setting = ?, settingvalue = ?}", (setting[0], setting[1]))
#             except sqlite3.Error as error:
#                 print('sqlite error ', error)
#                 self.cur.close()
#         else:
#             try:
#                 self.cur.execute("INSERT INTO settings (setting, settingvalue) VALUES(?,?)", (setting[0], setting[1]))
#             except sqlite3.Error as error:
#                 print('sqlite error ', error)
#                 self.cur.close()
        
#         self.connection.commit()
#         self.cur.close()
            
#     def __enter__(self):
#         return self
            
#     def close(self):
#         self.connection.close()
        
#     def execute(self, new_data):
#         self.cur.execute(new_data)
        
#     def executemany(self, many_new_data):
#         self.cur.executemany('INSERT INTO settings (setting, settingvalue) VALUES(?, ?)', ['1','1'])
        
#     def create_table_settings(self):
#         self.cur.execute('''CREATE TABLE IF NOT EXISTS settings(id integer PRIMARY KEY AUTOINCREMENT, \
#                                                             setting text, 
#                                                             settingvalue text
#                                                             )''')
#     def checktablesettings(self):
#         tablename = 'settings'
#         self.cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='settings' ''')
#         if self.cur.fetchone()[0] == 1:
#             return True
#         else:
#             return False
        
#     def commit(self):
#         self.connection.commit()
    