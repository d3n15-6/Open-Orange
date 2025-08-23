#encoding: utf-8
# Mayo 2009 - Martin Salcedo
from OpenOrange import *
from Report import Report

class AttachList(Report):

    def run(self):
        record = self.getRecord()
        self.printReportTitle("Attach List")

        aquery = Query()
        aquery.sql  = "SELECT A.internalId, A.Type, A.OriginRecordName, A.OriginId, A.Comment, A.Value " 
        aquery.sql += "FROM [Attach] [A] "
        aquery.sql += "WHERE?AND A.Type = i|3| "
        if (record.RecordName):
            aquery.sql += "WHERE?AND A.OriginRecordName = s|%s| " %(record.RecordName)
        
        if (aquery.open()):
            self.startTable()
            self.startHeaderRow()
            self.addValue("Number")
            self.addValue("Title")
            self.addValue("Text")
            self.endHeaderRow()

            for aline in aquery:
                self.startRow()
                self.addValue(aline.internalId,Window="AttachNoteWindow",FieldName="internalId")
                self.addValue(aline.Comment)
                self.addValue(aline.Value)
                self.endRow()
            self.endTable()