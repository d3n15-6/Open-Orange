# encoding: utf-8
from OpenOrange import *
from string import *
from ReportTools import *
from Palette import *
from GlobalTools import *
import sys
from core.database.Database import DBError
from xml.sax import handler, saxutils
from Report import *


class TxtReport(Report):

    def startTable(self, *vargs, **kwargs):
        pass

    def endTable(self):
        pass

    def printReportTitle(self,title=""):
        self.addHTML("Title: %s\n" % title)

    def addValue(self, v, *vargs, **kwargs):
        self.addHTML("%s\t" % v )

    def startHeaderRow(self, htmlclass=None):
        self.addHTML("")

    def endHeaderRow(self):
        self.addHTML("\n")

    def startRow(self, *vargs, **kwargs):
        self.addHTML("")

    def endRow(self):
        self.addHTML("\n")

    def row(self, *vargs):
        self.addHTML("\t".join(map(str,vargs)) + "\n")

    def header(self, *vargs):
        self.addHTML("\t".join(map(str,vargs)) + "\n")

    def startReport(self):
        pass

    def endReport(self):
        pass

