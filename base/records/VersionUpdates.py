#encoding: utf-8
from OpenOrange import *
import os

ParentVersionUpdates = SuperClass("VersionUpdates","Master",__file__)
class VersionUpdates(ParentVersionUpdates):

    @classmethod
    def checkUpdatesFiles(objclass):
        for lfile in sorted(os.listdir("base/updates")):
            fname = lfile.split(".")[0]
            fext = lfile.split(".")[-1]
            #alert((lfile,fname.startswith("Update") , fext == ".py" , len(fname) == 10))
            if (fname.startswith("Update") and fext == "py" and len(fname) == 10):
                #alert(("OK",lfile))
                vu = VersionUpdates.bring(lfile)
                if (vu):
                    if (not vu.Done):
                        objclass.performUpdate(lfile)
                else:
                    vu = VersionUpdates()
                    vu.defaults()
                    vu.Code = lfile
                    res = vu.save()
                    if (res):
                        commit()
                        objclass.performUpdate(lfile)

    @classmethod
    def performUpdate(objclass, lfile):
        vu = VersionUpdates.bring(lfile)
        if (vu):
            cname = lfile.replace(".py","")
            exec("from base.updates.%s import %s" %(cname,cname))
            exec("ufile = %s()" %(cname))
            if ("performUpdate" in dir(ufile)):
                vu.RunDate = today()
                vu.RunTime = now()
                vu.User = currentUser()
                vu.Description = ufile.Description
                res = vu.store()
                if (res):
                    commit()
                else:
                    message("%s %s" %(tr("Error Updating"),cname))
                    return
                postMessage("%s %s" %(tr("Performing Update"),cname))
                mess  = "%s %s" %(tr("Performing Update"),cname)
                mess += "<font color='red'> %s: </font> \n %s " %(tr("Description"),ufile.Description)
                message(mess)
                res = ufile.performUpdate()
                if (res):
                    message("%s %s %s" %(tr("Performing Update"),cname, tr("OK")))
                    vu.UpdateResult = ufile.UpdateResult
                    vu.Done = True
                    vu.Success = True
                    res = vu.store()
                    if (res):
                        commit()
                else:
                    vu.UpdateResult = ufile.UpdateResult
                    if (hasattr(ufile,"Persistent")):
                        persistent = ufile.Persistent
                    else:
                        persistent = False
                    if (not persistent):
                        vu.Done = True
                    vu.Success = False
                    res = vu.store()
                    if (res):
                        commit()
                    message("Error in Update, see details in log")
                    log(("Error in Update %s, %s" %(cname,res)))