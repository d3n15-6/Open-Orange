import re
from Embedded_OpenOrange import getQueryLogging, NewRecord, Embedded_Record
from Log import log
from core.database.Database import Database, DBError, DBConnectionLost

class Query:
    table_pattern = re.compile("([^\\\])\[([^\]]*?)\]")
    field_pattern = re.compile("\{([^\}]*?)\}")
    value_pattern = re.compile("[svdt]\|([^\|]*?)\|")
    integer_value_pattern = re.compile("i\|([^\|]*?)\|")
    boolean_value_pattern = re.compile("b\|([^\|]*?)\|")
    where_and_pattern = re.compile("(WHERE\?AND)")
    
    schemas_pattern = re.compile("\[([^\]]*?)\]")
    __schemas__ = None  
    loading_schemas_map = False
    
    
    def __init__(self, database):
        self.database = database
        self.cursor = None
        self.sql = ""
        self.result = []
        from core.Record import Record
        self.result_class = Record
        self.lastrowid = None
        self.params = []
            

    def setResultClass(self, cls):
        self.result_class = cls

    def setResultClassName(self, classname):
        
        self.result_class = NewRecord(classname).__class__

    
    def open_fromC(self):
        try:
            return self.open()
        except DBError, e:
            from functions import processDBError, utf8
            processDBError(e, {}, utf8(e))
        return None
        
    def open(self):
        self.sql = self.resolveSchemas(self.sql)    
        self.sql = self.processSQL(self.sql)
        res = self.rawOpen()
        return res

    def execute_fromC(self):
        try:
            return self.execute()
        except DBError, e:
            from functions import processDBError, utf8
            processDBError(e, {}, utf8(e))
        return None
        
    def execute(self):
        self.sql = self.resolveSchemas(self.sql)    
        self.sql = self.processSQL(self.sql)
        return self.rawExecute()
        

    def pre_execute(self):
        #import threading
        #log("PRE_EXECUTING Connection (%i,%s) from thread %i" % (id(self.database.db), self.database.db.__class__.__name__, id(threading.currentThread())), True)    
        if not self.database.isConnected(): raise DBConnectionLost
        self.cursor = self.database.db.cursor()
        self.lastrowid = None
        self.matchedrows = 0
        self.result_description = None
        self.result = []
        if self.params:
            if getQueryLogging(): 
                log(self.sql)        
                log(self.params)        
            self.cursor.execute(self.sql, self.params)
        else:
            if getQueryLogging(): 
                log(self.sql)                
            self.cursor.execute(self.sql)
        if self.sql[:3].upper() in ("UPD", "INS", "DEL"):
            self.database.modifying_queries += 1
        self.params = []
        self.result_description = self.cursor.description
        from functions import now
        self.database.last_query_ts = now()
        self.database.queries_count += 1
        

    def pre_executeMany(self, values_list):
        #import threading
        #log("PRE_EXECUTING Connection (%i,%s) from thread %i" % (id(self.database.db), self.database.db.__class__.__name__, id(threading.currentThread())), True)    
        if not self.database.isConnected(): raise DBConnectionLost
        self.cursor = self.database.db.cursor()
        self.lastrowid = None
        self.matchedrows = 0
        self.result_description = None
        self.result = []
        if getQueryLogging(): log(self.sql + "\nINSERT values: %s" % str(values_list))
        self.cursor.executemany(self.sql, values_list)
        self.result_description = self.cursor.description

    def post_execute(self):
        self.cursor.close()
        self.cursor = None

    def post_executeMany(self):
        self.cursor.close()
        self.cursor = None
        
    def rawOpen(self):
        self.pre_execute()
        for r in self.cursor.fetchall():
            #self.result.append(self.generateRecord(r))
            self.result.append(r)           
        self.post_execute()
        return True        
        
    def rawExecute(self):
        self.pre_execute()
        try:
            self.lastrowid = self.cursor.lastrowid
        except AttributeError, e: 
            #en Oracle, a veces lastrowid no viene definido (cuando no hay un INSERT, por ejemplo). entonces dejo el self.lastrowid en None.
            pass
        self.matchedrows = self.cursor.rowcount        
        self.post_execute()
        return True

    def rawExecuteMany(self,values_list):
        self.pre_executeMany(values_list)
        self.lastrowid = self.cursor.lastrowid
        self.matchedrows = self.cursor.rowcount
        self.post_executeMany()
        return True
        
    def close(self):
        self.result = []
        self.result_description = None
        self.lastrowid = None
        self.matchedrows = 0
        return True
        
    def __len__(self):
        return len(self.result)

    def __getitem__(self, idx):
        res = self.result[idx]
        if isinstance(res, Embedded_Record): return res
        if isinstance(res, list): return [self.generateRecord(r) for r in res] #esto es para cuando se pide in slice
        return self.generateRecord(res)


    def generateRecord(self, r):
        return None
        
    def getCurrentDBName(self):
        return self.database.dbname
        
    def count(self):
        return len(self.result)
        
    @classmethod
    def processSQL(classobj, sql):
        global k
        k = 0
        def where_and_replacer(mo):
            global k
            k += 1
            if k == 1: return "WHERE"
            return "AND"
        def value_replacer(mo):
            return "'%s'" % mo.group(1).replace("[","\\[").replace("{", "\\{")
        def integer_value_replacer(mo):
            return "%s" % mo.group(1).replace("[","\\[").replace("{", "\\{")
        def boolean_value_replacer(mo):
            return {"true": "1", "1": "1", "false": "0", "0": "0"}[mo.group(1).replace("[","\\[").replace("{", "\\{").lower()]
        sql = Query.value_pattern.sub(value_replacer, sql)
        sql = Query.boolean_value_pattern.sub(boolean_value_replacer, sql)
        sql = Query.integer_value_pattern.sub(integer_value_replacer, sql)
        sql = Query.table_pattern.sub("\g<1>`\g<2>`", sql)
        sql = Query.field_pattern.sub("`\g<1>`", sql)
        sql = Query.where_and_pattern.sub(where_and_replacer, sql)
        sql = sql.replace("\\[", "[").replace("\\{", "{")
        return sql

    def processSQL2(self, sql):
        return self.__class__.processSQL(sql)
        
    def setLimit(self, qty, offset=-1):
        if offset < 0:
            self.sql += " LIMIT %i" % (qty)
        else:
            self.sql += " LIMIT %i, %i" % (offset, qty)
        
    def getLastAutomaticValue(self):
        return self.lastrowid
        
    def matchedRows(self):
        return self.matchedrows

    def getSQL(self):
        return self.sql
        
    def setSQL(self, sql):
        self.sql = sql
        
    def addSQL(self, sql):
        self.sql += sql
        
    @classmethod
    def getSchemasMap(objclass):        
        if not Query.__schemas__:
            Query.__schemas__ = {}        
            if not Query.loading_schemas_map:
                from SchemaSettings import SchemaSettings
                Query.loading_schemas_map = True
                ss = SchemaSettings.bring()
                Query.loading_schemas_map = False
                if ss.Enabled:
                    for schema in ss.Schemas:
                        Query.__schemas__[schema.TableName] = schema.Schema
        return Query.__schemas__

    @classmethod
    def clearSchemasMap(objclass):
        from SchemaSettings import SchemaSettings
        SchemaSettings.buffer.clear()
        if Query.__schemas__ is not None: 
            Query.__schemas__ = None
        
    @classmethod
    def getSchemaForTable(objclass, tablename):
        try:
            sm = objclass.getSchemasMap() 
            return sm[tablename]
        except KeyError, e:
            return Database.getCurrentDB().dbname

    def getSchemaForTable_fromC(self, tablename):
        try:
            return self.__class__.getSchemaForTable(tablename)
        except DBError, e:
            from functions import processDBError, utf8
            processDBError(e, {}, utf8(e))
        return None
            
    @classmethod        
    def resolveSchemas(objclass, sql):
        def replacer(mo):
            try:
                if mo.group(1) == "SchemaSettings": return mo.group(0)
                sm = objclass.getSchemasMap()
                sch = sm[mo.group(1)]
                return ("[%s]." % sch) + mo.group(0)
            except KeyError, e:
                return mo.group(0)
        return Query.schemas_pattern.sub(replacer, sql)

    @classmethod #temporal para mac
    def resolveSchemas2(objclass, sql):
        def replacer(mo):
            try:
                sm = objclass.getSchemasMap()
                sch = sm[mo.group(1)]
                return ("[%s]." % sch) + mo.group(0)
            except KeyError, e:
                return mo.group(0)
        return Query.schemas_pattern.sub(replacer, sql)

    def composeSchema(self, schema):
        if schema:
            return Database.escapeTableName(schema) + "."
        return ""
        
    def escapeValue(self, value):
        return self.database.escapeValue(value)
        
    def resolveSchemas_fromC(self, sql):
        try:
            def replacer(mo):
                try:
                    sm = self.__class__.getSchemasMap()
                    sch = sm[mo.group(1)]
                    return ("[%s]." % sch) + mo.group(0)
                except KeyError, e:
                    return mo.group(0)
            return Query.schemas_pattern.sub(replacer, sql)
        except DBError, e:
            from functions import processDBError, utf8
            processDBError(e, {}, utf8(e))
        return None


    def composeSchema_fromC(self, schema):
        return self.composeSchema(schema)
        
    def fieldNames(self):
        if self.result_description:
            return [x[0] for x in self.result_description]
        return []
        
    @classmethod
    def extractTableNames(classobj, sql):
        import re
        tables = []
        ptrn = re.compile("[fF][rR][oO][mM][ \n\t`,]+([^ \n\t`,]*)")
        mo = ptrn.search(sql)
        if mo and mo.groups():
            tables.extend(mo.groups())
        ptrn = re.compile("[Jj][Oo][Ii][Nn][ \n\t`,]+([^ \n\t`,]*)")
        mo = ptrn.search(sql)
        if mo and mo.groups():
            tables.extend(mo.groups())
        return tables
                