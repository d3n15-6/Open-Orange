#encoding: utf-8
from OpenOrange import *

ParentRecordCommunication = SuperClass("RecordCommunication","Numerable",__file__)
class RecordCommunication(ParentRecordCommunication):

    def defaults(self):
        ParentRecordCommunication.defaults(self)
        from User import User
        user = User.bring(currentUser())
        if user:
            self.Person = user.Person
        
    def afterCopy(self):
        ParentRecordCommunication.afterCopy(self)
        self.RecordCommunicationNr = None
        self.User = currentUser()
    
    def beforeInsert(self):
        res = ParentRecordCommunication.beforeInsert(self)
        if not res: return res
        res = self.notifyPersons()
        if not res: return res
        return True

    def beforeUpdate(self):
        res = ParentRecordCommunication.beforeUpdate(self)
        if not res: return res
        res = self.notifyPersons()
        if not res: return res
        return True
        
    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentRecordCommunication.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if not res: return res
        return True
    
    def getOriginRecord(self):
        if self.OriginRecord:
            r = NewRecord(self.OriginRecord)
            r.setPortableId(self.OriginId)
            if r.load():
                return r
        return None
 

    def notifyPersons(self):
        origin = self.getOriginRecord()
        if not origin: return []
        persons = origin.getNotificationPersons()    
        mails = {}
        for p in persons:
            mailaddress = p.getMail()
            if mailaddress:
                mails[mailaddress] = True
        if len(mails):
            from Mail import Mail
            mail = Mail()
            mail.defaults()
            mail.MailTo = ",".join(mails.keys())
            sysprint(mail.MailTo)
            mail.Subject = "OpenOrange Communication about %s" % origin
            mail.MessageBody = "%s wrote: \n<br>" % self.Name + self.Message
            res = mail.save()
            if not res:
                return ErrorResponse("Error saving email")
            res = mail.send()
            return res
        return True