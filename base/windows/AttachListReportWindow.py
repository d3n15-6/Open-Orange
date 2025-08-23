#encoding: utf-8
# Mayo 2009 - Martin Salcedo
from OpenOrange import *

ParentAttachListReportWindow = SuperClass("AttachListReportWindow","Window",__file__)
class AttachListReportWindow(ParentAttachListReportWindow):

    def fillPasteWindow(self, pastewindowname, fieldname):
        if pastewindowname == "XPasteWindow":
            if fieldname == "RecordName":
                query = []
                wininfo = getWindowsInfo()
                for wInfo in wininfo.values():
                    z = NewRecord("X")
                    z.Code = wInfo["RecordName"]
                    z.Name = wInfo["Title"]
                    query.append(z)
                query.sort(key = lambda x: x.Name)
                return query
