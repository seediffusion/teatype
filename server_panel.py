import wx
from dialogs import AddServerDialog

class ServerPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_book = parent # This is the Simplebook
        
        # --- FIX: Get a reference to the main application frame ---
        self.main_frame = self.GetTopLevelParent()

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Name", width=150)
        self.list_ctrl.InsertColumn(1, "Hostname", width=150)
        self.list_ctrl.InsertColumn(2, "Port", width=60)
        self.list_ctrl.InsertColumn(3, "Username", width=120)
        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.connect_btn = wx.Button(self, label="&Connect")
        self.add_btn = wx.Button(self, label="&Add")
        self.edit_btn = wx.Button(self, label="&Edit")
        self.remove_btn = wx.Button(self, label="&Remove")
        
        hbox.Add(self.connect_btn)
        hbox.Add(self.add_btn, flag=wx.LEFT, border=5)
        hbox.Add(self.edit_btn, flag=wx.LEFT, border=5)
        hbox.Add(self.remove_btn, flag=wx.LEFT, border=5)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.TOP, 5)
        
        self.SetSizer(vbox)

        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        self.edit_btn.Bind(wx.EVT_BUTTON, self.on_edit)
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_connect)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)

        self.populate_list()
        self.update_button_states()

    def update_button_states(self):
        has_selection = self.list_ctrl.GetFirstSelected() != -1
        self.connect_btn.Enable(has_selection)
        self.remove_btn.Enable(has_selection)
        self.edit_btn.Enable(has_selection)
        
    def on_selection_changed(self, event):
        self.update_button_states()
        event.Skip()

    def populate_list(self):
        self.list_ctrl.DeleteAllItems()
        # --- FIX: Call get_servers on the correct object ---
        servers = self.main_frame.get_servers()
        for i, server in enumerate(servers):
            self.list_ctrl.InsertItem(i, server["name"])
            self.list_ctrl.SetItem(i, 1, server["host"])
            self.list_ctrl.SetItem(i, 2, str(server["port"]))
            self.list_ctrl.SetItem(i, 3, server["user"])
        self.update_button_states()

    def on_connect(self, event):
        selected_index = -1
        if isinstance(event, wx.ListEvent):
            selected_index = event.GetIndex()
        else:
            selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index != -1:
            # --- FIX: Call connect_to_server on the correct object ---
            self.main_frame.connect_to_server(selected_index)

    def on_add(self, event):
        with AddServerDialog(self, title="Add SSH Server") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                # --- FIX: Call add_server on the correct object ---
                self.main_frame.add_server(dlg.get_data())

    def on_edit(self, event):
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: return
        # --- FIX: Call edit_server on the correct object ---
        self.main_frame.edit_server(selected_index)

    def on_remove(self, event):
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: return

        servers = self.main_frame.get_servers()
        server_to_remove = servers[selected_index]
        confirm = wx.MessageBox(f"Are you sure you want to remove '{server_to_remove['name']}'?", "Confirm Deletion", wx.YES_NO | wx.ICON_QUESTION)
        if confirm == wx.YES:
            # --- FIX: Call remove_server on the correct object ---
            self.main_frame.remove_server(selected_index)