#encoding: utf-8
from OpenOrange import *

ParentHTMLRecordViewWindow = SuperClass("HTMLRecordViewWindow","MasterWindow",__file__)
class HTMLRecordViewWindow(ParentHTMLRecordViewWindow):

    def afterEdit(self, fieldname):
        record = self.getRecord()
        if (fieldname == "RecordRow"):
            record.reloadFields()

    def buttonClicked(self, buttonname):
        record = self.getRecord()
        if (buttonname=="Reload"):
            record.reloadFields()
        if (buttonname=="AddClause"):
            record.addClause()
    
    def fillPasteWindow(self, pastewindowname, fieldname):        
        if (pastewindowname == "GroupTablePasteWindow"):
            info = getWindowsInfo()
            from GroupTable import GroupTable
            l = []
            for table in info.keys():
                gt = GroupTable()
                gt.TableName = info[table]["RecordName"]
                gt.TableTitle = info[table]["Title"]
                l.append(gt)
            return l

    def beforeEditRow(self, fieldname, rowfieldname, rownr):
        record = self.getRecord()
        record.addField(self.currentRow("HTMLRecordViewRows"))
        
    def importHTML(self):
        if (self.getRecord().save()):
            fn = getOpenFileName()
            f = file(fn)
            html = f.read()
            import os.path
            self.getRecord().importHTML(html, os.path.dirname(fn))
            self.refresh()
