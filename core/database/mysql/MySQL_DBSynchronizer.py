from OpenOrange import *
from core.database.DBSynchronizer import DBSynchronizer

class MySQL_DBSynchronizer(DBSynchronizer):
    
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
            query.sql = "SHOW TABLES FROM `%s` LIKE s|%s|" % (schema, recordname)
        else:
            query.sql = "SHOW TABLES LIKE s|%s|" % (recordname)
        query.open()
        return bool(query.count())
                
    @classmethod
    def createTable(objclass, rinfo):
        recordname = rinfo["Name"]
        query = Query()
        query.sql = "CREATE TABLE IF NOT EXISTS [%s] (\n" % recordname
        sqllines = []
        primarykey = ""
        masterkey = ""
        for fn in rinfo["Fields"]:
            if rinfo["Fields"][fn]["Persistent"]:
                ftype = rinfo["Fields"][fn]["Type"]    
                length = rinfo["Fields"][fn]["Length"]    
                autoincrement = ""
                if ftype == "internalid":
                    autoincrement = "AUTO_INCREMENT"
                    primarykey = "{%s}" % fn
                elif ftype == "masterid":
                    masterkey = "{%s}" % fn
                sqllines.append("{%s} %s %s" % (fn, objclass.getDBTypeName(ftype, length),autoincrement))
        if primarykey: sqllines.append("PRIMARY KEY (%s)" % primarykey)
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
        query.sql += ",\n".join(sqllines)
        query.sql +="\n)  ENGINE = InnoDB DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci"
        return query.execute()
           

    @classmethod
    def getTableFieldNames(objclass, tablename):
        res = {}
        query = Query()
        query.sql = "SHOW COLUMNS FROM [%s]" % tablename
        query.open()
        for rec in query:
            res[rec.Field] = True
        return res

    @classmethod
    def getTableIndexNames(objclass, tablename):
        res = {}
        query = Query()
        query.sql = "SHOW INDEXES FROM [%s]" % tablename
        query.open()
        for rec in query:
            res[rec.Key_name] = True
        return res

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

        if not force and len(added) == 0: return True
                        
        query = Query()
        query.sql = "ALTER TABLE [%s] " % recordname
        sqllines = []
        primarykey = ""
        masterkey = ""
        for fn in equals:
            autoincrement = ""
            if rinfo["Fields"][fn]["Type"] == "internalid":
                autoincrement = "AUTO_INCREMENT"
                primarykey = fn
            elif rinfo["Fields"][fn]["Type"] == "masterid":
                masterkey = fn
            sqllines.append("CHANGE {%s} {%s} %s %s" % (fn,fn,objclass.getDBTypeName(rinfo["Fields"][fn]["Type"],rinfo["Fields"][fn]["Length"]), autoincrement))
        
        for fn in added:
            autoincrement = ""
            if rinfo["Fields"][fn]["Type"] == "internalid":
                autoincrement = "AUTO_INCREMENT"
                primarykey = fn
            elif rinfo["Fields"][fn]["Type"] == "masterid":
                masterkey = fn
            sqllines.append("ADD {%s} %s %s" % (fn,objclass.getDBTypeName(rinfo["Fields"][fn]["Type"],rinfo["Fields"][fn]["Length"]), autoincrement))

        for idx in tableindexes:
            if rinfo["Indexes"].has_key(idx):
                sqllines.append("DROP INDEX {%s}" % idx)

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
                sqllines.append("ADD %s {%s} (" % (idxtype, idx) + ",".join(idxlines) + ")")
        query.sql += ",\n".join(sqllines)
        query.sql += "\n,CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci"
        query.sql += "\n,DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci"
        return query.execute()
