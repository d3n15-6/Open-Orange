#encoding: utf-8
from OpenOrange import *
import time
import sys
import os

ParentVersionSettings = SuperClass("VersionSettings", "Setting", __file__)
class VersionSettings(ParentVersionSettings):
    buffer = SettingBuffer()

    def update(self):
        if os.path.exists("updates.disable"):
            return True
        if self.NewMode:
            return self.update_new()
        return self.update_old()

    def update_old(self):
        if sys.platform.startswith("win"):
            for pathrow in self.Paths:
                if pathrow.Enabled and (not pathrow.User or pathrow.User == currentUser()):
                    pathrow.update()

    def update_new(self, force_reinit = False):
        import os
        if sys.platform.startswith("win"):
            fn = "wc_update.bat"
        else:
            fn = "wc_update.sh"
        if os.path.exists(fn): os.remove(fn)
        if True:
            lines = []
            for pathrow in self.Paths:
                if pathrow.Enabled and (not pathrow.User or pathrow.User == currentUser()):
                    res = pathrow.update_new()
                    if res:
                        lines.append(res)
            pass
            if force_reinit or len(lines):
                if sys.platform.startswith("win"):
                    lines.insert(0, "echo Gracias")
                    lines.insert(0, "echo ATENCION!! no cierre esta ventana hasta finalizar la actualizacion")
                    lines.insert(0, "@echo off")
                else:
                    lines.insert(0, "echo \"Gracias\" ")
                    lines.insert(0, "echo \"ATENCION!! no cierre esta ventana hasta finalizar la actualizacion\" ")
                message("There Is an Update Available. OpenOrange Will Download The Update And Restart.")
                from Company import Company
                from User import User
                company = Company()
                company.Code = currentCompany()
                company.load()
                user = User.bring(currentUser())
                dbname = company.DBName
                if not dbname: dbname = company.Code
                script = '\n'.join(lines)
                if sys.platform.startswith("win"):
                    script += "\nDEL /Q /S *.pyc\nstart OpenOrange.exe --company=%s --dbhost=%s --dbport=%s --dbuser=%s --dbpassword=%s --dbname=%s --oouser=%s --oopassword=%s --scriptdirs=%s\n" % (currentCompany(), currentCompanyHost(), company.Port, company.User, decode(company.Password), dbname, user.Code, user.Password, ':'.join(reversed(getScriptDirs())))
                    script += "echo."
                elif getPlatform() == "linux":
                    script += "\nfind -iname *.pyc | xargs -i rm {} \n./OpenOrange.sh --company=%s --dbhost=%s --dbport=%s --dbuser=%s --dbpassword=%s --dbname=%s --oouser=%s --oopassword=%s --scriptdirs=%s\n" % (currentCompany(), currentCompanyHost(), company.Port, company.User, decode(company.Password), dbname, user.Code, user.Password, ':'.join(reversed(getScriptDirs())))
                else:
                    script += "\nrm -r OpenOrange.app\n"
                    script += "\ntar xvzf OpenOrange-OSX.tgz\n"
                    script += "\nfind -iname *.pyc | xargs -i rm {} \n./OpenOrange.app/Contents/MacOS/OpenOrange --company=%s --dbhost=%s --dbport=%s --dbuser=%s --dbpassword=%s --dbname=%s --oouser=%s --oopassword=%s --scriptdirs=%s\n" % (currentCompany(), currentCompanyHost(), company.Port, company.User, decode(company.Password), dbname, user.Code, user.Password, ':'.join(reversed(getScriptDirs())))
                log('\n'.join(lines))    
                wcupdate = open(fn, "w")
                wcupdate.write(script)
                wcupdate.close()
                if sys.platform.startswith("win"):
                    os.execl(fn,fn)
                else:
                    os.system("chmod 777 %s" % fn)
                    os.execl("/bin/sh", "sh", fn)

    def checkScriptDirs(self):
        res = True
        sd = getScriptDirs(999)
        sd.reverse()
        i = 0
        for row in self.ScriptDirs:
            if not row.User or row.User == currentUser():
                if i >= len(sd) or sd[i] != row.ScriptDir:
                    res = False
                    break
                i += 1
        if len(sd) != i: res = False
        if not res:
            sds = []
            for row in self.ScriptDirs:
                sds.append(row.ScriptDir)
            postMessage("La configuracion de scriptdirs para conectarse a esta base de datos debe ser: %s<br>Revisar el archivo %s." % (sds,getSettingsFileName()))
        return res

    def showVersionNovelties(self):
        #for u in [ x for x in self.NoveltiesUsers.split(",") if x ]:
        #    nrow = VersionSettingsNoveltyRow()
        #    nrow.User = u.split(":")[0]
        #    nrow.Revision = u.split(":")[1]
        #    self.Novelties.append(nrow)
        #self.NoveltiesUsers = None
        #res = self.save()
        #if (res):
        #    commit()
        #else:
        #    message(res)

        name,v = self.getNoveltiesFile();
        if (name):
            if (v > self.getLastNovelties(currentUser())):
                from VersionNoveltiesReport import VersionNoveltiesReport
                vnovel = VersionNoveltiesReport()
                vnovel.defaults()
                vnovel.noveltiesfilename = "%s.%s" %(name,v)
                vnovel.open(False)
                
    def getNoveltiesFile(self):
        from OurSettings import OurSettings
        oset = OurSettings.bring()
        import os
        name, v = "",0
        for fname in sorted(os.listdir('./tmp')):
            if (fname.startswith("VersionNovelties_%s" %(oset.Language))):
                name,v = fname.split(".")
                return utf8(name),utf8(v)
        return utf8(name),utf8(v)

    def getLastNovelties(self, usercode):
        rows = [x.Revision for x in self.Novelties if x.User == usercode]
        if (rows):
            return rows[0]
        return -1

    def setLastNovelties(self, usercode, version):
        updated = False
        for nrow in self.Novelties:
            if (nrow.User == usercode):
                nrow.Revision = version
                updated = True
        if (not updated):
            nrow = VersionSettingsNoveltyRow()
            nrow.User = usercode
            nrow.Revision = version
            self.Novelties.append(nrow)
        res = self.save()
        if (res):
            commit()
        else:
            log(res)

