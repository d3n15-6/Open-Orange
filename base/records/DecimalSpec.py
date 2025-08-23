#encoding: utf-8

from OpenOrange import *
from Currency import Currency

ParentDecimalSpec = SuperClass("DecimalSpec","Record",__file__)
class DecimalSpec(ParentDecimalSpec):
    buffer = RecordBuffer("DecimalSpec", timedelta()) #timeout disabled
    buffer.loaded = False

    def check(self):
        res = ParentDecimalSpec.check(self)
        if not res: return res
        if (self.ViewDecimals < 0 or not self.ViewDecimals):
            self.ViewDecimals = 0
        if (self.RoundDecimals < 0 or not self.RoundDecimals):
            self.RoundDecimals = 0
        record = NewRecord(self.RecordName)
        if ("Currency" in record.fieldNames()):
            if (not self.Currency):
                return self.FieldErrorResponse("NONBLANKERR","Currency")
        if (not self.RecordName):
            return self.FieldErrorResponse("NONBLANKERR","RecordName")
        if (not self.FieldName):
            return self.FieldErrorResponse("NONBLANKERR","FieldName")
        gri = getRecordsInfo()
        if (not self.RecordName in gri.keys()):
            return self.FieldErrorResponse("INVALIDVALUEERR","RecordName")
        if (not (self.FieldName in record.fieldNames() or self.FieldName in record.detailNames())):
            return self.FieldErrorResponse("INVALIDVALUEERR","FieldName")
        if (len(record.detailNames()) != 0):
            if self.RowFieldName and (not self.RowFieldName in record.details(self.FieldName).fieldNames()):
                return self.FieldErrorResponse("INVALIDVALUEERR","RowFieldName")
        return res

    @classmethod
    def loadBuffer(objclass):
        objclass.buffer.clear()
        query = Query()
        query.sql = "SELECT * FROM [DecimalSpec]"
        if query.open():
            for rec in query:
                objclass.buffer["%s|%s|%s|%s" % (rec.Currency, rec.RecordName, rec.FieldName, rec.RowFieldName)] = (rec.ViewDecimals, rec.RoundDecimals)
        objclass.buffer.loaded=True

    @classmethod
    def getRoundDecimals(objclass, currency, recordname, fieldname, rowfieldname=""):
        if not objclass.buffer.loaded: objclass.loadBuffer()
        res = objclass.buffer.get("%s|%s|%s|%s" % (currency, recordname, fieldname, rowfieldname), None)
        if res is None:
            return res
        return res[1]

    @classmethod
    def getViewDecimals(objclass, currency, recordname, fieldname, rowfieldname=""):
        if not objclass.buffer.loaded: objclass.loadBuffer()
        res = objclass.buffer.get("%s|%s|%s|%s" % (currency, recordname, fieldname, rowfieldname), None)
        if res is None:
            res = objclass.buffer.get("|%s|%s|%s" % (recordname, fieldname, rowfieldname), None)
            if res is None: return res
            return res[0]
        return res[0]

    ###EVENTS###
    def uniqueKey(self):
        return ('Currency', 'RecordName','FieldName', 'RowFieldName')

    #@classmethod
    #def bring(objclass, curr, rname, fname, rfname):
    #    uniquekey = "%s|%s|%s|%s" % (curr, rname, fname, rfname)
    #    try:
    #        return classobj.buffer[uniquekey]
    #    except:
    #        p = classobj()
    #        p.Currency = curr
    #        p.RecordName = rname
    #        p.FieldName = fname
    #        p.RowFieldName = rfname
    #        if p.load():
    #            classobj.buffer[uniquekey] = p
    #            return p
    #        classobj.buffer[uniquekey] = None

#runs every time this modules gets loaded
try:
    DecimalSpec.loadBuffer()
except DBError, e:
    processDBError(e, {}, str(e))
