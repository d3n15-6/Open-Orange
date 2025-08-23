import xml.parsers.expat
from ClientRequest import ClientRequest

        
        
class XMLParser(object):
    classes = {"request": ClientRequest}
    
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.startElement
        self.parser.EndElementHandler = self.endElement
        self.parser.CharacterDataHandler = self.characterData
        self.elements = []
        self.result = None
    
    def startElement(self, name, attrs):
        try:
            parent = self.elements[-1]
        except IndexError, e:
            parent = None
        element = XMLParser.classes[name.lower()](parent, attrs)
        self.elements.append(element)
        

    def endElement(self, name):
        self.result = self.elements.pop()
        
    def characterData(self, data):
        print "data", data
        
    def parse(self, file):
        return self.parser.ParseFile(file)
        
        
if __name__ == "__main__":
    p = XMLParser()
    import StringIO
    f = StringIO.StringIO('<request aa="i12"><request tipo="sA"></request><request tipo="sB"></request>datos</request>')
    p.parse(f)
    print p.result
    