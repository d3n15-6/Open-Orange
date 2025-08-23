#encoding: utf-8
from OpenOrange import *
from Payment import PaymentPayModeRow

ParentRetencion = SuperClass("Retencion","Master",__file__)
class Retencion(ParentRetencion):
    RetTypes = ["Ganancia","Ing.Brutos","IVA","Limpieza","SUSS","Security Agency", "Defraction", "Month VAT"]

    def updatePercepGroup(self, group, percent):   #Std ar
        """ updatePercepGroup (group,percent) -> None.
        Actualiza la alicuota perteneciente al grupo de percepcion dado en
        group al porcentaje dado en percent. Si el grupo no existe se crea."""
        updated=False
        for retRow in self.RetencionRows:
            if retRow.TaxGroup == group:
                retRow.Perc = float (percent)
                updated=True
        if not updated:
            retRow = RetencionRow ()
            retRow.TaxGroup = group
            retRow.Perc = percent
            self.RetencionRows.append(retRow)

    def updateRetencGroup(self, group, percent):   #Std ar
        #print "actualizando porcentaje para grupo %s a %f" % (group,percent)
        return self.updatePercepGroup(group,percent)



    def getHistPayments(self,SupCode,TransDate,Office=None, **kwargs):    #Std ar,py
        # net payments made the same month to a specific supplier
        # net implies discounting the part that covers taxes to be paid in the purchase inv.
        # note: issue might be resolved with a more sophisticated query but .. normally there arent many invoices anyway ..
        from PurchaseInvoice import PurchaseInvoice
        from TaxSettings import TaxSettings
        from Payment import Payment
        from VATCode import VATCode
        FromDate = StartOfMonth(TransDate)
        myPayMode = self.getPayMode()
        Witholdings = 0; netpayments = 0
        taxsett = TaxSettings.bring()
        q1 = Query()
        q1.sql  = "SELECT {SerNr} "
        q1.sql += "FROM [Payment] "
        q1.sql += "WHERE?AND {TransDate} BETWEEN d|%s| AND d|%s| " % (FromDate,TransDate)
        q1.sql += "WHERE?AND {SupCode} = s|%s| " % (SupCode) 
        q1.sql += "WHERE?AND ({Invalid} = i|0| OR {Invalid} IS NULL) "
        if Office and taxsett and taxsett.RetenOnlyPaymentOffice:
            q1.sql += "WHERE?AND ({Office} = s|%s|) " % Office
            
        # the actual payment is not approved: so dont select on the status
        if(q1.open()):
            pinvret = []
            for row in q1:
                paym = Payment.bring(row.SerNr)
                sup = paym.getSupCodeRecord()
                if sup.VATCode:
                    vc = VATCode.bring(sup.VATCode)
                    vatpercent = vc.Percent
                elif taxsett.VATCodePL:
                    vc = VATCode.bring(taxsett.VATCodePL)
                    vatpercent = vc.Percent
                else:
                    vatpercent = 21.0
                    message(tr("Parameters Missing!", "Tax Settings", "Default Purchase VAT Code"))
                for paymrow in paym.PayModes:
                    if (myPayMode == paymrow.PayMode):
                        Witholdings += paymrow.Amount
                for pi in paym.Invoices:
                    if kwargs.get("isVATMonth", None):
                        if pi.InvoiceNr:
                            if pi.InvoiceNr not in pinvret:
                                pinv = PurchaseInvoice.bring(pi.InvoiceNr)
                                netpayments += pinv.VatTotal
                                pinvret.append(pi.InvoiceNr)
                        else:
                            netpayments += pi.Amount - ( pi.Amount / (1+vatpercent/100)) 
                    else:
                        if (pi.InvoiceNr):                              # if downpayment the taxes are 0: fully incluide whole payment!
                            pinv = PurchaseInvoice.bring(pi.InvoiceNr)
                            factor = pinv.getNetoFactor(self)
                        else:
                            factor = (1.0 / (1+vatpercent/100.0))
                        netpayment = pi.Amount * factor
                        netpayments += netpayment
        return (netpayments,Witholdings)

    @classmethod
    def getLastInvSum(self, supcode, transdate):    #Std ar
        fromdate = addMonths(transdate,-11)
        fromdate = StartOfMonth(fromdate)
        #print fromdate
        todate = transdate
        iquery = Query()
        iquery.sql  = "SELECT PI.Total,PI.CurrencyRate,PI.BaseRate,PI.TransDate, PI.Currency "
        iquery.sql += "FROM PurchaseInvoice PI "
        iquery.sql += "WHERE?AND PI.InvoiceType = 0 "
        #iquery.sql += "WHERE?AND PI.OpenFlag = 1 "
        iquery.sql += "WHERE?AND PI.SupCode = s|%s| " %(supcode)
        iquery.sql += "WHERE?AND PI.InvoiceDate BETWEEN d|%s| AND d|%s| " %(fromdate,transdate)

        total = 0
        from Currency import Currency
        base1 = Currency.getBases()[0]
        if (iquery.open()):
            for pinv in iquery:
                total += Currency.convertTo(pinv.Total,pinv.CurrencyRate,pinv.BaseRate,pinv.Currency,base1,pinv.TransDate)
        return (base1,total)

    def GetWithholdingReductionPL(self,TransDate,SupCode):  #Std ar,py
        # <-- doIVA
        # <-- doGAN
        # <-- doSUSS
        for reducRow in self.Reductions:
            if (SupCode == reducRow.CompanyCode):
               if (TransDate > reducRow.StartDate) and (TransDate < reducRow.EndDate):
                  return reducRow.Percent
        return 0

    @classmethod
    def doVATPerception(objclass, salesTrans):
        from Customer import Customer
        cust = salesTrans.getCustCodeRecord()
        if (cust and cust.DocType == 0):
            ret = Retencion()
            ret.RetType = ret.VAT
            ret.Type = ret.PERCEPTION
            if (ret.load()):
                percep =  ret.CalcRet3(salesTrans.SubTotal, FTrans=salesTrans)
                if percep:
                    taxRowName = "%sTaxRow" %(salesTrans.__class__.__name__)
                    itr = NewRecord(taxRowName)
                    if (not ret.TaxCode):
                        itr.TaxCode = "PIVA"
                    else:
                        itr.TaxCode = ret.TaxCode
                    itr.Amount  = salesTrans.roundValue(percep)
                    salesTrans.Taxes.append(itr)

    @classmethod
    def doIIBBPerception(objclass, salesTrans):  #Std ar, py
        from Province import Province
        
        from TaxSettings import TaxSettings
        tset = TaxSettings.bring()
        
        pquery = Query()
        pquery.sql  = "SELECT P.Code FROM Province P "
        pquery.sql += "WHERE?AND (P.IIBBCalcType <> i|0| OR P.IIBBCalcType IS NOT NULL) "
        pquery.sql += "WHERE?AND (P.Closed = i|0| OR P.Closed IS NULL) " 

        delprovince = salesTrans.getAgent2PercepProvince()
        if (not salesTrans.CustCode or not delprovince):
            return 0
        cust = salesTrans.getCustCodeRecord() 
        if (cust.TaxReg2Type == cust.IIBBEXENTO): #Exento de Ingresos Brutos
            return 0
        #alert("well")
        isLocal = False
        salesTrans.HighRiskOK = False
        if (pquery.open()):
            if (pquery.count() == 1):
                isLocal = True
            if (pquery.count() == 0):
                message("Atención!!! La empresa es agente de percepción pero no tiene marcado ninguna provincia para percibir")
            for pcode in pquery:
                #alert("Procesando %s" %(pcode.Code))
                prov = Province.bring(pcode.Code)
                if ((isLocal and prov.Code == delprovince) or (not isLocal)):
                    if (prov.IIBBCalcType == 1):    #CAPITAL FEDERAL
                        if cust and cust.TaxRegType == 1: 
                            return # Para consumidor Final no se calcula
                        if (delprovince in cust.ExemptFromTaxIn):
                            continue
                        if (prov.Code != delprovince): 
                            continue
                        #PROGRAMACI?N DE PADR?N DE ALTO RIESGO
                        from IIBBHighRiskRegister import IIBBHighRiskRegister
                        iibbhr = IIBBHighRiskRegister.bring(cust.TaxRegNr.replace("-",""))
                        if (iibbhr):
                            taxRowName = "%sTaxRow" %(salesTrans.__class__.__name__)
                            itr = NewRecord(taxRowName)
                            itr.TaxCode = tset.IIBBHighRiskTaxCode
                            if (not tset.IIBBHighRiskTaxCode):
                                message("Falta Cod. Impuesto Alto Riesgo en Opciones de Impuestos")
                            percep = salesTrans.getToPerceptTotal() * (iibbhr.AliPercep / 100)
                            if (salesTrans.hasField("InvoiceType") and salesTrans.InvoiceType == 1):
                                percep = percep * -1
                            itr.Amount  = salesTrans.roundValue(percep)
                            salesTrans.Taxes.append(itr)
                            #alert("c1t")
                            salesTrans.HighRiskOK = True
                        else:
                            AmountPerRetTable = {}
                            if tset.NotUseItemPerceptions:
                                rowNet = 0
                                #for irow in salesTrans.Items:
                                #    rowNet += irow.RowNet
                                rowNet = salesTrans.getToPerceptTotal()
                                AmountPerRetTable[tset.IIBBTaxCFPerTable] = rowNet
                            else:
                                itemDic = {}
                                for irow in salesTrans.Items:
                                    #monotributo se calcula con iva incluido
                                    if cust.TaxRegType == 5:
                                        amount = irow.RowTotal
                                    else:
                                        amount = irow.RowNet
                                    itemDic[irow.ArtCode] = itemDic.get(irow.ArtCode,0) + amount
                                itemCodes = "','".join(itemDic.keys())
                                q = Query()
                                q.sql  = "SELECT i.{Code}, ip.{Retencion} "
                                q.sql += "FROM IIBBPercep ip "
                                q.sql += "INNER JOIN [Item] i ON i.TaxCode1 = ip.ItemTaxGroup "
                                q.sql += "WHERE?AND i.{Code} IN ('%s') " %(itemCodes)
                                q.sql += "WHERE?AND ip.{Province} = s|%s| " %(delprovince)
                                if(q.open()):
                                    if (q.count() == 0):
                                        message("No está configurada la Tabla de Cod. Actividades para Ingresos Brutos o Faltan los códigos en los Artículos.")
                                    for rec in q:
                                        AmountPerRetTable[rec.Retencion] = AmountPerRetTable.get(rec.Retencion,0) + itemDic[rec.Code]
                                    q.close()
                            percep = 0
                            for retCode in AmountPerRetTable.keys():
                                retTable = retCode                    # concat to find the right table
                                ret = Retencion.bring(retTable)
                                if ret:
                                    percep += ret.CalcRet2(abs(AmountPerRetTable[retTable]))
                                rpercent = cust.getTaxReduction(0,salesTrans.TransDate,prov.Code)
                                if (rpercent):
                                    percep = percep - (percep * rpercent / 100)
                                if (percep):
                                    taxRowName = "%sTaxRow" %(salesTrans.__class__.__name__)
                                    itr = NewRecord(taxRowName)
                                    itr.TaxCode = ret.TaxCode
                                    if (not ret.TaxCode):
                                        message("Falta Cod. de Impuestos de Venta tabla Retención %s" %(ret.Code))
                                    if (salesTrans.hasField("InvoiceType") and salesTrans.InvoiceType == 1):
                                        percep = percep * -1
                                    itr.Amount  = salesTrans.roundValue(percep)
                                    salesTrans.Taxes.append(itr)
                    elif (prov.IIBBCalcType == 2):  #PROVINCIA DE BUENOS AIRES
                        #INICIO RESOLUCION NORMATIVA A.R.B.A. 10/08 (P.B.A.)
                        #La Plata, 15 de febrero de 2008
                        #B.O.: 22/2/08 (P.B.A.)
                        if (salesTrans.name() == "Invoice"):
                            if (salesTrans.InvoiceType == salesTrans.CREDITNOTE and salesTrans.AppliesToInvoiceNr):
                                from Invoice import Invoice 
                                inv = Invoice.bring(salesTrans.AppliesToInvoiceNr)
                                if (inv):
                                    a = salesTrans.roundValue(abs(salesTrans.SubTotal + salesTrans.VatTotal))
                                    b = inv.roundValue(abs(inv.SubTotal + inv.VatTotal))
                                    if (not roundedZero(a-b)):
                                        return
                            elif (salesTrans.InvoiceType == salesTrans.CREDITNOTE and not salesTrans.AppliesToInvoiceNr):
                                return 
                        #FIN RESOLUCION NORMATIVA A.R.B.A. 10/08 (P.B.A.)
                        IIBBCondition = False
                        NotIsExempt = True
                        PercepInDelProvince = False
                        MayPercept = False
                        if (cust.TaxCat1):
                            taxGroup = cust.TaxCat1
                        else:
                            taxGroup = tset.IIBBTaxPerDefault
                        #Es Convenio o est? inscripto en la provincia que percibo
                        if ((cust.TaxReg2Type == cust.IIBBCONVENIO) or (cust.TaxReg2Type == cust.IIBBLOCAL and prov.Code in cust.TaxReg2Province)):
                            IIBBCondition = True
                        #Si es exento en la provincia de percepci?n
                        if (prov.Code in cust.ExemptFromTaxIn):
                            NotIsExempt = False
                        #Si la provincia de entrega es igual a la provincia de percepci?n
                        if (prov.Code == delprovince):
                            PercepInDelProvince = True
                        #Si no es exento y es local y no estoy entregando en la provincia que estoy calculando
                        if (NotIsExempt and cust.TaxReg2Type == cust.IIBBLOCAL and not (prov.Code in cust.TaxReg2Province)):
                            if (PercepInDelProvince):
                                MayPercept = True
                        else:
                            if (IIBBCondition and NotIsExempt):
                                if (PercepInDelProvince):
                                    MayPercept = True
                        if (MayPercept):
                            tptotal = abs(salesTrans.getToPerceptTotal())
                            rpercent = cust.getTaxReduction(0,salesTrans.TransDate,prov.Code)
                            if (rpercent):
                                tptotal = abs(tptotal - (tptotal * rpercent / 100))
                            ret = Retencion.bring(prov.PercepAgent2Code)
                            if (ret):
                                ppercent = ret.getAgent2PercepPercent(taxGroup)
                                ret.showMessages()
                                if (tptotal > ret.MinAmount):
                                    taxRowName = "%sTaxRow" % salesTrans.__class__.__name__
                                    trow = NewRecord(taxRowName)
                                    trow.TaxCode = ret.TaxCode
                                    trow.Amount = round(tptotal * ppercent / 100,2)
                                    if (salesTrans.hasField("InvoiceType") and salesTrans.InvoiceType == 1):
                                        trow.Amount = trow.Amount * -1
                                    salesTrans.Taxes.append(trow)
                    elif (prov.IIBBCalcType == 3):  #Provincia de TUCUMAN
                        percent = 0.0
                        if (cust.TaxReg2Type == cust.IIBBLOCAL):#Debe calcular siempre
                            if (prov.Code == delprovince): 
                                if (cust.TaxReg2Province == prov.Code and cust.TaxRegType == 0):
                                    percent = tset.IIBBLocalTucInscrip
                                elif (cust.TaxReg2Province == prov.Code and cust.TaxRegType != 0):
                                    percent = tset.IIBBLocalTucNoInscr
                        elif (cust.TaxReg2Type == cust.IIBBCONVENIO):
                            from IIBBAgreementPart import IIBBAgreementPart
                            apart = IIBBAgreementPart.bring(cust.Code,prov.Code)
                            if (apart):
                                if (apart.Coefficient > tset.IIBBTucAgreementCoef):
                                    percent = tset.IIBBTucAgreement
                        ret = Retencion.bring(prov.PercepAgent2Code)
                        if (ret):
                            tptotal = salesTrans.getToPerceptTotal()
                            rpercent = cust.getTaxReduction(0,salesTrans.TransDate,prov.Code)
                            if (rpercent):
                                tptotal = tptotal - (tptotal * rpercent / 100)
                            percept = abs(salesTrans.roundValue(tptotal * percent / 100))
                            if (percept > ret.MinAmount):
                                taxRowName = "%sTaxRow" % salesTrans.__class__.__name__
                                trow = NewRecord(taxRowName)
                                trow.TaxCode = ret.TaxCode
                                trow.Amount = salesTrans.roundValue(percept)
                                if (salesTrans.hasField("InvoiceType") and salesTrans.InvoiceType == 1):
                                    trow.Amount = trow.Amount * -1
                                salesTrans.Taxes.append(trow)
                    elif (prov.IIBBCalcType == 4):  #Provincia de SAN LUIS
                        percent = 0.0
                        if (cust.TaxReg2Type == cust.IIBBLOCAL):#Debe calcular siempre
                            if (prov.Code == delprovince): 
                                if (cust.TaxReg2Province == prov.Code and cust.TaxRegType == 0):
                                    percent = tset.IIBBLocalSLInscrip
                                elif (cust.TaxReg2Province == prov.Code and cust.TaxRegType != 0):
                                    percent = tset.IIBBLocalSLNoInscr
                        elif (cust.TaxReg2Type == cust.IIBBCONVENIO):
                            from IIBBAgreementPart import IIBBAgreementPart
                            apart = IIBBAgreementPart.bring(cust.Code,prov.Code)
                            if (apart):
                                if (apart.Coefficient > tset.IIBBSLAgreementCoef):
                                    percent = tset.IIBBSLAgreement
                        ret = Retencion.bring(prov.PercepAgent2Code)
                        if (ret):
                            tptotal = salesTrans.getToPerceptTotal()
                            rpercent = cust.getTaxReduction(0,salesTrans.TransDate,prov.Code)
                            if (rpercent):
                                tptotal = tptotal - (tptotal * rpercent / 100)
                            percept = abs(salesTrans.roundValue(tptotal * percent / 100))
                            if (percept > ret.MinAmount):
                                taxRowName = "%sTaxRow" % salesTrans.__class__.__name__
                                trow = NewRecord(taxRowName)
                                trow.TaxCode = ret.TaxCode
                                trow.Amount = salesTrans.roundValue(percept)
                                if (salesTrans.hasField("InvoiceType") and salesTrans.InvoiceType == 1):
                                    trow.Amount = trow.Amount * -1
                                salesTrans.Taxes.append(trow)



    def getAgent2PercepPercent(self, pcode):    #Std ar,py
        if (not pcode):
            self.appendMessage('No existe grupo de percepción por defecto. <BR> Controle Opciones de Impuestos')
        for pline in self.RetencionRows:
            if (pcode == pline.TaxGroup):
                return pline.Perc
        return 0.0

    def doIVA(self, **kwargs):  
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []

        # First payment allways has to BE the calculated withholding !
        # Partial first payments are not allowed
        from Supplier import Supplier
        sup = Supplier.bring(SupCode)
        retiva = 0
        Coef = 1
        if (sup.TaxRegType != 5):
            from PurchaseInvoice import PurchaseInvoice
            retiva= 0;
            for invrow in FTrans.Invoices:
                pi = PurchaseInvoice.bring(invrow.InvoiceNr)
                if not pi: continue
                if (invrow.Amount<0):
                    Coef= -1
                else:
                    Coef= 1
                MPaid = pi.Total - pi.Saldo * Coef
                if ((MPaid==0) and (invrow.InvoiceNr)):
                    retiva +=  self.CalcRet3(pi.VatTotal, FTrans=FTrans)
                    Reduc = self.GetWithholdingReductionPL(TransDate,SupCode)
                    if (Reduc):
                        retiva += (retiva*((100-Reduc)/100))
            if (retiva * Coef > 0):
                rec = Record()
                rec.Amount = retiva * Coef
                retres.append(rec)
        else:
            cur,bimp = self.getLastInvSum(SupCode,TransDate)
            if (bimp != 0):
                from TRT5Settings import TRT5Settings
                exceed = TRT5Settings.exceedSupplierLimit(SupCode,cur,bimp)
                if (exceed or sup.TRT5Retention):
                    for iline in FTrans.Invoices:
                        retiva = self.CalcRet3(iline.InvoiceTotal, FTrans=FTrans)
                        retiva = FTrans.roundValue(retiva)
                        if (retiva * Coef > 0):
                            from PurchaseInvoice import PurchaseInvoice
                            pinv = PurchaseInvoice.bring(iline.InvoiceNr)
                            if (pinv):
                                oldret = pinv.getOldWithholding(self.RetType,self.Type)
                                retiva -= oldret
                        if (retiva * Coef > 0):
                            rec = Record()
                            rec.Amount = retiva * Coef
                            rec.InvoiceNr = iline.InvoiceNr
                            retres.append(rec)
        return retres

    def doGAN(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []
        
        from Supplier import Supplier
        sup = Supplier.bring(SupCode)
        retgan = 0
        Coef = 1
        if (sup.TaxRegType != 5):
            (tt,yaRet) = self.getHistPayments(SupCode,TransDate, Office)
            retgan = self.CalcRet3(tt, FTrans=FTrans)
            retgan = FTrans.roundValue(retgan - yaRet)
            Reduc = self.GetWithholdingReductionPL(TransDate,SupCode)
            if (Reduc):
                retgan = retgan*((100-Reduc)/100)
            if (retgan * Coef > 0):
                rec = Record()
                rec.Amount = retgan * Coef
                retres.append(rec)
        else:
            cur,bimp = self.getLastInvSum(SupCode,TransDate)
            if (bimp != 0):
                from TRT5Settings import TRT5Settings
                exceed = TRT5Settings.exceedSupplierLimit(SupCode,cur,bimp)
                if (exceed or sup.TRT5Retention):
                    for iline in FTrans.Invoices:
                        if (iline.InvoiceNr):
                            retgan = self.CalcRet3(iline.Amount, FTrans=FTrans)
                            if (retgan * Coef > 0):
                                from PurchaseInvoice import PurchaseInvoice
                                pinv = PurchaseInvoice.bring(iline.InvoiceNr)
                                if (pinv):
                                    oldret = pinv.getOldWithholding(self.RetType,self.Type)
                                    retgan -= oldret
                            if (retgan * Coef > 0):
                                retgan = FTrans.roundValue(retgan)
                                rec = Record()
                                rec.Amount = retgan * Coef
                                rec.InvoiceNr = iline.InvoiceNr
                                retres.append(rec)
        return retres

    def doIBR(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []

        from Supplier import Supplier
        from PurchaseInvoice import PurchaseInvoice
        from TaxSettings import TaxSettings
        from VATCode import VATCode
        ts = TaxSettings.bring()
        s = Supplier.bring(SupCode)
        TaxCat = s.TaxCat1
        if (not s.TaxCat1):
            TaxCat = ts.IIBBTaxRetDefault
        from Province import Province
        prov = Province.bring(s.ProvinceCode)    # la provinca del proveedor !!!
        MPaid = 0.0
        taxfact = 0
        for invrow in FTrans.Invoices:
            if s and s.VATCode:
                vc = VATCode.bring(s.VATCode)
                vatpercent = vc.Percent
            elif ts and ts.VATCodePL:
                vc = VATCode.bring(ts.VATCodePL)
                vatpercent = vc.Percent
            else:
                message(tr("Parameters Missing!", "Tax Settings", "Default Purchase VAT Code"))
                vatpercent = 21.0

            if invrow.InvoiceNr:
                pi = PurchaseInvoice.bring(invrow.InvoiceNr)
                taxfact = pi.getNetoFactor(self)
            else:
                if (s.TaxRegType == 5):   # monotributista
                    taxfact = 1.0
                else:
                    taxfact = (1.0 / (1+vatpercent/100.0))
            Coef = 1  # Comento esta parte porque si la idea es no cobrar retenciones a las NC. Al multiplicarlas por -1 la estoy sumando. JIC
            #if (invrow.Amount<0):
            #  Coef= -1
            #else:
            #  Coef= 1
            MPaid += taxfact * invrow.Amount * Coef
        #Se comenta lo siguiente ya que es algo que puede configurarse
        #if (MPaid < 400.00): 
        #    if (s.ProvinceCode == "BSAS"):
        #        return []
        retibr = self.CalcRet2(MPaid,TaxCat) # vuelve monto neg

        if (retibr > 0):
            rec = Record()
            rec.Amount = retibr
            retres.append(rec)
        return retres

    def doREL(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []

        # Rentencion Empresas de Limpieza
        (tt,yaRet) = self.getHistPayments(SupCode,TransDate)
        retrel = self.CalcRet3(tt, FTrans=FTrans)
        retrel = retrel - yaRet
        Reduc = self.GetWithholdingReductionPL(TransDate,SupCode)
        Coef = 1
        if (Reduc):
            retrel = retrel*((100-Reduc)/100)

        if (retrel * Coef > 0):
            rec = Record()
            rec.Amount = retrel * Coef
            retres.append(rec)
        return retres

    def doSUSS(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []

        # Rentencion SUSS se calcula igual que GAN
        (tt,yaRet) = self.getHistPayments(SupCode,TransDate)
        retsuss = self.CalcRet3(tt, FTrans=FTrans)
        retsuss = FTrans.roundValue(retsuss - yaRet)

        if (retsuss > 0):
            rec = Record()
            rec.Amount = retsuss
            retres.append(rec)
        return retres

    def doSEG(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []

        # Rentencion SEG (AGENCIAS DE SEGURIDAD) se calcula igual que SUS
        (tt,yaRet) = self.getHistPayments(SupCode,TransDate)
        retseg = self.CalcRet3(tt, FTrans=FTrans)
        retseg = FTrans.roundValue(retseg - yaRet)

        if (retseg > 0):
            rec = Record()
            rec.Amount = retseg
            retres.append(rec)
        return retres

    def doVATMonth(self, **kwargs):
        FTrans = kwargs.get("FTrans",None)
        TransDate = FTrans.TransDate
        Office = FTrans.Office
        SupCode = FTrans.SupCode
        Amount = kwargs.get("Amount",0)
        retres = []
        
        from Supplier import Supplier
        sup = Supplier.bring(SupCode)
        retgan = 0
        Coef = 1
        if (sup.TaxRegType != 5):
            (tt,yaRet) = self.getHistPayments(SupCode,TransDate, Office, isVATMonth=True)
            retgan = self.CalcRet3(tt, FTrans=FTrans)
            retgan = FTrans.roundValue(retgan - yaRet)
            Reduc = self.GetWithholdingReductionPL(TransDate,SupCode)
            if (Reduc):
                retgan = retgan*((100-Reduc)/100)
            if (retgan * Coef > 0):
                rec = Record()
                rec.Amount = retgan * Coef
                retres.append(rec)
        return retres

ParentRetencionRow = SuperClass("RetencionRow","Record",__file__)
class RetencionRow(ParentRetencionRow):
    pass

ParentRetencionAffectedAccRow = SuperClass("RetencionAffectedAccRow","Record",__file__)
class RetencionAffectedAccRow(ParentRetencionAffectedAccRow):

    def pasteAccount(self, record):
        from Account import Account
        acc = Account.bring(self.Account)
        if (acc):
            self.Name = acc.Name
        else:
            self.Name = ""
