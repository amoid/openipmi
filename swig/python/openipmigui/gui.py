import wx
import _domainDialog

class IPMITreeCtrl(wx.TreeCtrl):
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)

    def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        self.log.WriteText('compare: ' + t1 + ' <> ' + t2 + '\n')
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1

class IPMICloser:
    def __init__(self, ui, count):
        self.ui = ui
        self.count = count
    
    def domain_cb(self, domain):
        domain.close(self)

    def domain_close_done_cb(self):
        self.count = self.count - 1
        if (self.count == 0):
            self.ui.Close(True)

class IPMIGUI(wx.Frame):
    def __init__(self, mainhandler):
        wx.Frame.__init__(self, None, 01, "IPMI GUI")

        self.mainhandler = mainhandler
        
        menubar = wx.MenuBar()
        
        filemenu = wx.Menu()
        filemenu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.quit, id=wx.ID_EXIT);
        item = filemenu.Append(-1, "&Open Domain\tCtrl-O", "Open Domain")
        self.Bind(wx.EVT_MENU, self.openDomain, item);
        item = filemenu.Append(-1, "&Save Prefs\tCtrl-s", "Save Prefs")
        self.Bind(wx.EVT_MENU, self.savePrefs, item);
        menubar.Append(filemenu, "&File")
        
        self.SetMenuBar(menubar)

        box = wx.BoxSizer(wx.HORIZONTAL)

        isz = (16, 16)
        self.tree = IPMITreeCtrl(self)
        self.treeroot = self.tree.AddRoot("Domains")
        self.tree.SetPyData(self.treeroot, None)
        box.Add(self.tree, 1,
                wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALIGN_BOTTOM | wx.GROW,
                0)

        self.logwindow = wx.TextCtrl(self, -1,
                                     style=(wx.TE_MULTILINE
                                            | wx.TE_READONLY
                                            | wx.HSCROLL))
        box.Add(self.logwindow, 1,
                wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.ALIGN_BOTTOM | wx.GROW,
                0)
        self.logcount = 0
        self.maxloglines = 1000

        self.SetSizer(box);

        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.TreeMenu)
        self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.TreeExpanded)

        self.Show(True)

    def quit(self, event):
        self.closecount = len(self.mainhandler.domains)
        if (self.closecount == 0):
            self.Close(True)
            return
        closer = IPMICloser(self, self.closecount)
        for v in self.mainhandler.domains.itervalues():
            v.domain_id.convert_to_domain(closer)

    def openDomain(self, event):
        dialog = _domainDialog.OpenDomainDialog(self.mainhandler)
        dialog.CenterOnScreen();
        dialog.Show(True);

    def savePrefs(self, event):
        self.mainhandler.savePrefs()
        
    def new_log(self, log):
        newlines = log.count('\n') + 1
        self.logwindow.AppendText(log + "\n")
        self.logcount += newlines
        while (self.logcount > self.maxloglines):
            end = self.logwindow.GetLineLength(0)
            self.logwindow.Remove(0, end+1)
            self.logcount -= 1

    def add_domain(self, d):
        d.treeroot = self.tree.AppendItem(self.treeroot, str(d))
        self.tree.SetPyData(d.treeroot, d)
        d.entityroot = self.tree.AppendItem(d.treeroot, "Entities")
        d.mcroot = self.tree.AppendItem(d.treeroot, "MCs")
        self.tree.Expand(self.treeroot)

    def prepend_item(self, o, name, value, data=None):
        if (value == None):
            item = self.tree.PrependItem(o.treeroot, name + ":")
            self.tree.SetItemTextColour(item, wx.LIGHT_GREY)
        else:
            item = self.tree.PrependItem(o.treeroot, name + ":\t" + value)
            self.tree.SetItemTextColour(item, wx.BLACK)
        self.tree.SetPyData(item, data)
        return item

    def append_item(self, o, name, value, data=None):
        if (value == None):
            item = self.tree.AppendItem(o.treeroot, name + ":")
            self.tree.SetItemTextColour(item, wx.LIGHT_GREY)
        else:
            item = self.tree.AppendItem(o.treeroot, name + ":\t" + value)
            self.tree.SetItemTextColour(item, wx.BLACK)
        self.tree.SetPyData(item, data)
        return item

    def set_item_text(self, item, name, value):
        if (value == None):
            self.tree.SetItemText(item, name + ":")
            self.tree.SetItemTextColour(item, wx.LIGHT_GREY)
        else:
            self.tree.SetItemText(item, name + ":\t" + value)
            self.tree.SetItemTextColour(item, wx.BLACK)

    def get_item_pos(self, item):
        rect = self.tree.GetBoundingRect(item)
        if (rect == None):
            return None
        return wx.Point(rect.GetLeft(), rect.GetBottom())

    def TreeMenu(self, event):
        item = event.GetItem()
        data = self.tree.GetPyData(item)
        if (data != None) and (hasattr(data, "HandleMenu")):
            data.HandleMenu(event)

    # FIXME - expand of parent doesn't affect children...
    def TreeExpanded(self, event):
        item = event.GetItem()
        data = self.tree.GetPyData(item)
        if (data != None) and (hasattr(data, "HandleExpand")):
            data.HandleExpand(event)

    def remove_domain(self, d):
        if (hasattr(d, "treeroot")):
            self.tree.Delete(d.treeroot)

    def add_entity(self, d, e):
        e.treeroot = self.tree.AppendItem(d.entityroot, str(e))
        e.sensorroot = self.tree.AppendItem(e.treeroot, "Sensors")
        e.controlroot = self.tree.AppendItem(e.treeroot, "Controls")
        self.tree.SetPyData(e.treeroot, None)
        self.tree.SetPyData(e.sensorroot, None)
        self.tree.SetPyData(e.controlroot, None)
    
    def remove_entity(self, e):
        if (hasattr(e, "treeroot")):
            self.tree.Delete(e.treeroot)

    def add_mc(self, d, m):
        m.treeroot = self.tree.AppendItem(d.mcroot, m.name)
        self.tree.SetPyData(m.treeroot, None)

    def remove_mc(self, m):
        if (hasattr(m, "treeroot")):
            self.tree.Delete(m.treeroot)

    def add_sensor(self, e, s):
        s.treeroot = self.tree.AppendItem(e.sensorroot, str(s))

    def remove_sensor(self, s):
        if (hasattr(s, "treeroot")):
            self.tree.Delete(s.treeroot)

    def add_control(self, e, c):
        c.treeroot = self.tree.AppendItem(e.controlroot, str(c))

    def remove_control(self, c):
        if (hasattr(c, "treeroot")):
            self.tree.Delete(c.treeroot)

