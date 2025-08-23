#encoding: utf-8
from OpenOrange import *

class GenericExporter:

    def __init__(self, file):
        self.file = file
        
    def exportHeader(self, rec):
        self.file.write(rec.name() + '\n')
        self.fieldnames = rec.fieldNames()
        self.file.write('\t'.join(self.fieldnames))
        self.file.write('\n')
        self.detailnames = rec.detailNames()
        self.details = {}
        for dn in self.detailnames:
            detail = rec.details(dn)
            self.details[dn] = rec.details(dn).fieldNames()
            self.file.write(dn)
            self.file.write('\n')
            self.file.write('\t'.join(self.details[dn]))
            self.file.write('\n')                        
        self.file.write('\n')
    
    def exportRecordValues(self, rec, fieldnames):
        values = []
        for fn in fieldnames:
            field = rec.fields(fn)
            if field.isNone():
                values.append(u'\\N')
            elif field.getType() == "memo":
                values.append(unicode(field.getValue().replace('\n', chr(11)).replace('\r', chr(12))))
            elif field.getType() == "string":
                values.append(utf8(field.getValue().replace('\n', chr(11)).replace('\r', chr(12))).decode("utf8"))
            elif field.getType() == "set":
                values.append(utf8(field.getValue().replace('\n', chr(11)).replace('\r', chr(12))).decode("utf8"))
            else:
                values.append(utf8(field.getValue()).decode("utf8"))
        s = '\t'.join(values)
        self.file.write(s)
        self.file.write('\n')

    def exportRecord(self, rec):
        self.exportRecordValues(rec, self.fieldnames)
        for dn in self.detailnames:
            detail = rec.details(dn)
            for row in detail:
                self.exportRecordValues(row, self.details[dn])
            self.file.write('\n')        

    def exportTable(self, recordname, fromDate=None, toDate=None,fromsernr=None, tosernr=None):
        rec = NewRecord(recordname)
        if not rec: 
            return ErrorResponse(tr("INVALIDVALUEERR"))
        self.exportHeader(rec)
        query = Query()
        query.sql = "SELECT {internalId} FROM [%s]" % recordname
        if fromDate and toDate and ("TransDate" in rec.fieldNames()):
            query.sql += "WHERE?AND {TransDate} BETWEEN d|%s| AND d|%s| " % (fromDate, toDate)
        if (fromsernr and tosernr and ("SerNr" in rec.fieldNames())):
            query.sql += "WHERE?AND {SerNr} BETWEEN i|%s| AND i|%s| " % (fromsernr, tosernr)
        
        if query.open():
            for rec in query:
                record = NewRecord(recordname)
                record.internalId = rec.internalId
                record.load()
                self.exportRecord(record)
