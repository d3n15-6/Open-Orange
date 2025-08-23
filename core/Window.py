#coding: utf-8
from Embedded_OpenOrange import *
from core.Responses import *
from functions import *
from DecoratedFunctions import *
from datetime import date
from core.database.Database import DBError
import cPickle
from xml.sax import handler, saxutils

class Window(Embedded_Window):
    __session_state__ = {}
    __pending_refreshs__ = []

    def updateViewDecimals(self):
        record = self.getRecord()
        currency = None
        defdec = 2
        if record.hasField("Currency"):
            currency = record.Currency
            if currency:
                from Currency import Currency
                currdefdec = Currency.getRoundOff(currency)
                if currdefdec is not None: defdec = currdefdec
        if hasattr(record,"getDecimalFieldNames"):
            from DecimalSpec import DecimalSpec
            for fn in record.getDecimalFieldNames():
                dec = DecimalSpec.getViewDecimals(currency, record.name(), fn)
                if dec is not None:
                    self.setFieldDecimals(fn, dec, True) #primera prioridad. Los decimales estan definidos en la tabla decimals
                else:
                    self.setFieldDecimals(fn, defdec, False) #aca le digo que temo el de XML, sino que tome el que le paso por parametro
            frfn = record.getDecimalRowFieldNames()
            for dn in frfn:
                d = frfn[dn]
                for fn in d:
                    dec = DecimalSpec.getViewDecimals(currency, record.name(), dn, fn)
                    if dec is not None:
                        self.setRowFieldDecimals(dn, fn, dec, True)
                    else:
                        self.setRowFieldDecimals(dn, fn, defdec, False)

    @classmethod
    def refreshPendingWindows(classobj):
        for w in Window.__pending_refreshs__:
            if w.getRecord():
                w.getRecord().refresh()
                w.afterShowRecord()
        Window.__pending_refreshs__ = []

    @checkCommitConsistency
    def call_keyPressed(self, key, state):
        try:
            editorname = self.currentEditorName()
            return self.keyPressed(key, state, editorname, "", -1)
        except AppException, e:
            processExpectedError(e)
        except Exception, e:
            processUnexpectedError(e)

    @checkCommitConsistency
    def call_showHelp(self):
        return self.showHelp()

    def showHelp(self):
        record = self.getRecord()
        cfield = self.currentField()
        if (cfield in record.detailNames()):
            crow = self.currentRow(cfield)
        from OpenOrangeHelpCenter import OpenOrangeHelpCenter
        oohc = OpenOrangeHelpCenter()
        oohc.getRecord().TableName = record.name()
        if (cfield):
            oohc.getRecord().FieldName = cfield
        oohc.open(False)

    def keyPressed(self, key, state, editorname, columnname, rownr):
        if key == '\x01': # CTRL-a: add new feed.
            from FeedPublisherWindow import FeedPublisherWindow
            from FeedPublisher import FeedPublisher
            rec = FeedPublisher ()
            rec.defaults ()
            win = FeedPublisherWindow()
            win.setRecord (rec)
            win.open ()
            rec.setFocusOnField("User")
        elif key == '\x07': #CTRL-g: get help.
            from DocumentationTools import getFieldDocumentation
            tname =  self.getRecord ().__class__.__name__
            fn = self.currentField()
            #message (ifNone(getFieldDocumentation(tname, fn),"Not Specified."))
            from OpenOrangeHelpCenter import OpenOrangeHelpCenter
            oohelp = OpenOrangeHelpCenter()
            oorec = oohelp.getRecord()
            oorec.TableName = tname
            oorec.FieldName = fn
            oohelp.open(False)
        return True

    @checkCommitConsistency
    def call_getFieldSelectionItems(self, field, value):
        return self.getFieldSelectionItems(field, value)

    @checkCommitConsistency
    def call_activateNextField(self, currentfield):
        return self.activateNextField(currentfield)

    def activateNextField(self, currentfield):
        return None

    @checkCommitConsistency
    def call_buttonClicked(self, buttonname):
        try:
            return self.buttonClicked(buttonname)
        except AppException, e:
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e)

    def buttonClicked(self, buttonname):
        pass

    @checkCommitConsistency
    def call_afterEdit(self, fieldname):
        try:
            self.afterEdit(fieldname)
            self.getRecord().showMessages()
            fn = self.activateNextField(fieldname)
            if fn: self.getRecord().setFocusOnField(fn)
        except AppException, e:
            #message(e)
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e)

    @checkCommitConsistency
    def call_afterEditRow(self, fieldname, rowfieldname, rownr):
        try:
            self.afterEditRow(fieldname, rowfieldname, rownr)
            self.getRecord().showMessages()
            if rownr < self.getRecord().details(fieldname).count(): self.getRecord().details(fieldname)[rownr].showMessages()
        except AppException, e:
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e)

    @checkCommitConsistency
    def call_afterInsertRow(self, detailfieldname, rownr):
        try:
            res = self.afterInsertRow(detailfieldname, rownr)
            self.getRecord().showMessages()
            if rownr < self.getRecord().details(detailfieldname).count(): self.getRecord().details(detailfieldname)[rownr].showMessages()
            return res
        except AppException, e:
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e)

    def afterInsertRow(self, detailfieldname, rownr):
        row = self.getRecord().details(detailfieldname)[rownr]
        if hasattr(row, "defaults") and callable(row.defaults):
            self.getRecord().details(detailfieldname)[rownr].defaults()

    @checkCommitConsistency
    def invalidate_fromC(self):
        try:
            return self.invalidate()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    def invalidate(self):
        res = currentUserCanDo("CanInvalidate%s" % self.getRecord().name(), -1) #-1 allows to identify the access if not defined
        if res == -1: res = currentUserCanDo("CanInvalidateRecords", True)
        if not res:
            message(res)
            return res
        res = askYesNo(tr("Are you sure you want to invalidate this register?"))
        if not res: return False
        if res: res = self.getRecord().invalidate()
        if res: res = self.getRecord().store()
        if not res:
            message(res)
            self.Invalid = False
            rollback()
            self.getRecord().refresh()
        else:
            commit()
        return res

    @checkCommitConsistency
    def afterShowRecord_fromC(self):
        try:
            return self.afterShowRecord()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    @checkCommitConsistency
    def call_afterDeleteRow(self, detailfieldname, rownr):
        return self.afterDeleteRow(detailfieldname, rownr)

    def afterDeleteRow(self, detailfieldname, rownr):
        pass

    @checkCommitConsistency
    def call_beforeDeleteRow(self, detailfieldname, rownr):
        return self.beforeDeleteRow(detailfieldname, rownr)

    def beforeDeleteRow(self, detailfieldname, rownr):
        result = Embedded_Window.beforeDeleteRow(self, detailfieldname, rownr)
        if not result: return result
        res = currentUserCanDo("CanDelete" + self.getRecord().name() + detailfieldname, True)
        if not res: return res
        return True

    def afterShowRecord(self):
        self.updateViewDecimals()
        from HistoryManager import HistoryManager
        HistoryManager.addWindow(self)
        from SystemSettings import SystemSettings
        sset = SystemSettings.bring()
        if (sset.ShowEditingFieldName):
            sysprint("Opening Window: %s" %(self.name()))

    @checkCommitConsistency
    def call_nextRecord(self):
        return self.nextRecord()

    def nextRecord(self):
        try:
            record = self.getRecord()
            if self.getRecord().isModified():
                if askYesNo(tr("The current record is modified. Do you want to save it?")):
                    res = self.save()
                    if not res: return
            sortfields = self.getListWindowSortFields()
            if not sortfields: sortfields = ("internalId",)
            if sortfields[-1] != "internalId": sortfields.append("internalId")
            sortfieldtype = "s"
            filterstr = self.getListWindowFilter()
            if filterstr:
                filterstr = "AND " + filterstr
            else:
                filterstr = ""
            query = Query()
            comma = ""
            AND = ""
            sort_filterstr = ""
            sort_orderstr = ""
            if len(sortfields) == 1:
                sort_filterstr = "{%s} > s|%s|" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s}" % sortfields[0]
            elif len(sortfields) == 2:
                sort_filterstr = "({%s} = s|%s| AND {%s} > s|%s|) OR ({%s} > s|%s|)" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue(),sortfields[1],self.getRecord().fields(sortfields[1]).getValue(),sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s}, {%s}" % (sortfields[0], sortfields[1])
            elif len(sortfields) == 3:
                sort_filterstr = "({%s} = s|%s| AND {%s} > s|%s|) OR ({%s} > s|%s|)" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue(),sortfields[1],self.getRecord().fields(sortfields[1]).getValue(),sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s}, {%s}" % (sortfields[0], sortfields[1])
            query.sql = "SELECT {internalId} FROM [%s] t WHERE (%s) %s ORDER BY %s" % (record.tableName(), sort_filterstr, filterstr, sort_orderstr)
            query.setLimit(1)
            if query.open():
                for r in query:
                    newrecord = NewRecord(record.__class__.__name__)
                    newrecord.internalId = r.internalId
                    if newrecord.load():
                        self.setRecord(newrecord)
        except DBError, e:
            processDBError(e, {}, utf8(e))

    @checkCommitConsistency
    def call_prevRecord(self):
        return self.prevRecord()

    def prevRecord(self):
        try:
            record = self.getRecord()
            if self.getRecord().isModified():
                if askYesNo(tr("The current record is modified. Do you want to save it?")):
                    res = self.save()
                    if not res: return
            sortfields = self.getListWindowSortFields()
            if not sortfields: sortfields = ("internalId",)
            if sortfields[-1] != "internalId": sortfields.append("internalId")
            sortfieldtype = "s"
            filterstr = self.getListWindowFilter()
            if filterstr:
                filterstr = "AND " + filterstr
            else:
                filterstr = ""
            query = Query()
            comma = ""
            AND = ""
            sort_filterstr = ""
            sort_orderstr = ""
            if len(sortfields) == 1:
                sort_filterstr = "{%s} < s|%s|" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s} DESC" % sortfields[0]
            elif len(sortfields) == 2:
                sort_filterstr = "({%s} = s|%s| AND {%s} < s|%s|) OR ({%s} < s|%s|)" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue(),sortfields[1],self.getRecord().fields(sortfields[1]).getValue(),sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s} DESC, {%s} DESC" % (sortfields[0], sortfields[1])
            elif len(sortfields) == 3:
                sort_filterstr = "({%s} = s|%s| AND {%s} < s|%s|) OR ({%s} < s|%s|)" % (sortfields[0], self.getRecord().fields(sortfields[0]).getValue(),sortfields[1],self.getRecord().fields(sortfields[1]).getValue(),sortfields[0], self.getRecord().fields(sortfields[0]).getValue())
                sort_orderstr = "{%s} DESC, {%s} DESC" % (sortfields[0], sortfields[1])
            query.sql = "SELECT {internalId} FROM [%s] t WHERE (%s) %s ORDER BY %s" % (record.tableName(), sort_filterstr, filterstr, sort_orderstr)
            query.setLimit(1)
            if query.open():
                for r in query:
                    newrecord = NewRecord(record.__class__.__name__)
                    newrecord.internalId = r.internalId
                    if newrecord.load():
                        self.setRecord(newrecord)
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def sendMail_fromC(self):
        try:
            return self.sendMail()
        except DBError, e:
            processDBError(e, {}, utf8(e))
            return False

    def sendMail(self):
        record = self.getRecord()
        from Mail import Mail
        from MailWindow import MailWindow
        mail = Mail()
        mail.defaults()
        try:
            mail.OriginId = record.getPortableId()
            mail.OriginRecordName = record.name()
        except:
            pass
        mail.store() # i save the record here, because importHTML method needs internalId value defined.
        mail.importHTML(record.getHTML())
        commit()
        if record.hasField("CustCode"):
            mail.EntityType = 0
            mail.CustCode = record.CustCode
            from Customer import Customer
            cust = Customer.bring(record.CustCode)
            mail.pasteCustCode()
        elif record.hasField("SupCode"):
            mail.EntityType = 1
            mail.CustCode = record.SupCode
            mail.pasteCustCode()             # pastes sup data as well!
        if record.hasField("Contact"):
            from Person import Person
            pers = Person.bring(record.Contact)
            if pers and pers.Email:
                mail.MailTo = pers.getMail()

        if record.hasField("SerNr"):
            mail.Subject = "%s %i" % (record.getTitle(),record.SerNr)
        elif record.hasField("Code"):
            mail.Subject = "%s %s" % (record.getTitle(),utf8(record.Code))

        mailWindow = MailWindow()
        mailWindow.setRecord(mail)
        mailWindow.open()
        return mailWindow

    @checkCommitConsistency
    def call_newTask(self):
        self.newTask()

    def newTask(self):
        from Activity import Activity
        from ActivityWindow import ActivityWindow
        act = Activity()
        act.defaults()
        act.OriginRecordName = self.getRecord().name()
        act.OriginId = self.getRecord().getPortableId()
        act.Type = 1 #Task
        act.Users = currentUser()
        actwnd = ActivityWindow()
        actwnd.setRecord(act)
        actwnd.open()
        return act

    @checkCommitConsistency
    def call_showTasks(self):
        return self.showTasks()

    def showTasks(self):
        from Activity import Activity
        from Numerable import Numerable
        from RecordActivitiesReport import RecordActivitiesReport
        act = Activity()
        act.OriginRecordName = self.getRecord().name()
        act.OriginId = self.getRecord().getPortableId()
        report = RecordActivitiesReport()
        report.window = self
        report.OriginRecordName = self.getRecord().name()
        report.OriginId = self.getRecord().getPortableId()
        if (act.load()):
            report.open(False)
        else:
            self.newTask()

    def balance_fromC(self):
        try:
            return self.balance()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def balance(self):
        record = self.getRecord()
        record.balance()

    def viewAttachs_fromC(self):
        try:
            return self.viewAttachs()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def viewAttachs(self):
        if not self.getRecord().isNew():
            from ViewAttachsReport import ViewAttachsReport
            report = ViewAttachsReport()
            report.source_record = self.getRecord()
            report.open()
        else:
            message(tr("REGISTERNOTSAVED"))

    @checkCommitConsistency
    def call_activateNextCell(self, matrixname, row, col):
        return self.activateNextCell(matrixname, row, col)

    def activateNextCell(self, matrixname, row, col):
        columns = self.getMatrixColumns(matrixname)
        col += 1
        if col >= len(columns):
            row += 1
            col = 0
        return (row, col)

    @checkCommitConsistency
    def call_exportRecord(self):
        return self.exportRecord()


    def exportRecord(self):
        record = self.getRecord()
        filename = getSaveFileName(tr("Enter Filename"),DefaultFileName="%s_%s.txt" %(record.__class__.__name__,record.getPortableId().replace("|","_")))
        if filename:
            import codecs
            file = codecs.open(filename,"wb", "utf8")
            record.exportRecord(file)

    def webSetFieldDecimals(self, fieldname, decimals):
        #used in webmode
        return None

    def webSetRowFieldDecimals(self, detailfieldname, fieldname, decimals):
        #used in webmode
        return None

    def webName(self):
        #used in webmode
        return self.__class__.__name__

    def webGetRecord(self):
        #used in webmode
        return self.__record__

    def webSetRecord(self, record):
        #used in webmode
        self.__record__ = record
        return None

    def webGetOriginalTitle(self):
        if self.__record__:
            return self.__record__.__class__.__name__
        else:
            return ""

    def showHistory_fromC(self):
        try:
            return self.showHistory()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def showHistory(self):
        from LogSettings import LogSettings
        ls = LogSettings.bring()
        if not ls.shouldLogEvents(self.getRecord().name()):
            message(tr("Record History has not been configured, check Settings/Register logging"))
        else:
            from RecordHistoryReport import RecordHistoryReport
            report = RecordHistoryReport()
            report.getRecord().TableName = self.getRecord().name()
            try:
                report.getRecord().Id = self.getRecord().getPortableId()
            except:
                report.getRecord().recInternalId = self.getRecord().internalId
            report.getRecord().FromDate = date(1900,1,1)
            report.getRecord().ToDate = date(2100,1,1)
            report.getRecord().Type = 0 #records
            report.open(False)


    @checkCommitConsistency
    @checkCurrentUserCanDoAction
    def call_action(self, methodname):
        try:
            method = getattr(self, methodname)
            self.getRecord().showMessages()
            res = method()
            return res
        except AppException, e:
            #message(e)
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": methodname, "class": str(self.__class__)})

    @checkCommitConsistency
    def call_beforeEdit(self, fieldname):
        try:
            self.saveSessionState()
            res = self.beforeEdit(fieldname)
            if res:
                self.lastField = fieldname
            return res
        except AppException, e:
            message(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": "beforeEdit", "fieldname": fieldname, "class": str(self.__class__)})

    #def currentMatrixName(self):
    #    if not hasattr(self, "_current_matrix_name"):
    #        self._current_matrix_name = Embedded_Window.currentMatrixName(self)
    #    return self._current_matrix_name

    @checkCommitConsistency
    def call_beforeEditRow(self, matrixname, fieldname, rowfieldname, rownr):
        try:
            self.saveSessionState()
            #postMessage(matrixname)
            #self._current_matrix_name = matrixname
            res = self.beforeEditRow(fieldname, rowfieldname, rownr)
            return res
        except AppException, e:
            message(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e,{"method": "beforeEdit", "fieldname": fieldname, "rowfieldname": rowfieldname, "rownr": rownr, "class": str(self.__class__)})

    def beforeEdit(self, fieldname):
        #self._current_matrix_name = ""
        res = self.getRecord().fieldIsEditable(fieldname)
        if not res and res is not None and res is not False: postMessage(str(res))
        from SystemSettings import SystemSettings
        sset = SystemSettings.bring()
        if (sset.ShowEditingFieldName):
            postMessage(u"%s: %s / %s : %s" %(tr("Window"),self.name(),tr("Editing"),fieldname))
        return res

    def beforeEditRow(self, detailfieldname, fieldname, rownr):
        try:
            from SystemSettings import SystemSettings
            sset = SystemSettings.bring()
            if (sset.ShowEditingFieldName):
                postMessage("%s : %s %s, %s %s" %(tr("Editing"),tr("Row"),detailfieldname,tr("Column"),fieldname))
            res = self.getRecord().fieldIsEditable(detailfieldname, fieldname, rownr)
        except Exception, err:
            res = True
        return res

    @checkCommitConsistency
    def deleteRecord_fromC(self):
        try:
            return self.deleteRecord()
        except AppException, e:
            #message(e)
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": "deleteRecord_fromC", "class": str(self.__class__)})

    def deleteRecord(self):
        res = askYesNo(tr("Are you sure you want to delete this register?"))
        if res:
            res = self.getRecord().delete_fromGUI()
            if not res:
                if (res != False):
                    message(res)
                return False
            else:
                self.close()
                return True
        return False

    #@checkCommitConsistency
    def call_getTitle(self):
        return self.getTitle()

    def getTitle(self):
        return Embedded_Window.getTitle(self)

    @checkCommitConsistency
    def call_beforeClose(self):
        return self.beforeClose()

    def beforeClose(self):
        return True

    @checkCommitConsistency
    def save_fromC(self):
        try:
            if not self.getRecord().isLocal(): rollback() # Para que se inicie una nueva transaccion
            return self.save()
        except AppException, e:
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": "save_fromC", "class": str(self.__class__)})

    def save(self):
        new_flag = self.getRecord().isNew()
        res = self.getRecord().save_fromGUI()
        self.getRecord().showMessages()
        Window.refreshPendingWindows()
        if not res:
            message(res)
        elif new_flag:
            from HistoryManager import HistoryManager
            HistoryManager.addWindow(self)
        return res

    def afterEdit(self, fieldname):
        record = self.getRecord()
        from RecordCheckPolicy import RecordCheckPolicy
        rcp = RecordCheckPolicy.bring(record.name())
        if (rcp):
            cases = rcp.getHeaderFieldCases()
            if (fieldname in cases):
                fvalue = record.fields(fieldname).getValue()
                sclass = fvalue.__class__.__name__
                if (sclass in ("str","unicode")):
                    if (cases[fieldname]["Case"] == 1):
                        fvalue = fvalue.upper()
                    elif (cases[fieldname]["Case"] == 2):
                        fvalue = fvalue.lower()
                    elif (cases[fieldname]["Case"] == 3):
                        fvalue = fvalue.title()
                    record.fields(fieldname).setValue(fvalue)

    def afterEditRow(self, fieldname, rowfieldname, rownr):
        from RecordCheckPolicy import RecordCheckPolicy
        import string
        record = self.getRecord()
        rcp = RecordCheckPolicy.bring(record.name())
        if (rcp):
            cases = rcp.getRowFieldsCases()
            if (fieldname in cases.keys()):
                if (rowfieldname in cases[fieldname].keys()):
                    fvalue = record.details(fieldname)[rownr].fields(rowfieldname).getValue()
                    sclass = fvalue.__class__.__name__
                    if (sclass in ("str","unicode")):
                        if (cases[fieldname][rowfieldname]["Case"] == 1):
                            fvalue = string.upper(fvalue)
                        elif (cases[fieldname][rowfieldname]["Case"] == 2):
                            fvalue = string.lower(fvalue)
                        elif (cases[fieldname][rowfieldname]["Case"] == 3):
                            fvalue = utf8(fvalue).title()
                        record.details(fieldname)[rownr].fields(rowfieldname).setValue(fvalue)


    @checkCommitConsistency
    def call_filterPasteWindow(self, fname):
        return self.filterPasteWindow(fname)

    def filterPasteWindow(self, fname):
        pass

    @checkCommitConsistency
    def call_beforeInsertRow(self, detailfieldname, rownr):
            return self.beforeInsertRow(detailfieldname, rownr)

    @checkCommitConsistency
    def call_joinPasteWindow(self, fname):
        return self.joinPasteWindow(fname)


    def joinPasteWindow(self, fname):
        pass

    @checkCommitConsistency
    def call_joinPasteWindowRow(self, fieldname, rowfieldname, rownr):
        return self.joinPasteWindowRow(fieldname, rowfieldname, rownr)

    def joinPasteWindowRow(self, fieldname, rowfieldname, rownr):
        pass

    @checkCommitConsistency
    def call_filterPasteWindowRow(self, fieldname, rowfieldname, rownr):
        return self.filterPasteWindowRow(fieldname, rowfieldname, rownr)

    def filterPasteWindowRow(self, fieldname, rowfieldname, rownr):
        pass

    def beforeInsertRow(self, detailfieldname, rownr):
        result = Embedded_Window.beforeInsertRow(self, detailfieldname, rownr)
        if not result: return result
        res = currentUserCanDo("CanInsert" + self.getRecord().name() + detailfieldname, True)
        if not res: return res
        return True

    def printRecord_fromC(self):
        try:
            return self.printRecord()
        except AppException, e:
            #message(e)
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": "printRecord_fromC", "class": str(self.__class__)})

    def printRecord(self):
        self.getRecord().isDraftTransaction = False
        self.getRecord().printRecord()

    def canBePrinted(self):
        doc = self.getDocument()
        if (doc):
            from DocumentSpec import DocumentSpec
            ds = DocumentSpec.bring(doc)
            if (ds):
                ds.normalizeFields()
                ds.store()
                commit()
        return True

    def copyRecord_fromC(self):
        try:
            return self.copyRecord()
        except AppException, e:
            #message(e)
            e.kwargs["ShouldBeProcessed"] = True
            processExpectedError(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e, {"method": "copyRecord", "class": str(self.__class__)})

    def copyRecord(self):
        newrec = self.getRecord().clone()
        newrec.afterCopy()
        self.setRecord(newrec)

    @classmethod
    def openRecord(classobj, record):
        try:
            wname = filter(lambda x: getWindowsInfo()[x]["RecordName"] == record.name(), getWindowsInfo())[0]
            w = NewWindow(wname)
            w.setRecord(record)
            w.open()
        except:
            raise

    def getReportView(self, name):
        return Embedded_Window.getReportView(self, name)

    def webGetReportView(self, name):
        from WebReportView import WebReportView
        wrv = WebReportView(name)
        wrv.window = self

    def call_copyRowToClipboard(self, matrixname, row):
        return self.copyRowToClipboard(matrixname, row)

    def copyRowToClipboard(self, matrixname, row):
        import cPickle
        return cPickle.dumps(self.getRecord().details(self.getMatrixFieldName(matrixname))[row])

    def call_pasteRowFromClipboard(self, matrixname, row, data):
        return self.pasteRowFromClipboard(matrixname, row, data)

    def pasteRowFromClipboard(self, matrixname, row, data):
        import cPickle
        ok = False
        try:
            datarow = cPickle.loads(data)
            fieldname = self.getMatrixFieldName(matrixname)
            row = self.getRecord().details(fieldname)[row]
            for fn in datarow.fieldNames():
                if datarow.fields(fn).isNone():
                    setattr(row, fn, None)
                else:
                    setattr(row, fn, getattr(datarow, fn))
            ok = True
        except Exception, e:
            datarows = data.split("\n")
            fieldname = self.getMatrixFieldName(matrixname)
            fieldstr = datarows.pop(0)
            fields = fieldstr.split("\t")
            for datarow in datarows:
              fieldvalues = datarow.split("\t")
              row = NewRecord( self.getRecord().details(fieldname).name() )
              rownr = len( self.getRecord().details(fieldname) )
              self.getRecord().details(fieldname).append(row)
              for (fn,value) in zip(fields,fieldvalues):
                setattr(row, fn, value)
                self.afterEditRow(fieldname,fn,rownr)
            pass
        if ok:
            self.afterPasteRowFromClipboard(fieldname, row)

    def afterPasteRowFromClipboard(self, fieldname, rownr):
        pass

    def getFieldSelectionItems(self, fieldname, currentvalue):
        r = self.getRecord()
        linkto = r.fields(fieldname).getLinkTo()
        res = []
        if linkto:
            m = NewRecord(linkto)
            from Master import Master
            if isinstance(m, Master):
                for c in m.__class__.getCodes():
                    if c.find(currentvalue) >= 0:
                        res.append(c)
        return res

    def showNLT(self):
        pass

    def showNLT_fromC(self):
        try:
            return self.showNLT()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def authorize(self):
        pass

    def authorize_fromC(self):
        try:
            return self.authorize()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def openInWeb_fromC(self):
        try:
            return self.openInWeb()
            return True
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    def openInWeb(self):
        url = self.getRecord().getURL()
        if url:
            import webbrowser
            webbrowser.open_new(url)

    def openCommunications_fromC(self):
        try:
            return self.openCommunications()
            return True
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    def openCommunications(self):
        if self.getRecord() and hasattr(self.getRecord(), "getPortableId"):
            from RecordCommunicationsReport import RecordCommunicationsReport
            report = RecordCommunicationsReport()
            report.getRecord().OriginRecord = self.getRecord().name()
            report.getRecord().OriginId = self.getRecord().getPortableId()
            report.open(False)

    def call_pasteMethod_fromC(self, methodname):
        try:
            return getattr(self, methodname)()
        except DBError, e:
            processDBError(e, {}, utf8(e))

    @checkCommitConsistency
    def call_fillPasteWindow(self, pastewindowname, fieldname):
        return self.fillPasteWindow(pastewindowname, fieldname)

    def fillPasteWindow(self, pastewindowname, fieldname):
        pass

    @checkCommitConsistency
    def call_getPasteWindowName(self,fieldname):
        return self.getPasteWindowName(fieldname)


    def getPasteWindowName(self,fieldname):
        pass

    @checkCommitConsistency
    def call_fillPasteWindowRow(self, pastewindowname, fieldname, rowfieldname,rownr):
        return self.fillPasteWindowRow(pastewindowname, fieldname, rowfieldname,rownr)

    def fillPasteWindowRow(self, pastewindowname, fieldname, rowfieldname,rownr):
        pass

    @checkCommitConsistency
    def call_getPasteWindowNameRow(self,fieldname,rowfieldname,rownr):
        return self.getPasteWindowNameRow(fieldname,rowfieldname,rownr)

    def getPasteWindowNameRow(self,fieldname,rowfieldname,rownr):
        pass

    """
    def getPasteWindowName(self,fieldname):
        record = self.getRecord()
        fname = getOpenFileName()
        if (fname):
          record.fields(fieldname).setValue(fname)
        return "FileNamePasteWindow"

    def fillPasteWindow(self, pastewindowname, fieldname):
        record = self.getRecord()
        if pastewindowname == "FileNamePasteWindow":
          fname = getOpenFileName()
          alert(fname)
          if (fname):
            record.fields(fieldname).setValue(fname)
        return None
    """

    def saveSessionState(self):
        r = self.getRecord()
        if r.__class__.__name__ not in ("Embedded_Record", "Record", "RawRecord"):
            r.__windowname__ = self.__class__.__name__
            Window.__session_state__[self] = r
            #sysprint("%s VALUES: %i" % (self.name(), len(Window.__session_state__.values())))
            #for r in Window.__session_state__.values():
            #    sysprint("value1: %s" % r.__class__.__name__)
            #    sysprint("value2: %s" % r.name())
            setSessionState(cPickle.dumps(Window.__session_state__.values()))

    def setRecord(self, record):
        if not isinstance(record, Embedded_Record):
            message("El objeto debe ser de tipo Record")
            return False
        return Embedded_Window.setRecord(self, record)

    def closing_fromC(self):
        try:
            del Window.__session_state__[self]
        except KeyError, e:
            pass
        return self.closing()

    def closing(self):
        pass

    @checkCommitConsistency
    def call_windowResized(self):
        return self.windowResized()

    def windowResized(self):
        pass

    def getWindowFileName(self):
        import os
        gwi = getWindowsInfo()
        rname = gwi[self.__class__.__name__]["RecordName"]
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

    def getWindowPatchFileName(self):
        import os
        gwi = getWindowsInfo()
        rname = gwi[self.__class__.__name__]["RecordName"]
        gsd = getScriptDirs()
        patchlist = []
        for sdir in gsd:
            if os.path.isdir("%s/interface" %(sdir)):
                #alert(self.__class__.__name__)
                for filename in os.listdir("%s/interface" %(sdir)):
                    #print "%s.patchwindow.xml" % (rname)
                    if "%s.windowpatch.xml" % (rname) == filename:
                        res = "%s/interface/%s" % (sdir,filename)
                        patchlist.append(res)
        patchlist.reverse()
        return patchlist

    def getWindowInfo(self, fname=None):
        self.winfolist = {}
        from xml.sax import make_parser
        from xml.sax.handler import feature_namespaces
        import os
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        xmlhandler = XMLRecordWindowHandler()
        xmlhandler.winfolist = self.winfolist
        parser.setContentHandler(xmlhandler)
        if (not fname):
            fname = self.getWindowFileName()
        if (os.path.exists(fname)):
            parser.parse(open(fname))
        patchlist = self.getWindowPatchFileName()
        for patch in patchlist:
            if (os.path.exists(patch)):
                parser.parse(open(patch))
        return self.winfolist

    def getFieldLabel(self, fname, fvalue=None, rowfname=None, rowfvalue=None):
        gwi = self.getWindowInfo()
        #print fname, fvalue, rowfname, rowfvalue
        res = ""
        if (fvalue != None):  fvalue = utf8(fvalue)
        if (rowfvalue != None): rowfvalue = utf8(rowfvalue)
        if (not "FieldsData" in gwi.keys()):
            return res
        if (fname):
            obj = gwi["FieldsData"].get(fname,"")
            if (obj):
                res = gwi["FieldsData"][fname]["Label"]
            else:
                return tr(res)
        else:
            return tr(res)
        if (fvalue):
            obj = gwi["FieldsData"][fname].get("OptionValues","")
            if (obj):
                res = "%s?" %(tr(res))
                #alert((fvalue,gwi["FieldsData"][fname]["OptionValues"]))
                if (fvalue in gwi["FieldsData"][fname]["OptionValues"]):
                    idx = gwi["FieldsData"][fname]["OptionValues"].index(fvalue)
                    res = gwi["FieldsData"][fname]["OptionLabels"][idx]
                else:
                    return tr(res)
            else:
                return tr(res)
        if (rowfname):
            obj = gwi["FieldsData"][fname].get("Columns","")
            if (obj):
                obj = gwi["FieldsData"][fname]["Columns"].get(rowfname,"")
                if (obj):
                    res = gwi["FieldsData"][fname]["Columns"][rowfname]["Label"]
                else:
                    return tr(res)
            else:
                return tr(res)
        if (rowfvalue):
            obj = gwi["FieldsData"][fname]["Columns"][rowfname].get("OptionValues","")
            if (obj):
                res = "%s?" %(tr(res))
                if (rowfvalue in gwi["FieldsData"][fname]["Columns"][rowfname]["OptionValues"]):
                    idx = gwi["FieldsData"][fname]["Columns"][rowfname]["OptionValues"].index(rowfvalue)
                    res = gwi["FieldsData"][fname]["Columns"][rowfname]["OptionLabels"][idx]
                else:
                    return tr(res)
            else:
                return tr(res)
        else:
            return tr(res)
        return tr(res)

    @checkCommitConsistency
    def call_rowFieldSelected(self, detailfieldname, rowfieldname, rownr):
        return self.rowFieldSelected(detailfieldname, rowfieldname, rownr)

class XMLRecordWindowHandler(handler.ContentHandler):
    accumchar = ""

    def startElement(self, name, attrs):
        winfolist = self.winfolist
        if (name == "window"):
            winfolist["Title"] = str(attrs.get("title",""))
            winfolist["Name"] = str(attrs.get("name",""))
            winfolist["RecordName"] = str(attrs.get("recordname",""))
            winfolist["FieldsData"] = {}
            winfolist["Actions"] = {}
            winfolist["Others"] = {}
        if (name in ("text","integer","date","time","checkbox")):
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            fieldname = str(attrs.get("fieldname",""))
            pastewindow = str(attrs.get("pastewindow",""))
            wi = str(attrs.get("width",""))
            he = str(attrs.get("height",""))
            ro = str(attrs.get("readonly",""))
            editor = str(name)
            nn = str(attrs.get("name",""))
            winfolist["FieldsData"][fieldname] = {}
            winfolist["FieldsData"][fieldname]["Label"] = label
            winfolist["FieldsData"][fieldname]["FieldName"] = fieldname
            winfolist["FieldsData"][fieldname]["PasteWindow"] = pastewindow
            winfolist["FieldsData"][fieldname]["Width"] = wi
            winfolist["FieldsData"][fieldname]["Editor"] = editor
            winfolist["FieldsData"][fieldname]["Height"] = he
            winfolist["FieldsData"][fieldname]["Name"] = nn
            winfolist["FieldsData"][fieldname]["ReadOnly"] = ro
        if (name in ("combobox","radiobutton")):
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            fieldname = str(attrs.get("fieldname",""))
            wi = str(attrs.get("width",""))
            he = str(attrs.get("height",""))
            editor = str(name)
            nn = str(attrs.get("name",""))
            winfolist["FieldsData"][fieldname] = {}
            winfolist["FieldsData"][fieldname]["Label"] = label
            winfolist["FieldsData"][fieldname]["FieldName"] = fieldname
            winfolist["FieldsData"][fieldname]["Width"] = wi
            winfolist["FieldsData"][fieldname]["Height"] = he
            winfolist["FieldsData"][fieldname]["Editor"] = editor
            winfolist["FieldsData"][fieldname]["Name"] = nn
            winfolist["FieldsData"][fieldname]["OptionValues"] = []
            winfolist["FieldsData"][fieldname]["OptionLabels"] = []
            self.curOptions = fieldname
            self.curMatrix = None
        if (name in ("combooption","radiooption")):
            if (self.curMatrix):
                value = attrs.get("value","").encode("ascii","xmlcharrefreplace")
                label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
                winfolist["FieldsData"][self.curMatrix]["Columns"][self.curOptions]["OptionValues"].append(value)
                winfolist["FieldsData"][self.curMatrix]["Columns"][self.curOptions]["OptionLabels"].append(label)
            else:
                if (self.curOptions):
                    value = attrs.get("value","").encode("ascii","xmlcharrefreplace")
                    label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
                    winfolist["FieldsData"][self.curOptions]["OptionValues"].append(value)
                    winfolist["FieldsData"][self.curOptions]["OptionLabels"].append(label)
        if (name == "matrix"):
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            fieldname = str(attrs.get("fieldname",""))
            wi = str(attrs.get("width",""))
            he = str(attrs.get("height",""))
            nn = str(attrs.get("name",""))
            if (not winfolist["FieldsData"].has_key(fieldname)):
                winfolist["FieldsData"][fieldname] = {}
                winfolist["FieldsData"][fieldname]["Label"] = ""
                winfolist["FieldsData"][fieldname]["FieldName"] = fieldname
                winfolist["FieldsData"][fieldname]["Width"] = wi
                winfolist["FieldsData"][fieldname]["Height"] = he
                winfolist["FieldsData"][fieldname]["Name"] = nn
                winfolist["FieldsData"][fieldname]["Columns"] = {}
            self.curMatrix = fieldname
        if (name == "matrixcolumn"):
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            fieldname = str(attrs.get("fieldname",""))
            wi = str(attrs.get("width",""))
            pastewindow = str(attrs.get("pastewindow",""))
            editor = str(attrs.get("editor",""))
            ro = str(attrs.get("readonly",""))
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname] = {}
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["Label"] = label
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["Width"] = wi
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["Editor"] = editor
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["ReadOnly"] = ro
            winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["PasteWindow"] = pastewindow
            if (editor == "combobox"):
                winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["OptionValues"] = []
                winfolist["FieldsData"][self.curMatrix]["Columns"][fieldname]["OptionLabels"] = []
                self.curOptions = fieldname
        if (name in ("action")):
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            mname = attrs.get("methodname","").encode("ascii","xmlcharrefreplace")
            scut = str(attrs.get("shortcut",""))
            winfolist["Actions"][mname] = {}
            winfolist["Actions"][mname]["Label"] = label
            winfolist["Actions"][mname]["ShortCut"] = scut
        if (name in ("pushbutton","reportview","listview","buttonareaview","scrollareaview")):
            oname = attrs.get("name","").encode("ascii","xmlcharrefreplace")
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            wi = str(attrs.get("width",""))
            he = str(attrs.get("height",""))
            winfolist["Others"][oname] = {}
            winfolist["Others"][oname]["Type"] = str(name)
            winfolist["Others"][oname]["Label"] = label
            winfolist["Others"][oname]["Width"] = wi
            winfolist["Others"][oname]["Height"] = he

    def endElement(self, name):
        if (name in ("combobox","radiobutton")):
            self.curOptions = None
        if (name  == "matrix"):
            self.curMatrix = None
            self.curOptions = None

    def characters(self, chars):
        pass
    #ATENCION!!! ESTE NO ES EL FINAL DE LA CLASE WINDOW, EL FINAL ESTA MAS ARRIBA
    
