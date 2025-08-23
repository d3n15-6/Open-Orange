#encoding: utf-8
from OpenOrange import *

ParentPeriod = SuperClass("Period", "Master", __file__)
class Period(ParentPeriod):
    __first__ = None

    @classmethod
    def firstPeriod(objclass):
        if not Period.__first__:
            q = Query()
            q.sql = "SELECT {Code} FROM [Period] ORDER BY {Code} ASC "
            q.setLimit(1)
            if q.open() and q.count():
                Period.__first__ = Period.bring(q[0].Code)
            else:
                Period.__first__ = Period()
        return Period.__first__