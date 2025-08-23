#encoding: utf-8
# -*- coding: utf-8 -*-
from OpenOrange import *
from SerNrControl import SerNrControl

ParentNumerable = SuperClass("Numerable","Record",__file__)
class Numerable(ParentNumerable):

    #Este diccionario contiene los Type para el Campo OriginType
    Origin = {}
    Origin["SalesOrder"] = 0
    Origin["Invoice"] = 1
    Origin["Receipt"] = 2
    Origin["ServiceOrder"] = 3
    Origin["Subscription"] = 4
    Origin["PurchaseInvoice"] = 5
    Origin["Payment"] = 6
    Origin["CashOut"] = 7
    Origin["CouponCons"] = 8
    Origin["CashIn"] = 9
    Origin["PosEvent"] = 10
    Origin["Nothing"] = 11
    Origin["StockRequest"] = 12
    Origin["Deposit"] = 13
    Origin["Clearing"] = 14
    Origin["Expenses"] = 15 # incorrectly the was GoodsReceipt before but should be Expenses
    Origin["Quote"] = 16
    Origin["Loan"] = 17
    Origin["Accreditation"] = 18
    Origin["BankReceipt"] = 19
    Origin["BankPayment"] = 20
    Origin["ServiceRequest"] = 21
    Origin["ServiceMaintenance"] = 22
    Origin["PurchaseQuote"] = 23
    Origin["Activity"] = 25
    Origin["CashierBalance"] = 27
    Origin["Project"] = 28
    Origin["StockComp"] = 29
    Origin["GoodsReceipt"] = 30
    Origin["ReturnSupplier"] = 50
    Origin["Booking"] = 51
    Origin["Auction"] = 52
    Origin["PurchaseOrder"] = 53
    Origin["Production"] = 54
    Origin["ProductionOrder"] = 55
    Origin["WedList"] = 56
    Origin["NLT"] = 58
    Origin["Opportunity"] = 59
    Origin["Delivery"] = 60
    Origin["StockDepreciation"] = 61
    Origin["StockMovement"] = 62
    Origin["BarTab"] = 63
    Origin["CloseNLTYear"] = 65 #por rutina de CloseNLTYear
    Origin["Reservation"] = 66
    Origin["JudicialCase"] = 98
    Origin["ValueReception"] = 99
    Origin["WheatLiq"] = 100
    Origin["PublicityOrder"] = 101
    Origin["DelivPrizes"] = 102
    Origin["Punish"] = 103
    Origin["Registration"] = 104
    Origin["CardLoss"] = 105
    Origin["AirMilesCardTransfer"] = 106
    Origin["Depreciation"] = 107
    Origin['NightMaintenance'] = 108
    Origin['RoomRow'] = 109
    Origin['PhoneCall'] = 111
    Origin['Property'] = 113
    Origin['WeddingList'] = 114
    Origin['Case'] = 115
    Origin['ChequeBounce'] = 116
    Origin['ProjectBudgetRow'] = 117
    Origin['ProjectItemRow'] = 118
    Origin['StockTransformation'] = 119
    Origin['ReturnCustomer'] = 120
    Origin['SaldoShifter'] = 121
    Origin['Depreciation'] = 122
    Origin['Revaluation'] = 123
    Origin['SalesBooking'] = 124
    Origin['OperationBooking'] = 125
    Origin['InternalService'] = 126
    Origin['OwnChequeBounce'] = 127
    Origin['PayRollGenerator'] = 128
    Origin['CouponBatchCons'] = 129
    Origin['RepeatItemRow'] = 130
    Origin['Vacation'] = 131
    Origin['FinancialMov'] = 132
    Origin['WayBill'] = 133
    Origin['Deferral'] = 134
    Origin['EarlyIn'] = 135
    Origin['LateOut'] = 136
    Origin['ProviderPayment'] = 137
    Origin['TableBooking'] = 138
    Origin['MoneyExchange'] = 139
    Origin["RecipeOrder"] = 140
    Origin["Absence"] = 141
    Origin["WorkHours"] = 142
    Origin["Mail"] = 143
    Origin["ChequeCaution"] = 144
    Origin["CollectionSheet"] = 145
    Origin["Importation"] = 146
    Origin["CashRegisterEvent"] = 147
    Origin["Calibration"] = 148
    Origin["Kilning"] = 149
    Origin["WoodReceived"] = 150
    Origin["Matching"] = 151
    Origin["WoodShipment"] = 152
    Origin["WoodPacking"] = 153
    Origin["Sanding"] = 154
    #INSERTAR LOS NUEVOS NUMEROS AQUI desde 155
    Origin["WeighingResult"] = 201  #Producción Textil
    Origin["RawStock"] = 202        #Producción Textil
    Origin["RouteSheet"] = 203      #Producción Textil
    #NO CONTINUAR DESDE 203 INSERTAR LOS NUEVOS NUMEROS DESDE 155 ARRIBA
    
    __origin_by_type__ = None

    @classmethod
    def getOriginsByType(classobj):
        if not classobj.__origin_by_type__:
            classobj.__origin_by_type__ = {}
            for name, nr in classobj.Origin.items():
                classobj.__origin_by_type__[nr] = name
        return classobj.__origin_by_type__

    @classmethod
    def getOriginTypeName(classobj, originType):
        for ele in classobj.Origin.keys():
           if (classobj.Origin[ele]==originType):
              return ele

    def getOriginType(self):
        for ele in Numerable.Origin.keys():
           if (Numerable.Origin[ele]==self.OriginType):
              return ele

    def getOriginRecord(self):
        tname = self.getOriginType ()
        record = None
        try:
            exec("from %s import %s; record = %s.bring (%i)" % (tname, tname, tname, self.OriginNr))
        except Exception, err:
            pass
        return record

    def getOriginWindowNames(self):
        tname = self.getOriginType ()
        if not tname: return None
        return Record.getRecordWindowNames (tname)

    def getOriginWindowTypes(self):
        tname = self.getOriginType ()
        wNameList = Record.getRecordWindowNames (tname)
        if wNameList is None: return None
        types = []
        for name in wNameList:
            exec ("from %s import %s; t=%s" % (name,name,name))
            types.append (t)
        return types

    def save_fromGUI(self):
        res = ParentNumerable.save_fromGUI(self)
        if res and hasattr(self, "buffer"):
            if getApplicationType() == 1 or self.isLocal():
                postMessage("Registro Grabado. Debe recargar modulos para que los cambios tengan efecto.")
        return res

    def store(self, **kwargs):
        res = ParentNumerable.store(self,**kwargs)
        if not res: return res
        if hasattr(self.__class__, "tmp_buffer"): self.__class__.tmp_buffer.clear()
        if hasattr(self.__class__, "buffer"): self.__class__.buffer.clear()
        return res

    def save(self,**kwargs):
        res = ParentNumerable.save(self,**kwargs)
        if not res: return res
        if hasattr(self.__class__, "tmp_buffer"): self.__class__.tmp_buffer.clear()
        if hasattr(self.__class__, "buffer"): self.__class__.buffer.clear()
        return res

    def uniqueKey(self):
        return ['SerNr']

    def defaults(self):
        ParentNumerable.defaults(self)
        from Office import Office
        from LocalSettings import LocalSettings
        from User import User
        self.Office = Office.default()
        self.Department = User.getDepartment(currentUser())
        ls = LocalSettings.bring()
        self.Computer = ls.Computer
        self.TransDate = today()
        self.TransTime = now()

    def afterSaveCancelation(self, error):
        if self.isNew() and self.SerNr and not self.checkSerNr():
            self.SerNr = None
            self.ToSerNr = None

    def check(self):
        result = ParentNumerable.check(self)
        if not result: return result
        ftype = self.findFormType()
        if (ftype):
            self.FormType = ftype
        result = self.checkSerNr()
        if not result: return result
        result = self.checkPrintingRowsCount()
        if not result: return result
        result = self.checkOffice()
        if not result: return result
        result = self.checkComputer()
        return result

    def findFormType(self, additional_varspace={}):
        from FormTypeDef import FormTypeDef
        return FormTypeDef.getFormType(self, additional_varspace)

    def afterCopy(self):
        ParentNumerable.afterCopy(self)
        from User import User
        from LocalSettings import LocalSettings
        self.SerNr = None
        self.ToSerNr = None
        self.Office = User.getOffice(currentUser())
        self.Department = User.getDepartment(currentUser())
        ls = LocalSettings.bring()
        self.Computer = ls.Computer
        self.TransDate = today()
        self.TransTime = now()

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.SerNr)

    def getTransType(self):
        return self.name()

    def checkSerNr(self):
        DocType = None
        InvoiceType = None
        TransDate = self.TransDate
        if self.hasField("DocType"): DocType = self.DocType
        if self.hasField("InvoiceType"): InvoiceType = self.InvoiceType
        if (self.SerNr):
            if (self.oldFields("SerNr").getValue() != self.SerNr):
                return SerNrControl.CheckSerNr(self.getTransType(), self.Office, self.SerNr,self.name(), TransDate, DocType, InvoiceType, False, self.Computer, self.FormType)
            else:
                return SerNrControl.CheckSerNr(self.getTransType(), self.Office, self.SerNr,self.name(), TransDate, DocType, InvoiceType, True, self.Computer, self.FormType)
        else:
            sernr = SerNrControl.getNextSerNr(self)
            if not sernr: return sernr
            self.SerNr = sernr
        return True

    def checkPrintingRowsCount(self):
        rowscount = self.getPrintingRowsCount()
        if not rowscount: return True
        res = self.getDocument()  #ahora viene como una tupla (RecordDoc, ClassName)
        if isinstance(res, tuple):
            doccode = res[0]
            docclass = res[1]
        else:
            doccode = res
            docclass = res
        if not doccode: return True
        from DocumentSpec import DocumentSpec
        document = DocumentSpec.bring(doccode)
        if not document or not document.PrePrinted:
            self.ToSerNr = None
            return True
            #return ErrorResponse("The document could not be found")  # it is no crime not having defined any document!
        if not document.RowsPerPage: return True
        if document.RowsPerPage >= rowscount:
            self.ToSerNr = self.SerNr
            if self.ToSerNr == 0: self.ToSerNr = None #ToSerNr nunca debe ser 0
            return True
        else:
            pages_count = int(round(float(rowscount) / document.RowsPerPage + 0.49999))
            self.ToSerNr = self.SerNr + pages_count-1
            if self.ToSerNr == 0: self.ToSerNr = None #ToSerNr nunca debe ser 0
            return self.checkToSerNr()

    def checkToSerNr(self):
        for sernr in range(self.SerNr+1, self.ToSerNr+1):
            if self.exists(sernr): return self.FieldErrorResponse("El registro requiere que el rango de numeros %i-%i se encuentre disponible. Numero %i ocupado." % (self.SerNr, self.ToSerNr, sernr),"SerNr")
        return True

    def checkOffice(self):
        if not self.Office:
            return self.NONBLANKERR("Office")
        return True

    def checkComputer(self):
        from Office import Office
        if (not self.Computer):
            return self.FieldErrorResponse("The computer field cannot be blank, please check your local settings","Computer")
        return True

    def pasteSerNr(self):
        self.ToSerNr = self.SerNr
        if self.ToSerNr == 0: self.ToSerNr = None #ToSerNr nunca debe ser 0

    def getPrintingRowsCount(self):
        return 0

    @classmethod
    def bring(ObjectClass, sernr):
        obj = ObjectClass()
        obj.SerNr = sernr
        if sernr is not None and obj.load():
            return obj
        else:
            return ErrorResponse("The object doesnt exist")

    @classmethod
    def exists(ObjectClass, SerNr):
        self = ObjectClass()
        res = False
        if SerNr != None:
            query = Query()
            query.sql = "SELECT {SerNr} FROM [%s] WHERE {SerNr}=s|%s| " % (self.tableName(), SerNr)
            query.setLimit(1)
            if (query.open()):
                if (query.count() >= 1):
                    res = True
                query.close()
            else:
                res = False
        return res

    def getPortableId(self, useOldFields=False):
        kstring = ""
        kd = []
        for kn in self.uniqueKey():
            if (useOldFields):
                kd.append(str(self.oldFields(kn).getValue()))
            else:
                kd.append(str(self.fields(kn).getValue()))
        kstring = "|".join(kd)
        return kstring

    def setPortableId(self, id):
        kd = id.split("|")
        kl = self.uniqueKey()
        for ki in range(0,len(kd)):
            self.fields(kl[ki]).setValue(kd[ki])



    @classmethod
    def getList(objclass, **kwargs):
        res = {}
        idsmap = {}
        sernrslist = kwargs.get("SerNrsList", [])
        filloldfields = kwargs.get("SaveAllowed", False)
        if len(sernrslist):
            sernrs = ','.join(map(lambda x: str(x), sernrslist))
            q = Query()
            fnames = kwargs.get("FieldNames", None)
            fnamesstr = "*"
            dnames = kwargs.get("DetailNames", None)
            if dnames is None:
                dnames = objclass().detailNames()
            if fnames is not None:
                if 'internalId' not in fnames: fnames = list(fnames) + ['internalId']
                if 'SerNr' not in fnames: fnames = list(fnames) + ['SerNr']
                fnamesstr = ','.join(map(lambda x: "{%s}" % x, fnames))
            q.sql = "SELECT %s FROM [%s] WHERE {SerNr} in (%s) ORDER BY {internalId}" % (fnamesstr, objclass.__name__, sernrs)
            if q.open():
                if fnames is None: fnames = q.fieldNames()
                for rec in q:
                    obj = objclass()
                    obj.setNew(False)
                    for fn in fnames:
                        if obj.hasField(fn):
                            if not rec.fields(fn).isNone():
                                obj.fields(fn).setValue(rec.fields(fn).getValue())
                                if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                    for dn in dnames:
                        obj.details(dn).setMasterId(obj.internalId)
                    res[obj.SerNr] = obj
                    idsmap[obj.internalId] = obj
            internalids = ','.join(map(lambda x: str(x), idsmap.keys()))
            for dn in dnames:
                detailrecordname = objclass().details(dn).name()
                q = Query()
                q.sql = "SELECT row.* FROM [%s] row " % detailrecordname
                q.sql += "INNER JOIN [%s] t ON t.{internalId} = row.{masterId} " % objclass.__name__
                q.sql += "WHERE row.{masterId} in (%s) ORDER BY {masterId}, {rowNr}" % internalids
                detailclass = NewRecord(detailrecordname).__class__
                q.setResultClass(detailclass)
                if q.open():
                    for rec in q:
                        obj = detailclass()
                        obj.setNew(False)
                        detail = idsmap[rec.masterId].details(dn)
                        detail.append(obj)
                        for fn in rec.fieldNames():
                            if obj.hasField(fn):
                                if not rec.fields(fn).isNone():
                                    obj.fields(fn).setValue(rec.fields(fn).getValue())
                                    if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                        obj.setModified(False)
            for sernr, obj in res.items(): obj.setModified(False)
        return res

    @classmethod
    def getSerNrControlComment(objclass, record):
        if (not record.isSubClassOf(Numerable)):
            return ""

        squery = Query()
        squery.sql  = "SELECT * FROM SerNrControl "
        squery.sql += "WHERE?AND TransType = s|%s| " %record.name()

        if (squery.open()):
            for sline in squery:
                TrHs = True
                if (sline.Office and record.Office <> sline.Office):
                    TrHs = False
                if (sline.Computer and record.Computer <> sline.Computer):
                    TrHs = False
                if (not (sline.FromNr <= record.SerNr <= sline.ToNr)):
                    TrHs = False
                if (not (sline.FromDate <= record.TransDate <= sline.ToDate)):
                    TrHs = False
                if (hasattr(record,"InvoiceType")):
                    if (sline.InvoiceType in (0,1,2) and record.InvoiceType <> sline.InvoiceType):
                        TrHs = False
                if (hasattr(record,"DocType")):
                    if (sline.DocType <> -1 and record.DocType <> sline.DocType):
                        TrHs = False
                if (TrHs):
                    return sline.Comment
        return ""

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentNumerable.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if (not res): return res
        if (fieldname == "Department"):
            res = currentUserCanDo("CanModifyDepartment",True)
        elif (fieldname == "Office"):
            res = currentUserCanDo("CanModifyOffice",True)
        elif (fieldname == "Computer"):
            res = currentUserCanDo("CanModifyComputer",True)
        elif (fieldname == "TransDate"):
            res = currentUserCanDo("CanModifyTransDate",True)
        return res
