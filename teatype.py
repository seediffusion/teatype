import wx
import json
import os
from dialogs import AddServerDialog
from terminal_frame import TerminalFrame
from security import (
    store_password, get_password, delete_password,
    store_passphrase, get_passphrase, delete_passphrase
)
import theme
from menu_mixin import SettingsMenuMixin

SERVERS_FILE = "servers.json"

class MainFrame(wx.Frame, SettingsMenuMixin):
    def __init__(self):
        super().__init__(None, title="Teatype - Server Manager", size=(600, 400))
        SettingsMenuMixin.__init__(self)
        self.servers = []
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Name", width=150)
        self.list_ctrl.InsertColumn(1, "Hostname", width=150)
        self.list_ctrl.InsertColumn(2, "Port", width=60)
        self.list_ctrl.InsertColumn(3, "Username", width=120)
        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.connect_btn = wx.Button(panel, label="&Connect")
        self.add_btn = wx.Button(panel, label="&Add")
        self.edit_btn = wx.Button(panel, label="&Edit")
        self.remove_btn = wx.Button(panel, label="&Remove")
        hbox.Add(self.connect_btn)
        hbox.Add(self.add_btn, flag=wx.LEFT, border=5)
        hbox.Add(self.edit_btn, flag=wx.LEFT, border=5)
        hbox.Add(self.remove_btn, flag=wx.LEFT, border=5)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.TOP, 5)
        panel.SetSizer(vbox)
        self.Bind(wx.EVT_BUTTON, self.on_connect, self.connect_btn)
        self.Bind(wx.EVT_BUTTON, self.on_add, self.add_btn)
        self.Bind(wx.EVT_BUTTON, self.on_edit, self.edit_btn)
        self.Bind(wx.EVT_BUTTON, self.on_remove, self.remove_btn)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_connect)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)
        theme.apply_dark_theme(self)
        self.load_servers()
        self.populate_list()
        self.Centre()
        self.Show()

    def update_server_last_path(self, server_name, last_path):
        """Finds a server by name and updates its last_path."""
        for server in self.servers:
            if server.get("name") == server_name:
                server["last_path"] = last_path
                self.save_servers()
                break

    def update_button_states(self):
        has_selection = self.list_ctrl.GetFirstSelected() != -1
        self.connect_btn.Enable(has_selection)
        self.remove_btn.Enable(has_selection)
        self.edit_btn.Enable(has_selection)
        
    def on_selection_changed(self, event):
        self.update_button_states()
        event.Skip()
        
    def load_servers(self):
        if os.path.exists(SERVERS_FILE):
            try:
                with open(SERVERS_FILE, "r") as f: self.servers = json.load(f)
            except json.JSONDecodeError: self.servers = []
        else: self.servers = []
        
    def save_servers(self):
        with open(SERVERS_FILE, "w") as f: json.dump(self.servers, f, indent=4)
        
    def populate_list(self):
        self.list_ctrl.DeleteAllItems()
        for i, server in enumerate(self.servers):
            self.list_ctrl.InsertItem(i, server["name"])
            self.list_ctrl.SetItem(i, 1, server["host"])
            self.list_ctrl.SetItem(i, 2, str(server["port"]))
            self.list_ctrl.SetItem(i, 3, server["user"])
        self.update_button_states()
        
    def on_add(self, event):
        with AddServerDialog(self, title="Add SSH Server") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.get_data()
                new_server = {
                    "name": data["name"], "host": data["host"], "port": data["port"],
                    "user": data["user"], "auth_method": data["auth_method"],
                    "password_stored": data["store_credential"]
                }
                if data["auth_method"] == "key":
                    new_server["key_path"] = data["key_path"]
                    new_server["has_passphrase"] = bool(data["passphrase"])
                if data["store_credential"]:
                    if data["auth_method"] == "password":
                        store_password(server_name=data["name"], host=data["host"], user=data["user"], password=data["password"])
                    else:
                        store_passphrase(server_name=data["name"], host=data["host"], user=data["user"], passphrase=data["passphrase"])
                self.servers.append(new_server)
                self.save_servers()
                self.populate_list()
                
    def on_edit(self, event):
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: return
        original_server = self.servers[selected_index]
        with AddServerDialog(self, title="Edit SSH Server", server_to_edit=original_server) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                new_data = dlg.get_data()
                if original_server.get("password_stored"):
                    if original_server.get("auth_method", "password") == "key":
                        delete_passphrase(server_name=original_server["name"], host=original_server["host"], user=original_server["user"])
                    else:
                        delete_password(server_name=original_server["name"], host=original_server["host"], user=original_server["user"])
                if new_data["store_credential"]:
                    if new_data["auth_method"] == "password" and new_data["password"]:
                        store_password(server_name=new_data["name"], host=new_data["host"], user=new_data["user"], password=new_data["password"])
                    elif new_data["auth_method"] == "key" and new_data["passphrase"]:
                        store_passphrase(server_name=new_data["name"], host=new_data["host"], user=new_data["user"], passphrase=new_data["passphrase"])
                
                updated_server = original_server.copy()
                updated_server.update({
                    "name": new_data["name"], "host": new_data["host"], "port": new_data["port"],
                    "user": new_data["user"], "auth_method": new_data["auth_method"],
                    "password_stored": new_data["store_credential"]
                })

                if new_data["auth_method"] == "key":
                    updated_server["key_path"] = new_data["key_path"]
                    if new_data["passphrase"]:
                        updated_server["has_passphrase"] = True
                    else:
                        # If the passphrase field was cleared, we must update has_passphrase
                        updated_server["has_passphrase"] = False
                
                self.servers[selected_index] = updated_server
                self.save_servers()
                self.populate_list()

    def on_remove(self, event):
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index != -1:
            server_to_remove = self.servers[selected_index]
            confirm = wx.MessageBox(f"Are you sure you want to remove '{server_to_remove['name']}'?", "Confirm Deletion", wx.YES_NO | wx.ICON_QUESTION)
            if confirm == wx.YES:
                if server_to_remove.get("password_stored", False):
                    auth_method = server_to_remove.get("auth_method", "password")
                    if auth_method == "password":
                        delete_password(server_name=server_to_remove["name"], host=server_to_remove["host"], user=server_to_remove["user"])
                    else:
                        delete_passphrase(server_name=server_to_remove["name"], host=server_to_remove["host"], user=server_to_remove["user"])
                self.servers.pop(selected_index)
                self.save_servers()
                self.populate_list()
                
    def on_connect(self, event):
        selected_index = -1
        if isinstance(event, wx.ListEvent):
            selected_index = event.GetIndex()
        else:
            selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: return
        server_info = self.servers[selected_index].copy()
        auth_method = server_info.get("auth_method", "password")
        connect_kwargs = {'hostname': server_info['host'], 'port': server_info['port'], 'username': server_info['user']}
        if auth_method == "password":
            password = None
            if server_info.get("password_stored"):
                password = get_password(server_name=server_info["name"], host=server_info["host"], user=server_info["user"])
            if password is None:
                with wx.PasswordEntryDialog(self, f"Enter password for {server_info['user']}@{server_info['host']}", "Password Required") as dlg:
                    if dlg.ShowModal() == wx.ID_OK: password = dlg.GetValue()
                    else: return
            connect_kwargs['password'] = password
        else:
            if not server_info.get("key_path"):
                wx.MessageBox("No private key path specified for this server.", "Error", wx.OK | wx.ICON_ERROR)
                return
            connect_kwargs['key_filename'] = server_info['key_path']
            passphrase = None
            if server_info.get("password_stored"):
                passphrase = get_passphrase(server_name=server_info["name"], host=server_info["host"], user=server_info["user"])
            if passphrase is None and server_info.get("has_passphrase", False):
                with wx.PasswordEntryDialog(self, f"Enter passphrase for key\n{server_info['key_path']}", "Passphrase Required", "Passphrase Required (leave blank if none)") as dlg:
                    if dlg.ShowModal() == wx.ID_OK: passphrase = dlg.GetValue()
                    else: return
            connect_kwargs['passphrase'] = passphrase
        TerminalFrame(self, server_info, connect_kwargs)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()