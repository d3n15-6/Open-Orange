#encoding: utf-8
from OpenOrange import *
import string
import re

ParentMailAccount = SuperClass("MailAccount","Master",__file__)
class MailAccount(ParentMailAccount):
    buffer = RecordBuffer("MailAccount")

    def defaults(self):
        from User import User
        ParentMailAccount.defaults(self)
        self.User = currentUser()
        self.pasteUser()
        self.POP3Port = 110
        self.SMTPPort = 25
        self.Mail = "@"
        footer_info = User.getMailFooter(currentUser())
        self.Name = "%s %s" % (footer_info.get("Name", ""), footer_info.get("LastName", ""))
        self.Phone = footer_info["Phone"]
        self.Address = footer_info["Address"]
        self.City = footer_info["City"]
        self.Country = footer_info["Country"]
        self.Company = footer_info["Company"]
        self.Site = footer_info["Site"]

    def pasteUser(self):
        if (not self.POP3User):
            self.POP3User = self.User
        if (not self.SMTPUser):
            self.SMTPUser = self.User

    def getFooterInfo(self):
        import Web
        iset = {}
        iset["Name"] = Web.escapeXMLValue(self.Name)
        iset["Phone"] = Web.escapeXMLValue(self.Phone)
        iset["CellPhone"] = Web.escapeXMLValue(self.CellPhone)
        iset["Address"] = Web.escapeXMLValue(self.Address)
        iset["City"] = Web.escapeXMLValue(self.City)
        iset["Province"] = Web.escapeXMLValue(self.Province)
        iset["Country"] = Web.escapeXMLValue(self.Country)
        iset["Company"] = Web.escapeXMLValue(self.Company)
        iset["Site"] = self.Site
        iset["OtherData"] = Web.escapeXMLValue(self.OtherData)
        return iset

    def getConnectedIMAPServer(self):
        import imaplib
        m=imaplib.IMAP4_SSL(self.POP3Server, self.POP3Port)
        m.login(self.POP3User,decode(self.POP3Password))
        return m
