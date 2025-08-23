#coding: utf-8
from OpenOrange import *
from Customer import Customer
from GeneralTools import formatValue
from GlobalTools import *
from Office import Office
from OurSettings import OurSettings
from Province import Province
from TaxSettings import TaxSettings
from Language import *
from core.database.Database import DBError
from FontStyle import FontStyle
from reportlab.lib.colors import *

def standardDocFields(doc):
    doc.setStringValue("CurrentPageNr",doc.curPageNr)
    doc.setStringValue("OfficialCopy",doc.getOfficialCopy())
    doc.lastPage = doc.lastPageNr()
    doc.setStringValue("LastPageNr",doc.lastPage)
    doc.setStringValue("PageCounter",'1 / ' + str(doc.lastPage))
    ourset = OurSettings.bring()
    doc.setStringValue("OurName",ourset.Name)
    doc.setStringValue("OurName1",ourset.Name)
    doc.setStringValue("OurFantasyName",ourset.FantasyName)
    doc.setStringValue("OurAddress",ourset.Address)
    doc.setStringValue("OurCity",ourset.City)
    doc.setStringValue("OurLocality",ourset.Locality)
    doc.setStringValue("OurProvince",ourset.Province)
    from Country import Country
    country = Country.bring(ourset.Country)
    if country:
        doc.setStringValue("OurCountryName",country.Name)
    doc.setStringValue("OurCountry",ourset.Country)
    pr = Province.bring(ourset.ProvinceCode)
    prov = ourset.Province
    if pr:
        doc.setStringValue("OurProvinceName",pr.Name)
        prov = ", " + pr.Name
    zipcode = " "
    if ourset.ZipCode:
      zipcode = " (" + ourset.ZipCode + ") "
    doc.setStringValue("OurCityProvince", ourset.City + zipcode + prov)
    doc.setStringValue("OurZipCode",ourset.ZipCode)
    doc.setStringValue("OurPhone",ourset.Phone)
    doc.setStringValue("OurFax",ourset.Fax)
    doc.setStringValue("OurWeb",ourset.WebSite)
    doc.setStringValue("OurEmail",ourset.Email)
    doc.setStringValue("OurLegalInfo",ourset.LegalInfo)
    if not ourset.fields("StartDate").isNone():
      doc.setStringValue("StartActivities", ourset.StartDate.strftime("%d/%m/%Y"))
    from TaxSettings import TaxSettings
    ts = TaxSettings.bring()
    doc.setStringValue("OurSalesTax",ts.TaxRegNr1)
    doc.setStringValue("OurLegalNr",ts.LegalNr)
    TaxRegNr = ""
    TaxRegType = ""
    TaxRegNr = ts.TaxRegNr
    TaxRegType = Customer.TaxRegTypes[ts.TaxRegType]
    doc.setStringValue("CuitEmpresa", TaxRegNr)
    doc.setStringValue("CondIva", TaxRegType)
    doc.setStringValue("OurTaxRegNr", TaxRegNr)
    doc.setStringValue("OurTaxRegType", TaxRegType)
    doc.setStringValue("Today", today().strftime("%d/%m/%Y"))
    doc.setStringValue("TodayLargeFormat", tr(today().strftime("%d"), LongMonthNames[int(today().strftime("%m"))], today().strftime("%Y")))
    doc.setStringValue("Now", now().strftime("%H:%M:%S"))
    doc.setStringValue("CurrentUser", currentUser())
    doc.setStringValue("CurrentOffice", Office.default())

    # information on standard bank account
    from FinAccount import FinAccount
    fa = FinAccount()
    fa.load()
    doc.setStringValue("OurIBAN", fa.IBAN)
    doc.setStringValue("OurBank", fa.Bank)
    doc.setStringValue("OurNatStdBankAcc", fa.BnkAccRouteNr)
    doc.setStringValue("OurSwiftCode", fa.SwiftCode)

def transactionFields(doc,trans):
    from Numerable import Numerable
    if hasattr(trans, "Printed"):
        if trans.Printed:
            doc.setStringValue("Printed",tr("Printed"))
    if hasattr(trans, "Invalid"):
        if trans.Invalid:
            doc.setStringValue("Invalid",tr("Invalid"))
    if hasattr(trans, "Status"):
        if trans.Status:
            doc.setStringValue("Status",tr("Status"))
    doc.setStringValue("SerNrControl.Comment",Numerable.getSerNrControlComment(trans))

