#encoding: utf-8
from OpenOrange import *

ParentDocumentLinkWindow = SuperClass("DocumentLinkWindow","MasterWindow",__file__)
class DocumentLinkWindow(ParentDocumentLinkWindow):

    def afterEditRow(self, fieldname, rowfieldname, rownr):
        docl = self.getRecord()
        if (fieldname == "Specs"):
            doclrow = docl.Specs[rownr]
            if (rowfieldname == "Conditions"):
                if (not doclrow.ClassName):
                    doclrow.ClassName = docl.Code + "Doc"


    def fillPasteWindow(self, pastewindowname, fieldname):
        if pastewindowname == "XPasteWindow":
            if fieldname == "Code":
                query = []
                wininfo = getWindowsInfo()
                for wInfo in wininfo.values():
                    z = NewRecord("X")
                    z.Code = wInfo["RecordName"]
                    z.Name = wInfo["Title"]
                    query.append(z)
                query.sort(key = lambda x: x.Name)
                return query
