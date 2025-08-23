#encoding: utf-8
from OpenOrange import *
from SerNrControl import SerNrControl
from Master import Master
from OurSettings import OurSettings

ParentAddressable = SuperClass("Addressable", "Master", __file__)
class Addressable(ParentAddressable):

    def pasteZipCode(self):
        from ZipCode import ZipCode
        res = ZipCode.getInfo(self.ZipCode)
        if res:
            (building,address,loc,city,prov) = res
            if (city):
                self.City = city
            if (loc):
                self.LocalityCode = loc
                self.pasteLocalityCode()
            if (prov):
                self.ProvinceCode = prov
                self.pasteProvinceCode()
            if (building):
               if not self.Address:
                  self.Address = building
               else:
                  self.FantasyName = building
            if not self.Address: self.Address = address   # user could have entered already house nr etc !
        return True

    def pasteLocalityCode(self):
        from Locality import Locality
        loc = Locality.bring(self.LocalityCode)
        if loc:
            self.Locality = loc.Description
            if not self.ZipCode:                   # if not you get endless recursion
                self.ZipCode = loc.ZipCode
                self.pasteZipCode()
        else:
            self.Locality = ""

    def pasteProvinceCode(self):
        from Province import Province
        province = Province.bring(self.ProvinceCode)
        if province:
            self.Province = province.Name
            self.Country  = province.Country
            self.pasteCountry()

    def pasteCountry(self):
        pass

    def pastePhone(self):
        from AreaCode import AreaCode
        from CRMSettings import CRMSettings
        #crm = CRMSettings.bring()
        #res = crm.formatPhoneNumber(self.Phone,self.Country)
        #if not res: return res
        self.Phone = CRMSettings.getStandardNumber(self.Phone)
        if not self.City:
            ddn = self.Phone.split("-")
            from AreaCode import AreaCode
            #alert(ddn[0][1:])
            ac = AreaCode()
            ac.Code = ddn[0][1:]
            if (ac.load()):
                self.City = ac.City
                self.ProvinceCode = ac.ProvinceCode
                self.Country = ac.Country
                self.pasteProvinceCode()
        return True

    def pasteCity(self):
        from City import City
        city = City.bring(self.City)
        if (city):
            self.ProvinceCode = city.Province
            self.pasteProvinceCode()