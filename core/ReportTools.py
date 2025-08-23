from OpenOrange import *
from Palette import Palette
from PIL import Image, ImageDraw, ImageFont, ImageFile
import urllib2, urllib


def getRotatedTextImage(txt, rotation, font = None):
    if not font: font = ImageFont.load_default()
    img_txt = Image.new('L', font.getsize(txt), 255)
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((0,0), txt, font=font, fill=0)
    return img_txt.rotate(rotation) 

class EmbeddedImage:
    ColorNamesToRGB = {"AliceBlue":"#F0F8FF",\
        "ANTIQUEWHITE":"#FAEBD7",\
        "AQUA":"#00FFFF",\
        "AQUAMARINE":"#7FFFD4",\
        "AZURE":"#F0FFFF",\
        "BEIGE":"#F5F5DC",\
        "BISQUE":"#FFE4C4",\
        "BLACK":"#000000",\
        "BLANCHEDALMOND":"#FFEBCD",\
        "BLUE":"#0000FF",\
        "BLUEVIOLET":"#8A2BE2",\
        "BROWN":"#A52A2A",\
        "BURLYWOOD":"#DEB887",\
        "CADETBLUE":"#5F9EA0",\
        "CHARTREUSE":"#7FFF00",\
        "CHOCOLATE":"#D2691E",\
        "CORAL":"#FF7F50",\
        "CORNFLOWERBLUE":"#6495ED",\
        "CORNSILK":"#FFF8DC",\
        "CRIMSON":"#DC143C",\
        "CYAN":"#00FFFF",\
        "DARKBLUE":"#00008B",\
        "DARKCYAN":"#008B8B",\
        "DARKGOLDENROD":"#B8860B",\
        "DARKGRAY":"#A9A9A9",\
        "DARKGREEN":"#006400",\
        "DARKKHAKI":"#BDB76B",\
        "DARKMAGENTA":"#8B008B",\
        "DARKOLIVEGREEN":"#556B2F",\
        "DARKORANGE":"#FF8C00",\
        "DARKORCHID":"#9932CC",\
        "DARKRED":"#8B0000",\
        "DARKSALMON":"#E9967A",\
        "DARKSEAGREEN":"#8FBC8F",\
        "DARKSLATEBLUE":"#483D8B",\
        "DARKSLATEGRAY":"#2F4F4F",\
        "DARKTURQUOISE":"#00CED1",\
        "DARKVIOLET":"#9400D3",\
        "DEEPPINK":"#FF1493",\
        "DEEPSKYBLUE":"#00BFFF",\
        "DIMGRAY":"#696969",\
        "DODGERBLUE":"#1E90FF",\
        "FIREBRICK":"#B22222",\
        "FLORALWHITE":"#FFFAF0",\
        "FORESTGREEN":"#228B22",\
        "FUCHSIA":"#FF00FF",\
        "GAINSBORO":"#DCDCDC",\
        "GHOSTWHITE":"#F8F8FF",\
        "GOLD":"#FFD700",\
        "GOLDENROD":"#DAA520",\
        "GRAY":"#808080",\
        "GREEN":"#008000",\
        "GREENYELLOW":"#ADFF2F",\
        "HONEYDEW":"#F0FFF0",\
        "HOTPINK":"#FF69B4",\
        "INDIANRED":"#CD5C5C",\
        "INDIGO":"#4B0082",\
        "IVORY":"#FFFFF0",\
        "KHAKI":"#F0E68C",\
        "LAVENDER":"#E6E6FA",\
        "LAVENDERBLUSH":"#FFF0F5",\
        "LAWNGREEN":"#7CFC00",\
        "LEMONCHIFFON":"#FFFACD",\
        "LIGHTBLUE":"#ADD8E6",\
        "LIGHTCORAL":"#F08080",\
        "LIGHTCYAN":"#E0FFFF",\
        "LIGHTGOLDENRODYELLOW":"#FAFAD2",\
        "LIGHTGREY":"#D3D3D3",\
        "LIGHTGREEN":"#90EE90",\
        "LIGHTPINK":"#FFB6C1",\
        "LIGHTSALMON":"#FFA07A",\
        "LIGHTSEAGREEN":"#20B2AA",\
        "LIGHTSKYBLUE":"#87CEFA",\
        "LIGHTSLATEGRAY":"#778899",\
        "LIGHTSTEELBLUE":"#B0C4DE",\
        "LIGHTYELLOW":"#FFFFE0",\
        "LIME":"#00FF00",\
        "LIMEGREEN":"#32CD32",\
        "LINEN":"#FAF0E6",\
        "MAGENTA":"#FF00FF",\
        "MAROON":"#800000",\
        "MEDIUMAQUAMARINE":"#66CDAA",\
        "MEDIUMBLUE":"#0000CD",\
        "MEDIUMORCHID":"#BA55D3",\
        "MEDIUMPURPLE":"#9370D8",\
        "MEDIUMSEAGREEN":"#3CB371",\
        "MEDIUMSLATEBLUE":"#7B68EE",\
        "MEDIUMSPRINGGREEN":"#00FA9A",\
        "MEDIUMTURQUOISE":"#48D1CC",\
        "MEDIUMVIOLETRED":"#C71585",\
        "MIDNIGHTBLUE":"#191970",\
        "MINTCREAM":"#F5FFFA",\
        "MISTYROSE":"#FFE4E1",\
        "MOCCASIN":"#FFE4B5",\
        "NAVAJOWHITE":"#FFDEAD",\
        "NAVY":"#000080",\
        "OLDLACE":"#FDF5E6",\
        "OLIVE":"#808000",\
        "OLIVEDRAB":"#6B8E23",\
        "ORANGE":"#FFA500",\
        "ORANGERED":"#FF4500",\
        "ORCHID":"#DA70D6",\
        "PALEGOLDENROD":"#EEE8AA",\
        "PALEGREEN":"#98FB98",\
        "PALETURQUOISE":"#AFEEEE",\
        "PALEVIOLETRED":"#D87093",\
        "PAPAYAWHIP":"#FFEFD5",\
        "PEACHPUFF":"#FFDAB9",\
        "PERU":"#CD853F",\
        "PINK":"#FFC0CB",\
        "PLUM":"#DDA0DD",\
        "POWDERBLUE":"#B0E0E6",\
        "PURPLE":"#800080",\
        "RED":"#FF0000",\
        "ROSYBROWN":"#BC8F8F",\
        "ROYALBLUE":"#4169E1",\
        "SADDLEBROWN":"#8B4513",\
        "SALMON":"#FA8072",\
        "SANDYBROWN":"#F4A460",\
        "SEAGREEN":"#2E8B57",\
        "SEASHELL":"#FFF5EE",\
        "SIENNA":"#A0522D",\
        "SILVER":"#C0C0C0",\
        "SKYBLUE":"#87CEEB",\
        "SLATEBLUE":"#6A5ACD",\
        "SLATEGRAY":"#708090",\
        "SNOW":"#FFFAFA",\
        "SPRINGGREEN":"#00FF7F",\
        "STEELBLUE":"#4682B4",\
        "TAN":"#D2B48C",\
        "TEAL":"#008080",\
        "THISTLE":"#D8BFD8",\
        "TOMATO":"#FF6347",\
        "TURQUOISE":"#40E0D0",\
        "VIOLET":"#EE82EE",\
        "WHEAT":"#F5DEB3",\
        "WHITE":"#FFFFFF",\
        "WHITESMOKE":"#F5F5F5",\
        "YELLOW":"#FFFF00",\
        "YELLOWGREEN":"#9ACD32"}

    def __init__(self, width, height, **params):
        self.width = width
        self.height = height
        self.colors={}
        self.colors["Background"] = params.get("BGColor", "white")
        import sys
        if sys.platform.startswith("win"):
            self.font = ImageFont.truetype(params.get("Font","arial.ttf"), params.get("FontSize",10))
        else:
            if params.has_key("Font"):
                self.font = ImageFont.load(params["Font"], params.get("FontSize",10))
            else:
                self.font = ImageFont.load_default()
        
    def save(self, filename):
        self.draw()
        return self.img.save(filename)
    
    def draw(self):
        self.img  = Image.new("RGBA", (self.width, self.height), self.colors["Background"])    
        

