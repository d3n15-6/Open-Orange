#encoding: utf-8
import xml.sax

script = """
<mx:Script><![CDATA[

import mx.collections.ArrayCollection;
import mx.collections.ICollectionView;
import mx.events.DataGridEvent;
import mx.events.MenuEvent;
import mx.events.DataGridEventReason;
import mx.rpc.events.ResultEvent;
import mx.controls.Alert;
import mx.utils.ObjectUtil;
import flash.utils.*;
import Ajax
import AjaxRequestType
import mx.rpc.xml.SimpleXMLDecoder
import flash.net.URLVariables

public var request_to_server_blocked:Boolean = false;

[Bindable] public var window :Object;

public function dumpObj(obj:*):void 
{
    //%(cc)s.text = ObjectUtil.toString(obj);
}
     
private function request_to_server(vars:URLVariables):Object 
{
    var url:String = 'cgi-bin/testflex.py?' + vars.toString();
    var ajax:Ajax = new Ajax(url);
    ajax.requestType = AjaxRequestType.GET;    
    ajax.async = false;               
    var xmlStr:String = ajax.send();
    var xmlDoc:XMLDocument = new XMLDocument(xmlStr);
    var decoder:SimpleXMLDecoder = new SimpleXMLDecoder(true);
    var responseobj:Object = decoder.decodeXML(xmlDoc);
    dumpObj(responseobj)
    showMessages(responseobj.response)
    return responseobj.response
}

public function showMessages(response: Object): void
{   
    if (response.messages != null)
    {
        if (getQualifiedClassName(response.messages.msg) != "mx.collections::ArrayCollection")
        {
            Alert.show(response.messages.msg)
        }
        else
        {
            for each (var msg:String in response.messages.msg)
            {
                Alert.show(msg)
            }
        }
   }
}

public function appComplete():void
{
    if (this.parameters["recordid"])
    {
        request_to_server_load()
    }
    else
    {
        request_to_server_new()
    }
    myreport.visible = true
    //myreport.source="http://127.0.0.1/cgi-bin/testflex.py?action=GET_REPORT_HTML&amp;&amp;reportname=VoucherPrintingReport"    
    //myreport.source="http://127.0.0.1/cgi-bin/index.py"
}

private function request_to_server_load():void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "LOAD"
    vars.windowname = "%(windowname)s"
    vars.recordname = "%(recordname)s"
    vars.recordid = this.parameters["recordid"]
    window = request_to_server(vars).window;
}

private function request_to_server_save():void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "SAVE"
    window = request_to_server(vars).window;
}

private function request_to_server_new():void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "NEW"
    vars.windowname = "%(windowname)s"
    vars.recordname = "%(recordname)s"
    vars.recordid = this.parameters["recordid"]    
    window = request_to_server(vars).window;
}

private function request_to_server_next():void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "NEXT"
    request_to_server(vars);
}

private function request_to_server_previous():void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "PREVIOUS"
    request_to_server(vars);
}

private function request_to_server_action(methodname:String):void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "ACTION"
    vars.methodname = methodname
    request_to_server(vars);
}

private function request_to_server_afterEdit(fieldname:String, value:*):void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "AFTEREDIT"
    vars.fieldname = fieldname
    vars.value = value
    window = request_to_server(vars).window;
}

private function request_to_server_beforeEdit(fieldname:String):Boolean
{
    var vars:URLVariables = new URLVariables();
    vars.action = "BEFOREEDIT"
    vars.fieldname = fieldname
    return request_to_server(vars).actionResponse;
}


[Bindable]private var keyName:int;                 // the primary key for the record
[Bindable]private var column:String;               // the field being edited
[Bindable]private var cellValue:String;            // the new value for the field being edited
private var prevCellValue:String = '';             // the old value for the field being edited     

public function stringToDate(d:String): Date
{
    var a:Array = d.split("-")
    return new Date(int(a[0]),int(a[1])-1,int(a[2]))
}

public function stringToBoolean(b:String): Boolean
{

    if (b=="1") return true;
    return false;
}

public function findComboOptionIndex(a:Object, v:String): int
{
    for(var i:uint; i < a.length; i++) 
    {
        if (a[i].value == v) 
        {
            return i;
        }
    }
    return -1;
}

public function afterEdit(event:FocusEvent, fieldname:String):void
{
   cellValue = event.currentTarget.text;
   request_to_server_afterEdit(fieldname, cellValue);
}

public function beforeEdit(event:FocusEvent, fieldname:String):void
{
   var responseAction:Boolean = request_to_server_beforeEdit(fieldname);
   if (!responseAction) 
   {
       //??
   }
}

public function afterEditCheckBox(event:MouseEvent, fieldname:String):void
{
   if (event.currentTarget.selected)
   {
        cellValue = "1";
   }
   else
   {
        cellValue = "0";
   }
   request_to_server_afterEdit(fieldname, cellValue);
}

public function afterEditComboBox(event:FocusEvent, fieldname:String):void
{
   cellValue = event.currentTarget.selectedItem.value;
   request_to_server_afterEdit(fieldname, cellValue);
}

public function afterEditRadioButton(event:MouseEvent, fieldname:String):void
{
   cellValue = event.currentTarget.value;
   request_to_server_afterEdit(fieldname, cellValue);
}

public function actionClicked(event:MenuEvent): void
{
    request_to_server_action(event.item.@methodname)
}

%(rowscript)s






]]></mx:Script>
"""



