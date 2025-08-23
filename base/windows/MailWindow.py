#encoding: utf-8
from OpenOrange import *
from MasterWindow import MasterWindow
import re

ParentMailWindow = SuperClass("MailWindow", "NumerableWindow", __file__)
class MailWindow(ParentMailWindow):

    def buttonClicked(self, buttonname):
        myMail = self.getRecord()
        if (buttonname=="MessageSend"):
            self.send()                    
        elif (buttonname=="MessageReply"):
            self.reply()
        elif (buttonname=="MessageForward"):
            self.forward()
        elif (buttonname=="genTrans"):
            transjes = ("Reservation","SalesOrder","Case","Opportunity","Quote")
            trans = getSelection(tr("Select"), transjes )
            if (not trans): return
            myMail.ProcessedFlag = True
            exec ("from %s import %s" % (trans,trans))
            exec ("from %sWindow import %sWindow" % (trans,trans))
            exec ("reg = %s()" % trans)
            exec ("win = %sWindow()" % trans)
            reg.defaults()
            reg.OriginNr = myMail.SerNr
            reg.OriginType = myMail.Origin[trans]
            win.setRecord(reg)
            win.open()
        elif (buttonname=="addContact"):
            fieldname = self.lastField
            if fieldname in ("MailTo","MailFrom","MailCc","MailBcc"):
                from Person import Person,ContactWay
                from PersonWindow import PersonWindow
                from Mail import *
                txt = myMail.fields(fieldname).getValue()
                names = Mail.getStdName(txt)
                pers = Person()
                pers.defaults()
                pers.Name = names.split(" ")[0]
                pers.LastName = names.split(" ")[1]
                cw = ContactWay()
                cw.Detail = Mail.getStdMail(txt)
                cw.ContactType = 3
                pers.ContactWays.append(cw)
                pw = PersonWindow()
                pw.setRecord(pers)
                pw.open()

    def afterShowRecord(self):
        ParentMailWindow.afterShowRecord(self)
        self.getRecord().setFocusOnField("MessageBody")


    def importHTML(self):
        import os
        fn = getOpenFileName()
        f = file(fn)
        html = f.read()
        pathdir = os.path.dirname(fn)
        self.getRecord().importHTML(html,False,pathdir)
        commit() #porque el refresh hace un rollback (SP) y ademas el importHTML hace un save (PDB)
        self.refresh()

    def afterEdit(self,fieldname):
        if (fieldname == "User"):
            self.getRecord().pasteUser()
        elif (fieldname == "MailCode"):
            self.getRecord().pasteMailCode()
        elif (fieldname == "CustCode"):
            self.getRecord().pasteCustCode()

    def filterPasteWindow(self,fieldname):
        record = self.getRecord()
        if (fieldname == "MailCode"):
            return "{User}=s|%s|" % (currentUser())
        elif (fieldname in ("MailTo","MailCc","MailBcc")):
            return "{CustCode}=s|%s|" % (record.CustCode)

    def fillPasteWindow(self,pastewindowname, fieldname):
        record = self.getRecord()
        if fieldname in ("MailTo", "MailCc", "MailBcc"):
            if record.CustCode:
                q = Query()
                q.sql = "SELECT p.Code, p.Name, p.LastName, p.JobPosition, IFNULL(cw.Detail, p.Email) as Email"
                q.sql += " FROM Person p "
                q.sql += "LEFT JOIN [ContactWay] [cw] ON [cw].{ContactType}=i|3| AND p.{internalId} = [cw].{masterId}"
                q.sql += "WHERE?AND p.CustCode = s|%s| " % record.CustCode
                if q.open():
                    return q

    def getPasteWindowName(self,fieldname):
        record = self.getRecord()
        if (fieldname == "CustCode"):
              from EntityList import EntityList
              report = EntityList()
              report.Mail = record
              specs = report.getRecord()
              report.open(False)
              return ""



    def send(self):
        myMail = self.getRecord()
        cuentas = Query()                    
        cuentas.sql = "SELECT * FROM [MailAccount] WHERE {Mail}=s|%s| AND {User}=s|%s|" % (myMail.getStdMail(myMail.MailFrom), currentUser())
        if (cuentas.open()):
            if (cuentas.count() > 0):
                for cuenta in cuentas:
                    server = cuenta.SMTPServer
                    port = cuenta.SMTPPort
                    passwd = None
                    user = None
                    if (cuenta.SMTPReqAuth):
                        passwd = cuenta.SMTPPassword    
                        user = cuenta.SMTPUser
                    res = myMail.send(server, port, user, passwd, cuenta.SMTPReqSSL)
                    myMail.showMessages()
                    if res:
                        commit() #send method saves the mail
                        message(tr("Message sent"))
                        return True
                    else:
                        commit() #send method saves the mail, also on error circunstances
                        message(tr("Message not sent!") + " " + str(res))
            else:
                message("El usuario %s no tiene una cuenta llamada %s" % (currentUser(), myMail.getStdMail(myMail.MailFrom)))
        else:
            message("El usuario %s no tiene una cuenta llamada %s" % (currentUser(), myMail.getStdMail(myMail.MailFrom)))
        return False

        
    def reply(self):
        myMail = self.getRecord()
        from Mail import Mail            
        reply = myMail.clone()
        reply.User = currentUser()
        reply.TransDate = today()
        reply.TransTime = now()
        reply.ParentId = myMail.Id
        reply.ThreadId = myMail.ThreadId
        reply.Id = None
        reply.MailTo = myMail.MailFrom
        reply.MailFrom = myMail.MailTo
        reply.Status = Mail.DRAFT # hasta que se logre enviar
        reply.Subject = re.sub("(Re: )+", "", reply.Subject)
        reply.Subject = "Re: %s" % reply.Subject
        aux = "> %s" % reply.MessageBody 
        aux.replace('\n','\n> ')
        aux = re.sub("<p>", "<p>&gt;&nbsp;<font color=\"red\">", aux)
        reply.MessageBody = "<br>" + re.sub("</p>", "</font></p>", aux)
        #reply.MessageBody = re.sub("^", "> ", aux)
        #reply.MessageBody = re.sub("\n", "\n> ", aux)            
        replyWindow = MailWindow()
        replyWindow.setRecord(reply)
        replyWindow.open()
        
    def forward(self):
        myMail = self.getRecord()
        from Mail import Mail            
        forward = myMail.clone()
        forward.defaults()
        forward.SerNr = None
        forward.TransDate = today()
        forward.TransTime = now()
        forward.ParentId = None
        forward.Id = None
        forward.ThreadId = myMail.ThreadId
        forward.MailTo = None
        forward.Status = Mail.DRAFT # hasta que se logre enviar
        forward.Subject = re.sub("(Fw: )+", "", forward.Subject)
        forward.Subject = "Fw: %s" % forward.Subject
        aux = "%s" % forward.MessageBody 
        forwMsg = "<br/><br/>-------- %s --------" % (tr("Original Message")) + "<br/>"
        forwMsg += "<table cellpadding=\"0\" cellspacing=\"0\" style=\"font-family:arial,sans-serif;font-size:8pt;color:black;\" >"
        forwMsg += "<tr><td align=\"right\"><strong>%s</strong></td><td>&nbsp;%s</td></tr>" % (tr("Subject"), myMail.Subject)
        forwMsg += "<tr><td align=\"right\"><strong>%s</strong></td><td>&nbsp;%s</td></tr>" % (tr("From"), myMail.MailFrom)
        forwMsg += "<tr><td align=\"right\"><strong>%s</strong></td><td>&nbsp;%s</td></tr>" % (tr("To..."), myMail.MailTo)
        forwMsg += "</table>"
        aux = re.sub("<p>", "<p>%s" % forwMsg, aux)
        forward.MessageBody = re.sub("</p>", "</p><br/>", aux)
        
        if myMail.attachFlag:
            res = forward.save()
            if not res: return message(ErrorResponse(res))
            for attach in myMail.getAttachs():
                forwattch = attach.clone()
                forwattch.OriginId = forward.getPortableId()
                res = forwattch.store()
                if not res: return message(ErrorResponse(res))
                forward.updateAttachFlag()
            commit()
        
        forwardWindow = MailWindow()
        forwardWindow.setRecord(forward)
        forwardWindow.open()
        
    def addSignature(self):
        res = self.getRecord().addSignature()
        commit()
        #alert(res)