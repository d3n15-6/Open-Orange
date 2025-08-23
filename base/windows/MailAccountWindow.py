#encoding: utf-8
from OpenOrange import *
from MasterWindow import MasterWindow

ParentMailAccountWindow = SuperClass("MailAccountWindow","MasterWindow",__file__)
class MailAccountWindow(ParentMailAccountWindow):

    #def getFooterInfo(self):
        #from User import User
        #footer_info = User.getMailFooter(currentUser())

    def getFooterInfo(self):
        iset = {}
        iset["Name"] = self.Name
        iset["Phone"] = self.Phone
        iset["Address"] = self.Address
        iset["City"] = self.City
        iset["Province"] = self.Province
        iset["Country"] = self.Country
        iset["Company"] = self.Company
        iset["Site"] = self.WebSite
        iset["OtherData"] = self.OtherData
        return iset