rowscript = """

private function request_to_server_afterEditRow(fieldname:String, rowfieldname:String, rownr:int, value:*):void 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "AFTEREDITROW"
    vars.fieldname = fieldname
    vars.rowfieldname = rowfieldname
    vars.rownr = rownr
    vars.value = value
    window = request_to_server(vars).window;
}

private function request_to_server_beforeInsertRow(fieldname:String, rownr:int): Boolean
{
    var vars:URLVariables = new URLVariables();
    vars.action = "BEFOREINSERTROW"
    vars.fieldname = fieldname
    vars.rownr = rownr
    return request_to_server(vars).actionResponse;
}

private function request_to_server_beforeEditRow(fieldname:String, rowfieldname:String, rownr:int):Boolean 
{
    var vars:URLVariables = new URLVariables();
    vars.action = "BEFOREEDITROW"
    vars.fieldname = fieldname
    vars.rowfieldname = rowfieldname
    vars.rownr = rownr
    return request_to_server(vars).actionResponse;
}

public function afterEditRow(fieldname:String, datagrid:DataGrid, event:DataGridEvent):void
{
   if(event.reason == DataGridEventReason.CANCELLED)
   {
        return;
   }
   
   cellValue = TextInput(event.currentTarget.itemEditorInstance).text;
   column = event.dataField;
   keyName = datagrid.selectedItem.ID;
   prevCellValue = datagrid.selectedItem[event.dataField];

   if( prevCellValue == cellValue)
   {
        return;
   }
   request_to_server_afterEditRow(fieldname, event.dataField, event.rowIndex, cellValue);
}

public function beforeEditRow(fieldname:String, datagrid:DataGrid, event:DataGridEvent):void
{
   var actionResponse:Boolean
   if (event.rowIndex + 1 == datagrid.dataProvider.length)
   {
        actionResponse = request_to_server_beforeInsertRow(fieldname, event.rowIndex);
        if (!actionResponse) event.preventDefault() //avoid editing this item
        //%(cc)s.text += actionResponse.toString()
   }
   else
   {   
       if(event.reason == DataGridEventReason.CANCELLED) return;
       //%(cc)s.text += "beforeEditRow: " + event.dataField + ", " + String(event.rowIndex) + "\\n"   
       actionResponse = request_to_server_beforeEditRow(fieldname, event.dataField, event.rowIndex);
       if (!actionResponse) event.preventDefault() //avoid editing this item
   }
}

"""

