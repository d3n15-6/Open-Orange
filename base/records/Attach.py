#encoding: utf-8
from OpenOrange import *

ParentAttach = SuperClass("Attach", "Record", __file__)
class Attach(ParentAttach):
    FILE = 0
    RECORD = 1
    IMAGE = 2
    NOTE = 3

    @classmethod
    def getStringId(self, record):
        if record.isNew(): return None
        return "%s|%s" % (record.name(), record.internalId)

    def defaults(self):
        ParentAttach.defaults(self)
        self.Type = self.NOTE

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentAttach.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if (not res): return res
        if (self.Type != self.NOTE and fieldname == "Value"):
            res = False
        return res

    def getOriginRecord(self):
        record = NewRecord(self.OriginRecordName)
        record.setPortableId(self.OriginId)
        if (record.load()):
            return record
        return None

    def uniqueKey(self):
        return ('OriginRecordName', 'OriginId')
    
    def getPortableId(self, useOldFields=False):
        originrecordname = self.OriginRecordName
        originid = self.OriginId
        if useOldFields: 
            originrecordname = self.oldFields('OriginRecordName').getValue()
            originid = self.oldFields('OriginId').getValue()
        return str("%s|%s" % (originrecordname,originid))
    
    def setPortableId(self, id):
        self.OriginRecordName, self.OriginId  = id.split('|')
    
    @classmethod
    def bring(classobj, originrecordname, originid):
        uniquekey = "%s|%s" % (originrecordname, originid)
        try:
            return classobj.buffer[uniquekey]
        except:
            p = classobj()
            p.Code = code
            p.CustCode = custcode
            if p.load():
                classobj.buffer[uniquekey] = p
                return p
            classobj.buffer[uniquekey] = None