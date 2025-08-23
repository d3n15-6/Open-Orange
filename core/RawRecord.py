from Embedded_OpenOrange import *
from core.Responses import *
from functions import *
from core.AppServerConnection import AppServerConnection
import cPickle
from Field import Field
from core.database.Database import Database, DBConnectionError
from core.database.Query import Query as QueryClass
from Log import log

use_query_optimizations = None

def get_use_query_optimizations():
    global use_query_optimizations
    if use_query_optimizations is None:
        from SystemSettings import SystemSettings
        try:
            ss = SystemSettings.bring()
        except:
            try:
                synchronizeRecord("SystemSettings", True, True)
                ss = SystemSettings.bring()
            except DBConnectionError, e:
                return False
        if ss:
            use_query_optimizations = ss.UseQueryOptimization
            if use_query_optimizations:
                sysprint("Using SQL Optimiztions.")
            else:
                sysprint("Not using SQL Optimizations.")
    return bool(use_query_optimizations)

    
class RawRecord(Embedded_Record):
    __linkedfields = None
    ALLOW_LINKED_ORPHANS = False #Si se pone en true, no chequea que los registros existan al utilizar linkto
    
    def showMessages(self):
        if hasattr(self,"message_queue"):
            for msg in self.message_queue:
                message(msg)
            self.message_queue = []
            
    def appendMessage(self, msg):
        if (msg):
            if hasattr(self, "message_queue"): 
                if msg not in self.message_queue:
                    self.message_queue.append(msg)
            else:
                self.message_queue = [msg]
            
    def persistentFields(self):
        return filter(lambda x: self.fields(x).isPersistent(), self.fieldNames())

    def getSetFields(self):
        return filter(lambda x: self.fields(x).getType() == "set", self.fieldNames())

    def persistentDetails(self):
        return filter(lambda x: self.details(x).isPersistent(), self.detailNames())
    
        
    @classmethod
    def getLinkedFields(objclass):
        if objclass.__linkedfields is None:
            objclass.__linkedfields = {}
            obj = objclass()
            for fn in obj.fieldNames():
                lt = obj.fields(fn).getLinkTo()
                if lt:
                    objclass.__linkedfields[fn] = lt
        return objclass.__linkedfields

    def checkLinkedFields(self, masterrecord=None, detailfieldname=None, rownr=None):
        flist = self.getLinkedFields()
        for lfield in flist:
            record = NewRecord(flist[lfield])
            if record and record.__class__.ALLOW_LINKED_ORPHANS: continue
            if self.fields(lfield).getType() != "set":
                SerNrCode = self.fields(lfield).getValue()
                if utf8(SerNrCode) and SerNrCode != 0:
                    record = record.bring(SerNrCode)
                    if not record or record.fields(record.uniqueKey()[0]).getValue() != SerNrCode: #the last part is because of tailing spaces mysql problem
                        if not detailfieldname:
                            return self.INVALIDVALUEERR(lfield)
                        else:
                            return masterrecord.INVALIDVALUEERR(detailfieldname, lfield, rownr)
            else:
                for SerNrCode in [v.strip() for v in self.fields(lfield).getValue().split(",")]:
                    if str(SerNrCode) and SerNrCode != 0:
                        record = record.bring(SerNrCode)
                        if not record or record.fields(record.uniqueKey()[0]).getValue() != SerNrCode: #the last part is because of tailing spaces mysql problem
                            if not detailfieldname:
                                return self.INVALIDVALUEERR(lfield, "", -1, SerNrCode)
                            else:
                                return masterrecord.INVALIDVALUEERR(detailfieldname, lfield, rownr, SerNrCode)
        for dn in self.detailNames():
            detail = self.details(dn)
            rownr=0
            for row in detail:
                res = row.checkLinkedFields(self, dn, rownr)
                rownr += 1
                if not res: return res
        return True

    def sql_rawStore_not_optimized(self, schema):
        if self.isNew():
            q = Query()
            q.sql, q.params = self.sql_insert(schema, q)
            res = q.rawExecute()
            if not res: 
                rollback()            
                return res
            self.internalId = q.getLastAutomaticValue()                
            res = self.sql_updateSetTables(schema, q)
            if not res: 
                rollback()
                return res    
            for dn in self.persistentDetails():
                detail = self.details(dn)
                detail.setMasterId(self.internalId)
                for row in detail:
                    if row.isModified():
                        res = row.sql_rawStore(schema)
                        if not res: 
                            rollback()
                            return res
                if detail.count():
                    q = Query()
                    q.sql = "UPDATE %s%s set `rowId`=`internalId` WHERE `masterId`=%i" % (q.composeSchema(q.getSchemaForTable(detail.name())), Database.escapeTableName(detail.name()), self.internalId)
                    res = q.rawExecute()
                    if not res:
                        rollback()
                        return res
                    for row in detail: row.rowId = row.internalId
            if not self.isDetail():
                from EventLog import EventLog
                self.logEvent(EventLog.INSERT)                            
        elif self.isModified():
            q = Query()
            q.sql, q.params = self.sql_update(schema, q)
            res = q.rawExecute()
            if not res: 
                rollback()
                return res
            if q.matchedRows() != 1: 
                rollback()
                return False
            res = self.sql_updateSetTables(schema, q)
            if not res: 
                rollback()
                return res
            for dn in self.persistentDetails():
                detail = self.details(dn)
                update_rowids = False
                for row in detail:
                    if row.isModified():
                        if row.isNew(): 
                            update_rowids = True
                            if not row.masterId: 
                                row.masterId = self.internalId #Esto no deberia ser necesario, pero por alguna razon a veces el masterId esta vacio!
                                log("Fila con masterId en NULL!!!")
                        res = row.sql_rawStore(schema)
                        if not res:
                            rollback()
                            return res
                for rrownr in range(detail.removedRecordsCount()):
                    rrow = detail.getRemovedRecord(rrownr)
                    if not rrow.isNew():
                        res = rrow.sql_rawDelete(schema)
                        if not res:
                            rollback()
                            return res
                if detail.count() and update_rowids:
                    q = Query()
                    q.sql = "UPDATE %s%s set `rowId`=`internalId` WHERE `masterId`=%i AND `rowId` IS NULL" % (q.composeSchema(q.getSchemaForTable(detail.name())), Database.escapeTableName(detail.name()), self.internalId)
                    res = q.rawExecute()
                    if not res:
                        rollback()
                        return res
                    for row in detail: 
                        if not row.rowId: row.rowId = row.internalId
            if not self.isDetail():
                from EventLog import EventLog
                self.logEvent(EventLog.UPDATE)                            
        return True
        
    def sql_rawStore(self, schema):
        if not get_use_query_optimizations(): return self.sql_rawStore_not_optimized(schema)
        updates = []
        inserts = []
        deletes = []
        if self.isModified():
            q = Query()
            inserts, updates, deletes = self.get_store_queries(q)
            res = self.run_sql_queries(q, inserts, updates, deletes)
            if not res: 
                rollback()
                return res
            if not self.isDetail():
                if self.isNew():
                    self.logEvent(0)
                else:
                    self.logEvent(1)
        return True

    def run_sql_queries(self, query, inserts, updates, deletes):
        #deletes
        for table, wfields in deletes:
            sql = "DELETE FROM %s WHERE %s" % (table, ' AND '.join(wfields))
            query.sql = sql
            res = query.rawExecute()
            if not res: return res
            #chequeo por matched fields???

        #inserts
        inserts_grouped = {}
        for ins in inserts:
            l = inserts_grouped.get((ins[4], ins[0]), [])
            l.append(ins)
            inserts_grouped[(ins[4], ins[0])] = l
        rowid_updates = []
        for order, tb in sorted(inserts_grouped.keys()): #recorro los grupos de insert ordenados primero por grupo y luego por tabla
            values_group = []
            n = 0
            for table, fields, values, record, sort_order in inserts_grouped[(order, tb)]:
                vv = []
                for v in values:
                    if not isinstance(v, tuple): 
                        vv.append(v)
                    else:
                        vv.append(v[0](*v[1]))
                n += 1
                values_group.extend(vv)
            sql = "INSERT INTO %s (%s) values %s" % (table, ','.join(fields), ','.join(["(%s)" % ','.join(['%s'] * len(vv))]*n))
            query.sql = sql
            query.params = values_group
            res = query.execute()
            if not res: return res
            if query.matchedRows() != len(inserts_grouped[(order, tb)]): return False
            internalId = query.getLastAutomaticValue()
            for table, fields, values, record, sort_order in inserts_grouped[(order, tb)]:
                if record:
                    record.internalId = internalId
                    for dn in record.detailNames(): record.details(dn).setMasterId(record.internalId)
                    if record.hasField("rowId"): rowid_updates.append(record)
                internalId += 1

        #updates
        max_joins = 60
        for i in range(0,len(updates),max_joins):
            t = 0
            allfields = []
            alltables = []
            allwfields = []
            allvalues = []
            if i < len(updates):
                torec = min(i+max_joins,len(updates))
                for j in range(i,torec):
                    table, fields, wfields, values = updates[j]
                    alltables.append("%s `t%s`" % (table,t))
                    for f in fields:
                        if isinstance(f, basestring):
                            allfields.append("t%s.%s" % (t, f))
                        else: #se supone que aca viene una tupla
                            allfields.append(''.join(["t%s.%s" % (t, ff) for ff in f]))
                    for f in wfields:
                        if isinstance(f, basestring):
                            allwfields.append("t%s.%s" % (t, f))
                        else: #se supone que aca viene una tupla
                            allwfields.append("t%s.%s" % (t, f[0] + f[1](*f[2])))
                    allvalues.extend(values)
                    t += 1
                try:
                    sql = "UPDATE %s SET %s WHERE %s" % (','.join(alltables), ','.join([r for r in allfields]), ' AND '.join(allwfields))
                    params = allvalues
                except Exception, e:
                    alert([(r, r.__class__.__name__, r.decode('utf8')) for r in allfields])
                    raise
                query.sql = sql
                query.params = params
                res = query.rawExecute()
                if not res: return res
                if query.matchedRows() != (torec-i): 
                    return False
        for record in rowid_updates:
            record.rowId = record.internalId
        return True


    def get_store_queries(self, query):
        inserts = []
        updates = []
        deletes = []
        if self.isModified():
            if self.isNew():
                self.internalId = None
                self.rowId = None
                ins, dels = self.get_sql_insert_components(query)
                inserts.extend(ins); updates.extend(dels)
            else:
                updates.extend(self.get_sql_update_components(query))
            ins, dels = self.get_sql_store_set_components(query)
            inserts.extend(ins); deletes.extend(dels)

            for dn in self.persistentDetails():
                detail = self.details(dn)
                for row in detail:
                    if row.isModified():
                        ins, upds, dels = row.get_store_queries(query)
                        inserts.extend(ins); updates.extend(upds); deletes.extend(dels)
                for rrownr in range(detail.removedRecordsCount()):
                    rrow = detail.getRemovedRecord(rrownr)
                    if not rrow.isNew():
                        deletes.extend(rrow.get_delete_queries(query))
        return inserts, updates, deletes

    def get_delete_queries(self, query):
        deletes = []
        if not self.isNew():
                deletes.append(self.get_sql_delete_components(query))
                deletes.extend(self.get_sql_delete_set_components(query))
        return  deletes
        

    def get_sql_update_components(self, query):
        table = "%s%s" % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), Database.escapeTableName(self.__class__.__name__))
        fnames = filter(lambda fname: self.fields(fname).getValue() != self.oldFields(fname).getValue() or self.fields(fname).isNone() != self.fields(fname).isNone(), self.persistentFields())
        if fnames:
            fields = ['`%s`=%s' % (fn, '%s') for fn in fnames]
            values = [self.fields(fn).getValue() for fn in fnames]
            #fields = []
            if self.isDetail():
                wfields = ["`internalId`=%s" % self.oldFields("internalId").getSQLValue()]
            else:
                wfields = ["`internalId`=%s" % self.oldFields("internalId").getSQLValue(), "`syncVersion` %s" % {True: "IS NULL", False: "="+self.oldFields("syncVersion").getSQLValue()}[self.oldFields("syncVersion").isNone()]]
            return [(table, fields, wfields, values)]
        return []

    def get_sql_insert_components(self, query):
        table = "%s%s" % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), Database.escapeTableName(self.__class__.__name__))
        fields = ['`%s`' % fn for fn in self.persistentFields()]
        if self.isDetail():
            order = 2
            values = []
            for fn in self.persistentFields():
                if fn == "masterId":
                    values.append((self.getMasterRecord().fields("internalId").getValue, ()))
                else:
                    values.append({True: None, False:self.fields(fn).getValue()}[self.fields(fn).isNone()])
            updates = [(table, [("`rowId`=", "`internalId`")], [("`internalId`=",self.fields("internalId").getSQLValue, ())], [])]
        else:
            order = 1
            values = [{True: None, False:self.fields(fn).getValue()}[self.fields(fn).isNone()] for fn in self.persistentFields()]
            updates = []
        return [(table, fields, values, self, order)], updates

    def get_sql_delete_components(self, query):
        table = "%s%s" % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), Database.escapeTableName(self.__class__.__name__))
        wfields = ["`internalId`=%s" % self.internalId]
        return (table, wfields)

    def get_sql_store_set_components(self, query):
        inserts = []
        deletes = []
        setfields = self.getSetFields()
        table = None
        for fn in setfields:
            field = self.fields(fn)
            rn = field.getRecordName()
            if rn:
                if  self.oldFields(fn).isNone() == field.isNone() and self.oldFields(fn).getValue() == field.getValue(): continue
                if not self.isNew():
                    if not table: table = "%s%s" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn))
                    wfields = ["`masterId`=%s" % self.internalId]
                    deletes.append((table, wfields))
                labels = filter(lambda x: x != '', map(lambda x: x.strip(), field.getValue().split(",")))
                for lab in labels:
                    if not table: table = "%s%s" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn))
                    fields = ["`masterId`", "`Value`"]
                    if self.isNew(): #todavia no tengo self.internalId
                        values = [(self.fields("internalId").getValue, ()), "%s" % lab]
                    else:
                        values = [self.internalId, "%s" % lab]
                    inserts.append((table, fields, values, None, 3))
        return (inserts, deletes)

    def get_sql_delete_set_components(self, query):
        inserts = []
        deletes = []
        setfields = self.getSetFields()
        table = None
        for fn in setfields:
            field = self.fields(fn)
            rn = field.getRecordName()
            if rn:
                if not self.isNew():
                    if not table: table = "%s%s" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn))
                    wfields = ["`masterId`=%s" % self.internalId]
                    deletes.append((table, wfields))
        return deletes

    @classmethod
    def sql_rawStoreMany(objclass, records):
        q = Query()
        q.sql = objclass.sql_insertMany(objclass, q)
        values_list = []
        fnames = objclass().persistentFields()
        fnames.remove('internalId')
        for record in records:
            values = []
            for fn in fnames:
                f = record.fields(fn)
                if f.isNone():
                    values.append(None) #because f.getSQLValue() returns "NULL"
                else:
                    values.append(f.getPythonSQLValue())
            values_list.append(values)
        res = q.rawExecuteMany(values_list)
        return res
    

    def sql_rawDelete(self, schema):
        if not self.isNew():
            q = Query()        
            q.sql = self.sql_delete(schema,q)
            res = q.rawExecute()
            if not res: 
                rollback()
                return res            
            if q.matchedRows() != 1: 
                rollback()
                return False            
            res = self.sql_deleteSetTables(schema,q)
            if not res: 
                rollback()
                return res            
            for dn in self.persistentDetails():
                detail = self.details(dn)
                q = Query()
                q.sql = "DELETE FROM %s%s WHERE `masterId`=%i" % (q.composeSchema(q.getSchemaForTable(detail.name())), Database.escapeTableName(detail.name()), self.internalId)
                res = q.rawExecute()
                if not res: 
                    rollback()
                    return res                
                for row in detail:
                    if not row.isNew():                
                        res = row.sql_deleteSetTables(schema,q)
                        if not res: 
                            rollback()
                            return res
                for rrownr in range(detail.removedRecordsCount()):
                    rrow = detail.getRemovedRecord(rrownr)
                    if not rrow.isNew():
                        q.sql = rrow.sql_delete(schema,q)
                        res = q.rawExecute()
                        if not res: 
                            rollback()
                            return res
                        res = rrow.sql_deleteSetTables(schema,q)
                        if not res: 
                            rollback()
                            return res
            if not self.isDetail():
                from EventLog import EventLog
                self.logEvent(EventLog.DELETE)
        return True
            
    def sql_insert(self, schema ,query):
        values = []
        fnames = self.persistentFields()
        fnames.remove('internalId')
        for fn in fnames:
            if self.fields(fn).isNone():
                values.append(None)
            else:
                values.append(self.fields(fn).getValue())
        return self.sql_insert_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), ",".join(['%s']*len(values))), values

    @classmethod
    def sql_insertMany(objclass, records, query):
        values = []
        fnames = objclass().persistentFields()
        fnames.remove('internalId')
        return objclass.sql_insert_generic() % (query.composeSchema(query.getSchemaForTable(objclass.__name__)),','.join(map(lambda x: "%s", fnames)))
        
    @classmethod
    def sql_insert_generic(classobj):
        if not hasattr(classobj, "_sql_insert_"):
            fnames = classobj().persistentFields()
            fnames.remove('internalId')
            classobj._sql_insert_ = "INSERT INTO %%s%s (%s) values (%s)" % (Database.escapeTableName(classobj.__name__), ','.join(map(lambda x: '`%s`' % x, fnames)), '%s')
        return classobj._sql_insert_

    @classmethod
    def sql_insertmany_generic(classobj):
        if not hasattr(classobj, "_sql_insertmany_"):
            fnames = classobj().persistentFields()
            fnames.remove('internalId')
            classobj._sql_insertmany_ = "INSERT INTO %%s%s (%s) values (%s)" % (Database.escapeTableName(classobj.__name__), ','.join(map(lambda x: '`%s`' % x, fnames)), "%s")
        return classobj._sql_insertmany_

    def sql_update(self, schema, query):
        fields = []
        values = []
        for fn in self.persistentFields():
            field = self.fields(fn)
            fields.append('`%s`=%s' % (fn, "%s"))
            values.append({True: None, False: field.getValue()}[field.isNone()])
        if self.isDetail():
            return self.sql_update_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), ','.join(fields), self.oldFields("internalId").getSQLValue()), values
        else:
            if self.oldFields("syncVersion").isNone():
                return self.sql_update_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), ','.join(fields), self.oldFields("internalId").getSQLValue()) + " AND `syncVersion` IS NULL", values
            else:
                return self.sql_update_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), ','.join(fields), self.oldFields("internalId").getSQLValue()) + " AND `syncVersion`=%s" % self.oldFields("syncVersion").getSQLValue(), values

    @classmethod
    def sql_update_generic(classobj):
        if not hasattr(classobj, "_sql_update_"):
            #fnames = classobj().persistentFields()
            classobj._sql_update_ = "UPDATE %%s%s set %s WHERE `internalId`=%s" % (Database.escapeTableName(classobj.__name__), '%s', '%s')
        return classobj._sql_update_

    def sql_delete(self, schema, query):
        if self.isDetail():
            return self.sql_delete_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), self.oldFields("internalId").getSQLValue())
        else:
            if self.oldFields("syncVersion").isNone():
                return self.sql_delete_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), self.oldFields("internalId").getSQLValue() + " AND `syncVersion` IS NULL")
            else:
                return self.sql_delete_generic() % (query.composeSchema(query.getSchemaForTable(self.__class__.__name__)), self.oldFields("internalId").getSQLValue() + " AND `syncVersion`=%s" % self.oldFields("syncVersion").getSQLValue())

    @classmethod
    def sql_delete_generic(classobj):
        if not hasattr(classobj, "_sql_delete_"):
            #fnames = classobj().persistentFields()
            #fnames.remove('internalId')
            classobj._sql_delete_ = "DELETE FROM %%s%s WHERE `internalId`=%s" % (Database.escapeTableName(classobj.__name__),'%s')
        return classobj._sql_delete_


    def sql_updateSetTables(self, schema, query):
        setfields = self.getSetFields()
        for fn in setfields:
            field = self.fields(fn)
            if self.oldFields(fn).getValue() == field.getValue(): continue
            rn = field.getRecordName()
            if rn:
                if not self.isNew():
                    q = Query()
                    q.sql = "DELETE FROM %s%s WHERE `masterId`=%s" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn), self.internalId)
                    res = q.rawExecute()
                    if not res: return res
                labels = filter(lambda x: x != '', map(lambda x: x.strip(), field.getValue().split(",")))
                for lab in labels:
                    q = Query()
                    q.sql = "INSERT INTO %s%s (`masterId`,`Value`) values (%s,'%s')" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn), self.internalId, lab)
                    res = q.rawExecute()
                    if not res: return res
        return True

    def sql_deleteSetTables(self, schema, query):
        if not self.isNew():
            setfields = self.getSetFields()
            for fn in setfields:
                field = self.fields(fn)
                rn = field.getRecordName()
                if rn:
                    q = Query()
                    q.sql = "DELETE FROM %s%s WHERE `masterId`=%s" % (query.composeSchema(query.getSchemaForTable(rn)), Database.escapeTableName(rn), self.internalId)
                    res = q.rawExecute()
                    if not res: return res
        return True

    def fields(self, fieldname):
        if self.hasField(fieldname):
            return Field(self, fieldname)
        return None
        
    @classmethod
    def local_readTable(objclass):
        import os
        f = open(os.path.join("local", objclass.__name__ + ".data"), "r")
        tablename = f.readline()
        fnames = f.readline()[:-1].split("\t")
                    
        tuples = [line[:-1].split("\t") for line in f.readlines()]
        records = []
        for t in tuples:
            k = 0
            record = objclass()
            for fn in fnames:
                setattr(record, fn, t[k])
                k += 1
            records.append(record)
        return records

    @classmethod
    def local_writeTable(objclass, records):
        import os
        f = open(os.path.join("local", objclass.__name__ + ".data"), "w")
        f.write(objclass.__name__ +"\n")
        fieldnames = objclass().fieldNames()
        f.write("\t".join(fieldnames) +"\n")
        for record in records:
            values = []
            for fn in fieldnames:
                v = getattr(record, fn)
                if record.fields(fn).isNone():
                    v = ""
                values.append(str(v))
            f.write("\t".join(values) + "\n")
        f.close()
        return True
        
    def local_rawDelete(self):
        records = self.__class__.local_readTable()
        #print '\n'.join([str(x) for x in self.__class__.diff(self, records[7])])
        records = filter(lambda r: len(self.__class__.diff(self, r)) != 0, records)
        #print len(records)
        return self.__class__.local_writeTable(records)
        