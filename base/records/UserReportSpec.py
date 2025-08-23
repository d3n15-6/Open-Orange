#encoding: utf-8
from OpenOrange import *

ParentUserReportSpec = SuperClass("UserReportSpec", "Record", __file__)
class UserReportSpec(ParentUserReportSpec):
    buffer = RecordBuffer("UserReportSpec")

    def beforeInsert(self):
        res = ParentUserReportSpec.beforeInsert(self)
        if (not res): return res
        self.updatingRows()
        return res

    def beforeUpdate(self):
        res = ParentUserReportSpec.beforeUpdate(self)
        if (not res): return res
        self.updatingRows()
        return res

    def fillReportFields(self, reportobj):
        record = reportobj.getRecord()
        self.Fields.clear()
        for fline in record.fieldNames():
            urow = UserReportSpecFieldRow()
            urow.FieldName = fline
            urow.Type = record.fields(fline).getType()
            urow.Value = str(record.fields(fline).getValue())
            flabel = record.getFieldLabel(fline)
            if (flabel):
                urow.FieldLabel = flabel
            else:
                urow.FieldLabel = fline
            self.Fields.append(urow)
            self.ReportLabel = reportobj.getLabel()
            self.User = currentUser()
            self.ReportName = reportobj.__class__.__name__

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentUserReportSpec.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if (not res): return res
        if (fieldname == "Fields"):
            urow = self.Fields[rownr]
            if (rowfieldname == "Value"):
                if (urow.Type in ("integer","boolean")):
                    res = False
                if (urow.Type == "date" and urow.DateTemplate <> 0):
                    res = False
            elif (rowfieldname == "DateTemplate"):
                if (urow.Type <> "date"):
                    res = False
        return res

    def updatingRows(self):
        for uline in self.Fields:
            if (uline.Type <> "date"):
                uline.DateTemplate = None
            else:
                if (uline.DateTemplate <> 0):
                    uline.Value = ""

    def refreshDateValues(self):
        mydate = today()
        for uline in self.Fields:
            if (uline.DateTemplate == 1):
                uline.Value = str(mydate)
            elif (uline.DateTemplate == 2):
                uline.Value = str(StartOfMonth(mydate))
            elif (uline.DateTemplate == 3):
                uline.Value = str(EndOfMonth(mydate))
            elif (uline.DateTemplate == 4):
                uline.Value = str(StartOfYear(mydate))
            elif (uline.DateTemplate == 5):
                uline.Value = str(EndOfYear(mydate))
            elif (uline.DateTemplate == 6):
                uline.Value = str(date(1900,1,1))

    def uniqueKey(self):
        return ('User', 'ReportName')

    def getPortableId(self, useOldFields=False):
        user = self.User
        reportname = self.ReportName
        if useOldFields: 
            user = self.oldFields('User').getValue()
            reportname = self.oldFields('ReportName').getValue()
        return str("%s|%s" % (user,reportname))
    
    def setPortableId(self, id):
        self.User, self.ReportName  = id.split('|')
    
    @classmethod
    def bring(classobj, user, reportname):
        uniquekey = "%s|%s" % (user, reportname)
        try:
            return classobj.buffer[uniquekey]
        except:
            p = classobj()
            p.User = user
            p.ReportName = reportname
            if p.load():
                classobj.buffer[uniquekey] = p
                return p
            classobj.buffer[uniquekey] = None

ParentUserReportSpecFieldRow = SuperClass("UserReportSpecFieldRow","Record",__file__)
class UserReportSpecFieldRow(ParentUserReportSpecFieldRow):

    def pasteDateTemplate(self, record):
        if (self.DateTemplate == 0):
            self.Value = str(today())
            return
        if (self.DateTemplate == 1):
            self.Value = str(today())
            return
        mydate = today()
        if (mydate):
            if (self.DateTemplate == 2):
                self.Value = str(StartOfMonth(mydate))
            elif (self.DateTemplate == 3):
                self.Value = str(EndOfMonth(mydate))
            elif (self.DateTemplate == 4):
                self.Value = str(StartOfYear(mydate))
            elif (self.DateTemplate == 5):
                self.Value = str(EndOfYear(mydate))
            elif (self.DateTemplate == 6):
                self.Value = str(date(1900,1,1))

    def pasteValue(self, record):
        if (self.DateTemplate == 0):
            self.Value = str(stringToDate(self.Value))