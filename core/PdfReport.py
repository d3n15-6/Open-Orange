from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.platypus import *
from reportlab.lib import colors
from functions import *
from reportlab.lib.units import inch,cm
from reportlab.lib.pagesizes import letter
from Report import *
from OpenOrange import *
import Web
from functions import es2en

class PdfReport(Report):

    def printReportTitle(self,title=""):
        self.ReportTitle = "Report: %s/n" % title

    def startReport(self):
        # First the top row, with all the text centered and in Times-Bold,
        # and one line above, one line below.
        ts = [('ALIGN', (1,1), (-1,-1), 'LEFT'),
             ('LINEABOVE', (0,0), (-1,0), 1, colors.purple),
             ('LINEBELOW', (0,0), (-1,0), 1, colors.purple),
             ('FONT', (0,0), (-1,0), 'Times-Bold'),
             ('FONTSIZE', (0, 0), (-1, -1), 8),
        # The bottom row has one line above, and three lines below of
        # various colors and spacing.
             #('LINEABOVE', (0,-1), (-1,-1), 1, colors.purple),
             #('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.purple,
             # 1, None, None, 4,1),
             #('LINEBELOW', (0,-1), (-1,-1), 1, colors.red),
             ('FONT', (0,-1), (-1,-1), 'Times-Bold')]
        self.ts = ts
        self.currenttable = None
        self.currentrow = None
        self.tables = []
        filename = "%s_%s_%s.pdf" %(self.name(),today().strftime("%Y%m%d"),now().strftime("%H%M"))
        self.doc = SimpleDocTemplate(filename,allowSplitting=1) #pagesize=(300,300)
        self.Story = [Spacer(1,1.5*cm)]
        self.ReportTitle = self.name()

    def endReport(self):
        #for t in self.tables:
        #    self.Story.append(t)
        def myLaterPages(canvas, doc):
            canvas.saveState()
            canvas.setFont('Times-Roman',9)
            canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, self.ReportTitle))
            canvas.restoreState()

        def myFirstPage(canvas, doc):
            canvas.saveState()
            canvas.setFont('Times-Bold',14)
            PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
            canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, self.ReportTitle)
            canvas.setFont('Times-Roman',9)
            canvas.drawString(inch, 0.75 * inch, "First Page / %s" % self.ReportTitle)
            canvas.restoreState()

        for table in self.tables:
            self.Story.append(table)
        self.doc.build(self.Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)   # save!

    def startTable(self, *args, **kwargs):
        if self.currenttable is None:
            self.currenttable = []

    def endTable(self, *args, **kwargs):
        if self.currenttable:
            #alert(self.currenttable)
            repLabTable = Table(self.currenttable, style=self.ts)
            self.tables.append(repLabTable)
            self.currenttable = None

    def startRow(self, *args, **kwargs):
        if self.currenttable is not None and self.currentrow is None:
            self.currentrow = []

    def endRow(self, *args, **kwargs):
        if self.currenttable is not None and self.currentrow is not None:
            self.currenttable.append(self.currentrow)
            self.currentrow = None

    def startHeaderRow(self, htmlclass=None):
        if self.currenttable is not None and self.currentrow is None:
            self.currentrow = []

    def endHeaderRow(self):
        if self.currenttable is not None and self.currentrow is not None:
            self.currenttable.append(self.currentrow)
            self.currentrow = None

    def addValue(self, value, *args, **kwargs):
        if self.currenttable is not None and self.currentrow is not None:
            colspan = int(kwargs.get("ColSpan",0))
            try:
                if (isinstance(value,str)):
                    self.currentrow.append(value.encode("ascii","ignore"))
                else:
                    self.currentrow.append(value)
                #self.currentrow.append(es2en(str(value)))
                #self.currentrow.append(str(Web.escapeXMLValue(value)))
            except Exception, err:
                self.currentrow.append(str(value))
            for q in range(0,colspan-1):
                self.currentrow.append("")

    def addImage(self, v, **kwargs):
        pass