class ColorChart(EmbeddedImage):

    def draw(self):
        self.img  = Image.new("RGBA", (self.width, self.height), "red")    
        drawer = ImageDraw.Draw(self.img)
        grd = 25        
        drawer.rectangle([(0, 0), (self.width, self.height)], "white")  
        ff00 = range(0xff, -1, -0x33)
        pal = [(r,g,b) for r in ff00 for g in ff00 for b in ff00]  # web-safe
        map_j = range(0,12,2)+range(11,0,-2)  # make better grouping
        for j in range(12):
          for i in range(18):
            k = 18*map_j[j] + i
            drawer.rectangle([(grd*i+1, grd*j+1), (grd*i+grd, grd*j+grd)], pal[k], pal[k])

class Fractal(EmbeddedImage):

    def draw(self):
        self.mandelbrot()

    def mandelbrot(self):
        EmbeddedImage.draw(self)
        drawer = ImageDraw.Draw(self.img)
        xaxis = self.width/2
        yaxis = self.height/1.5
        scale = 60
        iterations = 25  
  
        for y in range(self.height):
          for x in range(self.width):
            magnitude = 0
            z = 0+0j
            c = complex(float(y-yaxis)/scale, float(x-xaxis)/scale)
            for i in range(iterations):
              z = z**2+c
              if abs(z) > 2:
                v = 765*i/iterations
                if v > 510:
                  color = (255, 255, v%255)
                elif v > 255:
                  color = (255, v%255, 0)
                else:
                  color = (v%255, 0, 0)
                break
            else:
              color = (0, 0, 0)
            drawer.point((x,y),color)

        
