from OpenOrange import *

class WebReportView(object):
    
    def __init__(self, name):
        self.name = name
        self.window = None
        self.report = None

    def resize(self, w, h):
        pass