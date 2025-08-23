#encoding: utf-8
#only in spanish
from OpenOrange import *
from Report import Report
from TaxSettings import TaxSettings
from Customer import Customer
from OurSettings import OurSettings
from Invoice import Invoice
from VATCode import VATCode
from ItemTaxGroup import ItemTaxGroup
from Currency import Currency

class VATSales(Report):
    InvTypeSigns = [1,1,1]  # Fact,Nota Cred,Nota Deb
    InvTypeNames = ["Fc","Nc","Nd"]

    def defaults(self):
        Report.defaults(self)
        specs = self.getRecord()
        specs.AddVAT  = False
        specs.AddVATBases = True
        specs.WithOK = True
        specs.DocType = 6
        specs.Base = 0
        specs.NameLen = 32

    def showInscriptionStats(self,ncflag):
        table = {}
        specs = self.getRecord()
        for i in range(10):
          table[i] = {}
        query = Query()
        query.sql ="SELECT [s].{TaxRegType}, [pir].{VATCode}, SUM({RowNet} * IF({InvoiceType} = 1,-1,1)) AS {Total}, "
        query.sql+="{InvoiceType} ,[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate},[pi].{TransDate},[pi].{TransTime}, [pi].{CustCode} \n"
        query.sql+="FROM [InvoiceItemRow] pir \n"
        query.sql+="INNER JOIN [Invoice] pi ON pi.{internalId}= pir.{masterId}\n"
        query.sql+="INNER JOIN [Customer] s ON pi.{CustCode}= s.{Code}\n"
        query.sql+="WHERE?AND pi.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql+="WHERE?AND pir.{VATCode} IS NOT NULL \n"
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        if (specs.POSCode): query.sql += "WHERE?AND pi.{POSCode} = s|%s| \n" % specs.POSCode
        if (specs.DocType<>6):
          query.sql+="WHERE?AND pi.{DocType}=i|%i| \n" % specs.DocType
        if ncflag:
          query.sql+="WHERE?AND pi.{InvoiceType}=i|1| \n"
        else:
          query.sql+="WHERE?AND pi.{InvoiceType}<>i|1| \n"
        query.sql+="WHERE?AND (pi.{Internalflag} = 0 OR pi.{Internalflag} IS NULL) "
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|0|\n"
        query.sql+="GROUP BY s.{TaxRegType},pir.{VATCode},[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate}\n"
        if(query.open()):
            #esta funcion convierte la moneda del query
            newquery  = Currency.processQueryResult(Currency.getBase1(), query, ("TaxRegType","VATCode",), ("Total",), "Currency", "CurrencyRate", "BaseRate", "TransDate", "TransTime")
            for r in newquery:
                table[r.TaxRegType][r.VATCode] = r.Total
        self.startTable()
        self.startRow(Style="B")
        self.addValue("Codigo IVA")
        self.addValue("%")
        self.addValue("Descr.")
        for i in range(7):
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
            for y in range(7):
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

    def getUsedVATPercents(self):
        ''' arma un diccionario con los codigos usados de iva y sus porcentajes'''
        col = {}
        q = Query()
        q.sql  = "SELECT distinct VATCode, Percent FROM InvoiceItemRow "
        q.sql += "INNER JOIN VATCode ON VATCode.Code = InvoiceItemRow.VATCode "
        q.sql += "ORDER BY Percent asc "
        if(q.open()):
            for rec in q:
               col[rec.VATCode] = rec.Percent
        q.close()
        return col

    def getUsedItemTaxGroup(self):
        ''' arma un diccionario con los codigos usados de percepcion de iibb'''
        col = {}
        q = Query()
        q.sql  = "SELECT distinct itg.Code, itg.Name FROM InvoiceItemRow iir "
        q.sql += "INNER JOIN Item it ON it.Code = iir.ArtCode "
        q.sql += "INNER JOIN ItemTaxGroup itg ON itg.Code = it.TaxCode1 "
        q.sql += "ORDER BY itg.Code asc "
        if(q.open()):
            for rec in q:
               col[rec.Code] = rec.Name
        q.close()
        return col

    def encabezado(self):
        ts = TaxSettings.bring()
        os = OurSettings.bring()
        if self.pageNr<>1:
            if self.pageNr <> self.params.FromPage:
                if self.pageNr <> self.params.FromPage:
                    self.endTable()
                self.addPageBreak()     # cut page only if you export to hmtl and print from a browser
        self.startTable()
        self.startHeaderRow()
        self.addValue("%s %s"  % (os.Name,ts.TaxRegNr), ColSpan=5)
        self.endHeaderRow()
        self.startHeaderRow()
        self.addValue("Libro IVA Ventas, Pagina %d" % (self.pageNr), ColSpan=5)
        self.endHeaderRow()
        self.startHeaderRow()
        self.addValue("Desde:" + str(self.getRecord().FromDate)  + " Hasta: " + str(self.getRecord().ToDate), ColSpan=5)
        self.endHeaderRow()
        self.endTable()
        self.addHTML("<HR><BR><BR>")
        self.pageNr += 1

        self.startTable()

        self.startHeaderRow()
        self.addValue(tr("Date"))
        self.addValue(tr("Doc"))
        self.addValue(tr("Type"))
        self.addValue(tr("Nr."))
        if self.getRecord().ShowCustCode:
            self.addValue(tr("Code"))
        self.addValue(tr("Customer"))
        self.addValue(tr("Tax Reg.Nr."))
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
        if (self.params.LuxTax):
            self.addValue("Imp.Int.")
        if (self.params.IncludePercep):
            self.addValue("Percep.")
        self.addValue("Total")
        self.endHeaderRow()

    def curfactor(self,curcode,crate,brate):
        specs = self.getRecord()
        cur = Currency.bring(curcode)
        return cur.convertToBase(1,crate,brate,specs.Base)

    def run(self):
        self.invoiceList = []
        self.emisorResume = {}
        self.getView().resize(1000,600)
        self.params = self.getRecord()
        if (not self.params.FromDate) or (not self.params.ToDate):
            message("Combinación de Parámetros No Permitida")
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

        neto,lux = 0.0,0.0
        FirstTime=True
        net={} #acumula netos indexados por codigo de iva
        tot={} #acumula totales indexados por codigo de iva
        iva={} #acumula iva de la factura indexado por codigo de iva
        tnet = {}
        tiva = {}
        ttot = {}
        tlux = 0.0
        self.TotTot = 0.0;   self.TotTax = 0.0

        query = Query()
        query.sql  = "SELECT Invrow.{masterId}, Invrow.{VATCode}, Inv.{TotalTax}, Inv.{CustCode},Inv.{CustName}, Inv.{Invalid},Inv.{SerNr}, \n"
        query.sql += "Inv.{TaxRegType},Inv.{TransDate}, Inv.{DocType},Inv.{DelProvinceCode},{Total},{InvoiceType}, \n"
        query.sql += "Inv.{OfficialSerNr},Inv.{TaxRegNr},Inv.{internalId}, \n"
        query.sql += "Inv.{CurrencyRate},Inv.{BaseRate},Inv.{Currency}, \n"         # para fact en USD
        query.sql += "Inv.{TotalTax}, Inv.{Office}, Inv.{Comment}, Inv.{SubTotal}, Inv.{VATTotal}, Inv.PrintFormat, \n"
        query.sql += "(SELECT {CAI} FROM [SalesCAI] [SC] WHERE [Inv].{SerNr} > [SC].{SerNr} AND [Inv].{TransDate} < [SC].{DueDate} LIMIT 1) as {CAI}, \n"
        #query.sql += "I.ItemGroup, " query.sql += "
        query.sql += "ROUND(SUM({RowTotal}),8) AS RowTotal, ROUND(SUM({RowNet}),8) AS RowNet,SUM({LuxGoodTax}) AS LuxGoodTax \n"
        query.sql += "FROM [Invoice] Inv \n "
        query.sql += "LEFT JOIN [InvoiceItemRow] Invrow ON Inv.{internalId}=Invrow.{masterId} \n"
        #query.sql += "INNER JOIN Item I ON Invrow.ArtCode = I.Code "   query.sql += "
        #query.sql += "WHERE?AND Invrow.{ArtCode}<>'' "
        query.sql += "WHERE?AND Inv.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql += self.SQLRangeFilter("Inv", "Office", self.params.Office)
        if (self.params.POSCode): query.sql += "WHERE?AND Inv.{POSCode} = s|%s| \n" % self.params.POSCode
        if (self.params.DocType<>6):
          query.sql+="WHERE?AND [Inv].{DocType}=i|%i| \n" % self.params.DocType
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [Inv].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [Inv].{Status} = i|0|\n"
        query.sql += "WHERE?AND ([Inv].{Internalflag} = 0 OR [Inv].{Internalflag} IS NULL) "
        #query.sql += "WHERE?AND Inv.SerNr = 105109514 " #for debug
        #query.sql += "GROUP BY I.ItemGroup, Invrow.{VATCode},Invrow.{masterId} \n" #for debug
        query.sql += "GROUP BY Invrow.{VATCode},Invrow.{masterId} \n"
        query.sql += "ORDER BY Inv.[TransDate], Inv.{OfficialSerNr},{masterId}\n"
        if (query.open()):
            lines=0
            provPerAmount = {}
            self.encabezado()
            for i in self.percentTable.keys():
                ttot[str(i)],tnet[str(i)],tiva[str(i)],net[str(i)],iva[str(i)],tot[str(i)] = 0.0,0.0,0.0,0.0,0.0,0.0
            lastinv = 0
            #lastig = None
            for rec in query:
                if rec.SerNr not in self.invoiceList:
                    self.invoiceList.append(str(rec.SerNr))
                cur = Currency.bring(rec.Currency)
                RowNet     = cur.convertToBase(rec.RowNet,rec.CurrencyRate,rec.BaseRate,self.params.Base)
                RowTotal   = cur.convertToBase(rec.RowTotal,rec.CurrencyRate,rec.BaseRate,self.params.Base)
                LuxGoodTax = cur.convertToBase(rec.LuxGoodTax,rec.CurrencyRate,rec.BaseRate,self.params.Base)
                TotalTax   = cur.convertToBase(rec.TotalTax,rec.CurrencyRate,rec.BaseRate,self.params.Base)
                #if ((lastinv <> rec.masterId or lastig != rec.ItemGroup ) and not FirstTime):
                if (lastinv <> rec.masterId and not FirstTime):
                    if len(net) == 1 and lastrec.PrintFormat == 2: 
                        #correccion para facturas que agrupan por grupo de articulo y tienen diferencias de centavos en los totales netos y montos de iva
                        net = dict([(k,lastrec.SubTotal) for k in iva.keys()])
                        iva = dict([(k,lastrec.VATTotal) for k in iva.keys()])
                    self.displayInvoice(lastrec,tot,net,iva,lux)
                    lines += 1
                    if (not lastrec.Invalid):
                        for i in self.vatcodes: 
                            ttot[i]+=tot[i]
                            tot[i] = 0.0
                        for i in self.vatcodes: 
                            tnet[i]+=net[i]
                            net[i] = 0.0
                        for i in self.vatcodes: 
                            tiva[i]+=iva[i]
                            iva[i] = 0.0
                        tlux += lux; lux = 0.0
                        provPerAmount[rec.DelProvinceCode] = provPerAmount.get(rec.DelProvinceCode,0) + TotalTax
                        neto = 0.0
                    else: #initialize in zero
                        for i in self.vatcodes: 
                            tot[i] = 0.0
                        for i in self.vatcodes: 
                            net[i] = 0.0
                        for i in self.vatcodes: 
                            iva[i] = 0.0
                        neto,lux = 0.0,0.0
                    if (lines % pagelines) == 0:
                        if (self.pageNr<>1):
                            self.displayFooter("Transporte",self.TotTot,self.TotTax,tnet,tiva,tlux)
                        self.encabezado()
                    #lastig = rec.ItemGroup
                miva = RowTotal - RowNet - LuxGoodTax #(RowNet * self.percentTable[rec.VATCode]/100)
                mnet = RowNet
                mlux = LuxGoodTax
                #PEQUEÑO PARCHE PARA CUANDO EL IVA POR ARTICULOS AGRUPADOS NO DA IGUAL QUE LA FACTURA
                if ((abs(RowNet) > abs(RowTotal)) or (RowTotal > 0.0 and RowNet < 0.0) or (RowNet == 0.0 and abs(miva) > 0.0)):
                    #alert([RowNet,RowTotal])
                    mnet = RowTotal
                    miva = 0.0
                try:
                    tot[rec.VATCode] += mnet + miva
                    iva[rec.VATCode] += miva
                    net[rec.VATCode] += mnet
                    lux += mlux
                except:
                    if rec.VATCode:
                        message("La factura %s contiene un codigo de iva inexistente: '%s'" % (rec.SerNr, rec.VATCode))
                    else:
                        pass # comment lines and empty invoice lines of credit notes with percepciones
                neto += mnet
                FirstTime = False
                lastrec = rec
                lastinv = rec.masterId
            query.close()
            if not FirstTime:
               self.displayInvoice(lastrec,tot,net,iva,lux)
               if (not lastrec.Invalid):
                  for i in self.vatcodes: ttot[i]+=tot[i];
                  for i in self.vatcodes: tnet[i]+=net[i];
                  for i in self.vatcodes: tiva[i]+=iva[i];
                  tlux += lux
                  provPerAmount[rec.DelProvinceCode] = provPerAmount.get(rec.DelProvinceCode,0) + TotalTax
                  neto = 0.00

            self.displayFooter("Total",self.TotTot,self.TotTax,tnet,tiva,tlux)
            self.endTable()
            self.addHTML("<HR><br>")
            if self.params.Inscflag:
                self.startTable()
                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()
                self.startRow(Style="B")
                self.addValue(u"Resumen dÃ©bitos/crÃ©ditos", ColSpan=5)
                self.endRow()
                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()
                self.startRow(Style="A")
                self.addValue("VAT Debt", ColSpan=5)
                self.endRow()
                self.endTable()
                self.showInscriptionStats(False)

            if self.params.Inscflag:
                self.startTable()
                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()
                self.startRow(Style="A")
                self.addValue("VAT Credit", ColSpan=5)
                self.endRow()
                self.endTable()
                self.showInscriptionStats(True)
            if self.params.Provinceflag:
                self.printprovPerResume()
            if self.params.IncludeActivities:
                self.startTable()
                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()

                self.startRow(Style="B")
                self.addValue("Resumen Actividades", ColSpan=3)
                self.endRow()

                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()

                self.startRow(Style="A")
                self.addValue("Debitos", ColSpan=3)
                self.endRow()

                self.printCategoryPerResume(False)
                self.endTable()

                self.startTable()
                self.startRow()
                self.addValue("",BGColor=self.DefaultBackColor)
                self.endRow()

                self.startRow(Style="A")
                self.addValue("Creditos", ColSpan=3)
                self.endRow()
                self.printCategoryPerResume(True)
                self.endTable()

            if (self.params.ShowEmisorCenterResume):
                self.printResumePerEmisorCenter()

            #tot = 0.0
            #self.startTable()
            #self.startHeaderRow()
            #self.addValue("Provincia")
            #self.addValue("Monto")
            #self.endHeaderRow()
            #alert(provPerAmount)
            #from Province import Province
            #for p in provPerAmount.keys():
            #    province = Province.bring(p)
            #    self.startRow()
            #    if province :#and provPerAmount[p]:
            #        self.addValue(province.Name)
            #        self.addValue(provPerAmount[p])
            #        self.endRow()
            #        tot += provPerAmount[p]
            #    else:
            #        self.addValue("sin provincia")
            #        self.addValue(provPerAmount[p])
            #        self.endRow()
            #        tot += provPerAmount[p]
            #self.startRow()
            #self.addValue("Total")
            #self.addValue(tot)
            #self.endRow()
            #self.endTable()
        if self.params.ShowAccountancyResume:
            nltquery = Query()
            nltquery.sql = "SELECT n.OriginNr,n.SerNr,nr.Account,nr.Comment, "
            if not self.params.ShowAccountancyResumeDetailed:
                nltquery.sql += "SUM"
            nltquery.sql += "(IFNULL(nr.ValueBase1,0)) AS Amount "
            nltquery.sql += "FROM NLTRow nr INNER JOIN NLT n ON n.internalId = nr.masterId "
            nltquery.sql += "WHERE?AND n.OriginType = i|1| "
            nltquery.sql += "WHERE?AND n.OriginNr IN ('%s')  " % ("','".join(self.invoiceList))
            nltquery.sql += "WHERE?AND n.Status = i|1| "
            nltquery.sql += "WHERE?AND(n.Invalid = i|0| OR n.Invalid IS NULL) "
            if not self.params.ShowAccountancyResumeDetailed:
                nltquery.sql += "GROUP BY Account "
            self.startTable()
            if nltquery.open():
                self.header("Resumen Contable")
                if not self.params.ShowAccountancyResumeDetailed:
                    self.header("Account","Comment","Debe","Haber")
                else:
                    self.header("Factura","Asiento","Account","Comment","Debe","Haber")
                totdebe = 0.00
                tothaber = 0.00
                lastSerNr = ""
                for row in nltquery:
                    self.startRow()
                    if self.params.ShowAccountancyResumeDetailed:
                        if lastSerNr != row.OriginNr:
                            self.addValue(row.OriginNr,Window="InvoiceWindow",FieldName="SerNr",BGColor="grey")
                        else:
                            self.addValue("")
                        self.addValue(row.SerNr,Window="NLTWindow",FieldName="SerNr")
                    self.addValue(row.Account,Window="AccountWindow",FieldName="Code")
                    self.addValue(row.Comment)
                    if row.Amount >= 0:
                        self.addValue(abs(row.Amount))
                        totdebe += abs(row.Amount)
                        self.addValue("")
                    else:
                        self.addValue("")
                        self.addValue(abs(row.Amount))
                        tothaber += abs(row.Amount)
                    self.endRow()
                    lastSerNr = row.OriginNr
                if self.params.ShowAccountancyResumeDetailed:
                    colspan = 4
                else:
                    colspan = 2
                self.startHeaderRow()
                self.addValue("Totales",ColSpan=colspan)
                self.addValue(totdebe)
                self.addValue(tothaber)
                self.endHeaderRow()

    def displayInvoice(self,lastrec,tot,net,iva,lux):
        cur = Currency.bring(lastrec.Currency)
        Total      = cur.convertToBase(lastrec.Total,lastrec.CurrencyRate,lastrec.BaseRate,self.params.Base)
        TotalTax   = cur.convertToBase(lastrec.TotalTax,lastrec.CurrencyRate,lastrec.BaseRate,self.params.Base)
        if (lastrec.Invalid):
            self.startRow()
            self.addValue(lastrec.TransDate)
            self.addValue(self.InvTypeNames[lastrec.InvoiceType])
            if (self.params.ShowCommentInZInvoices and lastrec.DocType == 4):
                self.addValue(lastrec.Comment)
            else:
                self.addValue(Invoice.DocTypes[lastrec.DocType])   
            self.addValue(lastrec.OfficialSerNr,CallMethod="ZoomIn", Parameter = str(lastrec.SerNr),Wrap=False)
            self.addValue("ANULADO",Wrap=False)
            self.addValue("")
            self.addValue("")
            if (self.params.CAIFlag):
                if lastrec.CAI:
                    self.addValue(lastrec.CAI)
                else:
                    self.addValue("")
            self.addValue("")
            self.addValue("")
            if (self.params.AddVATBases):
              if (self.params.AddVAT):
                self.addValue("")
                self.addValue("")
              else:
                self.addValue("")
                for code in self.vatcodes:
                  if (self.percentTable[code]):
                     self.addValue("")
            else:
              for code in self.vatcodes:
                if (self.percentTable[code]):
                  self.addValue("")
                  self.addValue("")
            if (self.params.IncludePercep):
                  self.addValue("")
            self.endRow()
        else:
            self.TotTot += Total
            self.TotTax += TotalTax
            self.startRow()
            self.addValue(lastrec.TransDate)
            self.addValue(self.InvTypeNames[lastrec.InvoiceType])
            self.addValue(Invoice.DocTypes[lastrec.DocType])
            osernr = lastrec.OfficialSerNr
            if (self.params.ShowCommentInZInvoices and lastrec.DocType == 4):
                osernr = lastrec.Comment
            self.addValue(osernr,CallMethod="ZoomIn", Parameter = str(lastrec.SerNr),Wrap=False)
            if self.getRecord().ShowCustCode:
                self.addValue(lastrec.CustCode, Wrap=False)
            self.addValue(lastrec.CustName[:self.params.NameLen],Wrap=False)
            self.addValue(lastrec.TaxRegNr)
            self.addValue(Customer.TaxRegTypes[lastrec.TaxRegType],Wrap=False)
            
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
            emisorKey= self.getEmisorCenter(lastrec.SerNr, lastrec.Office)
            if self.emisorResume.has_key(emisorKey):
              self.emisorResume[emisorKey]["Gravado"] += base
              self.emisorResume[emisorKey]["Exento"] += exento
              for code in self.vatcodes:
                  if (self.percentTable[code]):
                      self.emisorResume[emisorKey][code] += iva[code]
            else:
              self.emisorResume[emisorKey] = {}
              self.emisorResume[emisorKey]["Gravado"] = base
              self.emisorResume[emisorKey]["Exento"] = exento
              for code in self.vatcodes:
                  if (self.percentTable[code]):
                      self.emisorResume[emisorKey][code] = iva[code]
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
            if (self.params.LuxTax):
                self.addValue(lux)
            if (self.params.IncludePercep):
                self.addValue(TotalTax)
            self.addValue(Total)
            self.endRow()

    def displayFooter(self,Titulo,TotTot,TotTax,tnet,tiva,tlux):
        self.startHeaderRow()
        self.addValue(Titulo)
        if self.getRecord().ShowCustCode:
            self.addValue("")
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
        if (self.params.LuxTax):
              self.addValue(tlux)
        if (self.params.IncludePercep):
              self.addValue(TotTax)
        self.addValue(TotTot)
        self.endRow()
        #self.addPageBreak()            # cut page only if you export to hmtl and print from a browser

    def GetPayTermConds(self):
        pterms = {}
        query = Query()
        query.sql  = "SELECT {Code},{InterestRate} "
        query.sql += "FROM [PayTerm] "
        query.sql += "WHERE {PayType}=1 "
        if(query.open()):
          for pt in query:
            pterms[pt.Code] = pt.InterestRate
        return pterms

    #def GetCapital(self,installs,cuota,rate):
    #    # should be method within payterm ...
    #    capital = cuota / (1 + installs * (rate/100))
    #    interes = capital * (rate/100)
    #    if (installs <= 10):
    #      captial = 0
    #    return (interes,capital)

    def ZoomIn(self,param,value):
        from InvoiceWindow import InvoiceWindow
        inv = Invoice.bring(int(param))
        if inv:
          invw = InvoiceWindow()
          invw.setRecord(inv)
          invw.open()

    def printprovPerResume(self):
        self.params = self.getRecord()
        query = Query()
        query.sql  = "SELECT {TaxCode},SUM({Amount}) as Amount,Inv.{CurrencyRate},Inv.{BaseRate},Inv.{Currency} \n"
        query.sql += "FROM [InvoiceTaxRow] Invtax\n"
        query.sql += "INNER JOIN [Invoice] Inv ON Inv.{internalId}=Invtax.{masterId} \n"
        query.sql += "WHERE?AND Inv.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        if (self.params.DocType<>6):
          query.sql+="WHERE?AND [Inv].{DocType}=i|%i| \n" % self.params.DocType
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [Inv].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [Inv].{Status} = i|0|\n"
        query.sql += "WHERE?AND ([Inv].{Internalflag} = 0 OR [Inv].{Internalflag} IS NULL) "
        query.sql += "WHERE?AND [Inv].{Invalid} = i|0| OR [Inv].{Invalid} IS NULL \n"
        query.sql += "GROUP BY Invtax.{TaxCode},Inv.{Currency},Inv.{CurrencyRate},Inv.{BaseRate} \n"
        if query.open():            
            self.startTable()
            self.startRow()
            self.addValue("",BGColor=self.DefaultBackColor)
            self.endRow()
            self.headerB("Resumen de Percepciones")
            self.startRow(Style="B")
            self.addValue("Percepcion")
            self.addValue("Monto")
            self.endRow()
            tot = 0.00
            b1, b2 = Currency.getBases()
            perDic = {}
            for rec in query:
                if rec.Amount:
                    amount = Currency.convertTo(rec.Amount,rec.CurrencyRate,rec.BaseRate,rec.Currency,b1)
                    if rec.TaxCode not in perDic.keys():
                        perDic[rec.TaxCode] = 0
                    perDic[rec.TaxCode] += amount
            for perc in perDic.keys():
                self.startRow()
                self.addValue(perc)
                self.addValue(perDic[perc])
                self.endRow()
                tot += perDic[perc]
            self.startRow(Style="B")
            self.addValue("Total")
            self.addValue(tot)
            self.endRow()
            self.endTable()

    def printCategoryPerResume(self, ncflag):
        table = {}
        specs = self.getRecord()
        for i in range(10):
          table[i] = {}
        query = Query()
        query.sql ="SELECT s.{TaxRegType},[it].{TaxCode1},SUM({RowNet} * IF(InvoiceType=1,-1,1)) AS Total, "
        query.sql+="{InvoiceType} ,[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate},[pi].{TransDate},[pi].{TransTime} \n"
        query.sql+="FROM [InvoiceItemRow] pir \n"
        query.sql+="INNER JOIN [Invoice] pi ON pi.{internalId}= pir.{masterId}\n"
        query.sql+="INNER JOIN [Customer] s ON pi.{CustCode}= s.{Code}\n"
        query.sql+="INNER JOIN [Item] [it] ON [it].{Code} = [pir].{ArtCode} \n"
        query.sql+="INNER JOIN [ItemTaxGroup] [itg] ON [itg].{Code} = [it].{TaxCode1} \n"
        query.sql+="WHERE?AND pi.{TransDate} BETWEEN d|%s| AND d|%s|\n" % (self.params.FromDate,self.params.ToDate)
        query.sql+="WHERE?AND pir.{VATCode} IS NOT NULL \n"
        query.sql += self.SQLRangeFilter("pi", "Office", self.params.Office)
        if ncflag:
          query.sql+="WHERE?AND pi.{InvoiceType}=i|1| \n"
        else:
          query.sql+="WHERE?AND pi.{InvoiceType}<>i|1| \n"
        if (specs.DocType<>6):
          query.sql+="WHERE?AND pi.{DocType}=i|%i| \n" % specs.DocType
        query.sql+="WHERE?AND (pi.{Invalid}<>i|1| OR pi.{Invalid} IS NULL)\n"
        if self.params.WithOK and not self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|1|\n"
        elif not self.params.WithOK and self.params.WithOutOK:
            query.sql+="WHERE?AND [pi].{Status} = i|0|\n"
        query.sql += "WHERE?AND ([pi].{Internalflag} = 0 OR [pi].{Internalflag} IS NULL) "
        query.sql += "GROUP BY s.{TaxRegType},it.{TaxCode1},[pi].{Currency},[pi].{CurrencyRate},[pi].{BaseRate}\n"
        if(query.open()):
          #esta funcion convierte la moneda del query
          newquery  = Currency.processQueryResult(Currency.getBase1(), query, ("TaxRegType","TaxCode1",), ("Total",), "Currency", "CurrencyRate", "BaseRate", "TransDate", "TransTime")
          for r in newquery:
            table[r.TaxRegType][r.TaxCode1] = r.Total
        self.startTable()
        self.startRow(Style="B")
        self.addValue("Categor?a")
        self.addValue("Nombre")
        for i in range(7):
          self.addValue(Customer.TaxRegTypes[i])
        self.endRow()
        tot = {}
        itemTaxGroupTable = self.getUsedItemTaxGroup()
        for x in itemTaxGroupTable.keys():
          self.startRow()
          self.addValue(x)
          self.addValue(itemTaxGroupTable[x])
          for y in range(7):
              if not y in tot.keys():
                tot[y] = 0.00
              self.addValue(table[y].get(x,0.0))
              tot[y] += table[y].get(x,0.0)
          self.endRow()
        self.startRow(Style="B")
        self.addValue("Totales", ColSpan = "2")
        for y in tot.keys():
            self.addValue(tot[y])
        self.endRow()
        self.endTable()

    # Esta funcion es para redefinir en customizations
    # ej. Amesud: Centro Emisor es invSerNr[2:3] <> invOffice
    def getEmisorCenter(self, invSerNr, invOffice):
        return invOffice

    def printResumePerEmisorCenter(self):
        self.startTable()

        self.startRow()
        self.addValue("",BGColor=self.DefaultBackColor)
        self.endRow()

        self.startRow(Style="B")
        self.addValue("Totales por Centro Emisor")
        self.endRow()

        self.startRow(Style="A")
        self.addValue("Centro Emisor")
        self.addValue("Neto Gravado")
        self.addValue("Exento")

        for code in self.percentTable.keys():
            if (self.percentTable[code]):
                self.addValue("IVA (%s)" % str(self.percentTable[code]) )
        self.endRow()
        for emisor in self.emisorResume.keys():
            self.startRow()
            self.addValue(emisor)
            self.addValue(self.emisorResume[emisor]["Gravado"])
            self.addValue(self.emisorResume[emisor]["Exento"])
            for code in self.percentTable.keys():
                if (self.percentTable[code]):
                    self.addValue(self.emisorResume[emisor][code])
            self.endRow()
        self.endTable()