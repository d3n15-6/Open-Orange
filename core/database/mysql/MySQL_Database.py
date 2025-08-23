from Embedded_OpenOrange import sysprint
from MySQL_Query import MySQL_Query
from core.database.Database import *
from MySQL_ModuleImporter import *
from Log import log, logConnection
import threading

class MySQL_Database(Database):

    @classmethod
    def getServerType(objclass):
        return MySQL_Database.MYSQL
        
    def __init__(self, company):
        Database.__init__(self, company)
        from functions import now
        self.last_query_ts = now()
        
    def connect(self, *args, **kwargs):
        conv = MySQLdb.converters.conversions
        conv[FIELD_TYPE.TIME] = Time_or_None
        try:
            try:
                
                #sysprint("        fethching connection from pool... Thread %s, Database %s" % (threading.currentThread().getName(), id(self)))
                #print "     connecting to db, queue:", Database.connections_pool.qsize()
                raise Queue.Empty
                self.db = Database.connections_pool.get_nowait()
                #print "     db obtenida del pool", self.db
                #log("THREAD: %s, DB: %s, CONN: %s: ASSIGNED (FROM POOL)" % (threading.currentThread().getName(), id(self), id(self.db)))
                #sysprint("        connection fetched from pool. Thread %s, Databsae %s, Conn %s" % (threading.currentThread().getName(), id(self), id(self.db)))
            except Queue.Empty:
                sysprint("connecting to database... Thread %s, Database %s, %s" % (threading.currentThread().getName(), id(self), (self.host,self.port,self.user,self.dbname)))
                self.db = MySQLdb.connect(host=self.host,port=self.port,user=self.user,passwd=self.password, client_flag=CLIENT.FOUND_ROWS, conv= conv, compress=True, charset = "utf8", use_unicode = True)
                #print "     db creada           ", self.db
                #log("THREAD: %s, DB: %s, CONN: %s: ASSIGNED NEW CONN" % (threading.currentThread().getName(), id(self), id(self.db)))
                #sysprint("        new connection established. Thread %s, Databsae %s, Conn %s" % (threading.currentThread().getName(), id(self), id(self.db)))
        except Connection.OperationalError, e:
            #sysprint("RAISING FROM CONNECT")
            self.process_Exception_OperationalError(e)        
        except Exception, e:
            from functions import processUnexpectedError
            processUnexpectedError(e, {}, "Can not connect to database server.")
            raise
        if kwargs.get("USE_DATABASE", True):
            q = self.getQuery()
            q.sql = "USE [%s]" % self.dbname
            q.execute()
                
        q = self.getQuery()
        q.sql = "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        q.execute()
        #sysprint("returning TRUE FROM CONNECT")
        return True
        
    def getQuery(self):
        return MySQL_Query(self)
            
    
    def rollback(self):
        #if not self.db: self.connect()    
        try:
            return Database.rollback(self)
        except DBConnectionLost, e:
            #problemas de conexion; puede haberse perdido la conexion, asi que intento reconectarme una vez.
            try:
                self.connect()
                return Database.rollback(self)
            except Connection.OperationalError, e:
                self.process_Exception_OperationalError(e)
                return        
        except Connection.OperationalError, e:
            if e[0] in (2006,2013):
                #problemas de conexion; puede haberse perdido la conexion, asi que intento reconectarme una vez.
                try:
                    self.connect()
                    return Database.rollback(self)
                except Connection.OperationalError, e:
                    self.process_Exception_OperationalError(e)
                    return
            self.process_Exception_OperationalError(e)
            return
                
    def commit(self):
        #if not self.db: self.connect()    
        try:
            Database.commit(self)
        except Connection.OperationalError, e:
            self.process_Exception_OperationalError(e)

            
    def process_Exception_OperationalError(self, e):
        import threading
        logConnection("Database connection lost. (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self), id(self.db)))
        self.db = None
        if e[0] == 1044: raise DBCantConnect
        if e[0] == 1045: raise DBCantConnect
        if e[0] == 1049: raise DBUnknownDatabase
        if e[0] == 1130: raise DBCantConnect
        if e[0] == 2003: raise DBCantConnect #Can't connect to MySQL server on 'xxx.xxxxxxxx.xxx' (10060)
        if e[0] == 2013: raise DBConnectionLost #Lost connection to MySQL server during query
        if e[0] == 2006: raise DBConnectionLost
        raise
        
    def createQuery(self):
        return MySQL_Query(self)