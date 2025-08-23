from Embedded_OpenOrange import *
from AppServerConnection import AppServerConnection

class ClientRecord(Embedded_Record):
   
    def save(self):   
        from functions import alert
        from PythonRecord import PythonRecord
        res, record = AppServerConnection.conn.saveRecord(self)
        pr = PythonRecord(record)
        pr.toRecord(self)
        return res
        
    def check(self):
        return True
        
    def beforeInsert(self):
        return True

    def beforeUpdate(self):
        return True

    def afterInsert(self):
        pass

    def afterUpdate(self):
        pass