#encoding: utf-8
from OpenOrange import *
from Record import Record

ParentNumerableWindow = SuperClass("NumerableWindow","Window",__file__)
class NumerableWindow(ParentNumerableWindow):

    def afterShowRecord(self):
        ParentNumerableWindow.afterShowRecord(self)
        self.getRecord().setFocusOnField("SerNr")
        record = self.getRecord()
        if ("OriginType" in record.fieldNames()):
            gwi = getWindowsInfo()
            rtitles = {}
            for v in gwi.values():
                rtitles[v["RecordName"]] = v["Title"]
            olist = []
            ismod = record.isModified()
            isnew = record.isNew()
            old = record.OriginType
            record.OriginType = -1
            for org in sorted(record.Origin.keys()):
                if (org in rtitles.keys()):
                    name = rtitles[org]
                    olist.append(("%s" %(record.Origin[org]),name))
            self.setFieldOptions("OriginType", tuple(olist))
            record.OriginType = old
            record.setModified(ismod)
            record.setNew(isnew)

    def afterEdit(self, fieldname):
        ParentNumerableWindow.afterEdit(self, fieldname)
        if (fieldname == "SerNr"):
            numerable = self.getRecord()
            numerable.pasteSerNr()

    def getTitle(self):
        rec = self.getRecord()
        if not rec: return self.getOriginalTitle()
        t = self.getOriginalTitle() + " " + str(rec.SerNr)
        from Company import Company
        lcom = Company.getLoguedCompanies()
        if (len(lcom) > 1):
            t = "[%s] %s" %(Company.getCurrent().Code,t)
        if rec.ToSerNr and rec.SerNr != rec.ToSerNr: 
            t += " / " + str(rec.ToSerNr)
        if not rec.internalId:
             t += ": " + tr("New")
        elif rec.isModified():
             t += ": " + tr("Modified")
        if rec.isInvalid():
            t += " (" + tr("INVALID") + ")"
            date = rec.getInvalidDate()
            if (date and str(date) != "0000-00-00"):
                t += " " + date.strftime("%d/%m/%Y")
        return t

    def fillPasteWindow(self, pastewindowname, fieldname):
        if fieldname == "SerNr":
            record = self.getRecord()
            res = []
            from X import X
            x = X()
            query = Query()
            query.sql = "SELECT FromNr, ToNr, Comment FROM SerNrControl\n"
            query.sql += "WHERE TransType = s|%s|\n" % record.name()
            query.sql += "AND d|%s| BETWEEN FromDate AND ToDate\n" % record.TransDate
            if ("DocType" in record.fieldNames()):
                query.sql += "AND (DocType = -1 OR DocType = s|%s| )\n" % record.DocType
            if ("InvoiceType" in record.fieldNames()):
                query.sql += "AND (InvoiceType = 3 OR InvoiceType = i|%s| )\n" % record.InvoiceType
            query.sql += "AND (Office IS NULL OR Office = '' OR Office = s|%s|)\n" % record.Office
            query.sql += "AND (Computer IS NULL OR Computer = '' OR Computer = s|%s|)\n" % record.Computer
            if query.open():
                for rec in query:
                    q = Query()
                    q.sql  = "SELECT MAX(IF(IFNULL(ToSerNr,SerNr) > SerNr,ToSerNr,SerNr)) as SerNr "
                    q.sql += "FROM [%s] " %(record.name())
                    q.sql += "WHERE SerNr BETWEEN i|%s| AND i|%s|" % (rec.FromNr, rec.ToNr)
                    if q.open() and q.count() and q[0].SerNr < rec.ToNr:
                        r = q[0]
                        x = X()
                        if r.SerNr == 0:
                            x.Code = str(rec.FromNr)
                        else:
                            x.Code = str(r.SerNr+1)
                        x.Name = rec.Comment
                        res.append(x)
                return res

    def openOriginWindow(self):
        record = self.getRecord()
        wlist = record.getOriginWindowTypes()
        if not wlist: 
            return False
        origin = record.getOriginRecord()
        if not origin: 
            return False
        w = wlist[0]()
        w.setRecord(origin)
        w.open()

    def buttonClicked(self, bname):
        ParentNumerableWindow.buttonClicked(self,bname)
        if (bname == "openOrigin"):
            self.openOriginWindow()