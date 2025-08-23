from OpenOrange import *

__author__ = 'PDB'

class ButtonList(list):
    pass
    
class ButtonObject(Embedded_ButtonObj):

    def __init__(self, label, color,image,xb, yb, xe, ye,buttonarea):
        self.label = label
        self.color = color
        self.image = image
        self.xb = xb
        self.yb = yb
        self.xe = xe
        self.ye = ye
        self.scroll_x = 0
        self.scroll_y = 0
        self.w = self.xe - self.xb
        self.h = self.ye - self.yb
        self.widthImage = 0
        self.heightImage = 0
        self.imagePosX = 0
        self.imagePosY = 0
        self.labelPosX = 0
        self.labelPosY = 0
        self.rectColor = color
        self.point = 0
        self.buttonArea = buttonarea
        self.hint = label

    def setImageSize(self, width, height):
        self.widthImage = width
        self.heightImage = height
   
    def setImagePosition(self,x,y):
        self.imagePosX = x
        self.imagePosY = y
       
    def setLabelPosition(self,x,y):
        self.labelPosX = x
        self.labelPosY = y
       
    def setBorder(self,color,point):
        self.rectColor = color
        self.point = point
       
    def clicked(self):
        pass

    def move(self, x, y):
        self.xb = x
        self.xe = x + self.w
        self.yb = y
        self.ye = y + self.h
        return Embedded_ButtonObj.move(self, x,y)
        
    def getPos(self):
        return (self.xb, self.yb)
    
    def getSize(self):
        return (self.w, self.h)
        
    def resize(self, w, h):
        self.w = w
        self.h = h
        Embedded_ButtonObj.resize(self,w,h)
        
    def moved(self):
        pass

    def updatePosition(self):
        self.xb, self.yb = self.getAbsolutePos()
        self.xe = self.xb + self.w
        self.ye = self.yb + self.h
        rx, ry = self.getRelativePos()
        self.scroll_x = self.xb - rx
        self.scroll_y = self.yb - ry
        
    def getRealPos(self):
        return self.getAbsolutePos()
        

"""
ParentCustomerWindow = SuperClass("CustomerWindow", "MasterWindow", __file__)
       
class CustomerWindow(ParentCustomerWindow):

    def afterEdit(self, fieldname):
        if fieldname == "FantasyName":
            self.showButtonArea() 
    
       
    def showButtonArea(self):
        from ButtonArea import *    
        bList = ButtonList()
        bo1 = ButtonObject("ocupado","red","fondo6.png",10,10,90,90)
        bo1.setImageSize(20,20)
        bo1.setImagePosition(30,30)
        bo1.setLabelPosition(20,20)
        bo2 = ButtonObject("libre","green","",100,50,200,100)
        bo2.setLabelPosition(30,30)
        bo3 = ButtonObject("reservado","blue","",150,150,300,250)
        bList.append(bo1)
        bList.append(bo2)
        bList.append(bo3)  
        ba = ButtonArea()
        ba.setStructure(bList)
        ba.setBackGroundColor("white")
        ba.setTotalSize(500,500);
"""
       