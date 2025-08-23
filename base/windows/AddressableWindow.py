#encoding: utf-8
from OpenOrange import *

ParentAddressableWindow = SuperClass("AddressableWindow","MasterWindow",__file__)
class AddressableWindow(ParentAddressableWindow):
    
    def afterEdit(self, fieldname):
        ParentAddressableWindow.afterEdit(self, fieldname)
        rec = self.getRecord()
        if (fieldname == "ZipCode"):
            rec.pasteZipCode()
        elif (fieldname == "LocalityCode"):
            rec.pasteLocalityCode()
        elif (fieldname == "ProvinceCode"):
            rec.pasteProvinceCode()
        elif (fieldname == "Country"):
            rec.pasteCountry()
        elif (fieldname == "City"):
            rec.pasteCity()
        return True 

    def buttonClicked(self, buttonname):
        ParentAddressableWindow.buttonClicked(self, buttonname)
        rec = self.getRecord()
        if buttonname == "getZipCode":
            from ZipCode import ZipCode
            ZipCode.get(rec)
            cpa = self.showZipCodeSelectionDialog(rec.ProvinceCode,rec.City,rec.Address)
            if cpa: 
                rec.ZipCode = cpa

        elif buttonname == "openWeb":
            fieldname = self.currentField()
            if fieldname in ("City","Address","Province","Latitude","Longitude"):
                if (not rec.Latitude and not rec.Longitude):
                    from geo import geocode,getGeoCodingAddress
                    from GeoSettings import GeoSettings
                    gs = GeoSettings.bring()
                    if (gs.Addressflag==1 and self.__class__.__name__=="Customer"):
                      fulladdress = getGeoCodingAddress(rec.DelCountry,rec.DelProvince,rec.DelCity,rec.DelAddress)
                    else:
                      fulladdress = getGeoCodingAddress(rec.Country,rec.Province,rec.City,rec.Address)
                    rec.Latitude,rec.Longitude = geocode(fulladdress)
                else:
                    from geo import openMap,distance
                    import webbrowser
                    import os
                    from OurSettings import OurSettings
                    dist = OurSettings.getDistance(rec.Latitude,rec.Longitude)
                    mylabel = "%s: at %.2f km" % (rec.Name,dist)
                    openMap(rec.Latitude,rec.Longitude,mylabel)
                    webbrowser.open("file:///%s/showdir.html" % os.getcwd())
            elif fieldname == "WebSite":
                    import webbrowser
                    webbrowser.open("http://" + rec.WebSite)
        elif buttonname == "checkTaxRegnr":
            #if not Validator.VATRegNrOK (rec.TaxRegNr, rec.Country):
            #    message (tr("WRONGTAXREGNR"))
            from OurSettings import OurSettings
            os = OurSettings.bring()
            if (os.Country=="pt"):
                import webbrowser
                import os
                url = "http://publicacoes.mj.pt/pt/Pesquisa.asp"
                params = "?iNIPC=%s&sFirma=&dfDistrito=&dfConcelho=&dInicial=&dFinal=&iTipo=0&sCAPTCHA=&pesquisar=Pesquisar&dfConcelhoDesc" % rec.TaxRegNr[2:]

                webbrowser.open(url + params)

        return True 


