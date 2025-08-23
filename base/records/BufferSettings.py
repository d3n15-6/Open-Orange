#encoding: utf-8
from OpenOrange import *

ParentBufferSettings = SuperClass("BufferSettings", "Setting", __file__)
class BufferSettings(ParentBufferSettings):
    __records__ = None
    
    @classmethod
    def loadExpirations(classobj):
        from core.database.Database import DBError    
        classobj.__records__ = {}
        try:
            bs = classobj.bring()
            for row in bs.Records:
                classobj.__records__[row.RecordName] = timedelta(hours=row.Expiration.hour, minutes=row.Expiration.minute, seconds=row.Expiration.second)
        except DBError, e:
            from functions import processDBError
            processDBError(e, {}, str(e))
    
    @classmethod        
    def getExpiration(classobj, recordname, default=RecordBuffer.defaulttimeout):
        if classobj.__records__ is None:
            from core.database.Database import DBConnectionError
            try:
                classobj.loadExpirations()
            except DBConnectionError, e:
                return timedelta()
        return classobj.__records__.get(recordname, default)