class Graph(EmbeddedImage):
    
    def __init__(self, width, height, **params):
        EmbeddedImage.__init__(self, width, height, **params)
        self.axis = {}
        self.grid = {}
        self.axis["Width"] = params.get("AxisWidth",1)
        self.axis["YSteps"] = params.get("YAxisSteps",6)
        self.axis["XSteps"] = params.get("XAxisSteps",6)
        self.axis["YMargin"] = params.get("YAxisMargin",30)
        self.axis["XMargin"] = params.get("XAxisMargin",30)
        self.grid["Horizontal"] = params.get("HorizontalGrid", True)
        self.grid["Vertical"] = params.get("VerticalGrid", True)
        self.grid["Color"] = params.get("GridColor", (200,200,200))
        self.grid["MaxY"] = params.get("MaxY", 0)
        self.grid["MaxX"] = params.get("MaxX", 0)
        self.xup = float(width/self.grid["MaxX"])
        self.yup = float(height/self.grid["MaxY"])
        self.x_cnt = self.grid["MaxX"]/self.axis["XSteps"]
        self.xAxis = range(0,self.grid["MaxX"],self.axis["XSteps"])
        self.yAxis = range(0,self.grid["MaxY"],self.axis["YSteps"])
        
    def save(self, filename):
        self.draw()
        return self.img.save(filename)
    
    def draw(self):
        EmbeddedImage.draw(self)
        
        interaxistext = 2
        xAxisWidth = 1
        yAxisWidth = 10
        margin = 10
        
        #calculo de variables
        barwidth = (self.width - 2*margin - self.axis["YMargin"]) / self.x_cnt
        barserwidth = barwidth / self.x_cnt
        basex = self.width - yAxisWidth - margin
        basey = self.height - xAxisWidth - margin
        
        drawer = ImageDraw.Draw(self.img)
        topv = self.height - 2*margin - xAxisWidth
        toph = self.width - 2*margin - yAxisWidth
        
        barwidth = barserwidth * self.x_cnt
        self.width = barserwidth * self.x_cnt * self.x_cnt + 2 * margin + self.axis["YMargin"]
        
        #drawing X Axis
        posx = self.axis["YMargin"]
        for label in self.xAxis:
            textwidth, textheight = drawer.textsize(str(label))
            drawer.text((posx + (barwidth - textwidth)/2, basey + interaxistext), str(label), fill=(0,0,0), font=self.font)
            posx += barwidth 
        
        #drawing Y Axis and Horizontal Grid
        posy = self.height - margin - xAxisWidth
        vstep = topv / len(self.yAxis)
        for yv in range(1,vstep+1):
            posy -= vstep
            drawer.line((self.axis["YMargin"] + margin - 3, posy, self.axis["YMargin"] + margin, posy), fill=(0,0,0), width=1)
            label = "%s" % (self.grid["MaxY"] * vstep * yv / topv)
            textwidth, textheight = drawer.textsize(label)
            drawer.text((self.axis["YMargin"] + margin - textwidth - 5, posy - textheight/2), label, fill=(0,0,0), font=self.font)
            if self.grid["Horizontal"]:
                drawer.line((self.axis["YMargin"] + margin, posy, self.width - margin, posy), fill=self.grid["Color"], width=1)
        
        #drawing Vertical Grid
        if self.grid["Vertical"]:
            posx = self.axis["YMargin"] + margin
            for col in range(1,self.x_cnt+1):
                posx += barwidth 
                drawer.line((posx, self.height - xAxisWidth - margin - topv, posx, self.height - xAxisWidth - margin), fill=self.grid["Color"], width=1)
           
        from math import sin
        d = {}
        posx = self.axis["YMargin"] + margin
        while (posx < self.width):
                x = float(posx/self.xup)
                d["x"] = x
                #y = eval(self.function,d)
                y = sin(x)
                posy = topv  - (y * self.yup)
                drawer.point((posx,posy),fill="red")
                posx += 1
        
        #drawing Axis Lines
        drawer.line((self.axis["YMargin"]+margin,margin,self.axis["YMargin"]+margin,self.height-xAxisWidth-margin), fill=(0,0,0), width=self.axis["Width"])
        drawer.line((self.axis["YMargin"]+margin,self.height-xAxisWidth-margin,self.width-margin, self.height-xAxisWidth-margin), fill=(0,0,0), width=self.axis["Width"])
        
        #alert(self.getYRange(self.function,0,10))

    def getYRange(self,function,xmin,xmax):
        from math import sin
        ymin = 0.0; ymax = 0.0; d = {}
        for x in range(xmin,xmax,1):
            d["x"] = x
            y = eval(function,d)
            if ymax > y: ymax = y
            if ymin < y: ymin = y
        return (ymin,ymax)

