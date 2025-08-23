#encoding: utf-8
from OpenOrange import *

class GenericImporter:
    UPDATERECORDS = 1
    SKIPRECORDS = 2
    INSERTRECORDS = 3
    
    def __init__(self, file, KeepInternalIds=True, mode=SKIPRECORDS):
        self.file = file
        self.keepinternalid = KeepInternalIds
        self.linenr = 0
        self.mode = mode
        if self.mode == 1:
            self.processRecord = self.processRecord_Updating
        elif self.mode == 2:
            self.processRecord = self.processRecord_Skipping
        
    def readline(self):
        self.linenr += 1
        return self.file.readline()
        
    def readFieldNames(self):
        fnames = map(lambda x: x.strip(), self.readline().split('\t'))
        while not fnames[-1]:
            fnames = fnames[:-1]
        return fnames
            

    def readDetailsHeader(self):
        line = self.readline().strip()
        while line:
            self.detailnames.append(line)
            self.details[line] = self.readFieldNames()
            line = self.readline().strip()
        
    def readHeader(self):
        self.recordname = self.readline().strip()
        self.modelrecord = NewRecord(self.recordname)
        if not self.modelrecord: 
            raise AppException, tr("The record does not exist.") + " " + self.recordname
        self.uniquefieldnames = self.modelrecord.uniqueKey()
        self.fieldnames = self.readFieldNames()
        self.detailnames = []
        self.details = {}
        self.readDetailsHeader()
    
    def readDetailValues(self, record, detailname):
        fnames = self.details[detailname]
        detail = record.details(detailname)
        line = self.readline()
        while line.strip():
            values = map(lambda x: x.strip(), line.split('\t'))
            row = NewRecord(detail.name())
            i = 0
            for fname in fnames:
                try:
                    if (self.keepinternalid or fname != "internalId"):
                        v = values[i]
                        if v != "\\N":
                            row.fields(fname).setValue(v.replace(chr(11),'\n').replace(chr(12),'\r'))
                    i += 1
                except Exception, e:
                    mstring  = "%s" %(tr("Error Importing File"))
                    mstring += "<br>%s: %s" %(tr("Column"),i+i)
                    mstring += "<br>%s: %s" %(tr("Field"),fname)
                    mstring += "<br>%s: %s " %(tr("Detail"),detailname)
                    message(mstring)
                    message(str(values))
                    message("|" + line + "|")
                    raise
            detail.append(row)
            line = self.readline()
            
    def readRecord(self):
        record = None
        line = self.readline()
        if line:
            values = map(lambda x: x.strip(), line.split('\t'))
            record = NewRecord(self.recordname)
            i = 0
            for fname in self.fieldnames:
                try:
                    if (self.keepinternalid or fname != "internalId"):
                        v = values[i]
                        if v != "\\N":
                            record.fields(fname).setValue(v.replace(chr(11), '\n'))
                    i += 1
                except:
                    message("Error in Column %i, Field %s, Line No. %s" % (i, fname, self.linenr))
                    raise
            for dname in self.detailnames:
                self.readDetailValues(record, dname)
            return record
        
    def showrecord(self, record):
        from InvoiceWindow import InvoiceWindow
        w = InvoiceWindow()
        w.setRecord(record)
        w.open()
     
    def processRecord(self, record):
        return False
        
    def processRecord_Updating(self, record):
        existentrecord = record.__class__()
        for fn in self.uniquefieldnames:
            v = record.fields(fn).getValue()
            if v != "\\N":
                existentrecord.fields(fn).setValue(v)
        if existentrecord.load():
            existentrecord.forceDelete()
        #if (record.OriginType <> 201):
        #    if (hasattr(record,"SerNr")):
        #        print "Grabando importación de %s, SerNr %s" %(record.name(),record.SerNr)
        #    res = record.store()
        #    if (res):
        #        commit()
        #    return res
        return record.store()

    def processRecord_Skipping(self, record):
        existentrecord = record.__class__()
        for fn in self.uniquefieldnames:
            v = record.fields(fn).getValue()
            if v != "\\N":
                existentrecord.fields(fn).setValue(v)
        if not existentrecord.load():
            return record.store()
        return False