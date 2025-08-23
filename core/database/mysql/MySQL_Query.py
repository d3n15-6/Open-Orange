from core.database.Query import Query
from MySQL_ModuleImporter import *
from core.database.Database import DBConnectionLost, DBFieldNotFound, DBTableNotFound, DBSyntaxError, DBIntegrityError, DBAccessDenied, DBDataTruncatedError, DBPacketTooBig, DBAlreadyExists, DBLockWaitTimeout, DBCantConnect, DBUnknownDatabase
from Log import log, logConnection
import sys
from array import array
from datetime import timedelta

#if sys.platform.startswith("mac"): FIELD_TYPE.BIT = 999999

class MySQL_Query(Query):
    
    types_map = {
        #FIELD_TYPE.BIT: "boolean",
        FIELD_TYPE.BLOB: "blob",
        FIELD_TYPE.CHAR: "string",
        FIELD_TYPE.DATE: "date",
        FIELD_TYPE.DATETIME: "time",
        FIELD_TYPE.DECIMAL: "value",
        FIELD_TYPE.DOUBLE: "value",
        FIELD_TYPE.ENUM: "integer",
        FIELD_TYPE.FLOAT: "value",
        FIELD_TYPE.GEOMETRY: "string",
        FIELD_TYPE.INT24: "integer",
        FIELD_TYPE.INTERVAL: "string",
        FIELD_TYPE.LONG: "integer",
        FIELD_TYPE.LONG_BLOB: "blob",
        FIELD_TYPE.LONGLONG: "integer",
        FIELD_TYPE.MEDIUM_BLOB: "blob",
        FIELD_TYPE.NEWDATE: "date",
        FIELD_TYPE.NEWDECIMAL: "value",
        FIELD_TYPE.NULL: "string",
        FIELD_TYPE.SET: "integer",
        FIELD_TYPE.SHORT: "integer",
        FIELD_TYPE.STRING: "string",
        FIELD_TYPE.TIME: "time",
        FIELD_TYPE.TIMESTAMP: "time",
        FIELD_TYPE.TINY: "boolean",
        FIELD_TYPE.TINY_BLOB: "memo",
        FIELD_TYPE.VAR_STRING: "string",
        #FIELD_TYPE.VARCHAR: "string",
        FIELD_TYPE.YEAR: "integer",
    }
    
    
    def __init__(self, database):
        Query.__init__(self, database)
        try:
            from functions import now
            if now() - self.database.last_query_ts > timedelta(minutes=3):
                logConnection("More than 3 minutes elapsed since last query. Doing ping")
                self.database.db.ping()
                logConnection("Ping OK")
                self.database.last_query_ts = now()
                from functions import Query as funcQuery
                q = funcQuery()
                q.sql = "USE %s" %(self.database.dbname)
                q.execute()
                logConnection("Using %s" %(self.database.dbname))
        except Connection.OperationalError, e:
            logConnection("Ping Error %s" %(e))
            self.database.connect()

    def generateRecord(self, r):
        res = self.result_class()
        i = 0 
        for d in self.result_description:
            if not res.hasField(d[0]):
                res.createField(d[0], MySQL_Query.types_map[d[1]], max(d[2], d[3]), True, "")
            if d[1] == FIELD_TYPE.BLOB and isinstance(r[i], array):
                res.fields(d[0]).setValue(r[i].tostring())
            else:
                res.fields(d[0]).setValue(r[i])
            i += 1
        res.setNew(False)
        res.setModified(False)
        return res

    def fillRecord(self, idx, rec, fieldsmap):
        r = self.result[idx]
        i = 0 
        for d in self.result_description:
            fn = fieldsmap.get(d[0], None)
            if fn:
                f = rec.fields(fn)
                if d[1] == FIELD_TYPE.BLOB and isinstance(r[i], array):
                    rec.fields(fn).setValue(r[i].tostring())
                    rec.oldFields(fn).setValue(r[i].tostring())
                else:
                    rec.fields(fn).setValue(r[i])
                    rec.oldFields(fn).setValue(r[i])
            i += 1
        rec.setNew(False)
        rec.setModified(False)
        return rec

    def fillRecord(self, idx, rec, fieldsmap):
        r = self.result[idx]
        i = 0 
        for d in self.result_description:
            fn = fieldsmap.get(d[0], None)
            if fn:
                f = rec.fields(fn)
                if d[1] == FIELD_TYPE.BLOB and isinstance(r[i], array):
                    rec.fields(fn).setValue(r[i].tostring())
                    rec.oldFields(fn).setValue(r[i].tostring())
                else:
                    rec.fields(fn).setValue(r[i])
                    rec.oldFields(fn).setValue(r[i])
            i += 1
        rec.setNew(False)
        rec.setModified(False)
        return rec


    def pre_execute(self):
        try:
            Query.pre_execute(self)
        except Connection.OperationalError, e:
            self.process_Exception_OperationalError(e)
        except Connection.DataError, e:
            self.process_Exception_DataError(e)
        except Connection.ProgrammingError, e:
            self.process_Exception_ProgrammingError(e)
        except Connection.IntegrityError, e:
            self.process_Exception_IntegrityError(e)
        except Connection.NotSupportedError, e:
            self.process_Exception_NotSupportedError(e)
        except Exception, e:
            raise


    def process_Exception_DataError(self, e):
        import threading
        if e[0] == 1265:
            logConnection("Data Error: (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBDataTruncatedError
        raise

    def process_Exception_OperationalError(self, e):
        import threading
        if e[0] == 1049: raise DBUnknownDatabase
        if e[0] == 1044: raise DBCantConnect
        if e[0] == 2003: 
            logConnection("Database connection lost (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBCantConnect
        if e[0] == 2013: 
            logConnection("Database connection lost (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBConnectionLost
        if e[0] == 2006: 
            logConnection("Mysql server has gone away (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBConnectionLost
        if e[0] == 1205: 
            logConnection("Lock wait timeout (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBLockWaitTimeout
        if e[0] == 1227: 
            logConnection("Access Denied (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBAccessDenied
        if e[0] == 1153: 
            logConnection("Packet too big (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBPacketTooBig
        if e[0] == 1054:
            import re
            fn = re.search("Unknown column '([^']*)'", e[1]).group(1)
            if not fn in self.result_class().fieldNames():
                #mstring = "Field %s Not Found in %s" %(fn,self.result_class.__name__)
                #sysprint(mstring) 
                raise DBFieldNotFound(self.result_class.__name__, fn)
            else:
                raise DBFieldNotFound(' , '.join(self.__class__.extractTableNames(self.sql)), fn)
        raise
        
    def process_Exception_ProgrammingError(self, e):
        if e[0] == 1007:
            raise DBAlreadyExists()    
        if e[0] == 1146:
            import re
            tn = re.search("Table '([^']*)' doesn't exist", e[1]).group(1)
            raise DBTableNotFound(tn)
        if e[0] == 1064:
            raise DBSyntaxError(str(e[1]))
        raise
        
    def process_Exception_IntegrityError(self, e):
        if e[0] == 1062:
            raise DBIntegrityError(str(e[1]))
        raise
        
    def process_Exception_NotSupportedError(self, e):
        if e[0] == 1235:
            raise DBSyntaxError(str(e[1]))
        raise