from xml.sax import handler, saxutils
class MXMLGeneratorHandler(handler.ContentHandler):
    WINDOW, LISTWINDOW, PASTEWINDOW = range(3)
    
    def __init__(self):
        self.xml =[]
        self.level = 0
        self.id = 0
        self.has_matrix = False
        self.windowtype = None
        self.windowname = None
        self.recordname = None
        self.cc = None
        self.actions = []
        
    def startElement(self, name, attrs):
        try:
            
            method = getattr(self, 'start_' + name)
            method(attrs)
        except Exception, e:
            pass
            print name, e
            raise
        self.level += 1
        
    def endElement(self, name):
        self.level -= 1
        try:
            method = getattr(self, 'end_' + name)
            method()
        except Exception, e:
            pass

    def start_listwindow(self, attrs):
        self.xml.append("  " * self.level + '<mx:Panel title="{window.title}" width="100%%" height="100%%" paddingTop="4" paddingBottom="4" paddingLeft="4" paddingRight="4" borderThicknessLeft="0" borderThicknessRight="0" borderThicknessTop="0" borderThicknessBottom="0">' % attrs)
        self.windowtype = MXMLGeneratorHandler.LISTWINDOW

    def end_listwindow(self):
        self.xml.append("  " * self.level + '</mx:Panel>')
        
    def start_window(self, attrs):
        self.xml.append("  " * self.level + '<mx:Panel title="{window.title}" width="100%%" height="100%%" paddingTop="4" paddingBottom="4" paddingLeft="4" paddingRight="4" borderThicknessLeft="0" borderThicknessRight="0" borderThicknessTop="0" borderThicknessBottom="0">' % attrs)
        self.xml.append("  " * self.level + '<mx:Form verticalGap="4" horizontalGap="0" width="100%" height="100%" color="0x323232" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')
        self.windowtype = MXMLGeneratorHandler.WINDOW
        self.windowname = attrs["name"]
        self.recordname = attrs["recordname"]

    def end_window(self):
        self.xml.append("  " * self.level + '</mx:Form>')
        self.xml.append("  " * self.level + '</mx:Panel>')

    def start_line(self, attrs):
        self.xml.append("  " * self.level + '<mx:HBox paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')
    
    def end_line(self):
        self.xml.append("  " * self.level + "</mx:HBox>")

    def start_column(self, attrs):
        self.xml.append("  " * self.level + '<mx:VBox paddingTop="4" paddingBottom="4" paddingLeft="4" paddingRight="4">')
        self.xml.append("  " * self.level + '<mx:Form width="100%" verticalGap="4" horizontalGap="0" color="0x323232" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')

    def end_column(self):
        self.xml.append("  " * self.level + '</mx:Form>')
        self.xml.append("  " * self.level + "</mx:VBox>")

    def start_tabs(self, attrs):
        self.xml.append("  " * self.level + '<mx:TabNavigator resizeToContent="true" width="100%" height="100%" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0" color="0x323232">')

    def end_tabs(self):
        self.xml.append("  " * self.level + "</mx:TabNavigator>")

    def start_tabpage(self, attrs):
        self.xml.append("  " * self.level + '<mx:VBox label="%(label)s" paddingTop="4" paddingBottom="4" paddingLeft="4" paddingRight="4" width="100%%" height="100%%">' % attrs)
        self.xml.append("  " * self.level + '<mx:Form verticalGap="4" horizontalGap="0" width="100%"  height="100%" color="0x323232" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')

    def end_tabpage(self):
        self.xml.append("  " * self.level + '</mx:Form>')
        self.xml.append("  " * self.level + "</mx:VBox>")

    def start_integer(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">' % attrs["label"])
        self.xml.append("  " * self.level + '<mx:TextInput id="field_%s_%s" text="{window.record.fields.%s}" focusOut="afterEdit(event, \'%s\');"/>' % (attrs["fieldname"], self.id, attrs["fieldname"], attrs["fieldname"]))
        self.xml.append("  " * self.level + '</mx:FormItem>')

    def start_text(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:TextInput focusIn="beforeEdit(event, \'%s\');" focusOut="afterEdit(event, \'%s\');" text="{window.record.fields.%s}" id="field_%s_%s"/></mx:FormItem>' % (attrs["label"], attrs["fieldname"], attrs["fieldname"], attrs["fieldname"], attrs["fieldname"], self.id))

    def start_memo(self, attrs):
        self.id += 1
        #self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:TextArea focusOut="afterEdit(event, \'%s\');" text="{window.record.fields.%s}" id="field_%s_%s" width="400" height="80"/></mx:FormItem>' % (attrs.get("label", ""), attrs["fieldname"], attrs["fieldname"], attrs["fieldname"], self.id))
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:TextArea  id="field_%s_%s" width="400" height="80"/></mx:FormItem>' % (attrs.get("label", ""), attrs["fieldname"], self.id))
        if attrs["fieldname"] == "Comment2": self.cc = "field_%s_%s" % (attrs["fieldname"], self.id)

    def start_date(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:DateField formatString="DD/MM/YYYY" id="field_%s_%s" selectedDate="{stringToDate(window.record.fields.%s)}" focusOut="afterEdit(event, \'%s\');"/></mx:FormItem>' % (attrs["label"], attrs["fieldname"], self.id, attrs["fieldname"], attrs["fieldname"]))

    def start_time(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:TextInput id="field_%s_%s" focusOut="afterEdit(event, \'%s\');" text="{window.record.fields.%s}" /></mx:FormItem>' % (attrs["label"], attrs["fieldname"], self.id, attrs["fieldname"], attrs["fieldname"]))
        
    def start_value(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:TextInput id="field_%s_%s" focusOut="afterEdit(event, \'%s\');" text="{window.record.fields.%s}" /></mx:FormItem>' % (attrs["label"], attrs["fieldname"], self.id, attrs["fieldname"], attrs["fieldname"]))


    def start_checkbox(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')
        self.xml.append("  " * self.level + '<mx:CheckBox label="%s" id="field_%s_%s" selected="{stringToBoolean(window.record.fields.%s)}" click="afterEditCheckBox(event, \'%s\');"/>'  % (attrs["label"], attrs["fieldname"], self.id,attrs["fieldname"], attrs["fieldname"]))
        self.xml.append("  " * self.level + '</mx:FormItem>')


    def start_combobox(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:FormItem label="%s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">' % attrs["label"])
        self.xml.append("  " * self.level + '<mx:ComboBox id="field_%s_%s" color="0x000000" selectedIndex="{findComboOptionIndex(field_%s_%s.dataProvider, window.record.fields.%s)}" focusOut="afterEditComboBox(event, \'%s\');">'  % (attrs["fieldname"], self.id, attrs["fieldname"], self.id, attrs["fieldname"], attrs["fieldname"]))
        self.xml.append("  " * self.level + '<mx:dataProvider><mx:Array>')

    def end_combobox(self):
        self.xml.append("  " * self.level + '</mx:Array></mx:dataProvider></mx:ComboBox></mx:FormItem>')

    def start_combooption(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:Object label="%(label)s" value="%(value)s"/>' % attrs)

    def start_radiobutton(self, attrs):
        self.id += 1
        self.current_fieldname = attrs["fieldname"]
        self.groupname = self.id
        self.xml.append("  " * self.level + '<mx:FormItem label="" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0"><mx:VBox label="%(label)s" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0" width="100%%" height="100%%">' % attrs)
        self.xml.append("  " * self.level + '<mx:Form borderColor="0xB7BABC" borderStyle="outset" verticalGap="0" horizontalGap="0" width="100%" height="100%" color="0x323232" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0">')
        self.xml.append("  " * self.level + '<mx:FormHeading label="%(label)s" paddingTop="0" />' % attrs)

    def end_radiobutton(self):
        self.xml.append("  " * self.level + '</mx:Form>')
        self.xml.append("  " * self.level + "</mx:VBox></mx:FormItem>")

    def start_radiooption(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:RadioButton label="%s" groupName="%s" id="field_%s_%s" value="%s" selected="{(window.record.fields.%s == %s)}" click="afterEditRadioButton(event, \'%s\');"/>' % (attrs["label"], self.groupname, self.current_fieldname, self.id, attrs["value"], self.current_fieldname, attrs["value"], self.current_fieldname))

    def start_matrix(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:DataGrid id="detail_%s_%s" itemEditBeginning="beforeEditRow(\'%s\', detail_%s_%s, event);" itemEditEnd="afterEditRow(\'%s\', detail_%s_%s, event);" width="100%%" height="100%%" paddingTop="0" paddingBottom="0" paddingLeft="0" paddingRight="0" color="0x323232" editable="true" dataProvider="{window.record.details.%s.record}">' % (attrs["name"], self.id,attrs["fieldname"], attrs["name"], self.id,attrs["fieldname"], attrs["name"], self.id,attrs["fieldname"]))
        self.xml.append("  " * self.level + '<mx:columns>')
        self.xml.append("  " * self.level + '<mx:DataGridColumn headerText="" dataField="matrixRowNr" editable="false"/>')
        self.has_matrix = True
        
    def start_matrixcolumn(self, attrs):
        self.id += 1
        self.xml.append("  " * self.level + '<mx:DataGridColumn headerText="%s" id ="detailfield_%s_%s" dataField="%s"/>' % (attrs["label"], attrs["fieldname"], self.id, attrs["fieldname"]))

    def end_matrix(self):
        self.xml.append("  " * self.level + '</mx:columns>')
        self.xml.append("  " * self.level + '</mx:DataGrid>') 

    def start_label(self, attrs):
        pass

    def start_pushbutton(self, attrs):
        pass

    def start_action(self, attrs):
        self.actions.append((attrs["label"], attrs["methodname"]))

    def start_webaction(self, attrs):
        self.actions.append((attrs["label"], attrs["methodname"]))

    def start_reportview(self, attrs):
        self.xml.append("  " * self.level + '<pdb:IFrame id="myreport" visible="true" source="http://127.0.0.1/cgi-bin/testflex.py?action=GET_REPORT_HTML&amp;&amp;reportname=VoucherPrintingReport" width="100%" height="100%"/>')
        
    def getResultXML(self):
        return self.xml
        
class MXMLGenerator:
    
    def generate(self, sourcefn):
          from xml.sax import make_parser
          from xml.sax.handler import feature_namespaces
          parser = make_parser()
          parser.setFeature(feature_namespaces, 0)
          handler = MXMLGeneratorHandler()
          parser.setContentHandler(handler)
          parser.parse(open(sourcefn))
          res = []
          res.append('<?xml version="1.0" encoding="utf-8"?>\n<mx:Application applicationComplete="appComplete();" xmlns:mx="http://www.adobe.com/2006/mxml"  xmlns:pdb="*" layout="vertical" verticalAlign="top" width="100%" horizontalAlign="center" pageTitle="Open Orange" backgroundGradientColors="[0x000000,0x323232]" paddingLeft="2" paddingTop="2" paddingBottom="2" paddingRight="2" viewSourceURL="srcview/index.html">')
          script_dict = {}
          script_dict["rowscript"] = ""
          script_dict["cc"] = handler.cc
          if handler.has_matrix: script_dict["rowscript"] = rowscript % script_dict
          
          script_dict["recordname"] = handler.recordname
          script_dict["windowname"] = handler.windowname
          res.append(script % script_dict)
          res.append("""
                     <mx:ApplicationControlBar width="100%%">
                       <mx:Button label="new" color="0x000000" click="request_to_server_new()"/>
                       <mx:Button label="save" color="0x000000" click="request_to_server_save()"/>
                       <!--mx:Button label="previous" color="0x000000" click="request_to_server_previous()"/>
                       <mx:Button label="next" color="0x000000" click="request_to_server_next()"/-->
                       <mx:Spacer/>
                       <mx:MenuBar id="myMenuBar" labelField="@label" itemClick="actionClicked(event)">
                            <mx:XMLList>
                                <menuitem label="Actions">
                                    %s
                                </menuitem>
                            </mx:XMLList>
                        </mx:MenuBar>                    
                    </mx:ApplicationControlBar>""" % ''.join(map(lambda x: '<menuitem label="%s" methodname="%s"/>' % (x[0],x[1]), handler.actions)))
                    
          res.extend(handler.getResultXML())
          res.append('</mx:Application>')
          return res
    
    
def run():
    parser = MXMLGenerator()
    res = parser.generate("g:/desarrollos/openorange/develop/standard/interface/Voucher.window.xml")
    #print '\n'.join(res)
    open("../../web/www/sample3.mxml","w").write('\n'.join(res))
    import os
    os.system("g:\\programas\\flex_sdk_3\\bin\\mxmlc G:\\desarrollos\\openorange\\develop\\web\\www\\sample3.mxml")

#run()