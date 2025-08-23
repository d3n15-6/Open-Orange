#encoding: utf-8
from OpenOrange import *
from core.database.Database import DBError

ParentTask = SuperClass("Task", "Numerable", __file__)
class Task(ParentTask):    

    def defaults(self):
        ParentTask.defaults(self)
        self.Background = True
        self.User = currentUser()
        self.ScheduleMode = 0

    def check(self):
        result = ParentTask.check(self)
        if not result:
            return result
        if (not self.Comment):
            return self.FieldErrorResponse("NONBLANKERR","Comment")
        if (self.ScheduleMode==0 and not self.DayTime):
            return self.FieldErrorResponse("NONBLANKERR","DayTime")
        if (self.ScheduleMode==1 and not self.WeekDay):  
            return self.FieldErrorResponse("NONBLANKERR","WeekDay")
        if (self.ScheduleMode==2 and not self.MonthDay in range(0,31)): 
            return self.FieldErrorResponse("INVALID","MonthDay")
        return True

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentTask.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if (fieldname == "DayTime" and self.ScheduleMode <> 0):
            return False
        elif (fieldname == "WeekDay" and self.ScheduleMode <> 1):
            return False
        elif (fieldname == "MonthDay" and self.ScheduleMode <> 2):
            return False
        elif (fieldname == "Interval" and self.ScheduleMode <> 4):
            return False
        return res
        
    def execute_fromC(self):
        #este metodo es llamado de C cada vez que la tarea se debe correr.
        try:
            self.execute()
        except DBError, e:
            processDBError(e, {}, str(e))


    def execute(self):
        try:
            if not self.Running:
                self.LastBeginRunDate = today()
                self.LastBeginRunTime = now()
                res = self.store()
                if res:
                    commit()
                    exec("from %s import %s as cls" % (self.RoutineName, self.RoutineName))
                    routine = cls()
                    routine.setTask(self)
                    routine.setBackground(self.Background)
                    self.Running = True                
                    routine.open(False)
        except Exception, e:
            self.Running = False
            raise
            
    def routineFinished(self):
        if self.Running:
            self.Running = False
            self.LastRunDate = today()
            self.LastRunTime = now()
            res = self.store()
            if res:
                commit()