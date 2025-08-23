from Parseable import Parseable

class ClientRequest(Parseable):
    attribute_name = "request"
    
    def __init__(self,parent, attrs):
        Parseable.__init__(self, parent, attrs)
        print "new clientrequest"

    def __repr__(self):
        return Parseable.__repr__(self) + ": " + str(self.__dict__)
        