ParentVersionSettingsPath = SuperClass("VersionSettingsPath", "Record", __file__)
class VersionSettingsPath(ParentVersionSettingsPath):

    def update_new(self):
        if sys.platform.startswith("win"):
            svnclientpath = "svnclient\\"
        elif sys.platform.startswith("linux"):
            svnclientpath = ""
        else:
            svnclientpath = "/usr/local/bin/"
        import os
        os.system(svnclientpath + "svn info --no-auth-cache --username %s --password %s \"%s\" > ./tmp/wc_info.tmp" % (self.SVNUserName, self.SVNPassword, self.Path))
        wcinfo = open("./tmp/wc_info.tmp")
        wcinfolines = wcinfo.readlines()
        try:
            wcrevision = int(wcinfolines[4][10:-1])
            url = wcinfolines[1][5:-1]
        except Exception, e:
            #cuando lo que se actualiza es un archivo y no un directorio, la fila de la revision en wc es la 6ta y no la 5ta.
            wcrevision = int(wcinfolines[5][10:-1])
            url = wcinfolines[2][5:-1]
        if wcrevision < self.Revision:
            os.system(svnclientpath + "svn info --no-auth-cache --username %s --password %s \"%s\" > repo_info.tmp" % (self.SVNUserName, self.SVNPassword, url))
            sysprint(svnclientpath + "svn info --no-auth-cache --username %s --password %s \"%s\" > repo_info.tmp" % (self.SVNUserName, self.SVNPassword, url))
            repoinfo = open("repo_info.tmp")
            repoinfolines = repoinfo.readlines()
            try:
                reporevision = int(repoinfolines[4][10:-1])
            except:
                #cuando lo que se actualiza es un archivo y no un directorio, la fila de la revision en wc es la 6ta y no la 5ta.
                reporevision = int(repoinfolines[5][10:-1])
            if reporevision >= self.Revision:
                return svnclientpath + "svn cleanup\n" + svnclientpath + "svn update --no-auth-cache --username %s --password %s -r %i \"%s\"" % (self.SVNUserName, self.SVNPassword, self.Revision, self.Path)
        return False

    #OLD METHOD STARTS HERE

    def get_login(self, realm, username, may_save ):
        return (True, self.SVNUserName, self.SVNPassword, False)

    def notify(self,  event):
        if str(event['action']) in ["update_update"]:
            for fn in self.locking_files:
                if event['path'].__str__().endswith(fn):
                    self.locking_files[fn] = True
        if str(event['content_state']) == 'conflicted':
            self.conflicts.append(event['path'].__str__())
        return


    def update(self):
        from VersionSettings import VersionSettings
        vset = VersionSettings.bring()
        self.conflicts = []
        import pysvn
        client = pysvn.Client()
        client.callback_get_login = self.get_login
        client.callback_notify = self.notify

        self.doupdate = True
        self.output = open('./tmp/changes.txt', 'wb')
        if self.Revision > 0:
            changes = client.status(self.Path, get_all=True, update=False, recurse=False)
            self.doupdate = False
            for change in changes:
                try:
                    self.output.write(str(change.entry.commit_revision.number) + '\t')
                except:
                    self.output.write('\t')
                if change.is_versioned and change.entry:
                    self.output.write(str(change.entry.copy_from_revision.number) + '\t'+ str(change.entry.commit_revision.number) + '\t'+ str(change.entry.revision.number) + '\t')
                    if not change.entry.revision.number or change.entry.commit_revision.number > change.entry.revision.number:
                        self.doupdate = True
                self.output.write(str(change.text_status) + '\t' + str(change.repos_text_status) + '\t' + str(change) + '\n')
                if change.is_versioned and change.entry:
                    if self.Revision > change.entry.revision.number:
                        self.doupdate=True
                        break
        if self.doupdate:
            self.locking_files = {"OpenOrange.exe":False,\
                                  "ODBC32.DLL":False, \
                                  "MSVCRTD.DLL":False,\
                                  "msvcr71.dll":False,\
                                  "libmySQL.dll":False,\
                                  "python24.dll":False,\
                                  "qt-mt334.dll":False,\
                                  "StackTrace.dll":False}
            try:
                self.output.write("updating...\n")
                rev = 'head'
                if self.Revision > 0: rev = self.Revision
                trmessage = tr("Updating OpenOrange version of",self.Path,"to revision",rev,"This operation could take a few minutes ...")
                if (vset.ShowPostInsteadAlerts):
                    postMessage(trmessage)
                else:
                    message(trmessage)
                #postMessage(trmessage, 1000, 100000)
                try:
                    rev=pysvn.Revision( pysvn.opt_revision_kind.head)
                    if self.Revision > 0:
                        rev=pysvn.Revision( pysvn.opt_revision_kind.number, self.Revision )
                    if sys.platform.startswith("win"):
                        for fn in self.locking_files:
                            if os.path.exists(fn + ".replaced"): os.remove(fn + ".replaced")
                            os.rename(fn, fn + ".replaced")
                            client.revert(fn)
                    client.update(self.Path, revision=rev, recurse=True)
                    while len(self.conflicts):
                        conflicts = self.conflicts
                        self.conflicts = []
                        for path in conflicts:
                            trmessage = tr("The file",path,"has local changes, do you want to revert those changes?")
                            message(trmessage)
                            if askYesNo():
                                client.callback_notify = self.notify
                                client.revert(path, recurse=False)
                                client.callback_notify = None
                                client.update(path, revision=rev, recurse=True)
                except Exception, e:
                    message(e)
                trmessage = tr("Your OpenOrange version was updated. Please restart OpenOrange to see the changes.")
                if (vset.ShowPostInsteadAlerts):
                    postMessage(trmessage)
                else:
                    message(trmessage)
            finally:
                if sys.platform.startswith("win"):
                    for fn in self.locking_files:
                        if not self.locking_files[fn] and os.path.exists(fn + ".replaced") and os.path.exists(fn):
                            try:
                                os.remove(fn)
                                os.rename(fn + ".replaced", fn)
                            except:
                                message(tr("The following file has been blocked by the Operating System") + fn)
        self.output.close()

ParentVersionSettingsNoveltyRow = SuperClass("VersionSettingsNoveltyRow","Record",__file__)
class VersionSettingsNoveltyRow(ParentVersionSettingsNoveltyRow):
    pass