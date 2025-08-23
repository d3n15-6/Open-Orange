#encoding: utf-8
from OpenOrange import *

ParentComputer = SuperClass("Computer","Master",__file__)
class Computer(ParentComputer):

    buffer = RecordBuffer("Computer")
    
    @classmethod
    def isPos(objclass): 
        from LocalSettings import LocalSettings
        from Computer import Computer
        ls = LocalSettings.bring()
        comp = Computer.bring(ls.Computer)
        posf = False
        if (comp):
           posf = comp.POSflag
        return posf
