#encoding: utf-8
from OpenOrange import * 

class PythonRecord:
    
    def __init__(self, record=None):
        self.__classname__ = None
        self.__modified__ = None
        self.__newflag__ = None
        self.__windowname__ = None
        self.fields = {}
        self.ftypes = {}
        self.oldFields = {}
        self.details = {}
        self.removed = {}
        if record: self.fromRecord(record)
    
    def fromRecord(self, record):
        self.__classname__ = record.name()
        self.__modified__ = record.isModified()
        self.__newflag__ = record.isNew()
        try:
            self.__windowname__ = record.__windowname__
        except:
            pass
        self.fields = {}
        self.ftypes = {}
        self.oldFields = {}
        self.details = {}
        self.removed = {}
        for fn in record.fieldNames():
            field = record.fields(fn)
            self.ftypes[fn] = (field.getType(), field.getMaxLength(), field.isPersistent(), field.getLinkTo())
            if field.isNone():
                self.fields[fn] = None
            else:
                self.fields[fn] = field.getValue()
            field = record.oldFields(fn)
            if field.isNone():
                self.oldFields[fn] = None
            else:
                self.oldFields[fn] = field.getValue()
        for dn in record.detailNames():
            detail = record.details(dn)
            self.details[dn] = []
            self.removed[dn] = []
            for row in detail:
                r = PythonRecord()
                self.details[dn].append(r)
                r.fromRecord(row)
            if not self.__newflag__:
                for i in range(detail.removedRecordsCount()):
                    row = detail.getRemovedRecord(i)
                    r = PythonRecord(row)
                    self.removed[dn].append(r)
        #self.__dict__ = record.__dict__
        #self.__doc__ = record.__doc__

    def toRecord(self, record=None):
        if not record: 
            record = NewRecord(self.__classname__)
        else:
            for dn in self.details.keys():
                record.details(dn).clear()
                record.details(dn).clearRemovedRecords()
        for fn in self.fields.keys():
            v = self.fields[fn]
            if not record.hasField(fn):
                try:
                    record.createField(fn, *self.ftypes[fn])                        
                except AttributeError, e:
                    continue
            field = record.fields(fn)                
            if v is not None:
                record.fields(fn).setValue(v)
            v = self.oldFields[fn]
            #if v is not None:
            field = record.oldFields(fn)
            if field: record.oldFields(fn).setValue(v)
        for dn in self.details.keys():
            detail = record.details(dn)
            if not detail is None:
                for row in self.details[dn]:
                    r = row.toRecord()
                    detail.append(r)
                if not self.__newflag__:
                    for row in self.removed[dn]:
                        r = row.toRecord()
                        detail.appendRemovedRecord(r)
        record.setModified(self.__modified__)
        record.setNew(self.__newflag__)            
        try:
            record.__windowname__ = self.__windowname__
        except:
            pass
        #record.__dict__ = self.__dict__
        #record.__doc__ = self.__doc__
        return record
        
    def __str__(self):
        return "Record %s:" % self.__classname__