class Standard_BarsChart(EmbeddedImage):

    def __init__(self, width, height, **params):
        EmbeddedImage.__init__(self, width, height, **params)
        self.params = params
        self.xAxis = []
        self.yAxis = []
        self.data = {}
        self.axis = {}
        self.grid = {}
        self.colors["BarFill"] = params.get("BarFillColor", (Palette.LevelBBackColor,Palette.LevelCBackColor,Palette.LevelDBackColor,Palette.LevelABackColor))
        self.colors["BarLines"] = params.get("BarLineColor", Palette.ReportTitleColor)
        self.axis["Width"] = params.get("AxisWidth",1)
        self.axis["YSteps"] = params.get("YAxisSteps",6)
        self.grid["Horizontal"] = params.get("HorizontalGrid", True)
        self.grid["Vertical"] = params.get("VerticalGrid", True)
        self.grid["Color"] = params.get("GridColor", (200,200,200))
        self.grid["MaxY"] = params.get("MaxY", 0)
        self.xTextAngle = params.get("XTextAngle", -90)
        self.val_cnt = 0
        self.ser_cnt = 0

    def setXAxis(self, axis):
        self.xAxis = axis
    
    def addData(self, serielabel, data, **kwargs):
        if not self.data.has_key(serielabel):
            self.data[serielabel] = data
            if len(data) > self.val_cnt: self.val_cnt = len(data)
            if kwargs.has_key("Color"): self.setSerieColor(self.ser_cnt, kwargs["Color"])
            self.ser_cnt += 1
    
    def setSerieColor(self, serienr, color):
        while serienr >= len(self.colors["BarFill"]):
            self.colors["BarFill"].append("gray")
        self.colors["BarFill"][serienr] = color
    
    def save(self, filename):
        self.draw()
        return self.img.save(filename)
    
    def draw(self):
        EmbeddedImage.draw(self)
        for serie in self.data:
            if not self.data[serie]: return

        self.calculateY()
        self.axis["YMargin"] = self.params.get("YAxisMargin",len("%.2f" % self.maxvalue) * 6)
        #seteo de constantes
        interbarwidth = 8
        interaxistext = 5
        xAxisWidth = 55
        margin = 10
        
        #calculo de variables
        barwidth = (self.width - 2*margin - self.axis["YMargin"] - (self.val_cnt-1)*interbarwidth) / self.val_cnt
        barserwidth = barwidth / self.ser_cnt
        barsheight = self.maxvalue - self.minvalue
        basey = self.height - xAxisWidth - margin
        #basey += (-self.minvalue) * (self.height - xAxisWidth - margin)/barsheight
        #self.height - xAxisWidth - margin
        
        drawer = ImageDraw.Draw(self.img)
        topv = self.height - 2*margin - xAxisWidth
        
        #correcciones por redondeo
        barwidth = barserwidth * self.ser_cnt
        self.width = barserwidth * self.ser_cnt * self.val_cnt + (interbarwidth * self.val_cnt-1) + 2 * margin + self.axis["YMargin"]
        
        #drawing X Axis
        posx = self.axis["YMargin"] + margin + interbarwidth/2
        for label in self.xAxis:
            im = getRotatedTextImage(str(label),self.xTextAngle)
            textwidth = im.size[0]
            #drawer.text((posx + (barwidth - textwidth)/2, basey + interaxistext), str(label), fill=(0,0,0), font=self.font)
            self.img.paste(im,(posx + (barwidth - textwidth)/2, basey + interaxistext))
            #drawer.bitmap((posx + (barwidth - textwidth)/2, basey + interaxistext),getRotatedTextImage(str(label),-90))
            posx += barwidth + interbarwidth
        #drawing Y Axis and Horizontal Grid
        posy = self.height - margin - xAxisWidth
        vstep = float(topv) / self.axis["YSteps"]
        dec = "%.2f"
        if self.maxvalue > 100: dec = "%.0f" 
        for yv in range(1,self.axis["YSteps"]+1):
            posy -= vstep
            drawer.line((self.axis["YMargin"] + margin - 3, posy, self.axis["YMargin"] + margin, posy), fill=(0,0,0), width=1)
            lb = (self.maxvalue * vstep * yv / topv)
            label = dec % lb
            textwidth, textheight = drawer.textsize(label)
            drawer.text((self.axis["YMargin"] + margin - textwidth - 5, posy - textheight/2), label, fill=(0,0,0), font=self.font)
            if self.grid["Horizontal"]:
                drawer.line((self.axis["YMargin"] + margin, posy, self.width - margin, posy), fill=self.grid["Color"], width=1)
        
        #drawing Vertical Grid
        if self.grid["Vertical"]:
            posx = self.axis["YMargin"] + margin
            for col in range(1,self.val_cnt+1):
                posx += barwidth + interbarwidth
                drawer.line((posx, self.height - xAxisWidth - margin - topv, posx, self.height - xAxisWidth - margin), fill=self.grid["Color"], width=1)
                


        #drawing values
        posx = self.axis["YMargin"] + margin + interbarwidth/2
        for n_val in range(self.val_cnt):
            serie_nr = 0
            for serie_key in self.data.keys():
                value = 0
                if n_val < len(self.data[serie_key]): value = self.data[serie_key][n_val]
                barheight = value * topv / self.maxvalue
                drawer.rectangle((posx,basey - barheight, posx+barserwidth, basey), fill=self.colors["BarFill"][serie_nr], outline=self.colors["BarLines"])
                serie_nr += 1
                posx += barserwidth
            posx += interbarwidth
            
        #drawing Axis Lines
        drawer.line((self.axis["YMargin"]+margin,margin,self.axis["YMargin"]+margin,self.height-xAxisWidth-margin), fill=(0,0,0), width=self.axis["Width"])
        drawer.line((self.axis["YMargin"]+margin,self.height-xAxisWidth-margin,self.width-margin, self.height-xAxisWidth-margin), fill=(0,0,0), width=self.axis["Width"])

    def calculateY(self):
        self.maxvalue = self.grid["MaxY"]
        self.minvalue = 0
        for serie in self.data:
            if not self.data[serie]:
                maxv = 100
                minv = 0
            else:            
                maxv = max(self.data[serie])
                minv = min(self.data[serie])
            if maxv > self.maxvalue:
                self.maxvalue = maxv
            if minv < self.minvalue:
                self.minvalue = minv
        if (self.maxvalue==0): self.maxvalue = 1       # if all values are 0


