#encoding: utf-8
from OpenOrange import *

ParentOurSettingsWindow = SuperClass("OurSettingsWindow","SettingWindow",__file__)
class OurSettingsWindow(ParentOurSettingsWindow):

    def afterEdit(self, fieldname):
        ParentOurSettingsWindow.afterEdit(self, fieldname)
        rec = self.getRecord()
        if fieldname in ("BaseCur1","Country"):
            message("Please recompile or Quit and Logon again")
        if (fieldname == "ZipCode"):
            rec.pasteZipCode()
        elif (fieldname == "LocalityCode"):
            rec.pasteLocalityCode()
        elif (fieldname == "ProvinceCode"):
            rec.pasteProvinceCode()
        elif (fieldname == "Country"):
            rec.pasteCountry()
        elif (fieldname == "Logo"):
            rec.attachLogo()
        return True

