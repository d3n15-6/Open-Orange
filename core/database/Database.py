from Embedded_OpenOrange import decode, getQueryLogging, sysprint
from Log import log
import threading
import Queue

class DBError(Exception): pass
class DBConnectionError(DBError): pass
class DBQueryError(DBError): pass
class DBDataTruncatedError(DBQueryError):
    def __str__(self): return "Column data can not be truncated."
class DBConnectionLost(DBConnectionError):
    def __str__(self): return "Database connection lost."
class DBUnknownDatabase(DBConnectionError):

    def __str__(self): 
        from base.tools.GlobalTools import getWrappedText
        from core.functions import tr 
        msg = getWrappedText(tr("Connection established to MySQL, but database doesn't exist in server. You can create the schema from Options, Edit Companies, YourCompany, Create Database."),50)
        msg = "<br>".join(msg) 
        return msg 

class DBCantConnect(DBConnectionError):
    def __str__(self): return "Can't connect to database server"
    
class DBNoCompanySelected(DBConnectionError): pass
class DBAccessDenied(DBQueryError): pass
class DBPacketTooBig(DBQueryError): pass

class DBAlreadyExists(DBQueryError):

    def __str__(self):
        return "Database already exists."

class DBObjectNameAlreadyExists(DBQueryError):

    def __init__(self, msg=None):
        DBQueryError.__init__(self,msg)
        self.msg = msg

    def __str__(self):
        return "Object name already exists. %s" % self.msg

class DBLockWaitTimeout(DBQueryError):

    def __str__(self): 
        from GlobalTools import getWrappedText
        msg = getWrappedText("Database Transaction locked. Please check if there is a routine running on the database. If not, MySQL Administrator report could help you unlocking the database.",50)
        msg = "<br>".join(msg) 
        return msg 
        
class DBFieldNotFound(DBQueryError):

    def __init__(self, tablename=None, fieldname=None):
        DBQueryError.__init__(self, tablename, fieldname)
        self.tablename = tablename
        self.fieldname = fieldname

    def __str__(self):
        from functions import tr
        if self.tablename:
            res  = tr("Field")
            res += " <b>%s</b>" %(self.fieldname)
            res += "<br>%s" %(tr("Not Found in Table"))
            res += " <b>%s</b>. " %(self.tablename)
            res += "<p>%s" %(tr("Use Menu System/Synchronize One Table To Fix The Problem"))
            return res
        else:
            res  = tr("Field")
            res += " <b>%s</b>" %(self.fieldname)
            res += "<br>%s" %(tr("Not Found in Table"))
            res += " <b>?</b>. " 
            res += "<p>%s" %(tr("Use Menu System/Synchronize Tables To Fix The Problem"))
            return res

class DBSyntaxError(DBQueryError):

    def __init__(self, msg=None):
        DBQueryError.__init__(self,msg)
        self.msg = msg

    def __str__(self):
        from GlobalTools import getWrappedText
        msg = getWrappedText(self.msg,50)
        msg = "<br>".join(msg) 
        return msg

class DBIntegrityError(DBQueryError):
    def __init__(self, msg=None):
        DBQueryError.__init__(self,msg)
        self.msg = msg
        
    def __str__(self):
        from GlobalTools import getWrappedText
        msg = getWrappedText(self.msg,50)
        msg = "<br>".join(msg) 
        return msg


class DBTableNotFound(DBQueryError):
    def __init__(self, tablename=None):
        DBQueryError.__init__(self,tablename)
        self.tablename = tablename

    def __str__(self):
        return "Table %s not found in database" % (self.tablename)