class Standard_SerieChart(EmbeddedImage):
    
    def __init__(self, width, height, **params):
        EmbeddedImage.__init__(self, width, height, **params)
        self.xAxis = []
        self.yAxis = []
        self.data = {}
        self.axis = {}
        self.grid = {}
        self.axis["XSteps"] = 0
        self.axis["YSteps"] = 10
        self.colors["BarFill"] = params.get("BarFillColor", ["green","blue","green","black"])
        self.axis["YMargin"] = params.get("YAxisMargin",30)
        self.grid["Color"] = params.get("GridColor", (200,200,200))
        self.grid["MaxY"] = 0
        self.grid["Period"] = params.get("Period",0)
        self.val_cnt = 0
        self.ser_cnt = 0

    def setXAxis(self, axis):
        self.xAxis = axis
    
    def addData(self, serielabel, data, **kwargs):
        if not self.data.has_key(serielabel):
            self.data[serielabel] = data
            if kwargs.has_key("Color"): 
                self.setSerieColor(self.ser_cnt, kwargs["Color"])
            else:
                self.setSerieColor(self.ser_cnt, "black")
            self.axis["XSteps"] = max(self.axis["XSteps"],len(data))
            self.grid["MaxY"]   = max(self.grid["MaxY"],max(data))
            self.ser_cnt += 1
    
    def setSerieColor(self, serienr, color):
        from Palette import *
        while serienr >= len(self.colors["BarFill"]):
            self.colors["BarFill"].append(Palette.getAnotherColor())
        self.colors["BarFill"][serienr] = color
    
    def save(self, filename):
        self.draw()
        return self.img.save(filename)
    
    def draw(self):
        EmbeddedImage.draw(self)
        for serie in self.data:
            if not self.data[serie]: return

        self.calculateY()
        
        #seteo de constantes
        interaxistext = 2
        xAxisWidth = 10
        margin = 50
        
        #calculo de variables
        barwidth = (self.width - 2 * margin - self.axis["YMargin"]) / self.axis["XSteps"]
        barserwidth = barwidth 
        barsheight = self.maxvalue - self.minvalue
        basey = self.height - xAxisWidth - margin

        drawer = ImageDraw.Draw(self.img)
        topv = self.height - 2 * margin - xAxisWidth

        #correcciones por redondeo
        barwidth = barserwidth 
        self.width = barserwidth * (self.axis["XSteps"]-1) + 2 * margin + self.axis["YMargin"]
        
        #drawing X Axis
        posx = self.axis["YMargin"] + margin
        for label in self.xAxis:
            textwidth, textheight = drawer.textsize(str(label))
            drawer.text((posx  - (textwidth)/2, basey + interaxistext), str(label), fill=(0,0,0), font=self.font)
            posx += barwidth 

        #drawing Y Axis and Horizontal Grid
        posy = self.height - margin - xAxisWidth
        vstep = topv / self.axis["YSteps"]
        for yv in range(1,self.axis["YSteps"]+1):
            posy -= vstep
            #drawer.line((self.axis["YMargin"] + margin - 3, posy, self.axis["YMargin"] + margin, posy), fill=(0,0,0), width=1)
            label = "%s" % (int(self.maxvalue * vstep * yv / topv))
            textwidth, textheight = drawer.textsize(label)
            drawer.text((self.axis["YMargin"] + margin - textwidth - 5, posy - textheight/2), label, fill=(0,0,0), font=self.font)
            drawer.line((self.axis["YMargin"] + margin, posy, self.width - margin, posy), fill=self.grid["Color"], width=1)

        #drawing Vertical Grid
        posx = self.axis["YMargin"] + margin
        for col in range(1,self.axis["XSteps"]):
            posx += barwidth 
            drawer.line((posx, self.height - xAxisWidth - margin - topv, posx, self.height - xAxisWidth - margin), fill=self.grid["Color"], width=1)

        #drawing leyenda
        serie_nr = 0
        for serie_label in self.data.keys():
            drawer.text((self.width,50+20*serie_nr), str(serie_label), fill=self.colors["BarFill"][serie_nr], font=self.font)
            serie_nr += 1

        #drawing values
        serie_nr = 0
        for serie_key in self.data.keys():
           yold = None
           posx = self.axis["YMargin"] + margin 
           for n_val in range(self.axis["XSteps"]):
                value = 0
                if n_val < len(self.data[serie_key]): value = self.data[serie_key][n_val]
                barheight = value * topv / self.maxvalue
                if yold:
                    drawer.line((xold,yold,posx,basey - barheight), fill=self.colors["BarFill"][serie_nr],width=2)
                xold,yold = posx,basey - barheight
                posx += barserwidth
           serie_nr += 1
            
        #drawing Axis Lines
        drawer.line((self.axis["YMargin"]+margin,margin,self.axis["YMargin"]+margin,self.height-xAxisWidth-margin), fill=(0,0,0), width=1)
        drawer.line((self.axis["YMargin"]+margin,self.height-xAxisWidth-margin,self.width-margin, self.height-xAxisWidth-margin), fill=(0,0,0), width=1)

    def calculateY(self):
        self.maxvalue = self.grid["MaxY"]
        self.minvalue = 0
        for serie in self.data:
            maxv = max(self.data[serie])
            minv = min(self.data[serie])
            if maxv > self.maxvalue:
                self.maxvalue = maxv
            if minv < self.minvalue:
                self.minvalue = minv
        if (self.maxvalue==0): 
            self.maxvalue = 1       # if all values are 0



