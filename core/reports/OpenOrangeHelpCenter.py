#encoding: utf-8
from OpenOrange import *
from Report import Report
from GlobalTools import *
from DocumentationTools import getFieldDocumentation
from DocumentationTools import getIndexDocumentation

class OpenOrangeHelpCenter(Report):

    def run(self):
        self.getView().resize(400,600)
        record = self.getRecord()
        
        self.startTable(Border="0",CellPadding="0",CellSpacing="0")
        self.startRow()
        self.addImage("openorange.png",Height="22",BGColor=self.LevelBBackColor,VAlign="center")
        self.addValue("Open Orange Help Center",BGColor=self.LevelBBackColor,Color=self.LevelBForeColor,VAlign="center")
        self.endRow()
        self.endTable()
        self.addHTML("<hr>")

        if (not hasattr(self,"prevList")):
            self.prevList = []
            self.nextList = []

        if (not hasattr(self,"viewMode")):
            self.viewMode = "field"
        
        self.startTable()
        self.startRow(Style="A")
        self.addValue(tr("Index"),CallMethod="internalAction",Parameter="index,0,0",Underline=True)
        self.addValue(tr("Close"),CallMethod="internalAction",Parameter="close,0,0",Underline=True)
        if (len(self.prevList) > 0):
            #self.addValue(len(self.prevList))
            self.addValue(tr("Previous"),Underline=True,CallMethod="internalAction",Parameter="prev,0,0")
        else:
            self.addValue(tr("Previous"),Color=self.DefaultBackColor)
        if (len(self.nextList) > 0):
            self.addValue(tr("Next"),Underline=True,CallMethod="internalAction",Parameter="next,0,0")
        else:
            self.addValue(tr("Next"),Color=self.DefaultBackColor)
        if (record.FieldName or record.TableName):
            if ("openorange" in getScriptDirs()):
                self.addValue(tr("Modify"),Underline=True,CallMethod="internalAction",Parameter="modify,%s,%s" %(record.TableName,record.FieldName))
            self.endRow()
        self.endTable()
        self.addHTML("<hr>")

        if (self.viewMode == "field"):

            docobj = getFieldDocumentation(record.TableName, record.FieldName)
            if (hasattr(docobj,"Data")):
                self.startTable(Border="0",CellSpacing="0")
                self.startRow(Style="B")
                self.addValue("%s.%s" %(tr(record.TableName),tr(record.FieldName)),Bold=True,Size="5")
                self.endRow()
                if (len(docobj.Data.FieldsArray) > 0):
                    for farray in docobj.Data.FieldsArray:
                        self.startRow(Style="A")
                        self.addValue(farray.Description,Width="100")
                        self.endRow()
                        
                        if (farray.LinksArray):
                            self.blankRow()
                            self.startRow(Style="B")
                            self.addValue(tr("See Also"),Italic=True)
                            self.endRow()
                            for larray in farray.LinksArray:
                                self.startRow(Style="L")
                                tstring = "%s.%s" %(tr(larray.TableName),tr(larray.FieldName))
                                linkstring = "%s.%s" %(larray.TableName,larray.FieldName)
                                self.addValue(tstring,CallMethod="seeAlso",Parameter="%s" %(linkstring),Underline=True)
                                self.endRow()
                else:
                    self.startRow(Style="A")
                    self.addValue(tr("Information for this field is not available yet"))
                    self.endRow()
                    
                    self.blankRow()
                    self.startRow(Style="L")
                    self.addValue(tr("Click here and suggest us this information"),CallMethod="internalAction",Parameter="submit,%s,%s" %(record.TableName,record.FieldName))
                    self.endRow()
                self.endTable()
            self.addHTML("<hr>")
        elif (self.viewMode == "index"):
            indexobj = getIndexDocumentation("")
            if (hasattr(indexobj,"Data")):
                self.startTable(Border="0",CellSpacing="0")
                self.startRow(Style="B")
                self.addValue("Index",Bold=True,Size="5")
                self.endRow()
                if (len(indexobj.Data.FieldsArray) > 0):
                    lastchar = ""
                    for farray in indexobj.Data.FieldsArray:
                        if (lastchar <> farray.Description[0]):
                            lastchar = farray.Description[0]
                            self.startRow()
                            self.addValue(lastchar,Bold=True,Size="4")
                            self.endRow()
                        self.startRow()
                        self.addValue("%s (%s)" %(farray.Description,farray.Count),CallMethod="internalAction",Parameter="index,%s,0" %(farray.TableName))
                        self.endRow()
        elif (self.viewMode == "fieldlist"):
            indexobj = getIndexDocumentation(record.TableName)
            if (hasattr(indexobj,"Data")):
                self.startTable(Border="0",CellSpacing="0")
                self.startRow(Style="B")
                self.addValue(tr(record.TableName),Bold=True,Size="5")
                self.endRow()
                if (len(indexobj.Data.FieldsArray) > 0):
                    lastchar = ""
                    for farray in indexobj.Data.FieldsArray:
                        self.startRow()
                        self.addValue(farray.FieldName,CallMethod="internalAction",Parameter="index,%s,%s" %(farray.TableName,farray.FieldName))
                        self.endRow()
                self.endTable()

    def seeAlso(self, param, value):
        if ("." in param):
            record = self.getRecord()
            if (len(self.nextList) > 0):
                self.nextList = []
            self.prevList.append((self.viewMode,record.TableName,record.FieldName))
            tname, fname = param.split(".")
            record.TableName = tname
            record.FieldName = fname
            self.refresh()

    def internalAction(self, param, value):
        action,tname,fn = param.split(",")
        record = self.getRecord()
        if (action == "submit"):
            from HelpDocumentation import HelpDocumentation
            hdoc = HelpDocumentation()
            if (hdoc):
                hdoc = HelpDocumentation()
                hdoc.defaults()
                hdoc.Record = tname
                hdoc.Field = fn
                hdoc.pasteField()
                hdoc.Company = getSettingRecordField("OurSettings","Name")
                hdoc.CompanyUserCode = currentUser()
                hdoc.CompanyUserName = getMasterRecordField("User","Name",currentUser())
                openWindow(hdoc)
        elif (action == "close"):
            self.close()
        elif (action == "index"):
            if (tname == "0"):
                if (len(self.nextList) > 0):
                    self.nextList = []
                self.prevList.append((self.viewMode,record.TableName,record.FieldName))
                self.viewMode = "index"
                record.TableName = ""
                record.FieldName = ""
                self.refresh()
            else:
                if (fn == "0"):
                    if (len(self.nextList) > 0):
                        self.nextList = []
                    self.prevList.append((self.viewMode,"",""))
                    self.viewMode = "fieldlist"
                    record.TableName = tname
                    record.FieldName = ""
                    self.refresh()
                else:
                    if (len(self.nextList) > 0):
                        self.nextList = []
                    self.prevList.append((self.viewMode,record.TableName,record.FieldName))
                    self.viewMode = "field"
                    record.TableName = tname
                    record.FieldName = fn
                    self.refresh()
        elif (action == "prev"):
            if (self.prevList):
                tnext = self.prevList.pop()
                self.nextList.append((self.viewMode,record.TableName,record.FieldName))
                self.viewMode    = tnext[0]
                record.TableName = tnext[1]
                record.FieldName = tnext[2]
                self.refresh()
        elif (action == "next"):
            if (self.nextList):
                tprev = self.nextList.pop()
                self.prevList.append((self.viewMode,record.TableName,record.FieldName))
                self.viewMode    = tprev[0]
                record.TableName = tprev[1]
                record.FieldName = tprev[2]
                self.refresh()
        elif (action == "modify"):
            from HelpDocumentation import HelpDocumentation
            hd = HelpDocumentation.bring("%s.%s" %(tname,fn))
            if (hd):
                openWindow(hd)