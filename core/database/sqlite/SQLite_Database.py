from Embedded_OpenOrange import sysprint
from SQLite_Query import SQLite_Query
from core.database.Database import *
from pysqlite2 import dbapi2 as sqlite
from Log import log
import threading

class SQLite_Database(Database):

    @classmethod
    def text_factory(classobj, txt):
        try:
            from functions import sysprint
            return unicode(txt, "latin1")
        except Exception, e:
            from functions import alert
            #alert((txt, str(e)))
            raise
        
    @classmethod
    def getServerType(objclass):
        return SQLite_Database.SQLITE
        
    def __init__(self, company):
        Database.__init__(self, company)
        
    def connect(self):
        try:
            try:
                #raise Queue.Empty
                #sysprint("        fethching connection from pool... Thread %s, Database %s" % (threading.currentThread().getName(), id(self)))
                self.db = Database.connections_pool.get_nowait()
                #log("THREAD: %s, DB: %s, CONN: %s: ASSIGNED (FROM POOL)" % (threading.currentThread().getName(), id(self), id(self.db)))
                #sysprint("        connection fetched from pool. Thread %s, Databsae %s, Conn %s" % (threading.currentThread().getName(), id(self), id(self.db)))
            except Queue.Empty:
                sysprint("connecting to database... Thread %s, Database %s, %s" % (threading.currentThread().getName(), id(self), (self.host,self.port,self.user,self.dbname)))
                self.db = sqlite.connect(self.dbname)
                self.db.text_factory = self.text_factory
                #log("THREAD: %s, DB: %s, CONN: %s: ASSIGNED NEW CONN" % (threading.currentThread().getName(), id(self), id(self.db)))
                #sysprint("        new connection established. Thread %s, Databsae %s, Conn %s" % (threading.currentThread().getName(), id(self), id(self.db)))
        except Exception, e:
            from functions import processUnexpectedError
            processUnexpectedError(e, {}, "Can not connect to database server.")
            raise
                
        #q = self.getQuery()
        #q.sql = "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        #q.execute()
        #sysprint("returning TRUE FROM CONNECT")
        return True
        
    def escapeValue(self, value):
        return value.replace("'","''")
        
    def getQuery(self):
        return SQLite_Query(self)
            
    
    def rollback(self):
        #if not self.db: self.connect()    
        try:
            Database.rollback(self)
        except Connection.OperationalError, e:
            self.process_Exception_OperationalError(e)
                
    def commit(self):
        #if not self.db: self.connect()    
        try:
            Database.commit(self)
        except Connection.OperationalError, e:
            self.process_Exception_OperationalError(e)

            
    def process_Exception_OperationalError(self, e):
        import threading
        log("Database connection lost. (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self), id(self.db)))
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
        return SQLite_Query(self)
        
    def createDatabase(self, dbname):
        #no es necesario en sqlite
        return True
        
    def releaseConnection(self, python_thread, **kwargs):
        #en sqlite no se hace pool para que las conexiones se usen en el thread en que se crean
        from core.database.Database import Database
        Database.mutex.acquire()        
        conn = self.db
        self.db = None
        del python_thread.database #importante porque parece que a veces los threads se reusan (python los vuelve a devolver)
        #log("Releasing Connection %i from thread %i" % (id(conn), id(python_thread)), True)
        #if(not kwargs.get("DROP_CONNECTION", False)): Database.connections_pool.put_nowait(conn)
        Database.mutex.release()    
        