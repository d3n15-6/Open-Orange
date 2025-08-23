#encoding: utf-8
from OpenOrange import *

ParentLocalSettings = SuperClass('LocalSettings','Setting',__file__)
class LocalSettings(ParentLocalSettings):
    buffer = SettingBuffer()

    def defaults(self):
        self.UserMode = 0 #normal user
        
    def check(self):
        res = ParentLocalSettings.check(self)
        if (not res): return res
        from Computer import Computer
        if not Computer.exists(self.Computer):
           return self.FieldErrorResponse("INVALIDVALUEERR","Computer")
        return True
