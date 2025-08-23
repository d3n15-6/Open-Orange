#coding: utf8
from OpenOrange import *
from Company import Company

class RecordSynchronizator(object):

    def __init__(self, source_company_code, destination_company_code):
        self.source = source_company_code
        self.destination = destination_company_code
    
    def switchToDestination(self):
        if currentCompany() != self.destination:
            cmp = Company.bring(self.destination)
            if not cmp: raise AppException, "Company %s not found" % self.destination
            cmp.setCurrent()
            
    def switchToSource(self):
        if currentCompany() != self.source:
            cmp = Company.bring(self.source)
            if not cmp: raise AppException, "Company %s not found" % self.source
            cmp.setCurrent()
    
    def synchronize(self, recordname, **kwargs):
        where = kwargs.get("where", "")
        sync_missings = kwargs.get("sync_missings", True)
        transfer_token = kwargs.get("transfer_token", False)
        dest_recordname = kwargs.get("destination_recordname", recordname)
        rec = NewRecord(recordname)
        clone = kwargs.get("clone_method", rec.__class__.clone)
        no_changes_token_transfer = kwargs.get("no_changes_token_transfer", True)
        override_changes = kwargs.get("override_changes", True)
        synchronize_days_ago = kwargs.get("synchronize_days_ago", False)
        if synchronize_days_ago:
            if where:
                where += " AND "
            else:
                where += " WHERE "
            where += "DATEDIFF(CURDATE(),TransDate) < i|%s|" % synchronize_days_ago
        dest_rec = NewRecord(dest_recordname)
        uk = rec.uniqueKey()
        current = Company.getCurrent()


        #cambio a la base de destination para traer los registros y sus versiones
        self.switchToDestination()
        q = Query()
        q.sql = "SELECT t.internalId, t.syncVersion, %s FROM [%s] t " % (','.join(uk), dest_recordname)
        q.sql += where
        q.setResultClass(rec.__class__)
        q.open()        
        versions = {}
        for r in q:
            pid = r.getPortableId()
            try:            
                versions[pid]["dver"] = r.syncVersion
                versions[pid]["did"] = r.internalId
            except KeyError, e:
                versions[pid] = {"sver": 0, "sid": 0, "dver": r.syncVersion, "did": r.internalId}


        #cambio a la base de source para traer los registros y sus versiones
        self.switchToSource()
        q = Query()
        q.sql = "SELECT t.internalId, t.syncVersion, %s FROM [%s] t " % (','.join(uk), recordname)
        q.sql += where
        q.setResultClass(rec.__class__)
        q.open()
        for r in q:
            pid = r.getPortableId()        
            try:
                versions[pid]["sver"] = r.syncVersion
                versions[pid]["sid"] = r.internalId
            except KeyError, e:
                versions[pid] = {"sver": r.syncVersion, "sid": r.internalId, "dver": 0, "did": 0}


        recs_to_store = []            
        recs_to_delete = []
        for pid, d in versions.items():
            if abs(d["sver"]) > abs(d["dver"]) or (no_changes_token_transfer and abs(d["sver"]) == abs(d["dver"]) and d["sver"] < 0) or (override_changes and abs(d["sver"]) != abs(d["dver"])):
                recs_to_delete.append(d)
                recs_to_store.append(d)
            else:
                if sync_missings and d["sver"] == 0:
                    recs_to_delete.append(d)
        
        source_records = rec.__class__.getListByInternalId(InternalIdsList = [d["sid"] for d in recs_to_store], SaveAllowed=True)
        token_transfering_records = []
        try:
            try:
                #vuelvo a la base de destino para grabar los registros traidos desde source
                self.switchToDestination()

                #primero borro los registros de la tabla que seran reemplazados
                commit_needed = False
                if recs_to_delete:
                    for dn in dest_rec.detailNames():
                        q = Query()
                        q.sql = "DELETE FROM [%s] WHERE masterId in (%s)" % (dest_rec.details(dn).name(), ','.join([str(d["did"]) for d in recs_to_delete]))
                        q.execute()            
                    q = Query()
                    q.sql = "DELETE FROM [%s] WHERE internalId in (%s)" % (dest_recordname, ','.join([str(d["did"]) for d in recs_to_delete]))
                    q.execute()
                    commit_needed = True
                if recs_to_store:
                    #ahora grabo los registros
                    if dest_recordname == "Invoice":
                        maxstores = 30 
                    else:
                        maxstores = 9999999
                    limite = 1
                    for id, r in source_records.items():
                        if limite <= maxstores:
                            newrec = clone(r)
                            if r.syncVersion < 0:
                                if transfer_token:
                                    newrec.syncVersion = r.syncVersion+1 #ej: -7 -> -6
                                    token_transfering_records.append(r)
                                else:
                                    newrec.syncVersion = -(r.syncVersion+1) #ej: -7 -> 6
                            else:
                                newrec.syncVersion = abs(r.syncVersion-1) #ej: 7 -> 6
                            res = newrec.store()
                            if not res:
                                message("Error grabando en la base de destino")
                                message(res)
                                return
                        else:
                            break
                        limite += 1
                    commit_needed = True
                log(commit_needed)
                if commit_needed: commit()
                if token_transfering_records:
                    #cambio a source para actualizar los registros que transfirieron el token
                    self.switchToSource()
                    for r in token_transfering_records:
                        r.syncVersion = -(r.syncVersion + 1) #ej -7 -> 6
                        res = r.store()
                        if not res:
                            message("Error actualizando tokens en base de origen para registro %s" % r.getPortableId())
                            message(res)
                        else:
                            commit() # aca hago un commit por registro para minimizar riesgo de no poder quitar el token a registros
                return len(recs_to_delete)
            except IOError, e:
                log(e)
        finally:
            if Company.getCurrent() != current:
                current.setCurrent()
    