def latin1_to_ascii(unicrap):
    """This replaces UNICODE Latin-1 characters with
    something equivalent in 7-bit ASCII. All characters in the standard
    7-bit ASCII range are preserved. In the 8th bit range all the Latin-1
    accented letters are stripped of their accents. Most symbol characters
    are converted to something meaninful. Anything not converted is deleted.
    """
    xlate={0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
        0xc6:'Ae', 0xc7:'C',
        0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
        0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
        0xd0:'Th', 0xd1:'N',
        0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
        0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
        0xdd:'Y', 0xde:'th', 0xdf:'ss',
        0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
        0xe6:'ae', 0xe7:'c',
        0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
        0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
        0xf0:'th', 0xf1:'n',
        0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
        0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
        0xfd:'y', 0xfe:'th', 0xff:'y',
        0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}',
        0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
        0xa9:'{C}', 0xaa:'^a', 0xab:'<<',
        0xad:'-', 0xaf:'_',
        0xb1:'+/-', 0xb2:'^2', 0xb3:'^3', 0xb4:"'",
        0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
        0xbb:'>>',
        0xbc:'1/4', 0xbd:'1/2', 0xbe:'3/4', 0xbf:'?',
        0xd7:'*', 0xf7:'/'
        }

    r = ''
    for i in unicrap:
        if xlate.has_key(ord(i)):
            r += xlate[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += i
    return r

class Document(Embedded_Document):
    NORMAL,PDF = (0,1)
    OFICIAL_COPY_LABELS = ("", tr("First Copy"), tr("Second Copy"), tr("Third Copy"), tr("Fourth Copy"))

    def __init__(self):
        Embedded_Document.__init__(self)
        self.__fields__ = {}
        self.__mode__ = Document.NORMAL
        self.curPageNr = 1

    @classmethod
    def getTextWidth(classobj, text,font):
        if graphicModeEnabled():
            return Embedded_Document.getTextWidth(classobj(), text, font.Family, font.Size, font.Underline, font.Bold)
        else:
            size = font.Size 
            if not font.Size:
                size = 13 # 13 es el tamaño de pixel de letra 'm' en Arial
            return (len(text)*size)+5

    def printDocument(self):
        #Devolver False para que Open Orange mande el documento a la impresora (o abra el dialogo de impresion).
        #Si se devuelve True, OO supone que el evento de impresion fue manejado desde python y no hace mas nada. En este caso hay que llamar al afterPrint explicitamente antes de salir de este metodo.
        record = self.getRecord()
        if not hasattr(record, "_one_preview") or not record._one_preview:
            document = self.getDocumentSpec()
            if document:
                if document.ShowOnlyOnePreview:
                    record.printAllCopies(False,None,None)
                    self.clearPrinter(document)
                    if hasattr(record,"afterPrint"):
                        record.afterPrint(document)
                    return True
        return False

    def clearPrinter(self,document):
        dp = NewRecord("DocumentPrinter")
        dp.Code = document.Code
        if dp.load():
            dp.delete()
        #fex = "./local/DocumentPrinter.data.example"
        #fex = file(fex, "r")
        #lines = fex.readlines()
        #fex.close()
        #
        #fname = "./local/DocumentPrinter.data"
        #f = file(fname, "w")
        #for line in lines:
        #    f.write(line)

    def getMode(self):
        return self.__mode__

    def getDocumentSpec(self):
        if not hasattr(self, "documentspec"):
           self.documentspec = Embedded_Document.getDocumentSpec(self)
        return self.documentspec

    def __load_field_decimals(self):
        self.__field_decimals__ = {}
        spec = self.getDocumentSpec()
        for row in spec.Fields:
            if not row.fields("Decimals").isNone():
                self.__field_decimals__[row.Name] = row.Decimals
            else:
                self.__field_decimals__[row.Name] = -1

    def __getFieldDecimals(self, fieldname):
        if not hasattr(self, "__field_decimals__"): self.__load_field_decimals()
        return self.__field_decimals__.get(fieldname, -1)

    def setRecord(self, record):
        self.__record__ = record
        self.__original_record__ = record

    def getRecord(self):
        if not hasattr(self, "__record__"):
            self.__record__ = Embedded_Document.getRecord(self)
            self.__original_record__ = self.__record__
            try:
                self.__record__._official_copy = self.__record__._official_copy
            except AttributeError, e:
                self.__record__._official_copy = 0
                self.__original_record__._official_copy = 0
            if hasattr(self.__record__, "printingFormat"):
                official_copy = self.__record__._official_copy
                self.__record__ = self.__record__.printingFormat()
                self.__record__._official_copy = official_copy
        return self.__record__

    def getOriginalRecord(self):
        if not hasattr(self, "__original_record__"):
            self.__original_record__ = Embedded_Document.getRecord(self)
        return self.__original_record__

    def getOfficialCopyNumber(self):
        try:
            cp = self.getRecord()._official_copy
        except AttributeError, e:
            cp = 1
        return cp

    def getOfficialCopy(self):
        return self.__class__.OFICIAL_COPY_LABELS[self.getOfficialCopyNumber()]

    def run_fromC(self):
        try:
            return self.run()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return None

    def run(self):
        self.printSettingFields("OurSettings")
        standardDocFields(self)
        transactionFields(self, self.getRecord())
        self.printStandardFields(self.getRecord(),None)

    def _getDecimals(self, fieldname, **kwargs):
        decimals = kwargs.get("Decimals",-1)
        if decimals < 0:
            decimals = self.__getFieldDecimals(fieldname)
        if decimals < 0:
            currencycode = kwargs.get("Currency",None)
            if currencycode:
                from Currency import Currency
                currency = Currency.bring(currencycode)
                decimals = currency.RoundOff
        if decimals >= 0:
            return decimals
        return 2

    def setStringValue(self,fieldname, value, **kwargs):
        if isinstance(value,float):
            value = formatValue(value, self._getDecimals(fieldname, **kwargs))
            if kwargs.get("ShowSymbol",False) and kwargs.has_key("Currency"): value = kwargs["Currency"] + " " +  value
        if self.getMode() == Document.NORMAL:
            v = value
            if not isinstance(v, basestring):
                v = str(value)
            Embedded_Document.setStringValue(self,fieldname, v)
        elif self.getMode() == Document.PDF:
            v = value
            if not isinstance(v, basestring):
                v = str(value)
            self.__fields__[fieldname] =  [v]

    def addString(self,fieldname, value, **kwargs):
        if isinstance(value,float):
            value = formatValue(value, self._getDecimals(fieldname, **kwargs))
            if kwargs.get("ShowSymbol",False) and kwargs.has_key("Currency"): value = kwargs["Currency"] + " " + value
        if self.getMode() == Document.NORMAL:
            v = value
            if not isinstance(v, basestring):
                v = str(value)
            Embedded_Document.addString(self,fieldname, v)
        elif self.getMode() == Document.PDF:
            l =  self.__fields__.get(fieldname, [])
            v = value
            if not isinstance(v, basestring):
                v = str(value)            
            l.append(v)
            self.__fields__[fieldname] = l

    def beforeChangePage(self):
        if (not hasattr(self,"curPageNr")):
            self.curPageNr = 1
        self.setStringValue("CurrentPageNr",self.curPageNr)
        if (not hasattr(self,"lastPage")):
            self.lastPage = self.lastPageNr()
        self.setStringValue("PageCounter",str(self.curPageNr) + ' / ' + str(self.lastPage))
        record = self.getRecord()
        nrlist = []
        if (record.ToSerNr > record.SerNr):
            for nr in range(record.SerNr,record.ToSerNr+1):
                nrlist.append(nr)
        else:
            nrlist.append(record.SerNr)
        if self.curPageNr-1 >= len(nrlist):
            self.setStringValue("CurrentPageSerNr",nrlist[len(nrlist)-1])
        else:
            self.setStringValue("CurrentPageSerNr",nrlist[self.curPageNr-1])

    def afterChangePage(self):
        self.curPageNr += 1
        self.setStringValue("CurrentPageNr",self.curPageNr)
        self.setStringValue("PageCounter",str(self.curPageNr) + ' / ' + str(self.lastPage))
        record = self.getRecord()
        nrlist = []
        if (record.ToSerNr > record.SerNr):
            for nr in range(record.SerNr,record.ToSerNr+1):
                nrlist.append(nr)
        else:
            nrlist.append(record.SerNr)
        if self.curPageNr-1 >= len(nrlist):
            self.setStringValue("CurrentPageSerNr",nrlist[len(nrlist)-1])
        else:
            self.setStringValue("CurrentPageSerNr",nrlist[self.curPageNr-1])

    def lastPageNr(self):
        #returns 0 if the record has no details. Otherwise returns the number of rows of the detail wich has the biggest number of rows
        record = self.getRecord()
        l = map(lambda dn: record.details(dn).count(), record.detailNames())
        l.append(1)
        rPerPage = self.getDocumentSpec().RowsPerPage
        if not rPerPage: rPerPage = 1
        res = int(round((float(max(l)) / rPerPage) + 0.49999999))
        self.lastPage = res
        return res

    #CUIDADO AL CAMBIAR ESTOS METODOS
    def printStandardFields(self, record, father=None, prefix=""):
        #Recorre los campos de cabecera y los imprime
        if not record: return
        if (not father):
            father = record
        for fname in record.fieldNames():
            fvalue = record.fields(fname).getValue()
            dfname = fname
            if (prefix):
                dfname = "%s.%s" %(prefix,fname)
            if (fvalue.__class__.__name__ == "date"):
                if (not record.fields(fname).isNone()):
                    self.addString(dfname,"%s" %fvalue.strftime("%d/%m/%Y"))
                else:
                    self.addString(dfname," ")
            else:
                if (fvalue):
                    #self.addString(dfname,fvalue)
                    value = fvalue
                    if record.fields(fname).getType() == "value":
                        cur = None
                        if father and father.hasField("Currency"): cur = father.Currency
                        if record.hasField("Currency"): cur = record.Currency               # the row can have a currency as well (receipt,payment) that one goes first
                        if (cur):
                            self.addString(dfname, value, Currency = cur)
                        else:
                            self.addString(dfname, value, Currency = cur)
                    elif record.fields(fname).getType() in ("integer",):
                        if record.getFieldLabel(fname) != record.getFieldLabel(fname, record.fields(fname).getValue()):
                            value = record.getFieldLabel(fname, record.fields(fname).getValue())
                        self.addString(dfname, value)
                    else:
                        self.addString(dfname, value)
                else:
                    self.addString(dfname," ")
        #Si existe la impresion adicional de campos
        addMethod = "printAditional%s" %(record.name())
        runAddMethod = None
        if (hasattr(self,addMethod)):
            runAddMethod = getattr(self,addMethod)
        if (runAddMethod):
            runAddMethod(record)

        #Recorre las campos tipo details e imprime cada fila
        rowprefix = ""
        if prefix:
            rowprefix =  prefix + "."
        for dn in record.detailNames():
            #Si existe la redefinición de la impresión de filas se llama a esa
            stdMethod = "print%s%s" %(record.name(),dn)
            runStdMethod = None
            if (hasattr(self,stdMethod)):
                runStdMethod = getattr(self,stdMethod)
            if (runStdMethod):
                runStdMethod(record, "%s%s." % (rowprefix, dn))
            #Si existe la impresión adicional de campos se llama a esa
            addRowMethod = "printAditional%s%s" %(record.name(),dn)
            runAddRowMethod = None
            if (hasattr(self,addRowMethod)):
                runAddRowMethod = getattr(self,addRowMethod)
            #------------
            detail = record.details(dn)
            for row in detail:
                if (not runStdMethod):
                    self.printStandardFields(row,record, "%s%s" % (rowprefix, dn))
                if (runAddRowMethod):
                    runAddRowMethod(row, "%s%s." % (rowprefix, dn))

    def printFieldsCopy(self, record, prefix="",copies=""):
        if not record: return
        for fname in record.fieldNames():
            fvalue = record.fields(fname).getValue()
            dfname = fname
            if (prefix):
                dfname = "%s.%s" %(prefix,fname)
            if (copies):
                dfname = "%s.%s" %(dfname,copies)
            if (fvalue.__class__.__name__ == "date"):
                if (not record.fields(fname).isNone()):
                    self.addString(dfname,"%s" %fvalue.strftime("%d/%m/%Y"))
                else:
                    self.addString(dfname," ")
            else:
                if (fvalue):
                    self.addString(dfname,fvalue)
                else:
                    self.addString(dfname," ")

    def printRecordFields(self, tname, regcode, prefix="", copies=""):
        exec("from %s import %s" %(tname,tname))
        exec("record = %s.bring('%s')" %(tname,regcode))
        if (not prefix):
            prefix = tname
        self.printStandardFields(record,None,prefix)

    def printRecordFieldsCopy(self, tname, regcode, prefix="", copies=""):
        exec("from %s import %s" %(tname,tname))
        exec("record = %s.bring('%s')" %(tname,regcode))
        if (not prefix):
            prefix = tname
        self.printFieldsCopy(record,prefix,copies)

    def printSettingFields(self, tname, prefix=""):
        exec("from %s import %s" %(tname,tname))
        exec("record = %s.bring()" %(tname))
        if (not prefix):
            prefix = tname
        self.printStandardFields(record,None,prefix)

    @classmethod
    def isSubClassOf(subclass, superclass):
        if superclass.__name__ == subclass.__name__:
            return True
        elif superclass.__name__ == "Document":
            return False
        else:
            if (not hasattr(subclass.__bases__[0],"isSubClassOf")):
                return False
            return subclass.__bases__[0].isSubClassOf(superclass)
        return False

    @classmethod
    def createCanvas(objclass, filename, pagesize="letter"):
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
        from reportlab import lib

        exec("pagesize = lib.pagesizes.%s" %(pagesize))
        pdfmetrics.registerFont(TTFont('Arial', './base/tools/fonts/Arial.ttf'))
        pdfmetrics.registerFont(TTFont('barcode', './base/tools/fonts/FRE3OF9X.TTF'))
        curCanvas = canvas.Canvas(filename,pagesize)

        return curCanvas

    ################ PDF Generation #########################
    def genPDF(self, filename=None, curCanvas=None, documentspec=None, pagesize="letter"):
        from DocumentSpec import DocumentSpec
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
        
        if not documentspec:
            self.documentspec = DocumentSpec.bring(self.__class__.__name__)
        else:
            self.documentspec = documentspec

        saveCanvas = False
        if (not curCanvas):
            saveCanvas = True
            curCanvas = self.createCanvas(filename, pagesize)

        curCanvas.getAvailableFonts()
        availableColors = getAllNamedColors()
        #['Courier', 'Courier-Bold', 'Courier-BoldOblique', 'Courier-Oblique',
        #'Helvetica', 'Helvetica-Bold', 'Helvetica-BoldOblique', 'Helvetica-Oblique',
        #'Symbol',
        #'Times-Bold', 'Times-BoldItalic', 'Times-Italic', 'Times-Roman',
        #'ZapfDingbats']
        curCanvas.setAuthor("OpenOrange PDF Generator")
        curCanvas.setTitle(self.__class__.__name__)
        #pdfmetrics.registerFontFamily("Arial",normal="Arial",bold="Courier-Bold",italic="Courier-Oblique",boldItalic="Courier-BoldOblique")
        page_width = curCanvas._pagesize[0]
        page_height = curCanvas._pagesize[1]
        wrate = page_width / self.documentspec.Width
        hrate = page_height / self.documentspec.Height
        def translateCoords(x, y, invert_Y=True):
            x = int(x * wrate)
            if invert_Y:
                y = int(page_height - (y * hrate))
            else:
                y = int(y * hrate)
            return x,y

        self.__mode__ = Document.PDF
        self.__fields__ = {}
        self.run()
        rows_per_page = self.getDocumentSpec().RowsPerPage
        if not rows_per_page: rows_per_page = 999999999
        cur_page = 0
        max_rows = 1
        while (cur_page*rows_per_page < max_rows):
            for dsimage in self.getDocumentSpec().Images:
                x = dsimage.X
                y = dsimage.Y
                xx,yy = translateCoords(x,y)
                w,h = translateCoords(dsimage.Width, dsimage.Height, False)
                yy -= h
                curCanvas.drawImage(getImagePath(dsimage.Filename), xx,yy, w, h)

            for dsfield in self.getDocumentSpec().Fields:
                fvalues = self.__fields__.get(dsfield.Name, [])
                x = dsfield.X
                y = dsfield.Y
                max_rows = max(max_rows, len(fvalues))
                fromidx = 0
                toidx = 9999999
                if dsfield.Type == 1: #matrix
                    fromidx = cur_page*rows_per_page
                    toidx = (cur_page+1)*rows_per_page
                for fvalue in fvalues[fromidx:toidx]:
                    xx,yy = translateCoords(x,y)
                    if dsfield.getStyleRecord().Color[:1] == "#":
                        rgb = HexColor(dsfield.getStyleRecord().Color)
                    elif dsfield.getStyleRecord().Color in availableColors.keys():
                        rgb = availableColors[dsfield.getStyleRecord().Color]
                    else:
                        rgb = HexColor("#000000")
                    curCanvas.setFillColorRGB(rgb.red, rgb.green, rgb.blue)
                    curCanvas.setFont(dsfield.getStyleRecord().getPDFFont(), dsfield.getStyleRecord().Size,True)
                    asc, desc  = pdfmetrics.getAscentDescent(dsfield.getStyleRecord().getPDFFont(), dsfield.getStyleRecord().Size)
                    yy -= +asc-desc
                    try:
                        curCanvas.drawString(xx,yy,fvalue)
                    except UnicodeDecodeError, e:
                        if fvalue is not None:
                            fvalue = latin1_to_ascii(fvalue)
                        try:
                            curCanvas.drawString(xx,yy,fvalue)
                        except UnicodeDecodeError, e:
                            curCanvas.drawString(xx,yy,repr(fvalue))
                    y+=15

            for dslabel in self.getDocumentSpec().Labels:
                if (not dslabel.getStyleRecord()): continue
                x = dslabel.X
                y = dslabel.Y
                xx,yy = translateCoords(x,y)
                if dslabel.getStyleRecord().Color[:1] == "#":
                    rgb = HexColor(dslabel.getStyleRecord().Color)
                elif dslabel.getStyleRecord().Color in availableColors.keys():
                    rgb = availableColors[dslabel.getStyleRecord().Color]
                else:
                    rgb = HexColor("#000000")
                curCanvas.setFillColorRGB(rgb.red, rgb.green, rgb.blue)
                curCanvas.setFont(dslabel.getStyleRecord().getPDFFont(), dslabel.getStyleRecord().Size)
                asc, desc  = pdfmetrics.getAscentDescent(dslabel.getStyleRecord().getPDFFont(), dslabel.getStyleRecord().Size)
                yy -= +asc-desc
                try:
                    curCanvas.drawString(xx,yy, dslabel.Text)
                except UnicodeDecodeError, e:
                    if dslabel.Text is not None:
                        fvalue = latin1_to_ascii(dslabel.Text)
                    try:
                        curCanvas.drawString(xx,yy,fvalue)
                    except UnicodeDecodeError, e:
                        curCanvas.drawString(xx,yy,repr(fvalue))

            for dsrect in self.getDocumentSpec().Rects:
                x = dsrect.X
                y = dsrect.Y
                w = dsrect.Width
                h = dsrect.Height

                bx,by = translateCoords(x,y)
                ex,ey = translateCoords(x+w,y+h)
                curCanvas.rect(bx,by, ex-bx, ey-by)
            curCanvas.showPage()  #cierra la pagina actual, lo que se imprimia despues se imprime en otra pagina
            cur_page += 1
        if (saveCanvas):
            curCanvas.save()
        return curCanvas

    def getFieldFontStyle(self, fn):
        ds = self.getDocumentSpec()
        for row in ds.Fields:
            if row.Name == fn:
                return row.Style
        return None

    def getFieldWidth(self, fn):
        ds = self.getDocumentSpec()
        for row in ds.Fields:
            if row.Name == fn:
                return row.Width
        return None

    def getCommentLines(self,comment,fieldname):
        parlist = comment.split('\n')
        limit = self.getFieldWidth(fieldname)
        if not limit:
            return parlist
        f = 1 #factor de correccion
        if sys.platform=='darwin':  #mac osx
            f = 1.35
        style = self.getFieldFontStyle(fieldname)
        fs = FontStyle.bring(style)
        if fs:
            res = []
            for par in parlist:
                l = Document.getTextWidth(par,fs)*f
                if l>limit:
                    list = par.split(" ")
                    text = ''
                    for s in list:
                        if (Document.getTextWidth(text + s + ' ',fs)*f)>limit:
                            res.append(text)
                            text = s + ' '
                        else:
                            text = text + s + ' '
                    res.append(text)
                else:
                    res.append(par)
            return res
        return []

    def getTextInLines(self,comment,fieldname):
        parlist = comment.split('\n')
        limit = self.getFieldWidth(fieldname)
        if not limit:
            return comment
        f = 1.03 #factor de correccion
        if sys.platform=='darwin':  #mac osx
            f = 1.35
        style = self.getFieldFontStyle(fieldname)
        fs = FontStyle.bring(style)
        if fs:
            res = []
            for par in parlist:
                l = Document.getTextWidth(par,fs)*f
                if l>limit:
                    list = par.split(" ")
                    text = ''
                    for s in list:
                        k = Document.getTextWidth(text + s,fs)*f
                        if k>limit:
                            res.append(text)
                            text = s + ' '
                        else:
                            text = text + s + ' '
                    res.append(text)
                else:
                    res.append(par)
            rtext = ""
            for line in res:
                rtext = rtext + line + '\n '
            return rtext


#    def genMultiPagePDF(self, docList, filename ):
#        if (filename.__class__.__name__ != "list"):
#            curCanvas = self.createCanvas(filename)
#
#            for curDoc in docList:
#                curCanvas = self.genPDF(filename,curCanvas)
#
#            curCanvas.save()