class Standard_PieChart(EmbeddedImage):
#TODO: hacer que se puedan mostrar las leyendas
#TODO: hacer que se vea un grid o algun grafico de fondo
#TODO: hacer que las graficas puedan ser en 3D (quedaria muy lindo)
#TODO: hacerlo mas compatible con la clase padre
    def __init__(self, width, height, **params):
        """__init__(width, height, **params):
        Inicia un nuevo grafico de torta. width es ancho maximo de la figura devuelta, height es alto.
        En params pueden recibirse algunos parametros:
        - Separation: en el que se indica la separacion por defecto del eje de la torta por cada porcion
        - ShowPercents: establece si se tienen que mostrar los porcentajes en el interior de las porciones
        - ShowLeyend: establece si se tiene que dibujar la caja de leyendas
        - LeyendSize: establece el tamanio maximo de la caja de lendas ((0,0) por defecto)
        - Font: estable las fuentes a utilizar en la grafica. 
        - LinesColor: (string) establece el color de las lineas externas de las porciones (negro por def)
        - ShowTitles: (Boolean) establece si se muestra el titulo de las porciones (True por def).
        - ShowPercents: (Boolean) establece si se muestran o no los valor recibido en data. 
        - TitlesRadio: (integer) establece la separacion entre la porcion y su nombre
        - BGColor: (string) establece el color de fondo (white por default)
        - BoxColor: (string) establece el color de la caja de recuadro (igual que BGColor por defecto) 
        - BoxLinesWidth: (integer) establece el ancho de las lineas del recuadro (1 por default)"""
        EmbeddedImage.__init__(self,width,height,**params)
        self.width                = width
        self.height               = height
        self.pieWidth             = width 
        self.pieHeight            = height
        self._startAngle          = 0
        #parametros
        self._colors              = [Palette.LevelABackColor,Palette.LevelBBackColor,Palette.LevelCBackColor,Palette.LevelDBackColor]
        self._colorptr            = 0
        self._radio               = params.get("Separation",0)
        self._maxRadio            = self._radio
        self._titlesRadio         = params.get("TitlesRadio",10)
        self._PercentsShow        = params.get("ShowPercents",False)
        self._legendSize          = params.get("LegendSize",(0,0))
        self._legendShow          = (self._legendSize != (0,0) or params.get("ShowLegend",False))
        self._lineColor           = params.get("LinesColor","black")
        self._titlesShow          = params.get("ShowTitles",True)
        self._percentsShow        = params.get("ShowPercents",True)
        self.colors["Background"] = params.get("BGColor","white") # para que la clase padre se encargue
        self._dynamicScale        = params.get("DynamicScale",True)
        self._acumData            = not self._dynamicScale # assigns 1 if dynamicScale is true, 0 otherwise
        self._boxColor            = params.get("BoxColor",self.colors["Background"])
        self._enableBox           = (self._boxColor != self.colors["Background"])
        self._boxLinesWidth       = params.get("BoxLinesWidth",1)
        self.pieces = {} # lugar donde iran todos los datos de cada "pedazo de torta"
        import sys
        if sys.platform.startswith("win"):
            self.font = ImageFont.truetype(params.get("Font","arial.ttf"), params.get("FontSize",10))
        else:
            if params.has_key("Font"):
                self.font = ImageFont.load(params["Font"], params.get("FontSize",10))
            else:
                self.font = ImageFont.load_default()
        self.val_cnt = 0
        self.ser_cnt = 0
        
    def addData(self, serielabel, data, **kwargs):
        """ addData(serielabel,data,**kwargs):
        Agrega una nueva porcion para graficar en el grafico de torta.
        Parametros:
        - serielabel: la etiqueta o nombre de la porcion.
        - data: el valor (de porcentaje o total) de la porcion.
        - kwargs: puede recibir los siguientes modificadores:
            - Color: (string) color para graficar la porcion
            - Separation: (float) separacion individual (solo para esta porcion) con respecto del eje
            - LineColor: (string) establece el color de la linea externa a la figura (negro por def)
            - ShowTitle: (Boolean) establece si se muestra el titulo de la porcion (True por def).
            - ShowPercent (Boolean) establece si se muestra o no el valor recibido en data"""
        self.pieces[serielabel] = {} 
        if self._dynamicScale == True: 
            self._acumData += data
        self.pieces[serielabel]["Percent"] =  data
        self.pieces[serielabel]["Color"] = self._getPieceColor(serielabel,kwargs.get("Color",None))
        pieceRadio = kwargs.get("Separation",self._radio) # para la separacion de la porcion respecto del eje de la torta
        self._maxRadio = max(pieceRadio,self._maxRadio)
        self.pieces[serielabel]["Radio"] = pieceRadio
        self.pieces[serielabel]["LineColor"]= kwargs.get("LineColor",self._lineColor)
        self.pieces[serielabel]["TitleShow"]= kwargs.get("ShowTitle",self._titlesShow)
        self.pieces[serielabel]["PercentShow"] = kwargs.get("ShowPercent",self._percentsShow)
        

    def addColors(self,*colors):
        """ addColors(*colors):
        Agrega colores al stock actual. Parametros:
            - colors = (strings) en colors, se esperan colores llamados por sus nombres en formato 
            sring y separados por comas."""
        self._colors+=colors
    
    def setColors(self,*colors):
        """ setColors(*colors):
        Elimina todos los colores actuales, y pone a *colors en el stock actual. (no hace nada con los
        colores ya utilizados del stock por las porciones actuales. Parametros:
        - *colors: (strings) se reciben colores (por su nombre y en formato string) separados por comas."""
        self._colors=colors

    def emphasize(self,label,**params):

        """ emphasize(label,**params):
        Resalta una porcion respecto del resto, esto se logra separandola del centro, y mostrando su
        nombre y porcentaje.
        Parametros:
        - label: el nombre de la porcion.
        - params:
            - Separation: la separacion con respecto del eje (10 por defecto)."""
        self._radio = 0
        radio = params.get("Separation", 10)
        for pieceLabel in self.pieces:    
            if pieceLabel == label:
                self.pieces[pieceLabel]["Radio"]        = radio
                self.pieces[pieceLabel]["PercentShow"]  = True
                self.pieces[pieceLabel]["TitleShow"]    = True
            else:
                self.pieces[pieceLabel]["Radio"]        = 0
                self.pieces[pieceLabel]["PercentShow"]  = False
                self.pieces[pieceLabel]["TitleShow"]    = False 
        
    def _getPieceColor(self, serielabel,color):
        if color: return color
        color = self._colors[self._colorptr]
        self._colorptr+=1
        if self._colorptr == len(self._colors): self._colorptr = 0
        return color

    # manejador principal del graficador
    def draw(self):
        EmbeddedImage.draw(self)
        self._drawPie()
        if self._drawBox:
            self._drawBox()
    
    # grafica las porciones de torta, junto con sus respectivos porcentajes y titulos
    def _drawPie(self):
        self.draw = ImageDraw.Draw(self.img)
        self._calculatePieRegion()
        width = self.pieWidth
        height = self.pieHeight
        # center 
        xc,yc = self.img.size
        xc/=2
        yc/=2
        #print "(%s,%s,%s,%s)" %(xc,yc,xdelta,ydelta)
        lastAng =  self._startAngle
        for label in self.pieces:
            p = self.pieces[label]["Percent"] 
            p /= float(self._acumData)
            c = self.pieces[label]["Color"]
            l = self.pieces[label]["LineColor"]
            radio = self.pieces[label]["Radio"]
            if p == 0: continue
            arc = 360*p
            arc = round(arc)
            theta = PieChart.GetTheta(lastAng,arc)      
            theta = round(theta)
            dx,dy = PieChart.GetDeltas(theta,radio)
            custXc = round(xc + dx)
            custYc = round(yc + dy)
            self.draw.pieslice( (custXc-width/2,custYc-height/2,custXc+width/2,custYc+height/2),
                            lastAng,lastAng+arc,fill=c,outline=l )
            if self.pieces[label]["PercentShow"]:
                pdx,pdy = PieChart.GetDeltas(theta,width/4)
                if (self._dynamicScale==True):
                    percStr = "%.2f" % self.pieces[label]["Percent"]
                else: 
                    percTemp = self.pieces[label]["Percent"]
                    percTemp *=100
                    percStr = "%.2f %%" % percTemp
                size = self.draw.textsize(percStr)
                self.draw.text((custXc+pdx-size[0]/2,custYc+pdy-size[1]/2),percStr,font=self.font,fill=Palette.ReportTitleColor)
            if self.pieces[label]["TitleShow"]:
                pdx,pdy = PieChart.GetDeltas(theta,width/2 + self._titlesRadio)
                if (theta > 90) and (theta < 270):
                    ts = self.draw.textsize(label)                
                    pdx-= ts[0]
                    pdy-= ts[1]
                self.draw.text((custXc+pdx,custYc+pdy),label,font=self.font,fill=Palette.ReportTitleColor)
            lastAng+=arc

    def _drawgeyend(self):
        pass        
    #crea un recuadro al rededor del area del grafico (en su interior).
    def _drawBox(self):
        for w in range(1,self._boxLinesWidth+1): 
            self.draw.line([w-1,w-1,self.width-w,w-1],fill = self._boxColor)
        for w in range(1,self._boxLinesWidth+1): 
            self.draw.line([w-1,self.height-w,self.width-w,self.height-w], fill = self._boxColor)
        for w in range(1,self._boxLinesWidth+1): 
            self.draw.line([w-1,w-1,w-1,self.height-w], fill = self._boxColor)
        for w in range(1,self._boxLinesWidth+1): 
            self.draw.line([self.width-w,w-1,self.width-w,self.height-w],fill=self._boxColor)

    # La siguiente calcula el area correcta para poder dibujar las porciones de la torta. Desde que el area
    # necesita ser un cuadrado, se calcula un unico valor de longitud, y luego se retorna una tupla conteniendo
    # un par con el mismo valor (largo,ancho) <largo = ancho>.
    def _calculatePieRegion(self):
        #considero radio de separacion de las porciones respecto de su eje
        hw= self.width - self._maxRadio*2 - 1 #-1 para asegurar las perdidas por redondeo
        #considero el ancho de las lineas de la caja de recuadro (si es que existe)
        if self._drawBox:
            hw-= self._boxLinesWidth*2
        # si se imprimen los titulos de las porciones, entonces tenemos que considerar el area ocupada por estos,
        # pero EN RELACION CON SU POSICION relativa de cada porcion. 
        if self._titlesShow:
            maxTx = 0
            maxTy = 0
            lastAng =  self._startAngle
            for label in self.pieces:
                r = self.pieces[label]["Radio"]
                p = self.pieces[label]["Percent"] 
                p /= float(self._acumData)
                arc = 360*p
                theta = PieChart.GetTheta(lastAng,arc)
                mx,my = PieChart.GetDeltas(theta,self._titlesRadio)
                rx,ry = PieChart.GetDeltas(theta, self.width/2 + r )
                ts = self.draw.textsize(label)
                tx = ts[0] + mx + rx - round(self.width/2) 
                ty = ts[1] + my + ry - round(self.width/2) 
                maxTx = max(maxTx,tx)
                maxTy = max(maxTy,ty)
        # como al final vamos a cumplir <ancho = largo>, nos decidimos por el mayor de ambos descuentos.
        hw-= max(maxTx,maxTy)*2 
        self.pieWidth  =  hw -1
        self.pieHeight =  hw -1

    @classmethod
    def GetTheta(classObj,init,arc):
      theta = init + arc/2

      return theta
    @classmethod
    def GetDeltas(classObj,theta,radio):
        import math
        theta = math.radians(theta)
        dx = round(radio*math.cos(theta))
        dy = round(radio*math.sin(theta))              
        return dx,dy


