
class Parseable(object):
    attribute_name = "parseable"
    list_attribute_name = None
    
    @classmethod
    def getListAttributeName(objclass):
        if not objclass.list_attribute_name: objclass.list_attribute_name = objclass.attribute_name + "s"
        
        return objclass.list_attribute_name
    def __init__(self, parent, attrs):
        for attr, v in attrs.items():
            setattr(self, attr, v)
        if parent:
            print id(parent)
            name = self.__class__.attribute_name
            if hasattr(parent, name):
                print 2
                setattr(parent, self.__class__.getListAttributeName(), [getattr(parent, name), self])
                delattr(parent, name)
            else:
                print 3
                if hasattr(parent, self.__class__.getListAttributeName()):
                    print 4
                    getattr(parent, self.__class__.getListAttributeName()).append(self)
                else:
                    print 5
                    setattr(parent, name, v)
            print id(parent)