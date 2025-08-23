#encoding: utf-8
from core.ClientServerTools import *

def checkCommitConsistency(fn):
    def decorated_function(*args, **kwargs):
        try:
            try:
                check_modifying_queries = True
                from database.Database import Database
                db = Database.getCurrentDB()
                old_modifying_queries = db.modifying_queries
            except Exception ,e:
                check_modifying_queries = False
            return fn(*args, **kwargs)
        finally:
            if check_modifying_queries and old_modifying_queries != db.modifying_queries and db.modifying_queries != 0:
                from functions import message, rollback, commit
                rollback()
                message("Commit expected and never received. Rolling back last changes. Please contact OpenOrange.")
    return decorated_function

def checkTransactionForAction(fn):
    def validRecord(*args, **kwargs):
        window = args[0]
        record = window.getRecord()
        if (record.isInvalid() or not record.confirmed() or record.isNew() or record.isModified()):
            from functions import message, tr
            message(tr("The Transaction Is Not Valid, Confirmed or Saved to Perform This Action"))
        else:
            return fn(*args, **kwargs)
    return validRecord

def checkIfNewOrModified(fn):
    def validRecord(*args, **kwargs):
        window = args[0]
        record = window.getRecord()
        if (record.isNew() or record.isModified()):
            from functions import message, tr
            message(tr("REGISTERNOTSAVED"))
        else:
            return fn(*args, **kwargs)
    return validRecord
    
def checkCurrentUserCanDoAction(fn):
    def userCanDo(*args, **kwargs):
        from functions import currentUserCanDo, alert, message, tr
        window = args[0]
        actionname = args[1]
        record = window.getRecord()
        res = currentUserCanDo("%sActions" %(window.name()),True)
        res = currentUserCanDo("%sActions.%s" %(window.name(),actionname),res)
        if (not res):
            message(tr("Action is not allowed"))
            return
        else:
            return fn(*args, **kwargs)
    return userCanDo

def runOnClient(fn):
    from functions import sysprint
    #sysprint(str(dir(fn)))
    def decorated_function(self, *args, **kwargs):
        cc = getClientConnection()
        if cc:
            return cc.runOnClient(self.__class__, fn.__name__, self, *args)
        else:
            return fn(self, *args)
    return decorated_function