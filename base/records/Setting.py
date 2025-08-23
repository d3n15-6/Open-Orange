#encoding: utf-8
from OpenOrange import *

class Setting(Record):
    
    @classmethod
    def bring(classobj):
        if classobj().isLocal():
            cc = getClientConnection()
            if cc:
                return cc.runOnClient(classobj, "bring", None)
        res = None
        if hasattr(classobj, "buffer"):
            try:
                res = classobj.buffer[None]
            except KeyError, e:
                res = classobj()
                res.load()
                classobj.buffer[None] = res
        else:
            res = classobj()
            res.load()
        return res