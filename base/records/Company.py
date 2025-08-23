#encoding: utf-8
from OpenOrange import *
from core.database.Database import DBError
import socket
import threading

ParentCompany = SuperClass("Company", "Master", __file__)

class Company(ParentCompany):    
    #this is a local record, so it cant inherits from Master
    #this class should never be in buffer!
    __logued_companies__ = []
    __current__ = None
    
    
    def logIntoApplicationServer(self):
        from core.AppServerConnection import AppServerConnection
        try:
            server = AppServerConnection.getConn(self)
            dbcompany = server.getDBConnInfo()
        except:
            postMessage(tr("OpenOrange couldnt estabish a connection with the server"))
            return False
        if dbcompany:
            dbcompany.DefaultUser = ''
            dbcompany.DefaultUserPassword = ''
            if dbcompany.Host == "127.0.0.1" or dbcompany.Host == "localhost":
                dbcompany.Host = self.Host
            return setCurrentDatabase(dbcompany)
        else:
            postMessage("No se pudieron obtener los datos de conexion a la base de datos")
            return False

    def defaults(self):
        #ParentCompany.defaults(self) #no debe llamar al padre!!! xq este registro se graba a veces sin estar conectado
        self.Port = 3306
        self.ApplicationType = 0
        self.DBEngine = 0

    def check(self):
        #no debe llamar al padre!!! xq este registro se graba a veces sin estar conectado
        c = Company()
        c.Code = self.Code
        if c.load():
            if c.internalId != self.internalId: return ErrorResponse("EXISTSERR", {"Record":self, "FieldName":"Code"})
        return True

    def getDatabaseName(self):
        if self.DBName: return self.DBName
        return self.Code

    @classmethod
    def resetCurrent(cls):
        from base.records.Company import Company as CC
        CC.__current__ = None
    
    @classmethod
    def getCurrent(cls):
        res = None
        from base.records.Company import Company as CC
        if CC.__current__:
            return CC.__current__
        else:
            if currentCompany():
                res = CC.bring(currentCompany())
                CC.__current__ = res
            else:
                clparams = getCommandLineParams()
                if clparams.has_key("--dbhost") and clparams.has_key("--dbport") and clparams.has_key("--dbuser") and clparams.has_key("--dbname"):
                    res = CC()
                    res.Code = ""
                    res.DBName = clparams["--dbname"]
                    res.Host = clparams["--dbhost"]
                    res.Port = int(clparams["--dbport"])
                    res.User = clparams["--dbuser"]
                    res.Password = genPassword(clparams["--dbpassword"])
                    res.DefaultUser = clparams["--oouser"]
                    res.DefaultUserPassword = clparams["--oopassword"]
                    CC.__current__ = res
                #if (getCommandLineParams())
        return res
    
    @classmethod
    def addLoguedCompany(cls, companycode, usercode, userpassword):
        from base.records.Company import Company as CC    
        companyname = ""
        if companycode:
            company = Company.bring(companycode)
            companyname = company.Name        
            CC.__current__ = company
        try:
            CC.tryLoadLoguedCompanies()
            CC.__logued_companies__.index((companycode, companyname, usercode, userpassword))
        except ValueError, e:
            CC.__logued_companies__.append((companycode, companyname, usercode, userpassword))
            if len(CC.__logued_companies__) > 1:enableSwitchCompanyButton()
                
                
    @classmethod
    def tryLoadLoguedCompanies(cls):
        from base.records.Company import Company as CC    
        import os
        if os.path.exists("./tmp/lc.tmp"):
            try:
                CC.__logued_companies__ = cPickle.load(open("./tmp/lc.tmp"))
                os.remove("./tmp/lc.tmp")
            except IOError, e:
                pass
            except EOFError, e:
                pass

    @classmethod
    def getLoguedCompanies(cls):
        from base.records.Company import Company as CC    
        CC.tryLoadLoguedCompanies()
        return cls.__logued_companies__

    def save_fromGUI(self, **kwargs):
        res = self.check()
        if not res: return res
        res = self.rawStore(**kwargs)
        return res


    def setCurrent(self):
        if self.ApplicationType == 0:
            from base.records.Company import Company as CC
            CC.__current__ = self
            from core.database.Database import Database
            setCurrentCompany(self.Code)
            Database.resetDatabases()
            Query().__class__.clearSchemasMap()
            res = False
            if self.DefaultUser:
                userpass = ""
                if (self.DefaultUserPassword):
                    userpass = self.DefaultUserPassword
                res = login(self.DefaultUser, userpass)
            if not res:
                res = login()
        elif self.ApplicationType == 1:
            from LoginDialog import LoginDialog
            ld = LoginDialog()
            if self.DefaultUser:
                ld.User = self.DefaultUser
                ld.Password = self.DefaultUserPassword
                res = self.loginDone(ld)
            else:
                from LoginDialogWindow import LoginDialogWindow
                w = LoginDialogWindow()
                w.setRecord(ld)
                w.accepted = self.loginDone
                w.rejected = self.loginCanceled
                w.open()
                res = True
        return res
    
    def loginCanceled(self, loginDialogRecord):
        exitProgram()
        
    def loginDone(self, loginDialogRecord):
        srv = self.getServerConnection(False)
        if srv:
            res = srv.login(loginDialogRecord.User, loginDialogRecord.Password)
            if res:
                from base.records.Company import Company as CC
                CC.__current__ = self
                from core.database.Database import Database
                setCurrentCompany(self.Code)
                Database.resetDatabases()
                Query().__class__.clearSchemasMap()
                from User import User
                embedded_setCurrentUser(User.bring(loginDialogRecord.User))                
                return True
            else:
                message(tr("Login Failed"))
                self.setCurrent()
        else:
            message(tr("Connection to server not established"))
        return False
    
    
    def getDatabase(self):
        from core.database.Database import Database
        return Database.createNew(self)

        
    def createServerConnection(self, automatic_login=True):
        from server.ProtocolInterface import ClientProtocolInterface
        try:
            conn = ClientProtocolInterface(self.Host, self.Port)
            if automatic_login:
                u = curUser()
                p = curUserPassword()
                if conn.login(u, p):
                    return conn
            else:
                return conn
        except socket.error, e:
            raise AppException, "Error connecting to server"
        
    def getServerConnection(self, automatic_login=True):
        if self.ApplicationType == 1:
            if not hasattr(threading.currentThread(), "server_connection") or not threading.currentThread().server_connection:
                threading.currentThread().server_connection = None
                threading.currentThread().server_connection = self.createServerConnection(automatic_login)
            return threading.currentThread().server_connection
        return None

    def getDBConnectionCompany(self):
        if self.ApplicationType == 1:
            srv = self.getServerConnection()
            if srv:
                return srv.getCurrentCompany()
        else:
            return self

    def isApplicationServerCompany(self):
        return (self.ApplicationType == 1)
        
    def tryReconnectToServer(self):
        threading.currentThread().server_connection = None
        sc = self.getServerConnection()
        return bool(sc)
