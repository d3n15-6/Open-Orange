from core.database.Query import Query
from MySQLdb.constants import FIELD_TYPE
import MySQLdb
from MySQLdb.connections import Connection
from core.database.Database import DBConnectionLost, DBFieldNotFound, DBTableNotFound, DBSyntaxError, DBIntegrityError, DBAccessDenied, DBDataTruncatedError, DBPacketTooBig, DBAlreadyExists
from Log import log
import sys


class SQLite_Query(Query):
    
    types_map = {
        #FIELD_TYPE.BIT: "boolean",
        unicode: "string",
        int: "integer",
        None.__class__: "string",
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

    def generateRecord(self, r):
        res = self.result_class()
        i = 0 
        from functions import sysprint,alert
        for d in self.result_description:
            if not res.hasField(d[0]):
                print d[0], r[i].__class__
                res.createField(d[0], SQLite_Query.types_map[r[i].__class__], 0, True, "")
            if isinstance(r[i], unicode):
                res.fields(d[0]).setValue(r[i])
            else:
                res.fields(d[0]).setValue(r[i]) 
            i += 1
        res.setNew(False)
        res.setModified(False)
        return res

    def pre_execute(self):
        from functions import alert
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
        except Exception, e:
            raise

    @classmethod        
    def resolveSchemas(objclass, sql):
        def replacer(mo):
            return mo.group(0)
        return Query.schemas_pattern.sub(replacer, sql)


    @classmethod
    def getSchemaForTable(objclass, tablename):
        return ""
            
    def process_Exception_DataError(self, e):
        import threading
        if e[0] == 1265:
            log("Data Error: (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBDataTruncatedError
        raise

    def process_Exception_OperationalError(self, e):
        import threading
        if e[0] == 2003: 
            log("Database connection lost (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBCantConnect
        if e[0] == 2013: 
            log("Database connection lost (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBConnectionLost
        if e[0] == 2006: 
            log("Mysql server has gone away (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            self.database.db = None
            raise DBConnectionLost
        if e[0] == 1227: 
            log("Access Denied (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBAccessDenied
        if e[0] == 1153: 
            log("Packet too big (%s) TH: %s, DB: %s, CONN: %s" % (e, threading.currentThread().getName(), id(self.database), id(self.database.db)))
            raise DBPacketTooBig
        if e[0] == 1054:
            import re
            fn = re.search("Unknown column '([^']*)'", e[1]).group(1)
            if fn in self.result_class().fieldNames():
                raise DBFieldNotFound(self.result_class.__name__, fn)
            else:
                raise DBFieldNotFound("", fn)
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
        