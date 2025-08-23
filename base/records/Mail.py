#encoding: utf-8
from OpenOrange import *
from Master import Master
import sys, smtplib, MimeWriter, base64, StringIO
import re

ParentMail = SuperClass("Mail","Numerable",__file__)
class Mail(ParentMail):
    RECEIVED = 0
    SENT = 1
    DRAFT = 2

    def defaults(self):
        ParentMail.defaults(self)
        from MailAccount import MailAccount
        mailacc = MailAccount()
        mailacc.User = currentUser()
        self.User = currentUser()
        if (mailacc.load()):
            self.MailCode = mailacc.Code
            self.MailFrom = mailacc.Mail
            self.Name = mailacc.Name
            self.MailBcc = mailacc.SendBCCCopy
        #self.pasteUser()
        Invalid = False
        self.Status    = 0
        self.SentFlag = False
        self.EntityType  = 0
        self.MessageType  = 0
        self.ReadFlag = 0

    def afterCopy(self):
        ParentMail.afterCopy(self)
        self.Id = None
        self.ReadFlag = False

    def invalidate(self):
        ParentMail.invalidate(self)
        self.Invalid = True
        return self.Invalid

    def pasteUser(self):
        from User import User
        user = User()
        user.Code = self.User
        self.FromMail = ""
        if user.load():
            from Person import Person
            person = Person()
            person.Code = user.Person
            if person.load():
                self.MailFrom = person.Email

    def pasteMailCode(self):
        from MailAccount import MailAccount
        acc = MailAccount()
        acc.Code = self.MailCode
        if (acc.load()):
            self.MailFrom = acc.Mail
            self.Name = acc.Name
            self.MailBcc = acc.SendBCCCopy

    def pasteCustCode(self):
        if (self.EntityType==0):
          from Customer import Customer
          cust = Customer.bring(self.CustCode)
          if (cust):
              self.CustName = cust.Name
              self.MailTo = cust.Email
        elif (self.EntityType==1):
            from Supplier import Supplier
            sup = Supplier.bring(self.CustCode)
            if sup:
              self.CustName = sup.Name
              self.MailTo = sup.Email
        elif (self.EntityType==2):
            from Person import Person
            sup = Person.bring(self.CustCode)
            if sup:
              self.CustName = sup.Name
              self.MailTo = sup.Email

    def seachThreadId(self,user = currentUser()):
        mailThreadId = self.Id
        parentId = self.ParentId
        if parentId != "" and parentId != None and parentId != "-1":
            parent = Mail()
            parent.Id = parentId
            if parent.load():
                mailThreadId = parent.ThreadId
        else:
            #busco por asunto
            query = Query()
            query.sql = "SELECT {ThreadId} FROM [Mail]\n"
            query.sql += "WHERE?AND {User}=s|%s|\n" % user
            query.sql += "WHERE?AND {Subject}=s|%s|\n" % self.Subject
            query.sql += "ORDER BY {TransDate} DESC\n"
            query.sql += "LIMIT 1\n"
            if query.open() and query.count():
                mailThreadId = query[0].ThreadId
                query.close()
        return mailThreadId

    def saveMail(self):
        """ Primero intento guardarlo con save, y si hubo algún error, obtengo
        el SerNr y hago el store
        """
        from SerNrControl import SerNrControl
        res = self.save()
        if not res:
            if not self.SerNr:
                self.SerNr = SerNrControl.getNextSerNr(self)
            return self.store()
        return res

    def getFooter(self):
        from OurSettings import OurSettings
        from MailAccount import MailAccount
        from User import User
        mailaccount = MailAccount.bring(self.MailCode)
        footer = ""
        if mailaccount and mailaccount.AddSignature:
            companylogo = ""
            qry = Query()
            qry.sql = "SELECT [att].{internalId} FROM [Attach] [att] \n"
            qry.sql += "WHERE [att].{OriginRecordName} = s|OurSettings| \n"
            qry.sql += "ORDER BY [att].{internalId} DESC \n"
            qry.sql += "LIMIT i|1| \n"
            oursett = OurSettings.bring()
            if (qry.open() and qry.count() >= 1) and (oursett and oursett.Logo):
                companylogo = '<img width="80" src="%s" />' % qry[0].internalId
                #alert(qry[0].internalId)
            #alert("companylogo : %s" % companylogo)

            footer_info = mailaccount.getFooterInfo()
            footer += '<table border="0" cellspacing="0" cellpadding="0">'
            footer += '  <tr> '
            footer += '    <td width="0" > %s </td>' % companylogo
            if footer_info["Name"]:
                footer += '    <td nowrap><p><font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90"><strong>%s</strong></font><br> ' % (footer_info["Name"], )
            if footer_info["Address"]:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s</font><br>'  % (footer_info["Address"], )
            # Filtro para que solo queden los campos que tienen alg?n valor.
            city = " - ".join(filter(lambda x: x,(footer_info["City"], footer_info["Province"], footer_info["Country"])))
            if city:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s</font><br>'  % (city)
            if footer_info["Phone"]:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s: %s</font><br>'  % (tr("Phone"), footer_info["Phone"], )
            if footer_info["CellPhone"]:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s: %s</font><br>'  % (tr("Cell Phone"), footer_info["CellPhone"], )
            if footer_info["Site"]:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s</font><br>'  % (footer_info["Site"], )
            if footer_info["OtherData"]:
                footer += '      <font face="Verdana, Arial, Helvetica, sans-serif" size="2" color="#A39A90">%s</font><br>'  % (footer_info["OtherData"], )
            footer += '        </p>'
            footer += '    </td>'
            footer += '  </tr>'
            footer += '</table>'

        footer += '<table><tr><td><a href="http://www.openorange.com/" ><img border="0" src="http://www.openorange.com/gen_by_oo.png" /></a></td></tr></table>'
        footer += '</body>'

        return footer


    def send(self, server=None, port=None, user=None, password=None, sslflag=None, quiet=False):
        res = False
        self.sendResponse = None
        if not server or not port or sslflag is None:
            from MailAccount import MailAccount
            mailaccount = MailAccount.bring(self.MailCode)
            if (mailaccount):
                server = mailaccount.SMTPServer
                sslflag = mailaccount.SMTPReqSSL
                port = mailaccount.SMTPPort
                if (mailaccount.SMTPReqAuth):
                    user = mailaccount.SMTPUser
                    password = mailaccount.SMTPPassword
        from ServerSettings import ServerSettings
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEText import MIMEText
        from email.MIMEImage import MIMEImage
        from email.MIMEBase import MIMEBase
        from email import Encoders
        import smtplib
        import email.Utils

        try:
            if (self.Name):
                strFrom = "\"%s\" <%s>" % (self.Name, self.MailFrom)
            else:
                strFrom = self.MailFrom
            strTo = re.sub(">.*$", "", re.sub("^.*<", "", self.MailTo))
            strCc = self.MailCc
            strBcc = self.MailBcc
            import email.Utils
            if (not self.Id): # si es la primera vez que mando el mailing
                self.Id = email.Utils.make_msgid()
                if self.ThreadId == "" or self.ThreadId == None or self.ThreadId == "-1":
                    self.ThreadId = self.Id
            strId = self.Id
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = self.Subject.replace("\r","").replace("\n","")
            msgRoot['From'] = strFrom
            msgRoot['To'] = strTo
            msgRoot['Cc'] = strCc
            msgRoot['Bcc'] = strBcc
            msgRoot['Message-Id'] = strId
            msgRoot.preamble = 'This is a multi-part message in MIME format.'

            msgAlternative = MIMEMultipart('alternative')
            msgRoot.attach(msgAlternative)

            body = self.MessageBody
            footer = self.getFooter()
            if self.RequestReadNotification:
                pass
                import base64
                from WebSettings import WebSettings
                ws = WebSettings.bring()
                webport = 80
                if ws.Port: webport = ws.Port
                webserver = ws.Host
                if webserver:
                    import urllib
                    params = {"id": base64.b64encode(self.Id)}
                    params = urllib.urlencode(params)
                    footer += '<img src="http://%s:%i/cgi-bin/rmnotify.py?i%s"/>' % (webserver, webport, params)

            if body.find('</body>') != -1:
                body = body.replace('</body>', footer)
            else: body += footer
            attids = []
            if not self.IgnoreImages:
                tags = self.getIMGTags(body)
                for tag in tags:
                    attid = self.getFilenameFromIMG(tag)
                    if attid:
                        newattid = attid.replace(attid, "cid:" + attid)
                        newtag = tag.replace(attid, newattid)
                        body = body.replace(tag, newtag)
                        attids.append(attid)

                i = 0
                for attachid in attids:
                    i += 1
                    imgstr = self.getAttachAsString(attachid)
                    if imgstr != "":
                        msgImage = MIMEImage(imgstr)
                        msgImage.add_header('Content-ID', "<%s>" % attachid)
                        msgRoot.attach(msgImage)
            for attach in self.getAttachs():
                if str(attach.internalId) not in attids:
                    if attach.Comment.endswith(".ics"):
                        part = MIMEBase('text/calendar','charset=US-ASCII; name="%s"' % attach.Comment)
                    else:
                        part = MIMEBase('application', "octet-stream")
                    part.set_payload( attach.Value )
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % attach.Comment)
                    msgRoot.attach(part)
            import codecs
            import encodings.utf_8
            msgText = MIMEText(body.encode("utf8"), 'html', 'utf-8')
            msgAlternative.attach(msgText)
            if sslflag:
                smtp = smtplib.SMTP_SSL(server, port)
            else:
                smtp = smtplib.SMTP(server, port)

            if (user and password):
                smtp.login(user, decode(password))
            #Genero una unica lista con todos los campos To
            if strTo:
                strTo = self.normalizeString(strTo)
            if strCc:
                strCc = self.normalizeString(strCc)
            if strBcc:
                strBcc = self.normalizeString(strBcc)

            to = []
            for a in strTo:
                to.append(a)
            for a in strCc:
                to.append(a)
            for a in strBcc:
                to.append(a)
            try:
                badSent = smtp.sendmail(strFrom, to, msgRoot.as_string().encode("utf8"))
            except Exception, e:
                if not quiet: message(utf8(e))
                log("Addresses Format Error: %s" %str(e))
                badSent = {".":(504,"Addresses Format Error")}
            self.sendResponse = badSent
            if (badSent):
                if not quiet:
                    self.appendMessage("Hubo errores con las siguientes direcciones:")
                log("Hubo errores con las siguientes direcciones:")
                for bad in badSent:
                    if not quiet:
                        self.appendMessage("Mail: %s, Error: %s" % (bad, badSent[bad]))
                    log("Mail: %s, Error: %s" % (bad, badSent[bad]))
                    self.SentFlag = False
                    self.Status = 0
                    self.saveMail()
            else:
                self.SentFlag = True
                self.Status = Mail.SENT
                self.saveMail()
                smtp.quit()
                res = True

        except Exception, e:
            import traceback
            import StringIO
            s = StringIO.StringIO()
            traceback.print_exc(file=s)

            res = ErrorResponse(s.getvalue())
            self.SentFlag = False
            self.Status = 0
            self.saveMail()
            try:
                smtp.quit()
            except:
                pass
            log("Error enviando mail receptor %s: %s" % (self.MailTo,s.getvalue()))
            log(e)

        return res

    def normalizeString(self, addresses):
        addresses = filter(lambda x: bool(x), addresses.replace(";", ",").replace(" ", "").split(","))
        return addresses

    def getIMGTags(self, html):
        tags = []
        regexp = re.compile("(<img[^>]*>)")
        pos = 0
        while True:
            search = regexp.search(html,pos)
            if search:
                pos = search.end(1) + 1
                for g in search.groups():
                    if g not in tags:
                        tags.append(g)
            else:
                break
        return tags

    def getFilenameFromIMG(self, tag):
        res = ""
        regexp = re.compile("src=[\"']?([^\"' >]*)")
        search = regexp.search(tag)
        if len(search.groups()) and not search.group(1).startswith("http"): res = search.group(1)
        return res

    def addHTML(self, html, quiet=False,pathdir = ""):
        #internalId must be defined for the record. Save the record before calling this method.
        #This is because importing html sometimes derives in attaching images, etc.; and this attachs are linked by the record internalId
        newhtml = html
        #log(newhtml)
        if not self.IgnoreImages:
            tags = self.getIMGTags(html)
            for tag in tags:
                imgfn = self.getFilenameFromIMG(tag)

                if imgfn != "":
                    try:
                        if pathdir and pathdir[-1] not in ("\\","/"): pathdir+="/"
                        img = file(pathdir+imgfn, "rb")
                        attachid = self.createMimeImageAttach(img.read())
                        img.close()
                        newtag = tag.replace(imgfn, attachid)
                        newhtml = newhtml.replace(tag, newtag)
                    except:
                        if not quiet: self.appendMessage(tr("File could not be opened:") + str(pathdir)+str(imgfn))
                        else: log(tr("File could not be opened:") + str(pathdir)+str(imgfn))
        self.MessageBody += newhtml
        return self.save()

    def importHTML(self, html, quiet=False,pathdir = ""):
        #internalId must be defined for the record. Save the record before calling this method.
        #This is because importing html sometimes derives in attaching images, etc.; and this attachs are linked by the record internalId
        newhtml = html
        #log(newhtml)
        if not self.IgnoreImages:
            tags = self.getIMGTags(html)
            for tag in tags:
                imgfn = self.getFilenameFromIMG(tag)

                if imgfn != "":
                    try:
                        if pathdir and pathdir[-1] not in ("\\","/"): pathdir+="/"
                        img = file(pathdir+imgfn, "rb")
                        attachid = self.createMimeImageAttach(img.read())
                        img.close()
                        newtag = tag.replace(imgfn, attachid)
                        newhtml = newhtml.replace(tag, newtag)
                    except:
                        if not quiet: self.appendMessage(tr("File could not be opened:") + str(pathdir)+str(imgfn))
                        else: log(tr("File could not be opened:") + str(pathdir)+str(imgfn))
        self.MessageBody = newhtml
        return self.save()
    # si una direccion viene de la forma: <nombre> "dir@algo.com"
    # devuelve dir@algo.com
    @staticmethod
    def getStdMail(dirMail):
        import re
        mails = re.findall("<.*>", dirMail)
        for mail in mails:
            return re.sub("[ <>]", "", mail)
        return dirMail

    # si una direccion viene de la forma: <nombre> "dir@algo.com"
    # devuelve nombre
    @staticmethod
    def getStdName(dirMail):
        import re
        return re.sub("\"", "", re.sub("<.*>", "", dirMail))

    def getMailPreferences(self):
        from MailAccount import MailAccount
        ma = MailAccount()
        ma.Mail = self.MailFrom
        mp = None
        if ma.load():
            from MailPreferences import MailPreferences
            mp = MailPreferences.bring(ma.Code)
        return mp

    def addSignature(self):
        mp = self.getMailPreferences()
        if mp and mp.Signature:
            res = self.addHTML(mp.Signature)
            """
            from Attach import Attach
            for imgid in mp.mimeImageAttachIds():
                att = Attach()
                att.internalId = imgid
                if att.load():
                    natt = att.clone()
                    natt.OriginRecordName="Mail"
                    natt.OriginId=str(self.SerNr)
                    res = natt.store()
                    if not res: return res
                sg = sg.replace("src=%s" % imgid, "src=%s" % str(natt.internalId))
            self.MessageBody += sg
            """
            if not res: return res
        return True
