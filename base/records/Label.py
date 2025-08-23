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

ParentLabel = SuperClass("Label", "Classifier", __file__)
class Label(ParentLabel):
    buffer = RecordBuffer("Label")


