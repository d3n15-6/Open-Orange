#encoding: utf-8
from Routine import Routine
from OurSettings import OurSettings
from Province import Province
from TaxSettings import TaxSettings
from Item import Item
from Customer import Customer
from Vehicle import Vehicle
from OpenOrange import *
import string

filename = ["AfipGanRet","AfipGanPer"]

class ExportAfipEntr(Routine):
  
    def run(self):
        specs = self.getRecord()
        from OurSettings import OurSettings
        os = OurSettings.bring()
        from WayBill import WayBill
        from Delivery import Delivery
        from TaxSettings import TaxSettings
        ts = TaxSettings.bring()
        nr = 0
        fname = filename[specs.Option] + ".txt"
        f = file(fname, "w")
        wb = WayBill.bring(specs.Nro)
        if not wb: return
        f.write(self.HeaderLine())
        for wbline in wb.WayBillRows:
           deli = Delivery.bring(wbline.DeliveryNr)
           f.write(self.DeliveryLine(deli,wb,ts,os))
           for delline in deli.Items:
             f.write(self.ProductLine(delline.ArtCode,delline.Name,delline.Qty))
             nr += 1
        f.write(self.FooterLine(nr))
        f.close()


    def formatFloat(self,valor,align):
       tmp = "%.2f" % valor               # tmp is needed otherwise it doesnt allign !!
       tmp = tmp.replace(".",",")
       return tmp.rjust(align," ")


    def FooterLine(self,nr):
       Line  = "04"
       Line += str(nr).ljust(10," ")
       return Line + "\n"

    def HeaderLine(self):
       from TaxSettings import TaxSettings
       os = TaxSettings.bring()
       Line  = "01"
       cuit = filter(lambda x: x.isdigit(),os.TaxRegNr)
       Line += cuit.ljust(13," ")
       return Line + "\n"

    def ProductLine(self,ArtCode,Comment,Qty):
       it = Item.bring(ArtCode)
       Line  = "03"
       Line += it.TaxCode1.ljust(6,"0")
       ut = Unit.bring()
       Line += ut.TaxOfficeCode.ljust(1,"0")
       tmp = str(round(Qty * 100,0))
       Line += tmp.rjust(15,"0")
       Line += ArtCode[0:25].ljust(25," ")     #  propio codigo producto
       Line += Comment[0:40].ljust(40," ")     #  desc
       Line += ut.Name[0:20].ljust(20," ")     #  desc unidad
       Line += 15 * " "                          #  mmm cantidad
       return Line + "\n"


    def CompanyLine(self,TaxRegNr,CustName,Adress,ZipCode,City,Province):
       cuit = filter(lambda x: x.isdigit(),TaxRegNr)
       Line += cuit.ljust(13," ")
       Line += CustName[0:50].ljust(50," ")     # 4. razon social
       Line += Address[0:40].ljust(40," ")     # 4. calle
       Line += 5 * " "                                     # comple
       Line += 3 * " "                                     #  piso
       Line += 4 * " "                                     #  departamento
       Line += 30 * " "                                     # 8. Barrio
       Line += ZipCode.ljust(8," ")                  # 6.zipcode
       Line += City[0:50].ljust(50," ")     
       Line += "B"
       return Line + "\n"


    def old(self,valor,align):
       Line += Province.getAFIPProvCode(Province) # 5. province
       tmp = ""
       zc = ZipCode.bring(p.ZipCode)
       if zc: tmp = zc.TaxOfficeCode
       Line += tmp.ljust(5," ")                           # 7. Codigo localidad
       Line += 4 * " "                                     # 10. Nro de Puerta
       Line += 1 * " "                                     # 11. Complemento nro puerto
       return Line + "\n"


    def DeliveryLine(self,deli,wb,ts,os):
       Line = "02"
       Line += deli.TransDate.strftime("%d/%m/%Y")                 # . fecha emision
       Line += "XX"                                  # codigo dgi
       Line += "X".rjust(2," ")                     # tipo comprobante
       tmp  =  str(deli.SerNr)[0:2]
       Line += tmp.rjust(4,"0")                     # office
       Line += str(deli.SerNr).rjust(8,"0")                     # nro comprobante
       Line += wb.DeliveryDate.strftime("%d/%m/%Y")                 # . fecha transporte
       Line += wb.DeliveryFromTime.strftime("%h/%m")                 # . hora transporte
       cust = Customer.bring(deli.CustCode)
       Line += "E"                                  # sujeto generador
       if (cust.TaxRegType==1):
         Line  += "1"
       else:  
         Line  += "0"
       Line += 3 * " "                                  # tipo de documento 
       Line += 11 * " "                                  #  documento 
       Line += self.CompanyLine(cust.TaxRegNr,deli.CustName,deli.Address,deli.ZipCode,deli.City,deli.Province)
       Line += 20 * " "                                     # ??
       Line += "SI"
       Line += self.CompanyLine(ts.TaxRegNr,os.Name,os.Adress,os.ZipCode,os.City,os.Province)
       trnComp = Customer.bring(deli.TransCompany)
       cuit = filter(lambda x: x.isdigit(),trnComp.TaxRegNr)
       Line += cuit.ljust(13," ")                           # cuit transoportista
       Line += "U"                                      # tipo recorrido
       Line += str(p.SerNr).ljust(20," ")                 # 15. nro comprobante
       Line += p.TransDate.strftime("%d/%m/%Y")                 # 16. fecha comprobante
       Line += 11 * " "                                     # 17. monto 
       Line += (50 * " ")                            # recorido
       Line += (40 * " ")                            # recorido
       Line += (40 * " ")                            # recorido
       vh = Vehicle.bring(wb.Vehicle)
       if vh:
         Line += vh.Plate[0:6].ljust(6," ")
       else:
         Line += (6 * " ")
       tr = Vehicle.bring(wb.Trailer)
       if tr:
         Line += tr.Plate[0:6].ljust(6," ")
       else:
         Line += (6 * " ")       
       return Line + "\n"


