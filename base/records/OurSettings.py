#encoding: utf-8
from OpenOrange import *

ParentOurSettings = SuperClass('OurSettings','Setting',__file__)
class OurSettings(ParentOurSettings):

    buffer = SettingBuffer()

    def check(self):
        res = ParentOurSettings.check(self)
        if not res: return res
        for fieldname in ("BaseCur1","BaseCur2","Name","FantasyName","DefOffice"):
            if not self.fields(fieldname).getValue():
                return self.FieldErrorResponse("NONBLANKERR",fieldname)
        return True

    def pasteZipCode(self):
        from ZipCode import ZipCode
        res = ZipCode.getInfo(self.ZipCode)
        if res:
            (building,address,loc,city,prov) = res
            self.City = city
            if loc:
                self.LocalityCode = loc
                self.pasteLocalityCode()
            if prov:
                self.ProvinceCode = prov
                self.pasteProvinceCode()
            if building:
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

    def pasteCountry(self):
        pass # dont delete

    def pasteProvinceCode(self):
        from Province import Province
        province = Province.bring(self.ProvinceCode)
        if province:
            self.Province = province.Name
            self.Country  = province.Country

    def pastePhone(self):
        from CRMSettings import CRMSettings
        crm = CRMSettings.bring()
        res = crm.formatPhoneNumber(self.Phone,self.Country)
        if not res: return res
        self.Phone = res
        if not self.City:
            ddn = self.Phone.split("-")
            from AreaCode import AreaCode
            ac = AreaCode.bring(ddn[0][1:])
            if ac:
                self.City = ac.City
                self.ProvinceCode = ac.ProvinceCode
                self.pasteProvinceCode()
        return True

    @classmethod
    def getDistance(objclass,lat,lng):
        mainoffice = OurSettings.bring().DefOffice
        from Office import Office
        hq = Office.bring(mainoffice)
        d1 = (hq.Latitude,hq.Longitude)
        d2 = (lat,lng)
        from geo import distance
        return distance(d1,d2)

    def attachLogo(self):
        if self.Logo:
            res = self.save()
            try:
                if res: res = self.attachFile(self.Logo)
            except IOError, e:
                rollback()
            if res:
                commit()
            else:
                message(res)

