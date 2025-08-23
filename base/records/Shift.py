#encoding: utf-8
from OpenOrange import *

ParentShift = SuperClass("Shift","Master",__file__)
class Shift(ParentShift):
    buffer = RecordBuffer("Shift")
    
    def defaults(self):
        self.Status = 0
        self.Type = 1
        list = ["Sun","Mon","Tue","Wen","Thu","Fri","Sat"]
        for field in list:
            self.fields(field).setValue(True)

    def check(self):
        result = ParentShift.check(self)
        if not result:
            return result
        for fieldname in ("Name","StartTime"):                            # Office should not be Compulsory
            if not self.fields(fieldname).getValue():
                return self.FieldErrorResponse("NONBLANKERR",fieldname)
        return True

    def pasteTime(self):
        sTime=timedelta(hours=self.StartTime.hour,minutes=self.StartTime.minute,seconds=self.StartTime.second)
        eTime=timedelta(hours=self.EndTime.hour,minutes=self.EndTime.minute,seconds=self.EndTime.second)
        diff = abs(eTime-sTime)
        total_secs = diff.seconds
        secs = total_secs % 60
        total_mins = total_secs / 60
        mins = total_mins % 60
        hours = total_mins / 60
        seg=str(secs).rjust(2,"0")
        self.Duration =  (hours + (mins/60.0))
