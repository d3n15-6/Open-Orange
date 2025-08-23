#encoding: utf-8
from OpenOrange import *
from Report import Report

class SQLConsoleReport(Report):

    def startNewDBTransaction(self): #llamado desde Report.py
        pass 
        
    def run(self):
        spec = self.getRecord()
        query = Query()
        query.sql = spec.sql

        self.startTable()
        self.startHeaderRow()
        self.addValue("Consulta: " + query.sql)
        self.endHeaderRow()    
        self.endTable()
        
        self.startTable()
        if query.sql.upper().strip().startswith("SELECT") or query.sql.upper().strip().startswith("SHOW") or query.sql.upper().strip().startswith("DESCRIBE"):
            if (query.open()):
                self.startHeaderRow()
                for fieldname in query.fieldNames():
                    self.addValue(fieldname)
                self.endHeaderRow()         
                for rec in query:
                    self.startRow()
                    for fieldname in query.fieldNames():
                        field = rec.fields(fieldname)
                        if field.isNone():
                            self.addValue("(Null)", Color="Gray")
                        else:
                            self.addValue(rec.fields(fieldname).getValue(), Decimals=5)
                    self.endRow()
                self.startRow()
                self.endRow()
                self.startHeaderRow()
                self.addValue("Registros: %i" % query.count(), ColSpan=2)
                self.endHeaderRow()
        else:
            if (query.execute()):
                self.startHeaderRow()
                self.addValue("Registros matcheados: %i" % query.matchedRows())    
                self.endHeaderRow()         
        self.endTable()
        
        

