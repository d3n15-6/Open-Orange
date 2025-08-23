#encoding: utf-8
from OpenOrange import *
from MasterWindow import MasterWindow
from Report import Report
from Classifier import Classifier
import ListViewItem


ParentClassifierWindow = SuperClass("ClassifierWindow", "MasterWindow", __file__)
class ClassifierWindow(ParentClassifierWindow):

    def appendChildNodes(self, node, parent, tree):
        if tree.has_key(node):
            for child in tree[node]:
                item = ClassifierNode(parent)
                item.setText(map(lambda x: utf8(x), child))
                item.window = self
                self.appendChildNodes(child[0], item, tree)

    def afterShowRecord(self):
        ParentClassifierWindow.afterShowRecord(self)
        listview = self.getListView("ClassifierListView")
        listview.setTreeMode()
        listview.setColumns((tr("Code"), tr("Name"), tr("Level")))
        record = self.getRecord()
        if record.Type:
            tree = record.__class__.getTree(record.Type)
            currentnode = listview
            rootnodes = [ x for x in tree.keys() if x=='' ]
            for rootnode in rootnodes:
                self.appendChildNodes(rootnode, listview, tree)

    def TreeConstruct(self,mother,tree,knot):
        if tree.has_key(knot):
          for child in tree[knot]:
            kid = Node(mother)
            kid.setText(child[1])
            self.TreeConstruct(kid,tree,child[0])

    def buttonClicked(self, buttonname):

        if (buttonname=="showClassifierTree"):
            tree = self.getRecord().__class__.getTree(self.getRecord().Type)
            if tree:
                tw = TreeWidget()
                root = Node(tw)
                root.setText(self.getRecord().Code)
                self.TreeConstruct(root,tree,self.getRecord().Code)
                tw.show()

class ClassifierNode(ListViewItem.ListViewItem):

    def selected(self):
        code = self.getText()[0]
        classifier = Classifier.bring(code)
        self.window.setRecord(classifier)