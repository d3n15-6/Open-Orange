#encoding: utf-8
from OpenOrange import *
from GlobalTools import *
from core.database.Database import DBError

ParentUser = SuperClass("User", "Master", __file__)
class User(ParentUser):
    buffer = RecordBuffer("User")

    @checkCommitConsistency
    def afterLogin_fromC(self):
        try:
            self.afterLogin()
            return True
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    def afterLogin(self):
        try:
            #Intervalo para chequeo de tareas:
            #si esta vacio o con 0, dejo el default.
            #sino lo seteo: valores < 0 detienen el chequeo.

            if self.TaskCheckingInterval: setTaskCheckingInterval(self.TaskCheckingInterval)
            #Limpia los buffer almacenados localmente
            postMessage("%s, %s" %(self.Name,tr("welcome to the system!")), None, 10000)
            #import os
            #if getPlatform() == "linux":
            #    showSystemOSD("%s, %s" %(self.Name,tr("welcome to the system!")))
            if getApplicationType() == 1:
                from AppServerConnection import AppServerConnection
                AppServerConnection.getConn().login()
            if (currentUserCanDo("CanSynchronizeRecords",False)):
                synchronizeRecord("VersionSettingsNoveltyRow")
            from VersionSettings import VersionSettings
            vs = VersionSettings.bring()
            if (not vs.NoveltiesDisabled and graphicModeEnabled()):
                vs.showVersionNovelties()
            if vs.CheckVersionEnabled:
                vs.update()
            if vs.CheckScriptDirsEnabled:
                if not vs.checkScriptDirs():
                    exitProgram()
        except Exception, e:
            if isinstance(e, DBError):
                raise
            else:
                log(e)

        from DatabaseManagement import DatabaseManagement
        dm = DatabaseManagement.bring()
        if (dm):
            dm.checkDBPassword()

        try:
            from VersionUpdates import VersionUpdates
            vu = VersionUpdates()
            vu.checkUpdatesFiles()
        except Exception, err:
            log(err)

        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        from Computer import Computer
        if not Computer.exists(ls.Computer):
           message(tr("Your computer code is not registered, Check Local Settings"))
        from Company import Company
        Company.addLoguedCompany(currentCompany(), self.Code, self.Password)
        self.checkRestoreState()

    def checkRestoreState(self):
        try:
            f = open("restore/%s.%s" % (currentCompany(),currentUser()), "rb")
            state = f.read()
            f.close()
            import os
            os.remove("restore/%s.%s" % (currentCompany(),currentUser()))
            import cPickle
            for r in cPickle.loads(state):
                if r.__windowname__:
                    w = NewWindow(r.__windowname__)
                    if w:
                        w.setRecord(r)
                        w.open()
            postMessage("Session recovered successfully.")
        except IOError, e:
            pass

    def uniqueKey(self):
        return ['Code']

    def maxDiscountAllowed(self, itemcode, pricedeal):
        res = 100
        if self.SalesGroup:
            from SalesGroup import SalesGroup
            sg = SalesGroup.bring(self.SalesGroup)
            if sg:
                res = sg.maxDiscountAllowed(itemcode, pricedeal)
        return res

    def canDo(self, actionname,default=True):
        if not self.AccessGroup: return default
        from AccessGroup import AccessGroup
        ag = AccessGroup.bring(self.AccessGroup)
        if not ag: return default
        return ag.canDo(actionname,default)

    @classmethod
    def getPerson(objclass, usercode):
        user = User.bring(usercode)
        if user:
            from Person import Person
            pe = Person.bring(user.Person)
            if pe: return pe
        return None

    @classmethod
    def getMailFooter(objclass, usercode):
        from OurSettings import OurSettings
        iset = {}
        oset = OurSettings.bring()
        iset["Address"] = oset.Address
        iset["City"] = oset.City
        iset["Province"] = oset.Province
        iset["Country"] = ""
        if oset.Country:
            from Country import Country
            c = Country.bring(oset.Country)
            iset["Country"] = c.Name
        iset["Company"] = oset.FantasyName
        iset["Site"] = oset.WebSite
        iset["Phone"] = oset.Phone
        iset["Email"] = oset.Email
        iset["Logo"] = oset.Logo
        user = User.bring(usercode)
        if user:
            from Person import Person
            pe = Person.bring(user.Person)
            if (pe):
                iset["Name"] = pe.Name
                iset["LastName"] = pe.LastName
                # GS: Lo saco porque esta enviando la información personal
                # en lugar de la laboral.
                #if (pe.Address):
                    #iset["Address"] = pe.Address
                    #iset["City"] = pe.City
                    #iset["Country"] = pe.Country
                pmail = pe.getMail()
                if (pmail): iset["Email"] = pmail
        return iset

    @classmethod
    def getShift(objclass, usercode):
        user = User.bring(usercode)
        if user:
            return user.Shift
        return None

    @classmethod
    def getSalesGroup(objclass, usercode):
        user = User.bring(usercode)
        if user:
            return user.SalesGroup
        return None

    @classmethod
    def getStockDepo(objclass, usercode):
        user = User.bring(usercode)
        res = ""
        if user and user.StockDepo:
            res = user.StockDepo
        else:
            from OurSettings import OurSettings
            os = OurSettings.bring()
            res = os.DefStockDepo
        return res

    @classmethod
    def getOffice(objclass, usercode):
        user = User.bring(usercode)
        if user and user.Office:
            res = user.Office
        else:
            from OurSettings import OurSettings
            os = OurSettings.bring()
            res = os.DefOffice
        return res

    @classmethod
    def getDepartment(objclass, usercode):
        user = User.bring(usercode)
        if user and user.Department:
            res = user.Department
        else:
            from OurSettings import OurSettings
            os = OurSettings.bring()
            res = os.DefDepartment
        return res

    @classmethod
    def currentCanDo(objclass, actionname,default=True):
        user = User.bring(currentUser())
        if user:
            return user.canDo(actionname,default)
        return default

    @classmethod
    def getUserNames(objclass):
        col = {}
        q = Query()
        q.sql  = "SELECT {Code}, {Name} "
        q.sql += "FROM [User] "
        if(q.open()):
            for rec in q:
               col[rec.Code] = rec.Name
        q.close()
        return col

    @classmethod
    def currentCanOpenRecord(objclass, recordname):
        user = User.bring(currentUser())
        if user:
            return user.canOpenRecord(recordname)
        return default

    def canOpenRecord(self, recordname):
        if not self.AccessGroup: return True
        from AccessGroup import AccessGroup
        ag = AccessGroup.bring(self.AccessGroup)
        if not ag: return default
        return ag.canViewModule(recordname,default)

    @classmethod
    def currentCanViewModule(objclass, modulename):
        user = User.bring(currentUser())
        if user:
            return user.canViewModule(modulename)
        return default

    @classmethod
    def getCurrentRecordVisibility(objclass, modulename):
        from AccessGroup import AccessGroup
        user = User.bring(currentUser())
        if user:
            return user.getRecordVisibility(modulename)
        return AccessGroup.ALL_RECORDS

    def getRecordVisibility(self, recordname):
        from AccessGroup import AccessGroup
        if not self.AccessGroup: return AccessGroup.ALL_RECORDS
        ag = AccessGroup.bring(self.AccessGroup)
        if not ag: return AccessGroup.ALL_RECORDS
        return ag.getRecordVisibility(recordname)

    def canViewModule(self, modulename):
        if not self.AccessGroup: return True
        from AccessGroup import AccessGroup
        ag = AccessGroup.bring(self.AccessGroup)
        if not ag: return default
        return ag.canViewModule(modulename)
