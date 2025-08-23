#encoding: utf-8
from OpenOrange import *

ParentDocumentSpec = SuperClass("DocumentSpec", "Master", __file__)
class DocumentSpec(ParentDocumentSpec):
    buffer = RecordBuffer("DocumentSpec")
    
    def check(self):
        res = ParentDocumentSpec.check(self)
        if not res: return res
        f = {}
        p = 0
        for fnrow in self.Fields:
            if f.has_key(fnrow.Name):
                return fnrow.FieldErrorResponse(tr("Duplicated Field"), "Name")
            f[fnrow.Name] = True
            p += 1
        return True

ParentDocumentSpecFieldsRow = SuperClass("DocumentSpecFieldsRow","Record",__file__)
class DocumentSpecFieldsRow(ParentDocumentSpecFieldsRow):
    
    def moveUp(self, pixel=1):
        self.Y -= pixel

    def moveLeft(self, pixel=1):
        self.X -= pixel

    def moveRight(self, pixel=1):
        self.X += pixel

    def moveDown(self, pixel=1):
        self.Y += pixel

    def moreWidth(self, pixel=1):
        self.Width += pixel

    def lessWidth(self, pixel=1):
        self.Width -= pixel

    def alignLeft(self):
        self.Alignment = 0

    def alignCenter(self):
        self.Alignment = 1

    def alignRight(self):
        self.Alignment = 2

ParentDocumentSpecLabelsRow = SuperClass("DocumentSpecLabelsRow","Record",__file__)
class DocumentSpecLabelsRow(ParentDocumentSpecLabelsRow):

    def moveUp(self, pixel=1):
        self.Y -= pixel

    def moveLeft(self, pixel=1):
        self.X -= pixel

    def moveRight(self, pixel=1):
        self.X += pixel

    def moveDown(self, pixel=1):
        self.Y += pixel

    def alignLeft(self):
        self.Alignment = 0

    def alignCenter(self):
        self.Alignment = 1

    def alignRight(self):
        self.Alignment = 2

ParentDocumentSpecRectsRow = SuperClass("DocumentSpecRectsRow","Record",__file__)
class DocumentSpecRectsRow(ParentDocumentSpecRectsRow):

    def moveUp(self, pixel=1):
        self.Y -= pixel

    def moveLeft(self, pixel=1):
        self.X -= pixel

    def moveRight(self, pixel=1):
        self.X += pixel

    def moveDown(self, pixel=1):
        self.Y += pixel

    def moreWidth(self, pixel=1):
        self.Width += pixel

    def lessWidth(self, pixel=1):
        self.Width -= pixel

    def moreHeight(self, pixel=1):
        self.Height += pixel

    def lessHeight(self, pixel=1):
        self.Height -= pixel

ParentDocumentSpecImagesRow = SuperClass("DocumentSpecImagesRow","Record",__file__)
class DocumentSpecImagesRow(ParentDocumentSpecImagesRow):

    def moveUp(self, pixel=1):
        self.Y -= pixel

    def moveLeft(self, pixel=1):
        self.X -= pixel

    def moveRight(self, pixel=1):
        self.X += pixel

    def moveDown(self, pixel=1):
        self.Y += pixel

    def moreWidth(self, pixel=1):
        self.Width += pixel

    def lessWidth(self, pixel=1):
        self.Width -= pixel

    def moreHeight(self, pixel=1):
        self.Height += pixel

    def lessHeight(self, pixel=1):
        self.Height -= pixel