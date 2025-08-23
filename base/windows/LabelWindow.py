#encoding: utf-8
from OpenOrange import *
from MasterWindow import MasterWindow
from Report import Report
from Label import Label
import ListViewItem


ParentLabelWindow = SuperClass("LabelWindow", "ClassifierWindow", __file__)
class LabelWindow(ParentLabelWindow):
    

    def appendChildNodes(self, node, parent, tree):
        if tree.has_key(node):
            for child in tree[node]:
                item = LabelNode(parent)
                item.setText(map(lambda x: utf8(x), child))
                item.window = self
                self.appendChildNodes(child[0], item, tree)

    def afterShowRecord(self):
        ParentLabelWindow.afterShowRecord(self)
        listview = self.getListView("ClassifierListView")
        listview.setTreeMode()
        listview.setColumns((tr("Code"), tr("Name"), tr("Level")))
        record = self.getRecord()
        if record.Type:
            tree = Label.getTree(record.Type)
            currentnode = listview
            rootnodes = filter(lambda x: (x == '' or x is None), tree.keys())
            for rootnode in rootnodes:
                self.appendChildNodes(rootnode, listview, tree)

    def TreeConstruct(self,mother,tree,knot):
        if tree.has_key(knot):
          for child in tree[knot]:
            kid = Node(mother)
            kid.setText(child[1])
            self.TreeConstruct(kid,tree,child[0])

    def buttonClicked(self, buttonname):

        if (buttonname=="showLabelTree"):
            tree = Label.getTree(self.getRecord().Type)
            if tree:
                tw = TreeWidget()
                root = Node(tw)
                root.setText(self.getRecord().Code)
                self.TreeConstruct(root,tree,self.getRecord().Code)
                tw.show()

class LabelNode(ListViewItem.ListViewItem):

    def selected(self):
        code = self.getText()[0]
        label = Label.bring(code)
        self.window.setRecord(label)

