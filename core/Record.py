# encoding: utf-8
from Embedded_OpenOrange import *
from core.Responses import *
from functions import *
from core.AppServerConnection import AppServerConnection
import cPickle
from RawRecord import RawRecord, get_use_query_optimizations
from core.database.Database import Database, DBConnectionError, DBError, DBConnectionLost, DBNoCompanySelected

import __builtin__

def PythonRecordToRecord(*args):
    return args[0].toRecord()

def linkToDecorator(func, fieldname, recordname):
    def wrapper(self):
        return func(self, fieldname, recordname)
    return wrapper

class Record(RawRecord):
    ATTACH_NORMAL,ATTACH_RECORD, ATTACH_EMBEDDED_IMAGE, ATTACH_NOTE, ATTACH_PHOTO = (0,1,2,3,4)
    _lock_nontoken_records = None
    __fieldnames = {}
    __detailnames = None #this one should be a dict by class name too
    __indexes = None
    __foreinglinks = None
    __navigationMethodsCreated = False

    def __init__(self):
        RawRecord.__init__(self)
        #sysprint("__INIT__ %s" % (self.__class__.__name__,))
        self.__createNavigationMethods__()
        #self.updateFieldDecimals() not working properly!

    def __bringLinkedRecord(self, fieldname, recordname):
        #exec("from %s import %s as cls" % (recordname, recordname))
        module = __builtin__.__import__(recordname, globals(), locals(), (recordname,))
        return module.__dict__[recordname].bring(self.fields(fieldname).getValue())

    def __createNavigationMethods__(self):
        classobj = self.__class__
        if not classobj.__navigationMethodsCreated and classobj.__name__ != "Record" and classobj.__module__ != "functions":
            for fn in self.fieldNames():
                linkto = self.fields(fn).getLinkTo()
                if linkto != "":
                    if not hasattr(classobj, "get" + fn + "Record"):
                        #sysprint("LINKTO: %s,%s -> %s" % (classobj.__name__, fn, linkto))
                        setattr(classobj, "get" + fn + "Record", linkToDecorator(classobj.__bringLinkedRecord, fn, linkto))
                    if not hasattr(classobj, "get" + linkto):
                        setattr(classobj, "get" + linkto, linkToDecorator(classobj.__bringLinkedRecord, fn, linkto))
            classobj.__navigationMethodsCreated = True

    def __getitem__ (self, key):
        return getattr(self,key)

    def __setitem__ (self, key, value):
        setattr (self,key, value)

    def __iter__ (self):
        for fn in self.fieldNames ():
            yield fn

    def invalidate(self):
        return ErrorResponse("CANNOTINVALIDATE")

    def isInvalid(self):
        #redefined in transaction
        return False

    def getInvalidDate(self):
        #redefined in transaction
        return None


    def save_fromGUI(self):
        from Company import Company
        cc = Company.getCurrent()
        if cc and cc.isApplicationServerCompany() and not self.isLocal():
            conn = cc.getServerConnection()
            if conn:    
                res = conn.saveRecordAndCommit(self)
                if res:
                    self.removeFromBuffer()
                return res
        else:
            res = self.save()
            if res and not self.isLocal():
                commit()
                return res
            return res

    def removeFromBuffer(self):
        pass
        
    def refresh(self):
        return Embedded_Record.refresh(self)
        
        
    def delete_fromGUI(self):
        res = self.delete()
        if res and not self.isLocal():
            commit()
        return res

    @classmethod
    def lock_nontoken_records(clsobj):
        if clsobj._lock_nontoken_records is None:
            clsobj._lock_nontoken_records = False
            try: #en algunas versiones viejas SynchronizationSettings no esta en base y esta en el modulo synchronization
                from SynchronizationSettings import SynchronizationSettings
                ss = SynchronizationSettings.bring()
                if ss.LockNonTokenRecords:
                    for rline in ss.TokenRecords:
                        if rline.TableName == clsobj.__name__:
                            clsobj._lock_nontoken_records = True
                            break
            except:
                pass
        return clsobj._lock_nontoken_records

    def shouldSendToken(self):
        return True #This function is redefine in customizations.

    def store(self, **kwargs):
        if not self.isModified(): return True
        res = self.rawStore(**kwargs)
        if not res: return res
        self.syncOldFields()
        return res

    def save(self, **kwargs):
        try:
            Database.getCurrentDB().blockCommits()
            start_time = now()
            qc = Database.getCurrentDB().getQueriesCount()
            if not self.isModified() and not self.isNew(): return True
            try:
                self.removeEmptyRows()
                self.beforeCheck()
                res = self.check()
                if res:
                    if self.isNew():
                        res = self.beforeInsert()
                        if res:
                            res = self.rawStore(**kwargs)
                            if not res: 
                                self.afterSaveCancelation(res)
                                return res
                            res = self.afterInsert()
                            if res is None: res = True
                    else:
                        res = self.beforeUpdate()
                        if res:
                            res = self.rawStore(**kwargs)
                            if not res: 
                                self.afterSaveCancelation(res)
                                return res
                            res = self.afterUpdate()
                            if res is None: res = True
                if res:
                    self.syncOldFields()
                    log("Record %s was saved with %i queries in %s" % (str(self), Database.getCurrentDB().getQueriesCount() - qc, now()-start_time))
                    return True
                else:
                    self.afterSaveCancelation(res)
                    rollback()
                    return res
            except AppException, e:
                rollback()
                e.kwargs["ShouldBeProcessed"] = True
                processExpectedError(e)
                return False
        finally:
            Database.getCurrentDB().unblockCommits()


    def delete(self, **kwargs):
        if self.isModified(): return ErrorResponse("REGISTERNOTSAVED")
        try:
            if self.isNew(): return True
            res = self.beforeDelete()
            if res:
                res = self.rawDelete(**kwargs)
                if res:
                    self.afterDelete()
                    return True
            if not res:
                if not self.isLocal():
                    rollback()
                return res
        except AppException, e:
            rollback()
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
            return False

    def forceDelete(self):
        if self.isModified(): return ErrorResponse("REGISTERNOTSAVED")
        try:
            if self.isNew(): return True
            res = self.rawDelete()
            if not res:
                if not self.isLocal():
                    rollback()
            return res
        except AppException, e:
            rollback()
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
            return False

    def defaults_fromC(self):
        try:
            return self.defaults()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def defaults(self):
        from RecordCheckPolicy import RecordCheckPolicy
        rcp = RecordCheckPolicy.bring(self.name())
        if (not rcp): return
        if (not rcp.Enabled): return
        for fline in rcp.FieldsList:
            if (fline.Default):
                if (fline.HeaderField in self.fieldNames()):
                    self.fields(fline.HeaderField).setValue(fline.Default)

    def check(self):
        res = self.checkLinkedFields()
        if not res: return res

        from RecordCheckPolicy import RecordCheckPolicy
        rcp = RecordCheckPolicy.bring(self.name())
        if (rcp):
            if (rcp.Enabled):
                nonblanklist = rcp.getNonBlankHeaderFields()
                #alert(nonblanklist)
                for fline in nonblanklist.keys():
                    if (fline in self.fieldNames() and (self.fields(fline).isNone() or self.fields(fline).getValue() == "")):
                        if (nonblanklist[fline]["DontSave"]):
                            return self.FieldErrorResponse(nonblanklist[fline]["Message"],fline)
                        else:
                            message(nonblanklist[fline]["Message"])
                            return True
                nonblankrowlist = rcp.getNonBlankRowFields()
                #alert(nonblankrowlist)
                for headerf in nonblankrowlist.keys():  #recorre la lista de los detalles a controlar
                    if (headerf in self.detailNames()):  #verificar que el campo a controlar este en el registro
                        for rowf in nonblankrowlist[headerf].keys():    #recorrer la lista de columnas a controlar
                            if (rowf in self.details(headerf).fieldNames()):    #verificar que la columna a controlar este en las filas
                                for rline in self.details(headerf): #recorre las filas
                                    rrow = rline
                                    #alert("controlando %s %s "%(headerf,rowf))
                                    if (not rrow.fields(rowf).getValue()):
                                        if (nonblankrowlist[headerf][rowf]["DontSave"]):
                                            mstr = "En fila %s, %s " %(rline.rowNr+1,nonblankrowlist[headerf][rowf]["Message"])
                                            return ErrorResponse(mstr)
                                        else:
                                            mstr = "En fila %s, %s " %(rline.rowNr+1,nonblankrowlist[headerf][rowf]["Message"])
                                            message(mstr)
                                            return True
                checkedfields = rcp.getHeaderCheckedFields()
                for headerf in checkedfields.keys():
                    if (headerf in self.fieldNames()):
                        fvalue = self.fields(headerf).getValue()
                        cvalue = checkedfields[headerf]["Value"]
                        fcheck = checkedfields[headerf]["Check"]
                        evalue = rcp.checkFieldValue(fvalue, cvalue, fcheck)
                        if (evalue):
                            return self.FieldErrorResponse(checkedfields[headerf]["Message"],headerf)
                checkedrowfields = rcp.getRowCheckedFields()
                for headerf in checkedrowfields.keys():
                    if (headerf in self.detailNames()):
                        for rowf in checkedrowfields[headerf].keys():
                            if (rowf in self.details(headerf).fieldNames()):
                                for rline in self.details(headerf): #recorre las filas
                                    fvalue = rline.fields(rowf).getValue()
                                    cvalue = checkedrowfields[headerf][rowf]["Value"]
                                    fcheck = checkedrowfields[headerf][rowf]["Check"]
                                    evalue = rcp.checkFieldValue(fvalue, cvalue, fcheck)
                                    if (evalue):
                                        return rline.FieldErrorResponse(checkedrowfields[headerf][rowf]["Message"],rowf)
        return True

    def afterSaveCancelation(self, error):
        pass

    def beforeCheck(self):
        pass
        
    def beforeInsert(self):
        return True

    def beforeUpdate(self):
        return True

    def afterInsert(self):
        return True

    def afterUpdate(self):
        return True

    def attachFile(self, filename, attach_type=ATTACH_NORMAL):
        #this method doesnt commit to database. You must commit after calling it.
        if self.isNew() or self.isModified(): return ErrorResponse("REGISTERNOTSAVED")
        import os
        f = open(filename, "rb")
        from Attach import Attach
        att = Attach()
        att.Comment = os.path.basename(filename)
        att.Value = f.read()
        att.Type = attach_type
        att.TransDate = today()
        att.TransTime = now().time()
        att.OriginRecordName = self.name()
        att.OriginId = self.getPortableId()
        f.close()
        res = att.store()
        if not res: return res
        res = self.updateAttachFlag()
        if (res):
            res = self.store()
            if not res:
                return res
        return att

    def attachString(self, comment, value, attach_type=ATTACH_NORMAL):
        #this method doesnt commit to database. You must commit after calling it.
        if self.isNew() or self.isModified(): return ErrorResponse("REGISTERNOTSAVED")
        import os
        from Attach import Attach
        att = Attach()
        att.Comment = comment
        att.Value = value
        att.Type = attach_type
        att.OriginRecordName = self.name()
        att.OriginId = self.getPortableId()
        res = att.store()
        if not res: return res
        res = self.updateAttachFlag()
        if (res):
            res = self.store()
            if not res:
                return res
        return att

    def createMimeImageAttach(self, bytearray):
        res = self.attachMimeImage(bytearray)
        if not res: return res
        return str(res.internalId)

    def attachMimeImage(self, image_str, attach_type=ATTACH_EMBEDDED_IMAGE):
        #this method doesnt commit to database. You must commit after calling it.
        if self.isNew(): return ErrorResponse("REGISTERNOTSAVED")
        import os
        from Attach import Attach
        att = Attach()
        att.Value = image_str
        att.Type = attach_type
        att.OriginRecordName = self.name()
        att.OriginId = self.getPortableId()
        res = att.store()
        if not res: return res
        return att

    def deleteAttach(self, internalId):
        from Attach import Attach
        att = Attach()
        att.internalId = internalId
        if (att.load()):
            res = att.delete()
            if (res):
                res = self.updateAttachFlag()
                if (res):
                    res = self.store()
                    if (not res):
                        return res
                    else:
                        commit()
        return True

    def detailNames(self):
        if self.name() and self.name() != "Record" and self.__class__.__module__ != "functions":
            if self.__class__.__detailnames is None:
                self.__class__.__detailnames = self.calculateDetailNames()
            return self.__class__.__detailnames
        else:
            return self.calculateDetailNames()

    def fieldNames(self):
        #this method is not a classmethod because sometimes is called from generic records (Report specs, for example).
        if self.__class__.__name__ != "Record" and self.__class__.__module__ != "functions":
            if not self.__class__.__fieldnames.get(self.__class__.__name__, False):
                self.__class__.__fieldnames[self.__class__.__name__] = self.calculateFieldNames()
            return self.__class__.__fieldnames[self.__class__.__name__]
        else:
            return self.calculateFieldNames()

    def indexes(self):
        if self.name() != "Record":
            if self.__class__.__indexes is None:
                self.__class__.__indexes = self.calculateIndexes()
            return self.__class__.__indexes
        else:
            return self.calculateIndexes()

    @classmethod
    def getForeignLinks(objclass):
        if objclass.__foreinglinks is None:
            objclass.__foreinglinks = []
            recsinfo = getRecordsInfo()
            for recname in recsinfo:
                rinfo = recsinfo[recname]
                if rinfo["Persistent"]:
                    rinfofields = rinfo["Fields"]
                    for fn in rinfofields:
                        if rinfofields[fn]["LinkTo"] == objclass.__name__:
                            objclass.__foreinglinks.append((recname, fn))
        return objclass.__foreinglinks

    def getDecimalFieldNames(self):
        res = []
        for fn in self.fieldNames():
            if self.fields(fn).getType() == "value":
                res.append(fn)
        return res

    def getDecimalRowFieldNames(self):
        res = {}
        for dn in self.detailNames():
            d = []
            detail = self.details(dn)
            for fn in detail.fieldNames():
                if detail.fieldType(fn) == "value":
                    d.append(fn)
            if len(d): res[dn] = d
        return res

    def removeEmptyRows(self):
        for dn in self.detailNames():
            detail = self.details(dn)
            try:
                for i in range(detail.count()-1, -1, -1):
                    row = detail[i]
                    for fn in row.fieldNames():
                        if fn != 'rowNr' and fn != 'masterId':
                            field = row.fields(fn)
                            if not (field.isNone() or not field.getValue()):
                                raise ""
                    detail.remove(i)
            except:
                pass

    def uniqueKey(self):
        return []

    def canBePrinted_fromC(self):
        try:
            return self.canBePrinted()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return None

    def canBePrinted(self):
        if not self.internalId or self.isModified():
            return ErrorResponse("REGISTERNOTSAVED")
        return True

    def printDocument(self, showPreview=None, showPrinterDialog=None, docParams=None):
        return self.printRecord(showPreview, showPrinterDialog, docParams)

    def printRecord(self, showPreview=None, showPrinterDialog=None, docParams=None):
        docinfo = self.getDocument()
        try:
            doccode, docclassname = docinfo
        except ValueError:
            doccode = docclassname = docinfo
        if not docclassname: docclassname = doccode
        if not doccode: return False
        from DocumentSpec import DocumentSpec
        document = DocumentSpec.bring(doccode)
        if not document: return document
        ofcopies = document.OfficialCopies
        if ofcopies <= 0: ofcopies = 1
        if document.ShowOnlyOnePreview:
            ofcopies = 1
        res = True;
        sp = showPreview
        if sp is None: sp = not document.DontShowPreview
        pd = showPrinterDialog
        if pd is None: pd = not document.DontShowPrinterDialog
        for cp in range(1,ofcopies+1):
            self._official_copy = cp
            self._one_preview = False
            res = printDocument(doccode, docclassname, self, sp, pd, docParams)
        return res

    def printAllCopies(self, showPreview=None, showPrinterDialog=None, docParams=None):
        docinfo = self.getDocument()
        try:
            doccode, docclassname = docinfo
        except ValueError:
            doccode = docclassname = docinfo
        if not docclassname: docclassname = doccode
        if not doccode: return False
        from DocumentSpec import DocumentSpec
        document = DocumentSpec.bring(doccode)
        if not document: return document
        ofcopies = document.OfficialCopies
        if ofcopies <= 0: ofcopies = 1
        res = True;
        sp = showPreview
        if sp is None: sp = not document.DontShowPreview
        pd = showPrinterDialog
        if pd is None: pd = not document.DontShowPrinterDialog
        for cp in range(1,ofcopies+1):
            self._official_copy = cp
            self._one_preview = True
            if cp==1:
                pd = True
            else:
                pd = None
            import os
            cwd = os.getcwd()
            res = printDocument(doccode, docclassname, self, sp, pd, docParams)
            os.chdir(cwd)
            if cp==1:
                imp = lastPrinterUsed()
                dp = NewRecord("DocumentPrinter")
                dp.Code = document.Code
                if dp.load():
                    dp.PrinterName = imp
                    res = dp.store()
                    if res:
                        commit()
                else:
                    dp.Code = document.Code
                    dp.PrinterName = imp
                    res = dp.store()
                    if res:
                        commit()
        return True

    def getDocument_fromC(self):
        try:
            return self.getDocument()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return None

    def getDocument(self, additional_varspace={}):
        # Should not have knowledge about how DocumentLink is implemented!
        from DocumentLink import DocumentLink
        documentlink = DocumentLink.bring(self.name())
        if documentlink:
            return documentlink.getDocument(self, additional_varspace)
        return ""

    def getHTMLTemplate(self):
        from HTMLRecordView import HTMLRecordView
        template = HTMLRecordView()
        template.RecordName = self.name()
        if (template.load()):
            return template
        else:
            return None

    def getGenericHTML(self):
        template = self.getHTMLTemplate()
        if (template != None):
            from HTMLRecordView import HTMLRecordView
            msg = HTMLRecordView.replaceNames(self, template.Message,self.tableName())
            return msg
        else:
            html = "<table border=\"1\">\n"
            for att in self.fieldNames():
                if (self.getFieldLabel(att, self.fields(att).getValue())):
                    html += " <tr>\n <td>" + self.getFieldLabel(att, self.fields(att).getValue()) + "</td>\n  <td>" + str(self.fields(att).getValue()) + "</td>\n </tr>"
            html += "</table>"
            return html

    def getXML(record):
        xml = []
        import string
        import Web
        xml.append("<record name=%s>" % Web.XMLAttr(record.__class__.__name__))
        for field in record.fieldNames():
            null = 0
            if record.fields(field).isNone(): null = 1
            xml.append("<field name=%s length=%s null=%s>%s</field>" % (Web.XMLAttr(field), Web.XMLAttr(record.fields(field).getMaxLength()), Web.XMLAttr(null), Web.escapeXMLValue(record.fields(field).getValue())))
        for dn in record.detailNames():
            detailrecord = record.details(dn)
            xml.append("<detailfield name=%s length=%s null=%s>" % (Web.XMLAttr(dn), Web.XMLAttr("0"), Web.XMLAttr("0")))
            for row in detailrecord:
                xml.append("<record name=%s>" % Web.XMLAttr(row.__class__.__name__))
                for fn in row.fieldNames():
                    if row.fields(fn).isNone(): null = 0
                    else: null = 1
                    xml.append("<field name=%s length=%s null=%s>%s</field>" % (Web.XMLAttr(fn), Web.XMLAttr(row.fields(fn).getMaxLength()), Web.XMLAttr(null), Web.escapeXMLValue(row.fields(fn).getValue())))
                xml.append("</record>")
            xml.append("</detailfield>")
        xml.append("</record>")
        log(string.join(xml, '\n'))
        return xml

    def getHTML(self):
        from RecordTemplate import RecordTemplate
        fn = RecordTemplate.findHTMLFilename(self.name())
        if not fn:
            exec("from GenericTemplate import GenericTemplate as Template")
            return Template.getHTML(self)        
        else:
            try:
                exec("from %sTemplate import %sTemplate as Template" % (self.name(), self.name()))
                return Template.getHTML(self)
            except ImportError, e:
                pass

    def getXMLSpecialTags(self):
        return ""

    def __str__(self):
        return "Registro de tipo %s" % self.name()

    def __unicode__(self):
        return "Registro de tipo %s" % self.name()

    def clone(self):
        name = self.name()
        if name is None: name = "Record"
        record = NewRecord(name)
        for field in self.fieldNames():
            if (not (self.fields(field).isNone() or field == "internalId" or field == "masterId" or field == "attachFlag" or field == "syncVersion")):
                record.fields(field).setValue(self.fields(field).getValue())
        if record.hasField("rowNr"): record.rowNr = None
        if record.hasField("rowId"): record.rowId = None
        for field in self.detailNames():
            for row in self.details(field):
                newrow = NewRecord(row.name())
                newrow = row.clone()
                record.details(field).append(newrow)
        return record

    def logEvent(self, action):
        if self.name() != "EventLog":
            from LogSettings import LogSettings
            ls = LogSettings.bring()
            if ls.shouldLogEvents(self.name()):
                from EventLog import EventLog

                eventlog = EventLog()
                eventlog.TableName = self.name()
                eventlog.Action = action
                eventlog.TransDate = today()
                eventlog.TransTime = now()
                eventlog.User = currentUser()
                eventlog.recInternalId = self.internalId
                eventlog.oldId = self.getPortableId(True)
                eventlog.newId = self.getPortableId(False)
                if ls.shouldStoreVersions(self.name()):
                    eventlog.Data = cPickle.dumps(self)
                eventlog.store()

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        from RecordCheckPolicy import RecordCheckPolicy
        rcp = RecordCheckPolicy.bring(self.name())
        if (rcp):
            if (rcp.Enabled):
                noeditable = rcp.getNoEditableHeaderFields()
                #alert(nonblanklist)
                if (fieldname in noeditable.keys()):
                    if (noeditable[fieldname]["Message"]):
                        message(noeditable[fieldname]["Message"])
                        return False
                    else:
                        postMessage("[RCP]" + tr("NOTEDITABLEERR") + ": "+ fieldname)
                        return False
                noedirow = rcp.getNoEditableRowFields()
                #alert(nonblanklist)
                if (fieldname in noedirow.keys()):
                    if (rowfieldname in noedirow[fieldname].keys()):
                        if (noedirow[fieldname][rowfieldname]["Message"]):
                            message(noedirow[fieldname][rowfieldname]["Message"])
                            return False
                        else:
                            postMessage("[RCP]" + tr("NOTEDITABLEERR") + ": "+ rowfieldname)
                            return False
        return True

    def beforeDelete(self):
        if self.isModified(): return ErrorResponse("REGISTERNOTSAVED")
        res = currentUserCanDo("CanDeleteRecords")
        if not res: return res
        res = currentUserCanDo("CanDelete" + self.name())
        if not res: return res
        if len(self.uniqueKey()):
            tbls = []
            fls = self.getForeignLinks()
            for fl in fls:
                if NewRecord(fl[0]).fields(fl[1]).isPersistent():
                    q = Query()
                    q.sql = "SELECT COUNT(*) as {N} FROM [%s] WHERE {%s} = s|%s|" % (fl[0], fl[1], self.fields(self.uniqueKey()[0]).getValue())
                    if q.open() and q[0].N > 0:
                        tbls.append(tr(fl[0]))
            if len(tbls):
                res = ErrorResponse(tr("Records cannot be deleted, references exist in the following tables") + ": " + str(tbls))
        if (not res): return res
        aquery = Query()
        aquery.sql  = "DELETE FROM [Attach] "
        aquery.sql += "WHERE?AND OriginRecordName = %s "
        aquery.sql += "WHERE?AND OriginId = %s "
        aquery.params = (self.name(), self.getPortableId())
        res = aquery.execute()
        if (not res):
            return res
        return res

    def getTitle(self):
        return filter(lambda x: x["RecordName"] == self.name(),getWindowsInfo().values())[0]["Title"]

    def __reduce__(self):
        from PythonRecord import PythonRecord
        return (PythonRecordToRecord, (PythonRecord(self),))

    def getRecordPath(self):
        import os.path
        recName = self.__class__.__name__ + ".xsl"
        for dir in getScriptDirs(999):
           path = dir + "/templates/" + recName
           if os.path.exists(path): return path
        return None

    def exportRecord(self, file):
        from GenericExporter import GenericExporter
        ge = GenericExporter(file)
        ge.exportHeader(self)
        ge.exportRecord(self)

    @classmethod
    def importRecord(objclass, file):
        from GenericImporter import GenericImporter
        gi = GenericImporter(file)
        gi.readHeader()
        return gi.readRecord()

    @classmethod
    def count(objclass):
        query = Query()
        query.sql =  "SELECT COUNT(*) as qty FROM [%s] " % objclass.__name__
        if query.open() and query.count()>0:
            return query[0].qty
        return 0

    @classmethod
    def getList(objclass, **kwargs):
        raise AppException, "The class %s has not defined the method getList" % objclass.__name__

    def __eq__(self, other):
        if other.__class__ != self.__class__: return False
        if self.fieldNames() != other.fieldNames(): return False
        if self.detailNames() != other.detailNames(): return False
        for fn in self.fieldNames():
            if self.fields(fn).isNone() != other.fields(fn).isNone(): return False
            if self.fields(fn).getValue() != other.fields(fn).getValue(): return False
        for dn in self.detailNames():
            selfdetail = self.details(dn)
            otherdetail = other.details(dn)
            if selfdetail.fieldNames() != otherdetail.fieldNames(): return False
            i=0
            for row in selfdetail:
                eq = (row == otherdetail[i])
                if not eq: return False
                i += 1
        return True

    def getPortableId(self, useOldFields=False):
        return ''

    def setPortableId(self, id):
        return None

    @classmethod
    def diff(objclass, first, second):
        res = []
        if first.fieldNames() != second.fieldNames(): res.append({"Action": "Fields Structure Change"})
        if first.detailNames() != second.detailNames(): res.append({"Action": "Details Structure Change"})
        for fn in first.fieldNames():
            if fn != "internalId" and fn != "masterId":
                if first.fields(fn).isNone() != second.fields(fn).isNone() or first.fields(fn).getValue() != second.fields(fn).getValue():
                    res.append({"Action": "Value Change", "FieldName": fn, "First": {"None": first.fields(fn).isNone(), "Value": first.fields(fn).getValue()}, "Second": {"None": second.fields(fn).isNone(), "Value": second.fields(fn).getValue()}})
        for dn in first.detailNames():
            selfdetail = first.details(dn)
            otherdetail = second.details(dn)
            if selfdetail.fieldNames() != otherdetail.fieldNames(): res.append({"Action": "Fields Structure Change", "DetailFieldName": dn})
            i=0
            for row in selfdetail:
                if otherdetail.count() > i:
                    rowres = objclass.diff(row, otherdetail[i])
                    for rowdiff in rowres:
                        rowdiff["DetailFieldName"] = dn
                        rowdiff["RowNr"] = i
                        res.append(rowdiff)
                else:
                    res.append({"DetailFieldName": dn, "RowNr": i, "Action": "Row Removed"})
                i += 1
            for i in range(selfdetail.count(), otherdetail.count()):
                res.append({"DetailFieldName": dn, "RowNr": i, "Action": "Row Added"})
        return res

    def getAttachs(self):
        res = []
        from Attach import Attach
        query = Query()
        query.sql = "SELECT * FROM [Attach] WHERE {OriginRecordName}=%s AND {OriginId}=%s AND {OriginId} IS NOT NULL"
        query.params =(self.name(), self.getPortableId())
        query.setResultClass(Attach)
        if query.open():
            res.extend(query)
        return res

    def balance(self, **kwargs):
        pass

    @classmethod
    def defaultLoggingMode(objclass):
        return 0

    def updateFieldDecimals(self, currency=None):
        try:
            if not currency and self.hasField("Currency"):
                currency = self.Currency
            if hasattr(self,"getDecimalFieldNames"):
                from DecimalSpec import DecimalSpec
                for fn in self.getDecimalFieldNames():
                    dec = DecimalSpec.getRoundDecimals(currency, self.name(), fn)
                    if dec is not None:
                        self.fields(fn).setDecimals(dec)
            for dn in self.detailNames():
                detail = self.details(dn)
                for row in detail:
                    row.updateFieldDecimals(currency)
        except ImportError, e:
            pass #very important!!
        except Exception, e:
            message((self.name() ,self.fieldNames(), utf8(e)))
            raise

    def NONBLANKERR(self, fieldname, rowfieldname="", rownr=-1):
        errorParams = {}
        errorParams["Record"] = self
        errorParams["FieldName"] = fieldname
        errorParams["RowFieldName"] = rowfieldname
        errorParams["RowNr"] = rownr
        return ErrorResponse("NONBLANKERR", errorParams)

    def INVALIDVALUEERR(self, fieldname, rowfieldname="", rownr=-1, value=None):
        errorParams = {}
        if value is None:
            if rowfieldname:
                value = self.details(fieldname)[rownr].fields(rowfieldname).getValue()
            else:
                value = self.fields(fieldname).getValue()
            errorParams["Record"] = self
            errorParams["FieldName"] = fieldname
            errorParams["RowFieldName"] = rowfieldname
            errorParams["RowNr"] = rownr
            errorParams["Value"] = value
        return ErrorResponse("INVALIDVALUEERR", errorParams)

    def FieldErrorResponse(self, errorCode, fieldname):
        errorParams = {}
        if (not self.isDetail()):
            errorParams["Record"] = self
            errorParams["FieldName"] = fieldname
        else:
            errorParams["Record"] = self.getMasterRecord()
            errorParams["RowFieldName"] = fieldname
            errorParams["RowNr"] = self.rowNr

            if (self):
                for dn in self.getMasterRecord().detailNames():
                    d = self.getMasterRecord().details(dn)
                    #print object.name(), dn, d.name()
                    if self.name() == d.name():
                        errorParams["FieldName"] = dn
        return ErrorResponse(errorCode, errorParams)

    def pasteCurrency(self):
        #ugly, but necesary...
        #self.updateFieldDecimals() not working properly!
        pass

    def fieldHasChanged(self, fieldname):
        res = self.fields(fieldname).isNone() != self.oldFields(fieldname).isNone()
        if res: return res
        return (self.fields(fieldname).getValue() != self.oldFields(fieldname).getValue())

    ### SQL Methods ###
    def syncOldFields(self):
        for fn in self.persistentFields():
            self.oldFields(fn).setValue(self.fields(fn).getValue())
        for dn in self.persistentDetails():
            detail = self.details(dn)
            for row in detail:
                row.syncOldFields()
            detail.clearRemovedRecords()
        self.setModified(False)
        self.setNew(False)

    def sync_rawStore(self, **kwargs):
        if not self.isPersistent(): return True
        if self.isLocal():
            res = RawRecord.rawStore(self)
        else:
            try:
                schema = "`%s`."% kwargs["schema"]
            except:
                try:
                    schema = self.__schema__ + "."
                except:
                    schema = ""
            res = self.sql_rawStore(schema)
        if not res:
            return StoreErrorResponse(self)
        return True

    def rawStore(self, **kwargs):
        if not self.isPersistent(): return True
        oldsyncversion = self.syncVersion
        if self.isNew() and not self.syncVersion:
            if self.__class__.lock_nontoken_records():
                self.syncVersion = -1
            else:
                self.syncVersion = 1
        else:
            try:
                self.syncVersion += abs(self.syncVersion) / self.syncVersion # +1 if positive, -1 if negative
            except:
                self.syncVersion = 1
            if self.lock_nontoken_records():
                if self.oldFields("syncVersion").getValue() > 0:
                    self.syncVersion = oldsyncversion
                    return ErrorResponse("This register is blocked by the Syncronization System")
        try:
            schema = "`%s`."% kwargs["schema"]
        except KeyError, e:
            try:
                schema = self.__schema__ + "."
            except:
                schema = ""
        if self.isLocal():
            res = RawRecord.rawStore(self)
        else:
            res = self.sql_rawStore(schema)
        if not res:
            self.syncVersion = oldsyncversion
            return StoreErrorResponse(self)
        try:
            from SystemSettings import SystemSettings
            ss = SystemSettings.bring()
        except DBNoCompanySelected, e:
            #entra aca cuando graba una empresa sin estar conectado a ninguna base de datos
            ss = SystemSettings()
        if ss and not ss.DontFocusUpdatedWindow:
            for wnd in getOpenWindowsList(): #se actualizan las ventanas que esten abiertas y que tengan al registro actual
                if hasattr(wnd, "getRecord") and wnd.getRecord() and wnd.getRecord().name() == self.name() and wnd.getRecord().hasField("internalId") and wnd.getRecord().hasField("syncVersion"):
                    if self.internalId == wnd.getRecord().internalId and self.syncVersion != wnd.getRecord().syncVersion:
                        from core.Window import Window
                        Window.__pending_refreshs__.append(wnd)
                        #wnd.getRecord().refresh()
                        #wnd.afterShowRecord()
        return True

    @classmethod
    def rawStoreMany(objclass, records):
        res = objclass.sql_rawStoreMany(records)
        return res

    def rawDelete(self, **kwargs):
        try:
            #lo pongo en try porque si no tienen cargado el modulo sincronizaci�n no hay control
            from SynchronizationSettings import SynchronizationSettings
            sysset = SynchronizationSettings.bring()
            if (sysset):
                for rline in sysset.TokenRecords:
                    if (rline.TableName == self.name()):
                        #Siempre empieza de -1 al crearse el registro.
                        if self.lock_nontoken_records():
                            if self.syncVersion > 0 or self.fields("syncVersion").isNone():
                                self.syncVersion = oldsyncversion
                                return ErrorResponse("This register is blocked by the Syncronization System")
        except:
            pass
        #res = Embedded_Record.rawStore(self)
        try:
            schema = "`%s`."% kwargs["schema"]
        except:
            schema = ""
        if self.isLocal():
            res = self.local_rawDelete()
        else:
            res = self.sql_rawDelete(schema)
        if not res:
            return StoreErrorResponse(self)
        return True

    @classmethod
    def isSubClassOf(subclass, superclass):

        if superclass.__name__ == subclass.__name__:
            return True
        elif superclass.__name__ == "Record":
            #print "este"
            return False
        else:
            if (not hasattr(subclass.__bases__[0],"isSubClassOf")):
                #print "este 2"
                return False
            return subclass.__bases__[0].isSubClassOf(superclass)
        #print "este 3"
        return False

    def load_fromC(self):
        try:
            return self.load()
        except DBError, e:
            processDBError(e, {}, utf8(e))
            return False

    def load_std(self):
        if self.isLocal(): return RawRecord.load(self)
        if not self.isPersistent(): return True
        w_fnames = []
        values = []
        persistentFields = self.persistentFields()
        for fn in persistentFields:
            if not self.fields(fn).isNone():
                w_fnames.append(fn)
        q = Query()
        select_columns = ','.join(map(lambda x: "{%s}" % x,persistentFields))
        where_condition = ' AND '.join(map(lambda x: "{%s}=%s" % (x, self.fields(x).getSQLValue()), w_fnames))
        if where_condition: where_condition = " WHERE " + where_condition
        q.sql = "SELECT %s FROM [%s] %s" % (select_columns, self.name(), where_condition)
        q.setLimit(1)
        q.result_class = self.__class__
        if q.open():
            if not q.count(): return False
            for r in q:
                for fn in persistentFields:
                    if not r.fields(fn).isNone():
                        self.fields(fn).setValue(r.fields(fn).getValue())
                        self.oldFields(fn).setValue(r.fields(fn).getValue())
            dnames = self.detailNames()
            for dn in dnames:
                detail = self.details(dn)
                detail.setMasterId(self.internalId)
                if detail.isPersistent():
                    aux = NewRecord(detail.name())
                    persistentFields = aux.persistentFields()
                    select_columns = ','.join(map(lambda x: "{%s}" % x,persistentFields))
                    q = Query()
                    q.sql = "SELECT %s FROM [%s] WHERE {masterId}=%i" % (select_columns, detail.name(), self.internalId)
                    q.result_class = aux.__class__
                    if not q.open(): return False
                    for r in q:
                        row = NewRecord(detail.name())
                        for fn in persistentFields:
                            if not r.fields(fn).isNone():
                                row.fields(fn).setValue(r.fields(fn).getValue())
                                row.oldFields(fn).setValue(r.fields(fn).getValue())
                        detail.append(row)
                        row.setModified(False)
                        row.setNew(False)
                        row.setLoadedType(1) #NormalLoaded
            self.setNew(False)
            self.afterLoad() #must be called before setModified(False)
            self.setModified(False)
            self.setLoadedType(1) #NormalLoaded
            return True
        return False
        
    def load(self):
        if not self.isPersistent(): return True
        if self.isLocal(): return RawRecord.load(self)    
        if self.__class__.__name__ in ("SystemSettings", "Company") or not get_use_query_optimizations(): return self.load_std()
        if len(self.persistentDetails()) == 0: return self.load_std()
        #aca empieza el nuevo metodo que hace un solo query aunque el registro tenga matriz
        cls = self.__class__
        fieldnames = {}
        dets = {}
        rfieldnames = self.persistentFields()
        aliases = [(cls.__name__, fn) for fn in self.persistentFields()]
        detail_record_names = {}
        detail_record_names_inverse = {}
        fieldsmaps = {}
        fieldsmap = {}
        fieldsmap.update([("%s__%s" % (cls.__name__, fn), fn) for fn in self.persistentFields()])
        fieldsmaps[cls.__name__] = fieldsmap
        for dn in self.persistentDetails():
            detail = self.details(dn)
            row = NewRecord(detail.name())
            detail_record_names[dn] = detail.name()
            detail_record_names_inverse[detail.name()] = dn
            aliases.extend([(detail.name(), fn) for fn in row.persistentFields()])
            fieldsmap = {}
            fieldsmap.update([("%s__%s" % (detail.name(), fn), fn) for fn in row.persistentFields()])
            fieldsmaps[detail.name()] = fieldsmap
        fields = ["%s %s" % ({False: "NULL", True: "{%s}" % alias[1]}[bool(alias[0] == cls.__name__)],"{%s__%s}" % alias)  for alias in aliases]
        w_fnames = filter(lambda fn: not self.fields(fn).isNone(), self.persistentFields())
        where_condition = ' AND '.join(map(lambda x: "{%s}=%s" % (x, self.fields(x).getSQLValue()), w_fnames))
        if where_condition: where_condition = " WHERE " + where_condition
        sqls = ["SELECT s|%s| as {_TABLE_NAME_}, %s FROM [%s] %s LIMIT 1" % (cls.__name__, ','.join(fields), cls.__name__, where_condition)]
        if self.internalId:
            master_wcondition = self.fields("internalId").getSQLValue()
        else:
            master_wcondition = "(select internalId from [%s] %s LIMIT 1)" %  (cls.__name__, where_condition)
        for dn in self.persistentDetails():
            table = detail_record_names[dn]
            fields = ["%s %s" % ({False: "NULL", True: "{%s}" % alias[1]}[bool(alias[0] == table)],"{%s__%s}" % alias)  for alias in aliases]
            sqls.append("(SELECT s|%s| as {_TABLE_NAME_}, %s FROM [%s] r WHERE r.masterId = %s ORDER BY {rowNr})" % (table, ','.join(fields), table, master_wcondition))
        sql = ' UNION ALL '.join(sqls)
        q = Query()
        q.sql = sql
        #t = now()
        if q.open() and q.count():
            #print "super bring query time", now()-t
            q.fillRecord(0, self, fieldsmaps[q.result[0][0]])
            for dn in self.detailNames(): self.details(dn).setMasterId(self.internalId)
            dn = None
            detail = None
            for idx in range(1,q.count()):
                ndn = detail_record_names_inverse[q.result[idx][0]]
                if ndn != dn:
                    dn = ndn
                    detail = self.details(dn)
                row = NewRecord(detail.name())
                q.fillRecord(idx, row, fieldsmaps[detail.name()])
                row.setLoadedType(1)
                detail.append(row) #normal load - not fast fields
            self.setNew(False)
            self.afterLoad() #must be called before setModified(False)
            self.setModified(False)
            self.setLoadedType(1) #NormalLoaded
            return True
        return False


    def getWindowNames(self):
        return Record.getRecordWindowNames(self.__class__.__name__)

    def getWindows(self):
        return Record.getRecordWindowTypes(self.__class__.__name__)

    def getWindowName(self):
        return self.getWindowNames()[0]

    @classmethod
    def getRecordWindowNames(classobj, recordName):
        inf = getWindowsInfo()
        return filter (lambda k: inf[k]["RecordName"] == recordName, inf)

    @classmethod
    def getRecordWindowTypes(classobj, recordName):
        wNameList = Record.getRecordWindowNames (recordName)
        if wNameList is None: return None
        types = []
        for name in wNameList:
            exec ("from %s import %s; t=%s" % (name, name, name))
            types.append (t)
        return types

    @classmethod
    def getAll(objclass, **kwargs):
        q = Query()
        q.sql = "SELECT internalId FROM [%s] " % objclass.__name__
        if q.open():
            ids = [rec.internalId for rec in q]
            kwargs["InternalIdsList"] = ids
            return objclass.getListByInternalId(**kwargs)
        return {}
                    
    
    @classmethod
    def getListByInternalId(objclass, **kwargs):
        res = {}
        idsmap = {}
        internalIdslist = kwargs.get("InternalIdsList", [])
        filloldfields = kwargs.get("SaveAllowed", False)
        if len(internalIdslist):
            internalids = '\"'+'\",\"'.join(map(lambda x: str(x), internalIdslist)) + '\"'
            q = Query()
            fnames = kwargs.get("FieldNames", None)
            fnamesstr = "*"
            if fnames is not None:
                if 'internalId' not in fnames: fnames = list(fnames) + ['internalId']
                fnamesstr = ','.join(map(lambda x: "{%s}" % x, fnames))
            q.sql = "SELECT %s FROM [%s] WHERE {internalId} in (%s) ORDER BY {internalId}" % (fnamesstr, objclass.__name__, internalids)
            if q.open():
                if fnames is None: fnames = q.fieldNames()
                for rec in q:
                    obj = objclass()
                    obj.setNew(False)
                    for fn in fnames:
                        if obj.hasField(fn):
                            if not rec.fields(fn).isNone():
                                obj.fields(fn).setValue(rec.fields(fn).getValue())
                                if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                    res[obj.internalId] = obj
                    idsmap[obj.internalId] = obj
            dnames = kwargs.get("DetailNames", None)
            if dnames is None:
                dnames = objclass().detailNames()
            for dn in dnames:
                detailrecordname = objclass().details(dn).name()
                q = Query()
                q.sql = "SELECT row.* FROM [%s] row " % detailrecordname
                q.sql += "INNER JOIN [%s] t ON t.{internalId} = row.{masterId} " % objclass.__name__
                q.sql += "WHERE row.{masterId} in (%s) ORDER BY {masterId}, {rowNr}" % internalids
                detailclass = NewRecord(detailrecordname).__class__
                q.setResultClass(detailclass)
                if q.open():
                    for rec in q:
                        obj = detailclass()
                        obj.setNew(False)
                        detail = idsmap[rec.masterId].details(dn)
                        detail.setMasterId(rec.masterId)
                        detail.append(obj)
                        for fn in rec.fieldNames():
                            if obj.hasField(fn):
                                if not rec.fields(fn).isNone():
                                    obj.fields(fn).setValue(rec.fields(fn).getValue())
                                    if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                        obj.setModified(False)
            for sernr, obj in res.items(): obj.setModified(False)
        return res

    def getWebTemplateName(self):
        return self.name() + ".html"
        
    def getURL(self):
        from WebSettings import WebSettings
        ws = WebSettings.bring()
        webport = 80
        if ws.Port: webport = ws.Port
        server = ws.Host
        if not server: return ""
        params = {}
        params["id"] = self.getPortableId()
        params["recordname"] = self.name()
        if self.hasField("TransTime"): params["T"] = self.TransTime.strftime("%H.%M.%S")
        import urllib
        params = urllib.urlencode(params)
        return "http://%s:%i/cgi-bin/recordtemplate.py?%s" % (server,webport,params)
        
    def getXML2(self):
        res = ['<record name="%s">' % self.name()]
        res.append("<fields>")
        for fn in self.fieldNames():
            res.append("<%s>%s</%s>" % (fn,getattr(self, fn), fn))
        res.append("</fields>")
        res.append("<details>")
        for dn in self.detailNames():
            detail = self.details(dn)
            res.append('<%s recordname="%s">' % (dn, detail.name()))
            rownr = 0
            for row in detail:
                res.append("<record>")
                for fn in row.fieldNames():
                    res.append("<%s>%s</%s>" % (fn,getattr(row, fn), fn))
                rownr += 1
                res.append("<matrixRowNr>%i</matrixRowNr>" % rownr)
                res.append("</record>")
            res.append("<record>")
            for fn in detail.fieldNames():
                res.append("<%s/>" % fn)
            rownr += 1
            res.append("<matrixRowNr>%i</matrixRowNr>" % rownr)
            res.append("</record>")
            res.append("</%s>" % dn)
        res.append("</details>")
        res.append("</record>")
        return res

    @classmethod
    def getChildrenClasses(objclass):
        res = []
        ri = getRecordsInfo()
        for k in ri.keys():
            if k != objclass.__name__:
                r = NewRecord(k)
                if isinstance(r, objclass): res.append(r.__class__)
        return res

    @classmethod
    def getChildrenTables(objclass):
        tables = {}
        for rn in getRecordsInfo().keys():
            #sysprint(rn)
            r = NewRecord(rn)
            for d in r.detailNames():
              if (r.name() not in tables.keys()):
                tables[r.name()] = []
              tables[r.name()].append(r.details(d).name())
        return tables

    @classmethod
    def getFatherTables(objclass,lowercase=False):
        fathers = {}
        for rn in getRecordsInfo().keys():
            r = NewRecord(rn)
            for d in r.detailNames():
              if (lowercase):
                fathers[r.details(d).name().lower()] = r.name().lower()
              else:
                fathers[r.details(d).name()] = r.name()
        return fathers

    def updateAttachFlag(self):
        aquery = Query()
        aquery.sql  = "SELECT [A].{internalId} FROM [Attach] [A]"
        aquery.sql += "WHERE?AND [A].{OriginRecordName} = s|%s| " %(self.__class__.__name__)
        aquery.sql += "WHERE?AND [A].{OriginId} = %s LIMIT 1" %( aquery.database.parseStringValue(self.getPortableId()))
        if (aquery.open()):
            if (aquery.count() > 0):
                self.attachFlag = True
            else:
                self.attachFlag = False
        return True

    def genPDF(self, filename=None, curCanvas=None):
        docspeccode = self.getDocument()
        try:
            doccode, docclassname = docspeccode
        except ValueError:
            doccode = docclassname = docspeccode
        if not docclassname: docclassname = doccode
        if docspeccode:
            exec("from %s import %s as cls" % (docclassname, docclassname))
            document = cls()
            document.setRecord(self)
            return document.genPDF(filename, curCanvas)
        return None

    @classmethod
    def storeMany(classobj, records):
        for record in records:
            if not record.isNew(): return ErrorResponse("storeMany method only accepts new records")
        res = classobj.rawStoreMany(records)
        if not res: return res
        for record in records: record.syncOldFields()
        return True

    def getOldVersion(self, date, ttime=None):
        if not ttime: ttime = time(23,59,59)
        if self.isNew(): return None, None, None
        q = Query()
        q.sql = "SELECT Data, TransDate, TransTime FROM EventLog\n"
        q.sql += "WHERE?AND TableName=s|%s|\n" % self.name()
        q.sql += "WHERE?AND recInternalId=i|%s|\n" % self.internalId
        q.sql += "WHERE?AND (TransDate < d|%s| OR (TransDate = d|%s| AND TransTime <= s|%s|))\n" % (date, date, ttime)
        q.sql += "ORDER BY TransDate DESC, TransTime DESC\n"
        q.setLimit(1)
        if q.open() and q.count() and q[0].Data:
            return cPickle.loads(q[0].Data), q[0].TransDate, q[0].TransTime
        return None, None, None

    def getRecordWindowFileName(self):
        import os
        rname = self.__class__.__name__
        gsd = getScriptDirs()
        res = ""
        for sdir in gsd:
            if os.path.isdir("%s/interface" %(sdir)):
                #alert(self.__class__.__name__)
                for filename in os.listdir("%s/interface" %(sdir)):
                    if "%s.window.xml" % (rname) == filename:
                        res = "%s/interface/%s" % (sdir,filename)
                        return res
        return res

    def getFieldLabel(self, fname, fvalue=None, rowfname=None, rowfvalue=None):
        gwi = getWindowsInfo()
        res = ""
        for win in gwi.keys():
            if (self.name() == gwi[win]["RecordName"]):
                exec("from %s import %s" %(win,win))
                exec("rwin = %s()" %(win))
                res = rwin.getFieldLabel(fname,fvalue,rowfname,rowfvalue)
        return res

    def getNotificationPersons(self):
        #usado para record communications. Redefinido en cada registro
        return []