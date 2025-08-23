#encoding: utf-8
from OpenOrange import *

ParentMasterWindow = SuperClass("MasterWindow","Window",__file__)
class MasterWindow(ParentMasterWindow):

    def afterShowRecord(self):
        ParentMasterWindow.afterShowRecord(self)
        self.getRecord().setFocusOnField("Code")
    
    def getTitle(self):
        rec = self.getRecord()
        if not rec: return self.getOriginalTitle()
        t = self.getOriginalTitle() + " " + rec.Code
        from Company import Company
        lcom = Company.getLoguedCompanies()
        if (len(lcom) > 1):
            t = "[%s] %s" %(Company.getCurrent().Code,t)
        if not rec.internalId:
             t += ": " + tr("New")
        elif rec.isModified():
             t += ": " + tr("Modified")
        return t

    def afterEdit(self, fieldname):
        ParentMasterWindow.afterEdit(self, fieldname)
        if (fieldname == "Code"):
            from SystemSettings import SystemSettings
            sset = SystemSettings.bring()
            if (sset.UseUpperCaseCode):
                record = self.getRecord()
                record.Code = str(record.Code).upper()

    def getPasteWindowName(self,fieldname):
        record = self.getRecord()
        if(fieldname == "Classification"):
          from ClassifierPaste import ClassifierPaste
          report = ClassifierPaste()
          report.tableName = record.name()
          report.record = record
          report.open(False)
          return ""
