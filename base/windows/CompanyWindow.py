#encoding: utf-8
from OpenOrange import *

ParentCompanyWindow = SuperClass("CompanyWindow","MasterWindow",__file__)
class CompanyWindow(ParentCompanyWindow):
    
    def afterShowRecord(self):
        #este registro se usa muchas veces sin estar conectado, asi que no debe llamar al padre, xq el
        #padre puede llegar a hacer consultas a la BD
        pass

    def beforeEdit(self, fieldname):
        #este registro se usa muchas veces sin estar conectado, asi que no debe llamar al padre, xq el
        #padre puede llegar a hacer consultas a la BD
        return True

    def afterEdit(self, fieldname):
        #este registro se usa muchas veces sin estar conectado, asi que no debe llamar al padre, xq el
        #padre puede llegar a hacer consultas a la BD
        return True
        
    def save(self):
        #este registro se usa muchas veces sin estar conectado, asi que no debe llamar al padre, xq el
        #padre puede llegar a hacer consultas a la BD    
        new_flag = self.getRecord().isNew()
        res = self.getRecord().save_fromGUI()
        self.getRecord().showMessages()
        if not res:
            message(res)
        elif new_flag:
            from HistoryManager import HistoryManager
            HistoryManager.addWindow(self)
        return res

    def buttonClicked(self, buttonname):
        company = self.getRecord()
        if buttonname == "portscan":
            import socket as sk
            try:
                sk.gethostbyname(company.Host)
            except:
                message("host '%s' unknown" % company.Host)
                return
            sd = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
            try:
                sd.connect((company.Host, company.Port))
                message("%s: %d esta abierto" % (company.Host, company.Port))
                sd.close()
            except: 
                message("%s: %d esta cerrado" % (company.Host, company.Port))


    def createDatabase(self):
        from core.database.Database import Database
        from core.database.Query import Query as DBQuery
        company = self.getRecord()
        ncompany = company.clone()
        ncompany.Code = None
        ncompany.DBName = None
        db = Database.createNew(ncompany)
        db.connect(USE_DATABASE=False)
        
        try:
            if db.createDatabase(company.getDatabaseName()):
                db.commit()
                #db.dbname = company.getDatabaseName()
                #db.connect()

                from base.records.Company import Company as CC
                CC.__current__ = company
                setCurrentCompany(company.Code)
                Database.resetDatabases()

                from SchemaSettings import SchemaSettings
                ss = SchemaSettings()
                ss.Enabled = False
                SchemaSettings.buffer[None] = ss
                synchronizeRecords()
                SchemaSettings.buffer[None] = None
        except DBError, e:
            processDBError(e, {}, str(e))

    def importDatabase(self):
        record = self.getRecord()
        from DatabaseManagement import DatabaseManagement
        dm = DatabaseManagement()
        fname = getOpenFileName(tr("Select File"))
        if (fname):
            dm.BackupFile = fname
            dm.ImpHost = record.Host
            dm.ImpPort = record.Port
            dm.ImpDBName = record.DBName
            dm.ImpUser = record.User
            dm.ImpPassword = record.Password
            res = getSelection("Fix MySQL Backup", (tr("No"), tr("Yes")))
            if (not res): return 
            if (res == tr("Yes")):
                dm.FixMySQLBackup = True
            dm.importDatabase()
