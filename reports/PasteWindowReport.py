#encoding: utf-8
from OpenOrange import *
from Report import Report

TranslateEditor = {"text":"s","value":"v"}
class PasteWindowReport(Report):
    
    def run(self):
        if not self.__dict__.has_key("firstrec"): self.firstrec = 0
        if not self.__dict__.has_key("where"): self.lastwhere = ""
        self.recsPerPage = 20
        spec = self.getRecord()
        self.startTable()
        self.startRow()
        query = Query()
        columns = self.lwinfo["Columns"]
        fieldnames = "{internalId}"
        for col in columns:
            fieldnames += ",{%s}" % (col["FieldName"])

        self.startRow()
        self.addValue("[Crear]", CallMethod="createRecord")
        self.endRow()

        self.startHeaderRow()
        where = ""
        for col in columns:
            self.addValue(col["Label"])
            fn = col["FieldName"]
            val = spec.fields(fn).getValue()
            if (not spec.fields(fn).isNone()):
                editor = col["Editor"]
                if editor in ("text","memo"):
                    where += " WHERE?AND {%s} LIKE %s|%s| " % (col["FieldName"], TranslateEditor[editor], "%"+val+"%")
                else:
                    where += " WHERE?AND {%s} = %s|%s| " % (col["FieldName"], TranslateEditor[editor], val)
                    
        self.endHeaderRow()

        if where != self.lastwhere:
            self.firstrec = 0
            self.lastwhere = where            
        
        query.sql = "SELECT %s FROM [%s] %s " % (fieldnames, self.recinfo["TableName"], where)
        query.setLimit(int(self.recsPerPage),int(self.firstrec)) 

        self.recsInPage = 0
        if query.open():
            lineColors = ("#BCCABC","#FBEEED")
            idcolor = 0
            for rec in query:
                self.startRow()
                for col in columns:
                    self.addValue(rec.fields(col["FieldName"]).getValue(), CallMethod="pasteValue", BGColor=lineColors[idcolor])
                #self.addValue("[Copiar]", CallMethod="copyRecord", Parameter=str(rec.internalId))                    
                #self.addValue("[Borrar]", CallMethod="deleteRecord", Parameter=str(rec.internalId))
                idcolor = not idcolor
                self.recsInPage += 1
                
                self.endRow()
        self.endTable()
        
        self.showCursors()
    
    def showCursors(self):
        self.startTable()
        self.startRow()
        if self.firstrec > 0: 
            self.addValue("[Anterior]", CallMethod="prevPage")
        else:
            self.addValue("[Anterior]", FGColor="gray")
        if self.recsInPage == self.recsPerPage: 
            self.addValue("[Siguiente]", CallMethod="nextPage")
        else:
            self.addValue("[Siguiente]", FGColor="gray")
        self.endRow()
        self.endTable()
    
    def prevPage(self, value):
        self.firstrec -= self.recsPerPage
        if self.firstrec < 0: self.firstrec = 0
        self.clear()
        self.run()
        self.render()
    
    def nextPage(self, value):
        self.firstrec += self.recsInPage
        self.clear()
        self.run()
        self.render()
        
    def pasteValue(self, value):
        self.setPasteFieldValue(value)
        self.close()
    
    def deleteRecord(self, internalid, value):
        pass
    
    def copyRecord(self, internalid, value):
        pass

    def createRecord(self, value):
        record = NewRecord(self.recinfo["Name"])
        window = NewWindow(self.lwinfo["WindowName"])
        window.setRecord(record)
        window.open()
        
        
    def getUserInputDef(self, param):
        self.lwinfo = getPasteWindowsInfo()[param]
        self.recinfo = getRecordsInfo()[self.lwinfo["RecordName"]]
        
        fieldsStr=""
        fields = self.recinfo["Fields"]
        columns = self.lwinfo["Columns"];        
        for col in columns:
            fn = col["FieldName"]
            fieldsStr += "<field name=\"%s\" type=\"%s\" length=\"%i\"/>\n" % (fn, fields[fn]["Type"], fields[fn]["Length"])
        
        columnsStr=""
        for col in columns:
            columnsStr += "<%s fieldname=\"%s\" label=\"%s\"/>\n" % (col["Editor"], col["FieldName"], col["Label"])
        
        res = """
        <reportuserinput>
            <reportrecord>%s</reportrecord>
            <reportwindow name="%s" title="%s">%s</reportwindow>
        </reportuserinput>
        """ % (fieldsStr, param, self.lwinfo["Title"], columnsStr)
        return res