#encoding: utf-8
from OpenOrange import *

ParentDocumentSpecWindow = SuperClass("DocumentSpecWindow","MasterWindow",__file__)
class DocumentSpecWindow(ParentDocumentSpecWindow):

    def buttonClicked(self, buttonname):
        if (buttonname == "addDocFields"):
            self.addDocFields()

    def moveUp(self):
        try:
            curfield = self.currentField()
            currow = self.currentRow(curfield)
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moveUp()
        except:
            pass

    def moveLeft(self):
        try:
            curfield = self.currentField()
            currow = self.currentRow(curfield)
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moveLeft()
        except:
            pass

    def moveRight(self):
        try:
            curfield = self.currentField()
            currow = self.currentRow(curfield)
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moveRight()
        except:
            pass

    def moveDown(self):
        try:
            curfield = self.currentField()
            currow = self.currentRow(curfield)
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moveDown()
        except:
            pass

    def moreWidth(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Rects","Images","Fields")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moreWidth()
        else:
            return

    def lessWidth(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Rects","Images","Fields")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.lessWidth()
        else:
            return

    def moreHeight(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Rects","Images")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.moreHeight()
        else:
            return

    def lessHeight(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Rects","Images")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.lessHeight()
        else:
            return

    def alignLeft(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Fields","Labels")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.alignLeft()
        else:
            return

    def alignCenter(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Fields","Labels")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.alignCenter()
        else:
            return

    def alignRight(self):
        curfield = self.currentField()
        currow = self.currentRow(curfield)
        if (curfield in ("Fields","Labels")):
            if (currow < 0): return
            record = self.getRecord()
            exec("dsrow = record.%s[%s] " %(curfield,currow))
            dsrow.alignRight()
        else:
            return

    def scale(self):
        factor = getValue("Factor de Escalado? (Ejemplo: 1.3)", 1.04)
        record = self.getRecord()
        for row in record.Fields:
            row.Width = int(round(row.Width * factor,0))
            row.X = int(round(row.X * factor,0))
            row.Y = int(round(row.Y * factor,0))
        for row in record.Labels:
            row.X = int(round(row.X * factor,0))
            row.Y = int(round(row.Y * factor,0))
        for row in record.Rects:
            row.X = int(round(row.X * factor,0))
            row.Y = int(round(row.Y * factor,0))
            row.Width = int(round(row.Width * factor,0))
            row.Height = int(round(row.Height * factor,0))
        for row in record.Images:
            row.X = int(round(row.X * factor,0))
            row.Y = int(round(row.Y * factor,0))
            row.Width = int(round(row.Width * factor,0))
            row.Height = int(round(row.Height * factor,0))

    def addDocFields(self):
        report = AddDocFields()
        report.curDocumentWindow = self
        report.open()

from Report import Report

class AddDocFields(Report):

    def run(self):
        record = self.getRecord()
        curDocument = self.curDocumentWindow.getRecord()
        
        doc = curDocument.Code
        recquery = Query()
        recquery.sql  = "SELECT {Code} FROM [DocumentLink] dl \n"
        recquery.sql += "INNER JOIN {DocumentLinkSpecRow} dlr ON [dl].{internalId} = [dlr].{masterId} \n"
        recquery.sql += "WHERE [dlr].{DocumentSpecCode} = s|%s| " % doc

        if recquery.open() and recquery.count() > 0:
            recdoc = recquery[0].Code
            self.recdoc = recdoc
            self.doc = doc
            if (not hasattr(self,"showtranslation")):
                self.showtranslation = False
            self.dict = {}
            self.genDict()
            self.printReport()

    def genDict(self):
        record = NewRecord(self.recdoc)
        self.fieldnames = record.fieldNames()
        igfield = ["internalId", "syncVersion", "attachFlag", "Synchronized", "masterId"]
        for fn in self.fieldnames:
            if not fn in igfield:
                self.dict[fn] = {}
                self.dict[fn]["Description"] = ""
                self.dict[fn]["Add"] = "False"
                self.dict[fn]["Type"] = "Header"
                self.dict[fn]["From"] = "Header"
        self.detailnames = record.detailNames()
        self.details = {}
        for dn in self.detailnames:
            detail = record.details(dn)
            self.details[dn] = record.details(dn).fieldNames()
            for dnline in self.details[dn]:
                if not dnline in igfield:
                    self.dict["%s.%s" % (dn,dnline)] = {}
                    self.dict["%s.%s" % (dn,dnline)]["Description"] = ""
                    self.dict["%s.%s" % (dn,dnline)]["Add"] = "False"
                    self.dict["%s.%s" % (dn,dnline)]["Type"] = "Matrix"
                    self.dict["%s.%s" % (dn,dnline)]["From"] = dn
        self.dict.keys().sort()

    def printReport(self):
        record = NewRecord(self.recdoc)
        self.startTable()
        self.startRow()
        self.addValue(tr("Add selected fields") ,Bold=True, CallMethod="addFields", Parameter="SEL", BGColor="Gray")
        self.addValue(tr("Add all fields"),Bold=True, CallMethod="addFields", Parameter="ALL", BGColor="Gray")
        self.addValue(tr("Toggle show translation"),Bold=True, CallMethod="showTranslation", Parameter="0", BGColor="Gray")
        self.endRow()
        self.endTable()

        self.startTable()
        self.header("Header fields")
        listfield = self.dict.keys()
        listfield.sort()
        column = 0
        for line in listfield:
            if (self.dict[line]["Type"] == "Header"):
                if (column == 0):
                    self.startRow()
                if self.dict[line]["Add"] == "True":
                    color = "Yellow"
                else:
                    color = "White"
                if (self.showtranslation):
                    self.addValue("%s" %(record.getFieldLabel(line)), CallMethod="YesNoField", Parameter=line, BGColor=color,Align="Right")
                    column += 1
                    self.addValue(": %s" %(line), CallMethod="YesNoField", Parameter=line, BGColor=color)
                else:
                    self.addValue(line, CallMethod="YesNoField", Parameter=line, BGColor=color)
                #self.addValue("Description")
                #if self.dict[line]["Add"] == "False":
                #    self.addValue(tr("No"), CallMethod="YesNoField", Parameter=line, BGColor=color)
                #else:
                #    self.addValue(tr("Yes"), CallMethod="YesNoField", Parameter=line, BGColor=color)
                column += 1
                if (column == 4):
                    self.endRow()
                    column = 0

        self.header("Matrix fields")
        column = 0
        for line in listfield:
            if (self.dict[line]["Type"] == "Matrix"):
                if (column == 0):
                    self.startRow()
                if self.dict[line]["Add"] == "True":
                    color = "Yellow"
                else:
                    color = "White"
                self.addValue(line, CallMethod="YesNoField", Parameter=line, BGColor=color)
                #self.addValue("Description")
                #if self.dict[line]["Add"] == "False":
                #    self.addValue(tr("No"), CallMethod="YesNoField", Parameter=line, BGColor=color)
                #else:
                #    self.addValue(tr("Yes"), CallMethod="YesNoField", Parameter=line, BGColor=color)
                column += 1
                if (column == 4):
                    self.endRow()
                    column = 0


        self.endTable()
        self.startTable()
        self.startRow()
        self.addValue(tr("Add selected fields"),Bold=True, CallMethod="addFields", Parameter="SEL", BGColor="Gray")
        self.addValue(tr("Add all fields"),Bold=True, CallMethod="addFields", Parameter="ALL", BGColor="Gray")
        self.addValue(tr("Toggle show translation"),Bold=True, CallMethod="showTranslation", Parameter="0", BGColor="Gray")
        self.endRow()
        self.endTable()

    def addFields(self, param, value):
        from DocumentSpecFieldsRow import DocumentSpecFieldsRow
        ds = self.curDocumentWindow.getRecord()
        if ds:
            for field in self.dict.keys():
                finded = False
                for row in ds.Fields:
                    if field == row.Name:
                        finded = True
                if (param == "SEL" and self.dict[field]["Add"] == "True" or param == "ALL") and not finded:
                    dsr = DocumentSpecFieldsRow()
                    dsr.Name = field
                    if self.dict[field]["Type"] == "Header":
                        dsr.Type = 0
                    else:
                        dsr.Type = 1
                    ds.Fields.append(dsr)
            self.close()

    def YesNoField(self, param, value):
        self.clear()
        if self.dict[param]["Add"] == "False":
            self.dict[param]["Add"] = "True"
        else:
            self.dict[param]["Add"] = "False"
        self.printReport()
        self.render()

    def showTranslation(self, param, value):
        self.showtranslation = not self.showtranslation
        self.refresh()