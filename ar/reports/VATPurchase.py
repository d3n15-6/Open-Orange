#encoding: utf-8
#only in spanish
from OpenOrange import *
from Report import *
from TaxSettings import TaxSettings
from OurSettings import OurSettings
from Currency import Currency
from Customer import Customer
import string

InvTypeSigns = [1,1,1]  # Fact,Nota Cred,Nota Deb
DocTypes = ["Fc","Nc","Nd"]

class VATPurchase(Report):

    def defaults(self):
        Report.defaults(self)
        record = self.getRecord()
        record.AddVATBases  = True
        record.Provinceflag = True
        record.PreIVAflag   = True
        record.WithOK = True
        record.Base = 0
        record.ShowInvDate = True
        record.NameLen = 32
        record.ShowPerception = True

    def run(self):
        self.getView().resize(1600,600)
        self.params = self.getRecord()
        if (not self.params.FromDate or not self.params.ToDate):
           return
        self.percentTable = self.getUsedVATPercents()
        self.vatcodes   = self.percentTable.keys()
        if self.params.FromPage:
            self.pageNr = self.params.FromPage
        else:
            self.pageNr = 1
        lines  = 0
        if self.params.OnPage:
            pagelines = self.params.OnPage
        else:
            pagelines = 999999
        provRetAmount = {}; provPerAmount = {}
        IVAperAmount = {}; GanperAmount = {}; GanretAmount = {}; IVAretAmount = {}
        vatacc = self.getVATAccounts()
        from TaxSettings import TaxSettings
        from OurSettings import OurSettings
        os = OurSettings()
        if not os.load() or not os.BaseCur1 or not os.BaseCur2:
            message("Faltan seteos de moneda en Datos de la Empresa")
            return False
        t = TaxSettings()
        t.load()
        taxacc = vatacc.keys();
        pivaacc = []; rivaacc = [];
        pingbr = []; ringbr = [];
        pganacc = []; rganacc = []
        impint = []

        # IVA
        for vacc in t.PercepIVA.split(","):
            taxacc.append(vacc)
            pivaacc.append(vacc)
            IVAperAmount[vacc] = [0.0,0.0]
          
        for vacc in t.RetenIVA.split(","):
            taxacc.append(vacc)
            rivaacc.append(vacc)
            IVAretAmount[vacc] = [0.0,0.0]

        # Ganancias
        taxacc.append(t.PercepGan)
        pganacc.append(t.PercepGan)
        GanperAmount[t.PercepGan] =  [0.0,0.0]

        taxacc.append(t.RetenGan)
        rganacc.append(t.RetenGan)
        GanretAmount[t.RetenGan] =  [0.0,0.0]

        if (self.params.SurplusVAT):
            taxacc.append(t.PLSurplusVATAcc)
        if (self.params.LuxTax):
            taxacc.append(t.LuxGoodTaxPLAcc)
            impint.append(t.LuxGoodTaxPLAcc)

        provs = Query()
        provs.sql  = "SELECT {Name},{IngBrutPerAcc},{IngBrutRetAcc} "
        provs.sql += "FROM [Province] "
        if provs.open():
            for p in provs:
              taxacc.append(p.IngBrutPerAcc)
              taxacc.append(p.IngBrutRetAcc)
              provRetAmount[p.IngBrutRetAcc] = 0.0
              provPerAmount[p.IngBrutPerAcc] = 0.0
        pingbr = provPerAmount.keys()
        ringbr = provRetAmount.keys()

        self.pivaacc = pivaacc
        self.rivaacc = rivaacc
        self.rganacc = rganacc
        self.pganacc = pganacc
        self.pingbr  = pingbr
        self.ringbr  = ringbr
        self.impint  = impint

        net={} #acumula netos indexados por codigo de iva
        tot={} #acumula totales indexados por codigo de iva
        iva={} #acumula iva de la factura indexado por codigo de iva

        ttot = {}
        tnet = {}
        tiva = {}
        ImportVat = []
        ImportVat.append({})
        ImportVat.append({})

        #acumuladores de totales en todas las facturas
        TotTot, TotIBP, TotIBR, TotIVAP,TotGanP, TotIVAR, TotGAN,TotSurPlusVAT,TotLuxTax = 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
        ImpInt = 0;

        query = self.getSQLQueryResumed()
        if(query.open()):
            FirstTime=True
            self.encabezado()

            #inicializo totales de columna
            for i in self.percentTable.keys():
                ttot[str(i)],tnet[str(i)],tiva[str(i)],net[str(i)],iva[str(i)],tot[str(i)],ImportVat[0][str(i)],ImportVat[1][str(i)] = 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
            gan,ibp,ibr,ivar,ivap,ganp,surplusvat,luxTax = 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0 #acumula retenciones y percepciones

            lastinv = 0
            for rec in query:
                f = self.curfactor(rec.Currency,rec.CurrencyRate,rec.BaseRate)
                RowNet = rec.RowNet * InvTypeSigns[rec.InvoiceType] * f
                RowTotal = rec.RowTotal * InvTypeSigns[rec.InvoiceType] * f

                if(lastinv<>rec.masterId and not FirstTime):
                    #mostrar este cambio a LO
                    f = self.curfactor(lastrec.Currency,lastrec.CurrencyRate,lastrec.BaseRate)
                    self.displayInvoice(lastrec,tot,net,iva,ibp,ivap,gan,ibr,ivar,ganp,surplusvat,luxTax,os)
                    TotTot += lastrec.Total * InvTypeSigns[lastrec.InvoiceType] * f
                    ImpInt += luxTax
                    lines += 1
                    #inicializo los acumuladores de valores
                    ivar,ganp,ivap,ibr,ibp,gan = 0,0,0,0,0,0
                    for i in self.vatcodes: ttot[i]+=tot[i]; tot[i] = 0.0
                    for i in self.vatcodes: tnet[i]+=net[i]; net[i] = 0.0
                    for i in self.vatcodes: tiva[i]+=iva[i]; iva[i] = 0.0
                    gan,ibp,ibr,ivar,ivap,ganp,surplusvat,luxTax =0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0     #acumula retenciones y percepciones
                    if (lines % pagelines) == 0:
                       if self.pageNr<>1:
                         self.displayFooter("Transporte",TotTot,tnet,tiva,TotIBP,TotIVAP,TotGAN,TotIBR,TotIVAR,TotGanP,TotSurPlusVAT,TotLuxTax)
                       self.encabezado()
                if not rec.Account in taxacc:
                    if (tot.has_key(rec.VATCode)):
                        # note depends on imput data
                        if self.percentTable[rec.VATCode]:
                          tasa = (self.percentTable[rec.VATCode]/100)
                          if (rec.Country != "ar"):
                             miva = 0
                          else:
                             #miva =  round(tasa * RowNet,2)
                             miva =  RowTotal - RowNet
                          #RowTotal = RowNet + miva
                        else:
                          miva = 0
                          RowTotal = RowNet
                        tot[rec.VATCode] += RowTotal
                        iva[rec.VATCode] += miva
                        net[rec.VATCode] += RowNet
                else:
                    # retenciones
                    if rec.Account in rganacc:
                        gan += RowNet; TotGAN += RowNet
                    elif rec.Account in rivaacc:
                        ivar += RowNet; TotIVAR += RowNet
                    elif rec.Account in ringbr:
                        ibr += RowNet; TotIBR += RowNet
                        provRetAmount[rec.Account] += RowNet
                    # percepciones
                    elif rec.Account in pivaacc:
                        ivap += RowNet; TotIVAP += RowNet
                        if (RowNet>0):
                          IVAperAmount[rec.Account][0] += RowNet
                        else:
                          IVAperAmount[rec.Account][1] += RowNet
                    elif rec.Account in pganacc:
                        ganp += RowNet; TotGanP += RowNet
                        if (RowNet>0):
                          GanperAmount[rec.Account][0] += RowNet
                        else:
                          GanperAmount[rec.Account][1] += RowNet
                    elif rec.Account in pingbr:
                        ibp += RowNet; TotIBP += RowNet
                        provPerAmount[rec.Account] += RowNet
                    elif rec.Account in vatacc.keys():
                    # importaciones
                        icode = vatacc[rec.Account]
                        iva[icode] = iva.get(icode, 0.0) + RowNet
                        if (RowNet>0):
                           ImportVat[0][icode] = ImportVat[0].get(icode, 0.0) + RowNet
                        else:
                           ImportVat[1][icode] = ImportVat[1].get(icode, 0.0) + RowNet
                    elif (rec.Account == t.LuxGoodTaxPLAcc):
                    # impuestos Internos
                        luxTax += RowNet
                        TotLuxTax += RowNet
                    elif (rec.Account == t.PLSurplusVATAcc):
                    # IVA No computable
                        surplusvat += RowNet; TotSurPlusVAT += RowNet

                FirstTime = False
                lastrec = rec
                lastinv = rec.masterId

            if not FirstTime:
                #mostrar este cambio a LO
                f = self.curfactor(lastrec.Currency,lastrec.CurrencyRate,lastrec.BaseRate)
                self.displayInvoice(lastrec,tot,net,iva,ibp,ivap,gan,ibr,ivar,ganp,surplusvat,luxTax,os)
                for i in self.vatcodes: ttot[i]+=tot[i]
                for i in self.vatcodes: tnet[i]+=net[i]
                for i in self.vatcodes: tiva[i]+=iva[i]
                TotTot += lastrec.Total * InvTypeSigns[lastrec.InvoiceType] * f
            self.displayFooter("Total",TotTot,tnet,tiva,TotIBP,TotIVAP,TotGAN,TotIBR,TotIVAR,TotGanP,TotSurPlusVAT,TotLuxTax)
            self.endTable()
            if self.params.PreIVAflag:
              from Account import Account
              self.startTable()
              self.startRow()
              self.addValue("",BGColor=self.DefaultBackColor)
              self.endRow()
              self.headerB("Cta Percepcion","Nombre","Monto (+)","Monto (-)")
              totplus,totmin = 0.00,0.00
              if t.PercepIVA.strip():
                  for vacc in map(lambda x: x.strip(), string.split(t.PercepIVA,",")):
                      self.startRow()
                      self.addValue(vacc)
                      ac = Account.bring(vacc)
                      self.addValue(ac.Name)
                      self.addValue(IVAperAmount[vacc][0] )
                      self.addValue(IVAperAmount[vacc][1] )
                      self.endRow()
                      totplus += IVAperAmount[vacc][0] 
                      totmin += IVAperAmount[vacc][1]
              self.startRow()
              self.addValue(t.PercepGan)
              acP = Account.bring(t.PercepGan)
              if acP:
                self.addValue(acP.Name)
              else:
                self.addValue("")
              if GanperAmount.has_key(t.PercepGan):
                  self.addValue(GanperAmount[t.PercepGan][0] )
                  self.addValue(GanperAmount[t.PercepGan][1] )
                  totplus += GanperAmount[t.PercepGan][0] 
                  totmin += GanperAmount[t.PercepGan][1]
              else:
                  self.addValue("")
                  self.addValue("")
              self.endRow()
              self.startRow(Style="B")
              self.addValue("Totales")
              self.addValue("")
              self.addValue(totplus)
              self.addValue(totmin)
              self.endRow()
              
              self.endTable()

              self.startTable()
              self.startRow()
              self.addValue("",BGColor=self.DefaultBackColor)
              self.endRow()
              self.headerB("IVA Importacion:","Monto (+)","Monto (-)")
              totPlus,totMin = 0.00,0.00
              for code in self.percentTable.keys():
                 if (self.percentTable[code]):
                    self.startRow()
                    self.addValue("Base (%s)" % str(self.percentTable[code]) )
                    self.addValue(ImportVat[0][code])
                    self.addValue(ImportVat[1][code])
                    self.endRow()
                    totPlus += ImportVat[0][code]
                    totMin += ImportVat[1][code]
              self.startRow(Style="B")
              self.addValue("Totales")
              self.addValue(totPlus)
              self.addValue(totMin)
              self.endRow()
              self.endTable()

              self.startTable()
              self.startRow()
              self.addValue("",BGColor=self.DefaultBackColor)
              self.endRow()
              self.startRow(Style="B")
              self.addValue(t.LuxGoodTaxPLAcc)
              self.addValue("Total Impuestos Internos:")
              self.addValue(ImpInt)
              self.endRow()
              self.endTable()

            if self.params.Provinceflag:
              totPerc,totRet = 0.00,0.00
              self.startTable()
              self.startRow()
              self.addValue("",BGColor=self.DefaultBackColor)
              self.endRow()
              self.startHeaderRow()
              self.addValue(tr("Province"))
              self.addValue(tr("Perception"))
              self.addValue(tr("Retention"))
              self.endHeaderRow()
              if provs.open():
                for p in provs:
                  if provPerAmount[p.IngBrutPerAcc] or provRetAmount[p.IngBrutRetAcc]:
                      self.startRow()
                      self.addValue(p.Name)
                      self.addValue(provPerAmount[p.IngBrutPerAcc])
                      self.addValue(provRetAmount[p.IngBrutRetAcc])
                      self.endRow()
                  totPerc += provPerAmount[p.IngBrutPerAcc]
                  totRet += provRetAmount[p.IngBrutRetAcc]
              self.startHeaderRow()
              self.addValue("Totales")
              self.addValue(totPerc)
              self.addValue(totRet)
              self.endHeaderRow()
              self.endTable()
            if self.params.BSMflag:
              self.showBSM()
            if self.params.Inscflag:
              self.showInscriptionStats(False)
            if self.params.Inscflag:
              self.showInscriptionStats(True)

    def LimitClause(self,query):
        # works on PostgreSQL as well
        if (self.params.Pages and self.params.OnPage and self.params.Pages):
          offset = (self.params.FromPage - 1) * self.params.OnPage # counting starts at 0 !
          rows = self.params.Pages * self.params.OnPage
          query.setLimit(int(rows),int(offset))
        return query

    def curfactor(self,curcode,crate,brate):
        specs = self.getRecord()
        cur = Currency.bring(curcode)
        (Base1,Base2) = cur.convert(1,crate,brate)
        if (specs.Base==0):
          return Base1
        else:
          return Base2

    def showBSM(self):
        Suplabels = ["Servicios","Mercaderia","Bienes"]
        table = {}
        for i in range(3):
          table[i] = {}
        query = Query()
        query.sql ="SELECT s.{PurchaseType},pir.{VATCode},SUM({RowNet}) AS Total, "
        query.sql+="{InvoiceType}\n"
        query.sql+="FROM [PurchaseInvoiceRow] pir \n"
        query.sql+="INNER JOIN [PurchaseInvoice] pi ON pi.{internalId}= pir.{masterId}\n"
        query.sql+="INNER JOIN [Supplier] s ON pi.{SupCode}= s.{Code}\n"
        query.sql+="WHERE?AND pi.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        query.sql+="WHERE?AND pi.{Status}=i|1|\n"
        query.sql+="WHERE?AND (pi.{Internalflag} = 0 OR pi.{Internalflag} IS NULL) "
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        if (self.params.Labels): query.sql += "WHERE?AND pi.{Labels} = s|%s|" % self.params.Labels
        if (self.params.ExLabels): query.sql += "WHERE?AND (pi.{Labels} <> s|%s| OR pi.{Labels} IS NULL) " % self.params.ExLabels
        query.sql+="GROUP BY s.{PurchaseType},pir.{VATCode}\n"
        if(query.open()):
          for r in query:
            table[r.PurchaseType][r.VATCode] = r.Total

        self.startTable()
        self.startHeaderRow()
        self.addValue("Codigo IVA",ColSpan=2)
        self.addValue("Porcentaje")
        self.addValue("Servicios",ColSpan=2)
        self.addValue("Mercaderia",ColSpan=2)
        self.addValue("Bienes de Uso",ColSpan=2)
        self.addValue("Totales",ColSpan=2)
        self.endHeaderRow()
        self.startRow(Style="B")
        self.addValue(tr("Code"))
        self.addValue(tr("Description"))
        self.addValue("")
        self.addValue("Neto")
        self.addValue("Impuesto")
        self.addValue("Neto")
        self.addValue("Impuesto")
        self.addValue("Neto")
        self.addValue("Impuesto")
        self.addValue("Neto")
        self.addValue("Impuesto")
        self.endHeaderRow()
        from VATCode import VATCode
        for x in self.percentTable.keys():
            self.startRow()
            self.addValue(x)
            vatcode = VATCode.bring(x)
            if not vatcode:
                log("No existe Cod de IVA %s" % x)
                self.addValue("")
            else:
                self.addValue(vatcode.Comment)
            self.addValue(self.percentTable[x])
            rownettotal = 0
            rowvattotal = 0
            for y in range(3):
                net = table[y].get(x,0.0)
                vat = net * (self.percentTable[x]/100)
                self.addValue(net)
                self.addValue(vat)
                rownettotal += net
                rowvattotal += vat
            self.addValue(rownettotal)
            self.addValue(rowvattotal)
            self.endRow()
        self.endTable()

    def showInscriptionStats(self,ncflag):     # Si hay facturas en moneda extranjero se genera una diff con el libro de iva de arriba
        table = {}

        for i in range(6):
          table[i] = {}
          for v in self.vatcodes:
            table[i][v] = 0.0

        query = Query()
        query.sql ="SELECT s.{TaxRegType},pir.{VATCode},SUM({RowNet}) AS Total, "
        query.sql+="{InvoiceType},[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate},[pi].{TransDate},[pi].{TransTime} \n"
        query.sql+="FROM [PurchaseInvoiceRow] pir \n"
        query.sql+="INNER JOIN [PurchaseInvoice] pi ON pi.{internalId}= pir.{masterId}\n"
        query.sql+="INNER JOIN [Supplier] s ON pi.{SupCode}= s.{Code}\n"
        query.sql+="WHERE?AND pi.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        if (self.params.Labels): query.sql += "WHERE?AND pi.{Labels} = s|%s|" % self.params.Labels
        if (self.params.ExLabels): query.sql += "WHERE?AND (pi.{Labels} <> s|%s| OR pi.{Labels} IS NULL) " % self.params.ExLabels
        query.sql+="WHERE?AND (pi.{Internalflag} = 0 OR pi.{Internalflag} IS NULL) "
        if ncflag:
            query.sql+="WHERE?AND pi.{InvoiceType}=i|1| \n"
            tag = "Debito Fiscal"
        else:
            query.sql+="WHERE?AND pi.{InvoiceType}<>i|1| \n"
            tag = "Credito Fiscal"
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        query.sql+="WHERE?AND (pir.Account NOT IN ('%s') " %("','".join(self.pivaacc))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.rivaacc))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.pganacc))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.rganacc))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.pingbr))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.ringbr))
        query.sql+="       AND pir.Account NOT IN ('%s') " %("','".join(self.impint))
        query.sql+=") "
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|0|\n"
        #query.sql+="GROUP BY s.{TaxRegType},pir.{VATCode}\n"
        query.sql+="GROUP BY s.{TaxRegType},pir.{VATCode},[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate}\n"
        
        if (query.open()):
            newquery  = Currency.processQueryResult(Currency.getBase1(), query, ("TaxRegType","VATCode",), ("Total",), "Currency", "CurrencyRate", "BaseRate", "TransDate", "TransTime")
            for r in newquery:
                table[r.TaxRegType][r.VATCode] += r.Total

        self.startTable()
        self.blankRow()
        self.startRow(Style="A")
        self.addValue("Total IVA: " + tag, ColSpan=3)
        self.endRow()
        self.startRow(Style="B")
        self.addValue("Codigo IVA")
        self.addValue("%")
        self.addValue("Descripcion")

        from VATCode import VATCode
        for i in range(6):
          self.addValue(Customer.TaxRegTypes[i])
        self.endRow()
        tot = {}
        for x in self.percentTable.keys():
          self.startRow()
          self.addValue(x)
          self.addValue(self.percentTable[x])
          vc = VATCode.bring(x)
          if vc:
            self.addValue(vc.Comment)
          else:
            self.addValue("")
          for y in range(6):
              if not y in tot.keys():
                tot[y] = 0.00
              self.addValue(table[y].get(x,0.0))
              tot[y] += table[y].get(x,0.0)
          self.endRow()
        self.startRow(Style="B")
        self.addValue("Totales")
        self.addValue("")
        self.addValue("")
        for y in tot.keys():
            self.addValue(tot[y])
        self.endRow()
        self.endTable()

    def getSQLQueryResumed(self):
        """ Always Select by Given date, but order by Invoice Date! """
        query = Query()
        query.sql ="SELECT {SerNr},{RowNet},{RowTotal},[pir].{VATCode},[pir].{Account},[pir].{masterId},[pi].{CAI}\n"
        query.sql+=",{InvoiceDate},{TransDate},{SupCode},{SupName},[pi].{TaxRegNr},{InvoiceNr}\n"
        query.sql+=",[s].{TaxRegType}\n"
        query.sql+=",[pi].{Country},{Total},{InvoiceType},[pi].{BaseRate},[pi].{CurrencyRate},[pi].Currency\n"
        query.sql+="FROM [PurchaseInvoiceRow] [pir]\n"
        query.sql+="INNER JOIN [PurchaseInvoice] [pi] ON [pi].{internalId}=[pir].{masterId}\n"
        query.sql+="INNER JOIN [Supplier] s ON [s].{Code}=[pi].{SupCode}\n"
        query.sql+="WHERE?AND pi.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        query.sql+="WHERE?AND (pi.{Internalflag} = 0 OR pi.{Internalflag} IS NULL) "
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        query.sql += self.SQLRangeFilter("s", "GroupCode", self.params.GroupCode)
        if (self.params.Labels): query.sql += "WHERE?AND pi.{Labels} = s|%s|" % self.params.Labels
        if (self.params.ExLabels): query.sql += "WHERE?AND (pi.{Labels} <> s|%s| OR pi.{Labels} IS NULL) " % self.params.ExLabels
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|0|\n"
        query.sql+="ORDER BY pi.{TransDate},[pir].{masterId},[pir].{internalId}\n" # necesary order by masterid
        #query = self.LimitClause(query)

        return query

    #************************************************************************************

    def getUsedVATPercents(self):
        ''' arma un diccionario con los codigos usados de iva y sus porcentajes'''
        col = {}
        q = Query()
        q.sql  = "SELECT distinct VATCode, Percent FROM PurchaseInvoiceRow "
        q.sql += "LEFT JOIN VATCode ON VATCode.Code = PurchaseInvoiceRow.VATCode "
        q.sql += "ORDER BY Percent asc "
        if(q.open()):
            for rec in q:
               col[rec.VATCode] = rec.Percent
        q.close()
        return col

    def getVATAccounts(self):
        ''' necesario para saber si iva import fue declarado'''
        # por cuenta registra que tipo de iva es
        col = {}
        q = Query()
        q.sql  = "SELECT Code, PurchVatAcc, Percent FROM VATCode "
        q.sql += "WHERE?AND ({Closed} IS NULL or {Closed} = 0) "
        if(q.open()):
            for rec in q:
               if (rec.Percent): col[rec.PurchVatAcc] = rec.Code
        q.close()
        return col

    #********************************************************************************

    def encabezado(self):
        record = self.getRecord()
        ts = TaxSettings.bring()
        os = OurSettings.bring()
        if self.pageNr!=1:
            if self.pageNr <> self.params.FromPage:
                self.endTable()
                    
        if self.pageNr!=1:
            self.addPageBreak()
           #self.endTable()
           
        self.startTable()
        self.startHeaderRow()
        self.addValue("%s %s"  % (os.Name,ts.TaxRegNr), ColSpan=5)
        self.endHeaderRow()
        self.startHeaderRow()
        #self.header("Libro IVA Compras, Fecha de Emision: %s, Pagina %d" % (str(today()),pageNr) )
        self.addValue("Libro IVA Compras, Pagina %d" % (self.pageNr), ColSpan=5)
        self.endHeaderRow()
        self.startHeaderRow()
        self.addValue("Desde: %s Hasta: %s" %(record.FromDate.strftime("%d/%m/%Y"),record.ToDate.strftime("%d/%m/%Y")),ColSpan=5)
        self.endHeaderRow()
        self.endTable()
        self.addHTML("<HR>")
        self.pageNr += 1
            
        self.startTable()
        self.startHeaderRow()
        self.addValue(tr("Date"))
        if self.params.ShowInvDate:
          self.addValue(tr("Invoice Date"))
        self.addValue(tr("Type"))
        self.addValue(tr("Nr."))
        if self.getRecord().ShowSupCode:
            self.addValue(tr("Code"))
        self.addValue(tr("Supplier"))
        self.addValue(tr("Tax Reg. Nr."))
        self.addValue(tr("VAT Cond."))
        if (self.params.CAIFlag):
          self.addValue("CAI")

        if (self.params.AddVATBases):
          if (self.params.AddVAT):
            self.addValue("Neto Gravado")
            self.addValue("IVA")
          else:
            self.addValue("Neto Gravado")
            for code in self.percentTable.keys():
              if (self.percentTable[code]):
                self.addValue("IVA (%s)" % str(self.percentTable[code]) )
        else:
          for code in self.percentTable.keys():
             if (self.percentTable[code]):
                self.addValue("Base (%s)" % str(self.percentTable[code]) )
                self.addValue("IVA")

        self.addValue("Exento")
        if (self.params.ShowPerception):
            self.addValue("Perc IVA")
        if (self.params.JoinIVAGan):
          self.addValue("Otras Perc.")
        else:
          if (self.params.ShowPerception):
              self.addValue("Perc IB")
              self.addValue("Perc Gan")
        if (self.params.ShowWithhold):
          self.addValue("Ret Gan")
          self.addValue("Ret IB")
          self.addValue("Ret IVA")
        if (self.params.SurplusVAT):
          self.addValue("IVA No Computable")
        if (self.params.LuxTax):
          self.addValue("Imp.Internos")
        self.addValue("Total")
        self.endHeaderRow()

    #********************************************************************************
    def displayFooter(self,Titulo,TotTot,tnet,tiva,TotIBP,TotIVAP,TotGAN,TotIBR,TotIVAR,TotGanP,TotSurPlusVAT,TotLuxTax):
        self.startHeaderRow()
        self.addValue(Titulo)
        if self.params.ShowInvDate:
          self.addValue("")
        if self.params.ShowSupCode:
          self.addValue("")
        self.addValue("")
        self.addValue("")
        self.addValue("")
        self.addValue("")
        self.addValue("")
        if (self.params.CAIFlag):
          self.addValue("")

        # Calculos
        base = 0; totiva = 0
        exento = 0
        for code in self.vatcodes:
          totiva  += tiva[code]
          if (self.percentTable[code]):
            base += tnet[code]
          else:
            exento += tnet[code]

        if (self.params.AddVATBases):
          if (self.params.AddVAT):
            self.addValue(base)
            self.addValue(totiva)
          else:
            self.addValue(base)
            for code in self.vatcodes:
              if (self.percentTable[code]):
                self.addValue(tiva[code])
        else:
          for code in self.vatcodes:
            if (self.percentTable[code]):
              self.addValue(tnet[code])
              self.addValue(tiva[code])
        self.addValue(exento)
        if (self.params.ShowPerception):
            self.addValue(TotIVAP)
        if (self.params.JoinIVAGan):
          self.addValue(TotIBP+TotGanP)
        else:
          if (self.params.ShowPerception):
              self.addValue(TotIBP)
              self.addValue(TotGanP)
        if (self.params.ShowWithhold):
          self.addValue(TotGAN)
          self.addValue(TotIBR)
          self.addValue(TotIVAR)
        if (self.params.SurplusVAT):
          self.addValue(TotSurPlusVAT)
        if (self.params.LuxTax):
            self.addValue(TotLuxTax)
        self.addValue(TotTot)
        self.endRow()
        #self.addPageBreak()            # cut page only if you export to hmtl and print from a browser

    def displayInvoice(self,lastrec,tot,net,iva,ibp,ivap,gan,ibr,ivar,ganp,surplusvat,luxTax,ourSettings):
        f = self.curfactor(lastrec.Currency,lastrec.CurrencyRate,lastrec.BaseRate)
        Total = lastrec.Total * InvTypeSigns[lastrec.InvoiceType]
        self.startRow()
        self.addValue(lastrec.TransDate)
        if self.params.ShowInvDate:       
            self.addValue(lastrec.InvoiceDate)
        self.addValue(DocTypes[lastrec.InvoiceType])
        self.addValue(lastrec.InvoiceNr,CallMethod="ZoomIn", Parameter = lastrec.SerNr,Wrap=False)
        if self.getRecord().ShowSupCode:
            self.addValue(lastrec.SupCode, Wrap=False)
        self.addValue(lastrec.SupName.title()[:self.params.NameLen],Wrap=False)
        self.addValue(lastrec.TaxRegNr, Wrap=False)
        self.addValue(Customer.TaxRegTypes[lastrec.TaxRegType], Wrap=False)

        if (self.params.CAIFlag):
            self.addValue(lastrec.CAI)
        # Calculos
        base = 0; totiva = 0;
        exento = 0
        for code in self.vatcodes:
          totiva  += iva[code]
          if (self.percentTable[code]):
            base += net[code]
          else:
            exento += net[code]

        if (self.params.AddVATBases):
          if (self.params.AddVAT):
            self.addValue(base)
            self.addValue(totiva)
          else:
            self.addValue(base)
            for code in self.vatcodes:
              if (self.percentTable[code]):
                self.addValue(iva[code])
        else:
          for code in self.vatcodes:
            if (self.percentTable[code]):
              self.addValue(net[code])
              self.addValue(iva[code])

        self.addValue(exento)
        if (self.params.ShowPerception):
            self.addValue(ivap)
        if (self.params.JoinIVAGan):
          self.addValue((ibp+ganp))
        else:
          if (self.params.ShowPerception):
            self.addValue(ibp)
            self.addValue(ganp)
        if (self.params.ShowWithhold):
          self.addValue(gan)
          self.addValue(ibr)
          self.addValue(ivar)
        if (self.params.SurplusVAT):
          self.addValue(surplusvat)
        if (self.params.LuxTax):
          self.addValue(luxTax)
        self.addValue(Total * f)
        self.endRow()

    def ZoomIn(self,param,value):
        from PurchaseInvoice import PurchaseInvoice
        from PurchaseInvoiceWindow import PurchaseInvoiceWindow
        pinv = PurchaseInvoice()
        pinv.SerNr = int(param)
        pinv.load()
        pinvw = PurchaseInvoiceWindow()
        pinvw.setRecord(pinv)
        pinvw.open()