class Database(object):
    (MYSQL,POSTGRESQL,ODBC,ORACLE, SQLITE) = (0,1,2,3,4)
    connections_pool = Queue.Queue(8)
    #threaddata = threading.local()
    mutex = threading.RLock()
    
    @classmethod
    def createNew(self, company):
        if company.DBEngine == Database.MYSQL:
            from mysql.MySQL_Database import MySQL_Database
            db = MySQL_Database(company)
            return db
        elif company.DBEngine == Database.ORACLE:
            from oracle.Oracle_Database import Oracle_Database
            db = Oracle_Database(company)
            return db
        elif company.DBEngine == Database.SQLITE:
            from sqlite.SQLite_Database import SQLite_Database
            db = SQLite_Database(company)
            return db
        raise Exception, "unimplemented server type: %s" % company.DBEngine
    
    @classmethod
    def setCurrentDB(objclass, database):
        Database.mutex.acquire()
        try:
            threading.currentThread().database = database
            from core.database.Query import Query
            from core.RawRecord import RawRecord
            Query.clearSchemasMap()
        finally:
            Database.mutex.release()

    def createDatabase(self, dbname):
        query = self.createQuery()
        query.sql = "CREATE DATABASE %s" % self.escapeTableName(dbname)
        return query.execute()

    @classmethod
    def getCurrentDB(objclass, tryconnect=True):
        #curthread = threading.currentThread()
        try:
            #sysprint("    ABOUT TO ACCQUIRE LOCK IN THREAD %s" % threading.currentThread().getName())
            Database.mutex.acquire()
            #sysprint("    LOCK ACQUIRED IN THREAD %s" % threading.currentThread().getName())
            try:
                #sysprint("THREADDATA IN THREAD:%s (%s) -> %s" % (id(threading.currentThread()),threading.currentThread().getName(), None))
                #db = Database.threaddata.database
                db = threading.currentThread().database
                from functions import now
                from datetime import timedelta
                if now() - db.last_query_ts > timedelta(seconds=28000):
                    sysprint("connection expired, creating new one...")
                    tryconnect=True
                    raise AttributeError
                #alert(str(threading.currentThread().__dict__).replace("<","("))
                #sysprint("    returning existing db: DB:%s, THREAD:%s (%s)" % (id(db), id(threading.currentThread()),threading.currentThread().getName()))
                return db
            except AttributeError, e:
                if not tryconnect: return None
                #sysprint("    creating new db object in thread %s..." % threading.currentThread().getName())
                from Company import Company
                curcomp = Company.getCurrent()
                if (not curcomp): raise DBNoCompanySelected
                company = curcomp.getDBConnectionCompany()
                if (not company): raise DBNoCompanySelected
                db = Database.createNew(company)
                #log("New Database Created %i in thread %i" % (id(db), id(threading.currentThread())), True)
                #Database.threaddata.database = db
                try:
                    db.connect()
                except DBError, e:
                    Company.resetCurrent()
                    raise e
                threading.currentThread().database = db                    
                #sysprint("    new db created: DB:%s, Conn: %s, Conn # %s, THREAD:%s (%s)" % (id(db), id(db.db), Database.connections_pool.qsize(), id(threading.currentThread()), threading.currentThread().getName()))                
                return db
        finally:
            #sysprint("RELEASING LOCK IN THREAD %s" % threading.currentThread().getName())
            Database.mutex.release()
        
    def __init__(self, company):
        from functions import alert
        self.host = company.Host #.encode("ascii", 'ignore')
        self.port = company.Port
        self.user = company.User #.encode("ascii", 'ignore')
        self.commit_blocker = 0
        self.modifying_queries = 0
        if company.Password is not None:
            self.password = decode(company.Password)
        else:
            self.password = ""
        self.dbname = company.getDatabaseName()
        self.idle_timeout = 5
        self.db = None        
        self.queries_count = 0

    def getQueriesCount(self):
        return self.queries_count
        
    def commit(self):
        #log("COMMITING Connection %i,%s from thread %i" % (id(self.db), self.db.__class__.__name__, id(threading.currentThread())), True)
        if not self.isConnected(): raise DBConnectionLost
        if not self.canCommit(): 
            from core.Responses import AppException
            raise AppException("Commit not allowed at this moment. Please contact OpenOrange.")
        self.db.commit()
        self.modifying_queries = 0
        if getQueryLogging(): log("COMMIT")
        return True

    def rollback(self):
        #log("ROLLINGBACK Connection %i,%s from thread %i" % (id(self.db), self.db.__class__.__name__, id(threading.currentThread())), True)
        if not self.isConnected(): raise DBConnectionLost
        if getQueryLogging(): log("ROLLBACK")
        res = self.db.rollback()
        self.modifying_queries = 0
        return True

    def isConnected(self):
        return bool(self.db)
        
    def connect(self, *args, **kwargs):
        raise Exception, "unimplemented method connect"
    
    def blockCommits(self):
        self.commit_blocker += 1

    def unblockCommits(self):
        self.commit_blocker -= 1
        if self.commit_blocker < 0: 
            from core.Responses import AppException
            raise AppException("Unblocking an unblocked connection is not allowed")
        
    def canCommit(self):
        return (self.commit_blocker == 0)
        
    def getQuery(self):
        raise Exception, "unimplemented method getQuery"

    def escapeValue(self, value):
        if isinstance(value, unicode):
            res =  self.db.escape_string(value.encode("utf8"))
        elif isinstance(value, str):
            res = self.db.escape_string(unicode(value, 'utf8', errors='replace'))
        else:
            res = self.db.escape_string(unicode(str(value), 'utf8', errors='replace'))
        return res

    @classmethod       
    def escapeTableName(self, tablename):
        return "`%s`" % tablename

    @classmethod
    def escapeFieldName(self, fieldname):
        return "`%s`" % fieldname

    def parseStringValue(self, value):
        return "'%s'" % self.escapeValue(value)
        
    def parseFieldValue(self, field, addEqualString):
        if field.isNone():
            res = "NULL"
            if addEqualString: res = " is " + res
        else:
            ftype = field.getType()
            if ftype in ("string", "memo", "blob", "set"):
                res = ("'%s'" % self.escapeValue(field.getValue()))
            elif ftype == "date":
                res = "'%s'" % field.getValue().isoformat()
            elif ftype == "time":
                res = "'%s'" % self.escapeValue(field.getValue())
            elif ftype == "boolean":
                if field.getValue():
                    res = "1"
                else:
                    res = "0"
            else:
                res = "%s" % field.getValue()
                
            if addEqualString: res = " = " + res
        return res

    def parsePythonFieldValue(self, field):
        if field.isNone():
            res = None
        else:
            ftype = field.getType()
            if ftype in ("string", "memo", "blob", "set"):
                res = "%s" % self.escapeValue(field.getValue())
            elif ftype == "date":
                res = field.getValue()
            elif ftype == "time":
                res = field.getValue()
            elif ftype == "boolean":
                if field.getValue():
                    res = 1
                else:
                    res = 0
            else:
                res = "%s" % field.getValue()
        return res
        

    @classmethod
    def resetDatabases(objclass, **kwargs):
        from core.database.Database import Database
        Database.mutex.acquire()        
        while not Database.connections_pool.empty():
            conn = Database.connections_pool.get()
        try:
            del threading.currentThread().database
        except AttributeError, e:
            pass
        Database.mutex.release()    
        
    def releaseConnection(self, python_thread, **kwargs):
        from core.database.Database import Database
        Database.mutex.acquire()        
        conn = self.db
        self.db = None
        del python_thread.database #importante porque parece que a veces los threads se reusan (python los vuelve a devolver)
        #log("Releasing Connection %i from thread %i" % (id(conn), id(python_thread)), True)
        if False and (not kwargs.get("DROP_CONNECTION", False)): Database.connections_pool.put(conn)
        Database.mutex.release()    

    @classmethod        
    def getEngine_fromC(classobj):
        if classobj.getCurrentDB().getServerType() == Database.MYSQL:
            return "MYSQL"
        elif classobj.getCurrentDB().getServerType() == Database.ORACLE:
            return "ORACLE"
        elif classobj.getCurrentDB().getServerType() == Database.SQLITE:
            return "SQLITE"
        return "NONE"

    @classmethod       
    def synchronizeRecord_fromC(classobj, recordname, force, silence):
        from functions import currentUserCanDo, message, sysprint
        res = currentUserCanDo("CanSynchronizeRecords", False)
        if res:
            if classobj.getCurrentDB().getServerType() == Database.MYSQL:
                from core.database.mysql.MySQL_DBSynchronizer import MySQL_DBSynchronizer as Synchronizer
            elif classobj.getCurrentDB().getServerType() == Database.ORACLE:
                from core.database.oracle.Oracle_DBSynchronizer import Oracle_DBSynchronizer as Synchronizer
            elif classobj.getCurrentDB().getServerType() == Database.SQLITE:
                from core.database.sqlite.SQLite_DBSynchronizer import SQLite_DBSynchronizer as Synchronizer
            return Synchronizer.synchronizeRecord(recordname, force)            
        else:
            if not silence: message(res)
            return False


    @classmethod        
    def tableExists_fromC(classobj, tablename):
        if classobj.getCurrentDB().getServerType() == Database.MYSQL:
            from core.database.mysql.MySQL_DBSynchronizer import MySQL_DBSynchronizer as Synchronizer
        elif classobj.getCurrentDB().getServerType() == Database.ORACLE:
            from core.database.oracle.Oracle_DBSynchronizer import Oracle_DBSynchronizer as Synchronizer
        elif classobj.getCurrentDB().getServerType() == Database.SQLITE:
            from core.database.sqlite.SQLite_DBSynchronizer import SQLite_DBSynchronizer as Synchronizer
        return Synchronizer.tableExists(tablename)            

            
    def createQuery(self):
        return None