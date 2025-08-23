#encoding: utf-8
from OpenOrange import *
import string
import Web
import os
import re

#clase para envío de mails en Threads
class MailThread(CThread):

    def setRecord(self, mailTo, subject, message="", curruser=None):
        self.mailTo = mailTo
        self.message = message
        self.subject = subject
        if not curruser:
            self.curruser = currentUser()
        else:
            self.curruser = curruser

    def run(self):
        try:
            to = self.mailTo
            subject = self.subject
            message = self.message
            from Mail import Mail
            mail = Mail()
            mail.defaults()
            currUser = self.curruser
            mail.User = currUser
            from MailAccount import MailAccount
            mailacc = MailAccount()
            mailacc.User = currUser
            if (mailacc.load()):
                mail.MailCode = mailacc.Code
                mail.MailFrom = mailacc.Mail
                mail.Name = mailacc.Name
            mail.MailTo = to
            mail.Subject = subject
            if (not mail.saveMail()):
                #el registro tiene que estar grabado para poder importar el mail
                log("Error al enviar el Mail. No se pudo grabar el registro")
                return
            mail.importHTML(self.getMessage(),True)

            resultMessage = ""
            cuentas = Query()
            cuentas.sql = "SELECT * FROM [MailAccount] WHERE {Mail}=s|%s| AND {User}=s|%s|" % (mail.getStdMail(mail.MailFrom), currUser)
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
                        if (mail.send(server, port, user, passwd, cuenta.SMTPReqSSL)):
                            resultMessage = "Mensaje enviado: %s" % subject
                            break
                        else:
                            resultMessage = "ERROR: Mail NO enviado"
                else:
                    resultMessage = "ERROR: El usuario %s no tiene una cuenta llamada %s" % (currUser, mail.getStdMail(mail.MailFrom))
            else:
                resultMessage = "ERROR: El usuario %s no tiene una cuenta llamada %s" % (currUser, mail.getStdMail(mail.MailFrom))
            log(resultMessage)
        except:
            import traceback,sys
            import StringIO
            stringio = StringIO.StringIO()
            traceback.print_exc(file=stringio)
            log(str(stringio.getvalue()))
            log("Error al enviar el Mail")

    def getMessage(self):
#        username = Web.escapeXMLValue(self.person.Name +" "+ self.person.LastName)
#        usercode = Web.escapeXMLValue(self.person.WebUser)
#        userpass = Web.escapeXMLValue(decode(self.person.WebPassword))
        if self.message.find("<html") != -1: message = "<html>%s</html>" % self.message
        else: message = self.message
        return message

