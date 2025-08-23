class ScrollStructure(list):
    def __init__(self,headerV, headerH,reference):
            list.__init__(self)
            self.headerV = headerV
            self.headerH = headerH
            self.reference = reference
    
    def setVerticalHeader(self, headerV):
        self.headerV = headerV

class ScrollLine(list):
    pass
    
class ScrollObject:
   def __init__(self, scrollarea, label, begin, end, color):
       self.scrollarea = scrollarea
       self.label = label
       self.begin = begin
       self.end = end
       self.color = color
       self.hint = None
   
   def clicked(self):
       pass

class ButtonHeader:
   def __init__(self, scrollarea, label):
       self.scrollarea = scrollarea
       self.label = label
       
   def clicked(self):
       pass


"""


Example:

        from ScrollArea import *
        headerV = []
        for j in range(100,110):
            headerV.append(str(j))
        
        headerH = []
        for i in range(1,31):
            headerH.append(str(i))
        
        
        structure = ScrollStructure(headerV,headerH,"hab/dia")
     
        
        line1 = ScrollLine()
        so1 = ScrollObject("ocupado", 10, 60, "red")
        so2 = ScrollObject("libre", 80,120,"green")
        line1.append(so1)
        line1.append(so2)
        structure.append(line1)
        
        line2 = ScrollLine()
        so3 = ScrollObject("bloqueada",20,400,"blue")
        line2.append(so3)
        structure.append(line2)
       
        line3 = ScrollLine()
        structure.append(line3)
       
        line4 = ScrollLine()
        so4 = ScrollObject("reservada",15,65,"yellow")
        so5 = ScrollObject("ocupada",80,300,"red")
        line4.append(so4)
        line4.append(so5)
        structure.append(line4)
          
       
            

        sa = ScrollArea()
        sa.setStructure(structure)
        sa.setLabelColor("lightGray")
        sa.setPercentVertical(30)
        sa.setBackGroundColor("white")
        sa.viewVerticalLines(True)
        sa.viewHorizontalLines(True)
        sa.setLabelFont("Helvetica", 10)
        sa.setWidthV(50)
        sa.setWidthH(20)
        sa.setHeightH(50)  
        sa.setHeightV(50)

"""