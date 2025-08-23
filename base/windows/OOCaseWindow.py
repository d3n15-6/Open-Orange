#encoding: utf-8
from OpenOrange import *

ParentOOCaseWindow = SuperClass("OOCaseWindow", "NumerableWindow", __file__)
class OOCaseWindow(ParentOOCaseWindow):
    
    def afterShowRecord(self):
        ParentOOCaseWindow.afterShowRecord(self)
        self.showOOCaseReport()
        
    def showOOCaseReport(self):
        rv = self.getReportView("CaseDetail")
        from OOCaseReport import OOCaseReport
        report = OOCaseReport()
        report.setView(rv)
        report.OOCaseNr = self.getRecord().OOCaseNr
        report.CaseTransTime = self.getRecord().TransTime
        report.window = self
        report.open()
        
        
    def save(self):
        res = ParentOOCaseWindow.save(self)
        if res:
            self.showOOCaseReport()
            self.getRecord().Message = ""
        return res
        
    def buttonClicked(self, buttonname):
        ParentOOCaseWindow.buttonClicked(self, buttonname)
        if buttonname == "showListWindow":
            openListWindow("OOCaseListWindow")
            r = self.getRecord()
            if not r.Subject and not r.Message:
                r.setModified(False)
                self.close()