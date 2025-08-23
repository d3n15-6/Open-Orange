from Embedded_OpenOrange import *

class AppCommand:
    
    def doit(self, server):
        pass

class AppCommand_Call(AppCommand):
    
    def doit(self, server):
        import OpenOrange
        func = getattr(OpenOrange, self.functionname)
        server.sendObject(func(*self.args, **self.kwargs))
        
    def __str__(self):
        return "call function %s" % self.functionname
        
class AppCommand_SaveRecord(AppCommand):
    
    def doit(self, server):
        from PythonRecord import PythonRecord
        record = self.record.toRecord()
        res = record.save_fromGUI()
        server.sendObject((res,PythonRecord(record)))
    
    def __str__(self):
        return "save record %s" % self.record


class AppCommand_ClientMessage(AppCommand):
    #this command goes from server to client
    
    def doit(self, server):
        from OpenOrange import message
        message(self.message)

    
    def __str__(self):
        return "Client Message: %s" % self.message
        
class AppCommand_GetDBConnInfo(AppCommand):
    
    def doit(self, server):
        from Company import Company
        company = Company.bring(currentCompany())
        server.sendObject(company)

    def __str__(self):
        return "send database information"
        
class AppCommand_Login(AppCommand):
    
    def doit(self, server):
        import OpenOrange
        OpenOrange.setCurrentUser(self.usercode)
        try:
            server.thread.setName("%s %s " % (OpenOrange.currentUser(),server.thread.client_address))
        except Exception, e:
            print str(e)
        server.sendObject(True)

    def __str__(self):
        return "%s loggin in" % self.usercode

class AppCommand_RunRoutine(AppCommand):
    
    def doit(self, server):
        import OpenOrange
        from PythonRecord import PythonRecord
        exec("from %s import %s" % (self.routinename, self.routinename))
        exec("routine = %s()" % self.routinename)
        sysprint("\nHH: %s\n" % self.record.fields['PriceList'])
        self.record.toRecord(routine.getRecord())
        sysprint('\nXXXXXX\n')
        server.sendObject(routine.open(False))
        
    def __str__(self):
        return "in routine %s" % self.routinename