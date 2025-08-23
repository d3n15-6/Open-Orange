#encoding: utf-8
from OpenOrange import *

ParentOffice = SuperClass("Office","Addressable",__file__)
class Office(ParentOffice):
    buffer = RecordBuffer("Office")

    @classmethod
    def getOfficeList(classobj):
        list = []
        query = Query()
        query.sql  = "SELECT {Code},{Name} "
        query.sql += "FROM [Office] "
        if query.open():
            for s in query:
                list.append(s.Code)
        return list

    @classmethod
    def default(objclass):
        from OurSettings import OurSettings
        from User import User
        os = OurSettings.bring()
        if (not os.OfficeDeterminator):
            of = User.getOffice(currentUser())
            if of: return of
        else:
            from Computer import Computer
            from LocalSettings import LocalSettings
            ls = LocalSettings.bring()
            cm = Computer.bring(ls.Computer)
            if (cm and cm.Office):
                return cm.Office
        return os.DefOffice

    def pasteCountry(self):
        pass                 # no borrar !! se llama desde addressable
