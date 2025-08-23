from OpenOrange import *
from core.AppServerConnection import AppServerConnection
from core.database.Database import DBError

class BackgroundRoutineRunner(CThread):

    def __init__(self, routine):
        CThread.__init__(self)
        self.routine = routine
        self.setName(routine.__class__.__name__)

    def run(self):
        try:
            self.routine.call_run()
            self.routine.afterRun()
        except DBError, e:
            processDBError(e, {}, utf8(e))

class ServerRoutineRunner(CThread):

    def __init__(self, routine):
        self.routine = routine
        self.setName("Server: " + routine.__class__.__name__)

    def run(self):
        try:
            from Company import Company
            sc = Company.getCurrent().getServerConnection()
            sc.runRoutine(self.routine.__class__.__name__, self.routine.getRecord())
        except DBError, e:
            processDBError(e, {}, utf8(e))

class Routine(object):

    def __init__(self, spec=None):
        self.__background__ = False
        self.__runOnServer__ = False
        if spec:
            self.__fixed_spec__ = True
            self.setRecord(spec)
        else:
            self.__fixed_spec__ = False
            self.setRecord(self.genRoutineRecord())
        self._should_finish = False
        self.__thread__ = None
        self.__task__ = None

    def setRecord(self, record):
        self.__record__ = record
        
    def setTask(self, task):
        self.__task__= task

    def getTask(self):
        return self.__task__

    def getRecord(self):
        return self.__record__

    def setBackground(self, b):
        self.__background__ = b

    def setRunOnServer(self, b):
        self.__runOnServer__ = b

    def getBackground(self):
        return self.__background__

    def getRunOnServer(self):
        return self.__runOnServer__

    def getRoutineUserInputXML(self):
        import os
        sdirs = getScriptDirs()
        for sd in sdirs:
            fn = os.path.join(sd,"interface", self.__class__.__name__ + ".routinewindow.xml")
            if os.path.exists(fn):
                res = open(fn, "rb").read()
                return res
        return None

    def genRoutineWindow(self):
        xml = self.getRoutineUserInputXML()
        if not xml: return None
        xml = xml.replace("\n","")
        import re
        windowxml = re.search("(<routinewindow.*?>.*</routinewindow>)", xml)
        w = None
        if windowxml:
            wxml = windowxml.group(1)
            wxml = wxml.replace("routinewindow", "window")
            wname = re.search('<window .*?name="([^"]*?)".*?>', wxml)
            w = createRoutineWindow(wxml)
            if wname:
                windowname = wname.group(1)    
                if not windowname.endswith("RoutineWindow"): windowname += "RoutineWindow"
                try:
                    exec("from %s import %s as cls" % (windowname, windowname))
                    w.__class__ = cls
                except ImportError, e:
                    pass
        return w

    def genRoutineRecord(self):
        xml = self.getRoutineUserInputXML()
        if not xml: return None
        xml = xml.replace("\n","")
        import re
        recordxml = re.search("(<routinerecord.*?>.*</routinerecord>)", xml)
        r = None
        if recordxml:
            rxml = recordxml.group(1)
            rxml = rxml.replace("routinerecord", "record")
            r = createRecord(rxml)
        return r

    def open(self, showWindow=True):
        if showWindow:
            w = self.genRoutineWindow()
            if not self.__fixed_spec__: self.defaults()
            if w:
                w.routine = self
                w.setRecord(self.getRecord())
                w.open()
            else:
                self.start()
        else:
            if not self.__fixed_spec__: self.defaults()
            self.start()

    def shouldFinish(self):
        if self.__thread__:
            return self.__thread__.shouldFinish()
        else:
            return self._should_finish

    def start(self):
        if self.getRunOnServer():
            self.__thread__ = ServerRoutineRunner(self)
            self.call_beforeRun()
            self.__thread__.start()        
        else:
            if self.getBackground():
                self.__thread__ = BackgroundRoutineRunner(self)
                self.call_beforeRun()
                self.__thread__.start()
            else:
                try:        
                    self.call_beforeRun()
                    self.call_run()
                    self.afterRun()
                except DBError, e:
                    processDBError(e, {}, utf8(e))

    def afterRun(self):
        if self.getTask():
            self.getTask().routineFinished()
        sysprint("Running Routine: %s" %(self.__class__.__name__))

    def call_beforeRun_fromC(self):
        try:
            res = self.call_beforeRun()
            return res
        except DBError, e:
            rollback()
            processDBError(e, {}, str(e))

    def call_beforeRun(self):
        try:
            rollback() #para que inicie una nueva transaccion
            res = self.beforeRun()
            return res
        except Exception, e:
            rollback()
            processUnexpectedError(e)

    def call_run_fromC(self):
        try:
            res = self.call_run()
            return res
        except DBError, e:
            rollback()
            processDBError(e, {}, str(e))

    def call_run(self):
        try:
            rollback() #para que inicie una nueva transaccion
            res = self.run()
            commit()
            return res
        except AppException, e:
            rollback()
            message(utf8(e))
        except DBError, e:
            raise
        except Exception, e:
            rollback()
            processUnexpectedError(e)

    def defaults(self):
        record = self.getRecord()
        if record and record.hasField("FromDate"):
            record.FromDate = date(today().year, today().month, 1)
        if record and record.hasField("ToDate"):
            if today().month == 12:
                record.ToDate = addDays(date(today().year+1,1,1),-1)
            else:
                record.ToDate = addDays(date(today().year, today().month+1,1),-1)

    def beforeRun(self):
        #este metodo se corre siempre en foreground
        pass

    def TransFilter(self,FromDate,ToDate,Status,Office,Shift,User,Computer):
        """ Filter should be used on all transaction reports """
        qstr = "WHERE {TransDate} BETWEEN d|%s| AND d|%s| " % (FromDate,ToDate)      # always used therefore : where
        if (Status==1):
           qstr += "AND {Status}=i|0| "
        elif (Status==2):
           qstr += "AND {Status}=i|1| "
        elif (Status==0):                # default is include both approved and non approved
           pass
        if False:   # user has restricted access: we need a setting for this
           from User import User
           us = User.bring(currentUser())
           if us:
             Office = us.Office
             Shift  = us.Shift
        if Office:   qstr += "AND {Office}=s|%s| " % Office
        if User:     qstr += "AND {User}=s|%s| " % User
        if Computer: qstr += "AND {Computer}=s|%s| " % Computer
        if Shift:    qstr += "AND {Shift}=s|%s| " % Shift
        return qstr
