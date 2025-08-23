from Embedded_OpenOrange import Embedded_Thread, sysprint
from core.database.Database import Database
from Log import log

class CThread(Embedded_Thread):

    def call_beforePleaseFinish_fromC(self):
        return self.beforePleaseFinish()

    def beforePleaseFinish(self):
        pass
        
    def run(self):
        pass
    
    def call_run_fromC(self):
        try:
            return self.run()
        finally:
            import threading
            if hasattr(threading.currentThread(), "database"):
                threading.currentThread().database.releaseConnection(threading.currentThread())

    def run(self):
        pass
        