class SerieChart(Standard_SerieChart):

    def save(self, filename):
        self.calculateY()
        params = {}
        params["cht"] = "lc"
        params["chs"] = "%sx%s" % (self.width, self.height)
        params["chd"] = "t:%s" % '|'.join([','.join([str(v) for v in serie ]) for serie in self.data.values()])
        params["chdl"] = "%s" % '|'.join([key for key in self.data.keys()])
        params["chxt"] = "x,y"
        params["chxr"] = "1,%s,%s" % (self.minvalue, self.maxvalue)
        params["chds"] = "%s,%s" % (self.minvalue, self.maxvalue)
        params["chbh"] = "a"
        params["chxl"] = "0:|%s" % '|'.join([utf8(v) for v in self.xAxis])
        params["chco"] = "%s" % ','.join([str(self.ColorNamesToRGB.get(v.upper(), v)).replace("#","") for v in self.colors["BarFill"]])
        params = urllib.urlencode(params)
        open("x.txt","w").write(params)
        #p = "?cht=p3&chs=%sx%s&chd=t:%s&chl=%s" % (self.width, self.height, ','.join([str(v["Percent"]) for v in self.pieces.values()]), '|'.join([v for v in self.pieces.keys()]))
        try:
            self.img_str = urllib2.urlopen("http://chart.apis.google.com/chart", params, 4).read()
            open(filename, "wb").write(self.img_str)
        except urllib2.URLError, e:
            return Standard_SerieChart.save(self, filename)


