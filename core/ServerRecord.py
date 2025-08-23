from Embedded_OpenOrange import *
from core.Responses import *

class ServerRecord(Embedded_Record):
    
    def save(self):
        res = self.check()
        if not res: 
            rollback()
            return res
        if self.isNew():
            res = self.beforeInsert()
            if not res: 
                rollback()
                return res
            res = self.store()
            if not res: 
                rollback()
                return StoreErrorResponse()
            self.afterInsert()
        else:
            res = self.beforeUpdate()
            if not res: 
                rollback()
                return res
            res = self.store()
            if not res: 
                rollback()
                return res
            self.afterUpdate()
        return True
        
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