#encoding: utf-8
#coding=iso-8859-15
from OpenOrange import *
from GlobalTools import *

ParentTRT5SettingsWindow = SuperClass("TRT5SettingsWindow","SettingWindow",__file__)
class TRT5SettingsWindow(ParentTRT5SettingsWindow):
    
    def afterEditRow(self, fname, rfname, rownr):
        afterEditRow(self, fname, rfname, rownr)