class BarsChart(Standard_BarsChart):

    def save(self, filename):
        self.calculateY()
        params = {}
        params["cht"] = "bvg"
        params["chs"] = "%sx%s" % (self.width, self.height)
        params["chd"] = "t:%s" % '|'.join([','.join([str(v) for v in serie ]) for serie in self.data.values()])
        params["chdl"] = "%s" % '|'.join([key for key in self.data.keys()])
        params["chxt"] = "x,y"
        params["chxr"] = "1,%s,%s" % (self.minvalue, self.maxvalue)
        params["chds"] = "%s,%s" % (self.minvalue, self.maxvalue)
        if len(self.xAxis):
            params["chbh"] = "%s" % int((self.width-200) / len(self.xAxis))
        params["chxl"] = "0:|%s" % '|'.join([utf8(v) for v in self.xAxis])
        params["chco"] = "%s" % ','.join([str(self.ColorNamesToRGB.get(v.upper(), v)).replace("#","") for v in self.colors["BarFill"]])
        params = urllib.urlencode(params)
        #p = "?cht=p3&chs=%sx%s&chd=t:%s&chl=%s" % (self.width, self.height, ','.join([str(v["Percent"]) for v in self.pieces.values()]), '|'.join([v for v in self.pieces.keys()]))
        try:
            self.img_str = urllib2.urlopen("http://chart.apis.google.com/chart", params, 4).read()
            open(filename, "wb").write(self.img_str)
        except urllib2.URLError, e:
            return Standard_BarsChart.save(self, filename)

class PieChart(Standard_PieChart):
            
    def save(self, filename):
        params = {}
        params["cht"] = "p3"
        #self.width, self.height = (800,300)
        params["chs"] = "%sx%s" % (self.width, int(self.height / 2.2))
        params["chd"] = "t:%s" % ','.join([str(v["Percent"]) for v in self.pieces.values()])
        params["chdl"] = "%s" % '|'.join([k + " (%.2f%%)" % (v["Percent"]*100) for k,v in self.pieces.items()])
        #params["chl"] = "%s" % '|'.join([k + " (%.2f%%)" % (v["Percent"]*100) for k,v in self.pieces.items()])
        params["chco"] = "%s" % ','.join([str(self.ColorNamesToRGB.get(v["Color"].upper(), v["Color"])).replace("#","") for v in self.pieces.values()])
        params = urllib.urlencode(params)
        #p = "?cht=p3&chs=%sx%s&chd=t:%s&chl=%s" % (self.width, self.height, ','.join([str(v["Percent"]) for v in self.pieces.values()]), '|'.join([v for v in self.pieces.keys()]))
        try:
            self.img_str = urllib2.urlopen("http://chart.apis.google.com/chart", params, 4).read()
            open(filename, "wb").write(self.img_str)
        except urllib2.URLError, e:
            return Standard_PieChart.save(self, filename)
        

class MapChart(EmbeddedImage):
            
    def save(self, filename):
        import random
        
        def regionColor(r):
            colors = ["ORANGE","RED","BLUE","GREEN"]
            i = random.randrange(0, len(colors) )
            return self.ColorNamesToRGB[ colors[i] ] [1:]              # dont pick up the first caracter
            
        params = {}
        from OurSettings import OurSettings
        from Province import Province
        os = OurSettings.bring()
        countrycode = os.Country.upper()
        #chco=CCCCCC,FF0000,000000
        #provinces = ["B","K","H","U","X","W","E","P","Y","L","F","M","N","Q","R","A","J","D","Z","S","G","V","T"]
        provinces = Province.getCodes()
        regioncolors = ["CCCCCC"] + [ regionColor(p)  for p in provinces ]
        regionlist = [countrycode] + [ countrycode+"-"+p for p in provinces ]
        #chf=bg,s,EAF7FE
        colorgradients = [0,50,100]
        params["cht"] = "map"
        self.width, self.height = (880,660)
        params["chs"] = "%sx%s" % (self.width, int(self.height / 2.2))
        params["chd"] = "t:%s" % ','.join([ str(c) for c in colorgradients])
        params["chld"] = "%s" % '|'.join(regionlist)
        #params["chtt"] = "%s" % '+'.join(["Sales","per","Province"])
        #params["chl"] = "%s" % '|'.join([k + " (%.2f%%)" % (v["Percent"]*100) for k,v in self.pieces.items()])
        params["chco"] = "%s" % ','.join(regioncolors)
        params = urllib.urlencode(params)
        try:
            self.img_str = urllib2.urlopen("http://chart.apis.google.com/chart", params, 4).read()
            #self.img_str = urllib2.urlopen("http://chart.apis.google.com/chart?cht=map:fixed=40,-10,60,10&chs=176x280&chld=GB|GB-LND&chco=676767|FF0000|0000BB&chf=bg,s,c6eff7", params, 4).read()
            open(filename, "wb").write(self.img_str)
            print self.img_str
        except urllib2.URLError, e:
            return Standard_PieChart.save(self, filename)
"""
Example Report
from OpenOrange import *
from Report import Report
from ReportTools import BarsChart

class TestReport(Report):

    def run(self):
        self.getView().resize(600,500)
        self.startTable()
        self.startRow()
        chart = BarsChart(530,200, YAxisSteps=10)
        data = [20,50,170,45,33,67,112,96,12,78]
        chart.addData("ventas", data)
        chart.setXAxis(("E","F","M","A","M","J","J","A","S","O"))
        self.addValue(chart)
        self.endRow()
        self.startRow()
        chart = BarsChart(530,200, YAxisSteps=10, BarFillColor=["blue","gray","yellow"])
        data = [3,110,70,75,13,117,172,196,62,28]
        chart.addData("compras", data)
        data = [12,40,80,175,313,217,72,96,162,228]
        chart.addData("stock", data)
        data = [12,40,80,0,113,217,72,96,162,228]
        chart.addData("stock2", data)        
        data = [12,0,80,0,113,217,72,96,162,228]
        chart.addData("stock3", data, Color="green")                
        chart.setXAxis(("E","F","M","A","M","J","J","A","S","O"))
        self.addValue(chart)        
        self.endRow()
"""
