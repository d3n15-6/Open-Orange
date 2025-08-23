from OpenOrange import *
from core.database.DBSynchronizer import DBSynchronizer

class SQLite_DBSynchronizer(DBSynchronizer):
    
    @classmethod        
    def getDBTypeName(objclass, ftype, length):
        d = {"string": "VARCHAR(%s)" % length,
             "memo": "MEDIUMTEXT",
             "blob": "LONGBLOB",
             "set": "VARCHAR(%s)" % length,
             "integer": "INTEGER",
             "boolean": "TINYINT(1)",
             "date": "DATE",
             "time": "TIME",
             "internalid": "INTEGER",
             "masterid": "INTEGER",
             "value": "DOUBLE"}
        return d[ftype]
        

    @classmethod
    def tableExists(objclass, recordname):
        query = Query()
        if (recordname != "SchemaSettings" and recordname != "SchemaSettingsRow"):
            schema = query.getSchemaForTable(recordname)
            #query.sql = "SHOW TABLES FROM `%s` LIKE s|%s|" % (schema, recordname)
            query.sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'" % recordname
        else:
            query.sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'" % recordname
        query.open()
        return bool(query.count())
                
    @classmethod
    def createTable(objclass, rinfo):
        recordname = rinfo["Name"]
        query = Query()
        query.sql = "CREATE TABLE IF NOT EXISTS [%s] (\n" % recordname
        sqllines = []
        masterkey = ""
        for fn in rinfo["Fields"]:
            if rinfo["Fields"][fn]["Persistent"]:
                ftype = rinfo["Fields"][fn]["Type"]    
                length = rinfo["Fields"][fn]["Length"]    
                autoincrement = ""
                primarykey = ""
                if ftype == "internalid":
                    autoincrement = "AUTO_INCREMENT"
                    primarykey = "PRIMARY KEY ASC"
                elif ftype == "masterid":
                    masterkey = "{%s}" % fn
                sqllines.append("{%s} %s %s" % (fn, objclass.getDBTypeName(ftype, length),primarykey))
        #if primarykey: sqllines.append("PRIMARY KEY (%s)" % primarykey)
        """
        for idx in rinfo["Indexes"]:
            if not rinfo["Indexes"][idx]["Primary"]:
                unique = rinfo["Indexes"][idx]["Unique"]
                idxfnames = rinfo["Indexes"][idx]["FieldNames"]
                idxtype = "INDEX"
                if unique: idxtype = "UNIQUE INDEX"
                idxlines = []
                for fn,kl in idxfnames:
                    klength = ""
                    if kl: klength = "(%s)" % kl
                    idxlines.append("{%s}%s" % (fn, klength))
                sqllines.append("%s {%s} (" % (idxtype, idx) + ",".join(idxlines) + ")")
        """
        query.sql += ",\n".join(sqllines)
        query.sql +="\n)"
        return query.execute()
           

    @classmethod
    def getTableFieldNames(objclass, tablename):
        res = {}
        query = Query()
        query.sql = "SELECT * FROM [%s] LIMIT 1" % tablename
        query.open()
        for desc in query.fieldNames():
            res[desc] = True
        return res

    @classmethod
    def getTableIndexNames(objclass, tablename):
        """
        res = {}
        query = Query()
        query.sql = " FROM [%s]" % tablename
        query.open()
        for rec in query:
            res[rec.Key_name] = True
        """
        return {}

    @classmethod
    def updateTable(objclass, rinfo, force):
        recordname = rinfo["Name"]
        equals = []
        added = []
        dropped = []
        equals_idx = []
        added_idx = []
        dropped_idx = []
        modified_idx = []
        
        tablefields = objclass.getTableFieldNames(recordname)
        tableindexes = objclass.getTableIndexNames(recordname)
        
        for fn in rinfo["Fields"]:
            if rinfo["Fields"][fn]["Persistent"]:
                if tablefields.has_key(fn):
                    equals.append(fn)
                else:
                    added.append(fn)
        for fn in tablefields:
            if not rinfo["Fields"].has_key(fn) or not rinfo["Fields"][fn]["Persistent"]:
                dropped.append(fn)

        if len(added) == 0: return True
                        
        query = Query()
        query.sql = "ALTER TABLE [%s] " % recordname
        sqllines = []
        primarykey = ""
        masterkey = ""
        
        for fn in added:
            autoincrement = ""
            if rinfo["Fields"][fn]["Type"] == "internalid":
                autoincrement = "AUTO_INCREMENT"
                primarykey = fn
            elif rinfo["Fields"][fn]["Type"] == "masterid":
                masterkey = fn
            sqllines.append("ADD {%s} %s %s" % (fn,objclass.getDBTypeName(rinfo["Fields"][fn]["Type"],rinfo["Fields"][fn]["Length"]), autoincrement))

        query.sql += ",\n".join(sqllines)
        return query.execute()
