#encoding: utf-8
from OpenOrange import *

def TreeWalk(tree,Node,level):
   if tree.has_key(Node):
     leaves = []
     for child in tree[Node]:
        leaves += TreeWalk(tree,child[0],level+1)
     return leaves
   else:
     return [Node]

ParentClassifier = SuperClass("Classifier", "Master", __file__)
class Classifier(ParentClassifier):    
    buffer = RecordBuffer("Classifier")

    def defaults(self):
        ParentClassifier.defaults(self)
        self.Level = 0

    def check(self):
        result = ParentClassifier.check(self)
        if not result: return result
        for fn in ("Type","Name"):
            if not self.fields(fn).getValue(): 
                return self.FieldErrorResponse("NONBLANKERR",fn)

        if (self.Level<>0):
            if (not self.PathToRoot):
                return self.FieldErrorResponse("If level is not 0 the Father cannot be blank","PathToRoot")
            else:
                #~ from Classification import Classification
                padre = self.__class__.bring(self.PathToRoot)
                if (padre.load()):
                    if (padre.Type != self.Type):
                        return self.FieldErrorResponse("Father has other Type","PathToRoot")        
                else:
                    return self.FieldErrorResponse("Father doesnt exist","PathToRoot")
        return True

    @classmethod
    def getTree(objclass, ClassifierType):
        tree = {}
        query = Query()
        query.sql  = "SELECT {Code},{Name},{Level},{PathToRoot} from [%s] \n" % objclass.__name__
        query.sql += "WHERE?AND {Type}=s|%s| \n" % ClassifierType
        query.sql += "ORDER BY {PathToRoot},{Code} \n"
        if(query.open()):
          for r in query:
            if not tree.has_key(r.PathToRoot):
              tree[r.PathToRoot] = []
            tree[r.PathToRoot].append((r.Code,r.Name,r.Level))
          query.close()
          return tree

    def getClassifierOnLevel(self,level):
        lab = self
        while (lab.Level<>level):
           lab = self.__class__.bring(lab.PathToRoot)   # go down one level
           if (not lab): return None
        return lab.Code


    @classmethod
    def matchesClassifier(objclass,itemClassifiers,Classifierfilter):
        """ Checks if itemClassifiers fits Classifierfilter: e.g. is Rutini Malbec a drink ? """
        Classifiers = itemClassifiers.split(",")
        for lab in Classifiers:
          p = objclass.bring(lab)
          while (p):
            if (p.Code in Classifierfilter): return True
            p = objclass.bring(p.PathToRoot)
        return False

    @classmethod
    def getTreeLeaves(objclass, startNode,ClassifierType=None):
        leaves = []; tree = {}
        query = Query()
        query.sql  = "SELECT {Code},{Name},{Level},{PathToRoot} from [%s] \n" % objclass.__name__
        if ClassifierType: query.sql += "WHERE?AND {Type}=s|%s| \n" % ClassifierType
        query.sql += "ORDER BY {PathToRoot},{Code} \n"
        if(query.open()):
            for r in query:
              if not tree.has_key(r.PathToRoot):
                tree[r.PathToRoot] = []
              tree[r.PathToRoot].append((r.Code,r.Name,r.Level))
            query.close()
            leaves = TreeWalk(tree,startNode,0)
        return leaves

        
    def getItems(self):
        itemset = []
        labset = self.__class__.getTreeLeaves(self.Code)
        query = Query()
        query.sql  = "SELECT {Code} from [Item] \n"
        query.sql += "WHERE?AND Classifiers IN ('%s') " % "','".join(labset)
        if(query.open()):
            for rec in query:
               itemset.append(rec.Code)
        return itemset

    @classmethod
    def getClassifiers(objclass,type):
        labs = []
        query = Query()
        query.sql = "SELECT {Code} FROM [%s] WHERE {Type} = s|%s| " % (objclass.__name__, type)
        if query.open():
           for x in query:
              labs.append(x.Code)
        return labs

