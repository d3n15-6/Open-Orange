#encoding: utf-8
from OpenOrange import *

ParentSerNrControl = SuperClass("SerNrControl","Record",__file__)
class SerNrControl(ParentSerNrControl):
    __records_by_recordname__ = {}

    @classmethod
    def getSerNrControlsForRecordName(classobj, recordname):
        if SerNrControl.__records_by_recordname__.get(recordname, None) is None:
            l = []
            q = Query()
            q.sql = "SELECT internalId FROM SerNrControl where TransType=s|%s|" % recordname
            if q.open():
                for r in q:
                    obj = SerNrControl()
                    obj.internalId = r.internalId
                    if obj.load():
                        l.append(obj)
            SerNrControl.__records_by_recordname__[recordname] = l
        return SerNrControl.__records_by_recordname__[recordname]

    def defaults(self):
        self.InvoiceType = 3
        self.DocType = -1

    def check(self):
        result = ParentSerNrControl.check(self)
        if (result): result = self.checkRange()
        if (result): result = self.checkOverlap()
        return result

    def checkRange(self):
        if (self.FromNr < 0 or self.ToNr < 0):
            return ErrorResponse("ONLYPOSNRSERR")
        if (self.ToNr < self.FromNr):
            return ErrorResponse("INVERTEDRANGEERR")
        return True

    def checkOverlap(self):
        query = Query()
        query.sql = "SELECT {FromNr}, {ToNr} FROM [SerNrControl]"
        query.sql += " WHERE {TransType} = s|%s|" % self.TransType
        query.sql += " AND {internalId} != i|%s|" % str(self.internalId)
        if (query.open()):
            for rec in query:
                if (self.overlaps((self.FromNr, self.ToNr), (rec.FromNr, rec.ToNr))):
                    return ErrorResponse("%s - \n %s \n %s" %(tr("RANGEOVERLAPERR"),(self.FromNr,self.ToNr),(rec.FromNr,rec.ToNr)))
            query.close()
        return True

    @staticmethod
    def overlaps(r1, r2):
        if( (r2[0]-r1[1]) <= 0 and (r1[0]-r2[1])<= 0):
            return True
        return False

    @staticmethod
    def CheckSerNr(TransType, Office, SerNr, recordName, TransDate = None, DocType = -1, InvoiceType = -1, update = False, Computer = None, FormType = None):
        res = True
        #En caso de no haber un rango definido para esa transaccion en ninguna fecha
        #dejo que se grabe
        #PDB Optizacion Begins
        if not SerNrControl.controlExists(TransType): return res
        controls = SerNrControl.getSerNrControlsForRecordName(TransType)
        for control in controls:
            InvoiceTypeTest = InvoiceType
            DocTypeTest = DocType
            if control.InvoiceType == 3 or control.InvoiceType < 0:
                InvoiceTypeTest = -1
            if control.DocType < 0:
                    DocTypeTest = -1
            if (not Office or control.Office in (Office, '')) and \
                (not Computer or control.Computer in (Computer, '')) and \
                (not FormType or control.FormType in (FormType, '')) and \
                (control.FromDate <= TransDate and control.ToDate >= TransDate) and \
                (control.FromNr <= SerNr and control.ToNr >= SerNr) and \
                (DocTypeTest < 0 or control.DocType == DocTypeTest) and \
                (InvoiceTypeTest < 0 or control.InvoiceType in (InvoiceTypeTest, 3)):
                    if (not update):
                        q = Query()
                        q.sql = "SELECT count(*) as cnt FROM [%s] WHERE {SerNr} = i|%s|" % (TransType, SerNr)
                        q.setLimit(1)
                        if q.open() and q[0].cnt > 0: return ErrorResponse("RANGEERR5")
                    return True
        return ErrorResponse("RANGEERR4")
        #PDB Optizacion Ends
        query = Query()
        query.sql = "SELECT {FromNr},{ToNr} FROM [SerNrControl]"
        query.sql += " WHERE?AND {TransType}=s|%s|" % TransType
        if (FormType): query.sql += " WHERE?AND ({FormType}=s|%s| OR {FormType}='' OR {FormType} IS NULL)" % FormType
        if (Office): query.sql += " WHERE?AND ({Office}=s|%s| OR {Office}='' OR {Office} IS NULL)" % Office
        if (Computer): query.sql += " WHERE?AND ({Computer}=s|%s| OR {Computer}='' OR {Computer} IS NULL)" % Computer
        query.sql += " WHERE?AND {FromDate}<=d|%s|" % TransDate
        query.sql += " WHERE?AND {ToDate}>=d|%s|" % TransDate
        query.sql += " WHERE?AND {FromNr}<=i|%s|" % SerNr
        query.sql += " WHERE?AND {ToNr}>=i|%s|" % SerNr
        if (DocType>=0): query.sql += " WHERE?AND ({DocType}=i|%s| OR {DocType}=i|-1|)" % DocType
        if (InvoiceType>=0): query.sql += " WHERE?AND ({InvoiceType}=i|%s| OR {InvoiceType}=i|3| OR {InvoiceType}=i|-1|)" % InvoiceType
        if (query.open() and query.count()>0):
            if (not update):
                rec = NewRecord(recordName)
                rec.SerNr = SerNr
                if (rec.load()):
                    return ErrorResponse("RANGEERR5")
        else:
            return ErrorResponse("RANGEERR4")
        return res

    @staticmethod
    def getNextSerNr(numerable):
        DocType = -1
        InvoiceType = -1
        TransDate = numerable.TransDate
        if numerable.hasField("DocType"): DocType = numerable.DocType
        if numerable.hasField("InvoiceType"): InvoiceType = numerable.InvoiceType
        if SerNrControl.controlExists(numerable.__class__.__name__):
            control = SerNrControl.getControlForNumerable(numerable)
            if (control):
                if control.InvoiceType == 3 or control.InvoiceType < 0:
                    InvoiceType = -1
                if control.DocType < 0:
                    DocType = -1
                numerable.SerNr = control.getControlNextSerNr(control.TransType, control.Office, DocType, InvoiceType, control.Computer, None, control.FormType)
            else:
                return ErrorResponse("RANGEERR1",{"Verifique Control de Numeros Seriales":""})
        else:
            numerable.SerNr = SerNrControl.getLastSerNr(numerable.__class__.__name__)
        if (numerable.SerNr):
            if (SerNrControl.CheckSerNr(numerable.getTransType(), numerable.Office, numerable.SerNr, numerable.name(), TransDate, DocType, InvoiceType, False, numerable.Computer,numerable.FormType)):
                return numerable.SerNr
            else:
                return ErrorResponse("%s - %s" %(tr("RANGEERR2"),numerable.SerNr), {"Verifique Control de Numeros Seriales":""})
        else:
            return ErrorResponse("RANGEERR3")

    def getControlNextSerNr(self, TransType, Office, DocType = -1, InvoiceType = -1, Computer = None, TransDate = None, FormType = None):
        query = Query()
        query.sql = "SELECT {SerNr} as MaxSerNr, {ToSerNr} as MaxToSerNr FROM [%s] " % TransType
        query.sql += " WHERE {SerNr} = (SELECT MAX({SerNr}) FROM [%s] " % TransType
        query.sql += " WHERE {SerNr}<=i|%s|" % self.ToNr
        if (FormType): query.sql += " AND {FormType}=s|%s|" % FormType
        if (Office): query.sql += " AND {Office}=s|%s|" % Office
        if (Computer): query.sql += " AND {Computer}=s|%s|" % Computer
        if (DocType>=0): query.sql += " AND {DocType}=i|%s|" % DocType
        if (InvoiceType>=0): query.sql += " AND {InvoiceType}=i|%s|" % InvoiceType
        query.sql += ")"
        if query.open() and query.count()>0 and query[0].MaxSerNr > 0:
            res = query[0].MaxSerNr
            if res < query[0].MaxToSerNr: res = query[0].MaxToSerNr
            res += 1
            if res < self.FromNr: res = self.FromNr
            if res > self.ToNr: res = self.ToNr
            log("getControlNextSerNr A: " + str(res))
            return res
        else:
            log("getControlNextSerNr B: " + str(self.FromNr))
            return self.FromNr

    @staticmethod
    def getLastSerNr(TransType):
        query = Query()
        query.sql = "SELECT {SerNr} as MaxSerNr, {ToSerNr} as {MaxToSerNr} FROM [%s] " % TransType
        query.sql += "WHERE SerNr = (SELECT MAX(SerNr) FROM [%s])" % TransType
        res = 0
        if (query.open()):
            if (query.count()>0):
                res = query[0].MaxSerNr
                if res <query[0].MaxToSerNr: res = query[0].MaxToSerNr
        log("getLastSerNr: " + str(res+1))
        return res + 1

    @staticmethod
    def getControlForNumerable(numerable):
        #PDB Optimizacion Begins
        controls = SerNrControl.getSerNrControlsForRecordName(numerable.__class__.__name__)
        for control in controls:
            if (control.Office in (numerable.Office,'') and \
                control.Computer in (numerable.Computer, '') and \
                control.FormType in (numerable.FormType, '') and \
                control.FromDate <= numerable.TransDate and control.ToDate >= numerable.TransDate and \
                (not numerable.hasField("DocType") or control.DocType in (numerable.DocType, -1)) and \
                (not numerable.hasField("InvoiceType") or control.InvoiceType in (numerable.InvoiceType,3,-1)) and \
                (not numerable.SerNr or (control.FromNr <= numerable.SerNr and control.ToNr >= numerable.SerNr))):
                        return control
        return None
        #PDB Optimizacion Ends
        id = None
        query = Query()
        query.sql = "SELECT {internalId} FROM [SerNrControl] "
        query.sql += " WHERE?AND ({Office}=s|%s| OR {Office}='' OR {Office} IS NULL)" % numerable.Office
        query.sql += " WHERE?AND ({Computer}=s|%s| OR {Computer}='' OR {Computer} IS NULL)" % numerable.Computer
        query.sql += " WHERE?AND ({FormType}=s|%s| OR {FormType}='' OR {FormType} IS NULL)" % numerable.FormType
        query.sql += " WHERE?AND {TransType}=s|%s|" % numerable.__class__.__name__
        query.sql += " WHERE?AND {FromDate} <= d|%s| WHERE?AND {ToDate} >= d|%s|" % (str(numerable.TransDate), str(numerable.TransDate))
        if (numerable.hasField("DocType")): query.sql += " WHERE?AND ({DocType}=i|%s| OR {DocType}=i|-1|)" % numerable.DocType
        if (numerable.hasField("InvoiceType")): query.sql += " WHERE?AND ({InvoiceType}=i|%s| OR {InvoiceType}=i|3| OR {InvoiceType}=i|-1|)" % numerable.InvoiceType
        if (numerable.SerNr): query.sql += " WHERE?AND {FromNr} <= i|%i| AND {ToNr} >= i|%i| " % (numerable.SerNr,numerable.SerNr)
        if (query.open() and query.count()):
            id = query[0].internalId
            query.close()
        if (id):
            control = SerNrControl()
            control.internalId = id
            control.load()
            return control
        return id

    @classmethod
    def controlExists(classobj, recordname):
        res= bool(len(SerNrControl.getSerNrControlsForRecordName(recordname)) > 0)
        return res

    @staticmethod
    def isManualTransaction(numerable):
        control = SerNrControl.getControlForNumerable(numerable)
        if (control):
            return control.IsManualTransaction
        return False    

    def getPortableId(self, useOldFields=False):
        if useOldFields: return str("%s|%s|%s" % (self.oldFields('TransType').getValue(),self.oldFields('FromNr').getValue(),self.oldFields('ToNr').getValue()))
        return str("%s|%s|%s" % (self.TransType,self.FromNr,self.ToNr))
        
    def setPortableId(self, id):
        self.TransType, self.FromNr, self.ToNr = id.split('|')