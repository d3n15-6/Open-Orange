#encoding: utf-8
from OpenOrange import *

ParentBufferSettingsWindow = SuperClass("BufferSettingsWindow","SettingWindow",__file__)
class BufferSettingsWindow(ParentBufferSettingsWindow):
        
    def fillPasteWindowRow(self, pastewindowname, fieldname, rowfieldname,rownr):
        if pastewindowname == "XPasteWindow":
            if fieldname == "Records":
                query = []
                wininfo = getWindowsInfo()
                for wInfo in wininfo.values():
                    z = NewRecord("X")
                    z.Code = wInfo["RecordName"]
                    z.Name = wInfo["Title"]
                    query.append(z)
                query.sort(key = lambda x: x.Name)
                return query
