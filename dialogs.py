import wx
import theme
import stat
import os
import threading
import tempfile
import shutil
from sftp_helpers import upload_item, download_item, delete_item

class AddServerDialog(wx.Dialog):
    def __init__(self, parent, title="Add SSH Server", server_to_edit=None):
        super(AddServerDialog, self).__init__(parent, title=title, size=(400, 420))
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self.panel, label="Server Name:"), flag=wx.RIGHT, border=8)
        self.name = wx.TextCtrl(self.panel)
        hbox1.Add(self.name, proportion=1)
        self.vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(self.panel, label="Hostname/IP:"), flag=wx.RIGHT, border=8)
        self.host = wx.TextCtrl(self.panel)
        hbox2.Add(self.host, proportion=1)
        self.vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(wx.StaticText(self.panel, label="Port:"), flag=wx.RIGHT, border=8)
        self.port = wx.TextCtrl(self.panel, value="22")
        hbox3.Add(self.port, proportion=1)
        self.vbox.Add(hbox3, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(wx.StaticText(self.panel, label="Username:"), flag=wx.RIGHT, border=8)
        self.username = wx.TextCtrl(self.panel)
        hbox4.Add(self.username, proportion=1)
        self.vbox.Add(hbox4, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        auth_methods = ["Password", "SSH Key"]
        hbox_auth = wx.BoxSizer(wx.HORIZONTAL)
        hbox_auth.Add(wx.StaticText(self.panel, label="Auth Method:"), flag=wx.RIGHT, border=8)
        self.auth_choice = wx.Choice(self.panel, choices=auth_methods)
        self.auth_choice.SetSelection(0)
        hbox_auth.Add(self.auth_choice, proportion=1)
        self.vbox.Add(hbox_auth, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        self.password_sizer = wx.BoxSizer(wx.VERTICAL)
        hbox_pass = wx.BoxSizer(wx.HORIZONTAL)
        hbox_pass.Add(wx.StaticText(self.panel, label="Password:"), flag=wx.RIGHT, border=8)
        self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.password.SetHint("Leave blank to keep unchanged")
        hbox_pass.Add(self.password, proportion=1)
        self.password_sizer.Add(hbox_pass, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        self.store_password_cb = wx.CheckBox(self.panel, label="Store password securely")
        self.password_sizer.Add(self.store_password_cb, flag=wx.LEFT|wx.TOP, border=10)
        self.vbox.Add(self.password_sizer, 0, flag=wx.EXPAND)
        self.key_sizer = wx.BoxSizer(wx.VERTICAL)
        hbox_key_path = wx.BoxSizer(wx.HORIZONTAL)
        hbox_key_path.Add(wx.StaticText(self.panel, label="Private Key:"), flag=wx.RIGHT, border=8)
        self.key_path = wx.TextCtrl(self.panel)
        hbox_key_path.Add(self.key_path, 1, wx.RIGHT, 5)
        browse_btn = wx.Button(self.panel, label="Browse...")
        hbox_key_path.Add(browse_btn)
        self.key_sizer.Add(hbox_key_path, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        hbox_passphrase = wx.BoxSizer(wx.HORIZONTAL)
        hbox_passphrase.Add(wx.StaticText(self.panel, label="Passphrase:"), flag=wx.RIGHT, border=8)
        self.passphrase = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.passphrase.SetHint("Leave blank to keep unchanged")
        hbox_passphrase.Add(self.passphrase, proportion=1)
        self.key_sizer.Add(hbox_passphrase, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        self.store_passphrase_cb = wx.CheckBox(self.panel, label="Store passphrase securely")
        self.key_sizer.Add(self.store_passphrase_cb, flag=wx.LEFT|wx.TOP, border=10)
        self.vbox.Add(self.key_sizer, 0, flag=wx.EXPAND)
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_button = wx.Button(self.panel, label="Add", id=wx.ID_OK)
        cancel_button = wx.Button(self.panel, label="Cancel", id=wx.ID_CANCEL)
        hbox_buttons.Add(self.ok_button)
        hbox_buttons.Add(cancel_button, flag=wx.LEFT, border=5)
        self.vbox.Add(hbox_buttons, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        self.panel.SetSizer(self.vbox)
        self.auth_choice.Bind(wx.EVT_CHOICE, self.on_auth_method_change)
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_key)
        self.password.Bind(wx.EVT_TEXT, self.on_credential_change)
        self.passphrase.Bind(wx.EVT_TEXT, self.on_credential_change)
        if server_to_edit:
            self.SetTitle("Edit SSH Server")
            self.ok_button.SetLabel("Save")
            self.populate_fields(server_to_edit)
        self.on_auth_method_change(None)
        theme.apply_dark_theme(self)
        self.name.SetFocus()
    def populate_fields(self, server):
        self.name.SetValue(server.get("name", ""))
        self.host.SetValue(server.get("host", ""))
        self.port.SetValue(str(server.get("port", 22)))
        self.username.SetValue(server.get("user", ""))
        auth_method = server.get("auth_method", "password")
        if auth_method == "key":
            self.auth_choice.SetSelection(1)
            self.key_path.SetValue(server.get("key_path", ""))
            self.store_passphrase_cb.SetValue(server.get("password_stored", False))
        else:
            self.auth_choice.SetSelection(0)
            self.store_password_cb.SetValue(server.get("password_stored", False))
    def on_credential_change(self, event):
        is_password_method = self.auth_choice.GetStringSelection() == "Password"
        if is_password_method:
            has_credential = bool(self.password.GetValue())
            self.store_password_cb.Enable(has_credential)
            if not has_credential: self.store_password_cb.SetValue(False)
        else:
            has_credential = bool(self.passphrase.GetValue())
            self.store_passphrase_cb.Enable(has_credential)
            if not has_credential: self.store_passphrase_cb.SetValue(False)
        if event: event.Skip()
    def on_auth_method_change(self, event):
        is_password = self.auth_choice.GetStringSelection() == "Password"
        self.vbox.Show(self.password_sizer, is_password, recursive=True)
        self.vbox.Show(self.key_sizer, not is_password, recursive=True)
        self.on_credential_change(None)
        self.panel.Layout()
    def on_browse_key(self, event):
        with wx.FileDialog(self, "Open SSH private key", wildcard="All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            self.key_path.SetValue(fileDialog.GetPath())
    def get_data(self):
        is_password = self.auth_choice.GetStringSelection() == "Password"
        data = {
            "name": self.name.GetValue(),
            "host": self.host.GetValue(),
            "port": int(self.port.GetValue() or 22),
            "user": self.username.GetValue(),
            "auth_method": "password" if is_password else "key",
            "store_credential": self.store_password_cb.GetValue() if is_password else self.store_passphrase_cb.GetValue()
        }
        if data["auth_method"] == "password":
            data["password"] = self.password.GetValue()
        else:
            data["key_path"] = self.key_path.GetValue()
            data["passphrase"] = self.passphrase.GetValue()
        return data

class FileBrowserDialog(wx.Dialog):
    def __init__(self, parent, sftp_client, edit_callback):
        super(FileBrowserDialog, self).__init__(parent, title="SFTP File Browser", size=(600, 480))
        
        self.sftp = sftp_client
        self.current_path = self.sftp.getcwd() or "/"
        self.edit_callback = edit_callback
        self.progress_dialog = None
        self.copy_temp_dir = None

        panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.path_text = wx.StaticText(panel, label=self.current_path)
        self.vbox.Add(self.path_text, 0, wx.ALL|wx.EXPAND, 5)
        self.file_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.file_list.InsertColumn(0, "Name", width=250)
        self.file_list.InsertColumn(1, "Size", width=100)
        self.file_list.InsertColumn(2, "Type", width=100)
        self.vbox.Add(self.file_list, 1, wx.ALL|wx.EXPAND, 5)
        
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_button = wx.Button(panel, label="Upload")
        self.download_button = wx.Button(panel, label="Download")
        self.copy_button = wx.Button(panel, label="Copy")
        self.edit_button = wx.Button(panel, label="Edit")
        self.delete_button = wx.Button(panel, label="Delete")
        close_button = wx.Button(panel, label="Close", id=wx.ID_CANCEL)
        
        hbox_buttons.Add(self.upload_button)
        hbox_buttons.Add(self.download_button, flag=wx.LEFT, border=5)
        hbox_buttons.Add(self.copy_button, flag=wx.LEFT, border=5)
        hbox_buttons.Add(self.edit_button, flag=wx.LEFT, border=5)
        hbox_buttons.Add(self.delete_button, flag=wx.LEFT, border=5)
        hbox_buttons.AddStretchSpacer()
        hbox_buttons.Add(close_button)
        self.vbox.Add(hbox_buttons, 0, wx.ALL|wx.EXPAND, 5)
        
        self.status_text = wx.StaticText(panel, label=" ")
        self.vbox.Add(self.status_text, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        panel.SetSizer(self.vbox)

        self.file_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)
        self.file_list.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_button)
        self.upload_button.Bind(wx.EVT_BUTTON, self.on_upload)
        self.download_button.Bind(wx.EVT_BUTTON, self.on_download)
        self.copy_button.Bind(wx.EVT_BUTTON, self.on_copy)
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        theme.apply_dark_theme(self)
        self.populate_files()

    def on_close(self, event):
        if self.copy_temp_dir and os.path.exists(self.copy_temp_dir):
            try: shutil.rmtree(self.copy_temp_dir)
            except Exception as e: print(f"Warning: Could not remove copy temp dir {self.copy_temp_dir}: {e}")
        self.Destroy()

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_BACK: self.go_to_parent_directory()
        elif event.GetKeyCode() == wx.WXK_DELETE: self.on_delete(None)
        elif event.ControlDown() and event.GetKeyCode() == ord('V'): self.on_paste_upload()
        elif event.ControlDown() and event.GetKeyCode() == ord('C'): self.on_copy(None)
        else: event.Skip()

    def on_selection_changed(self, event):
        selected_count = self.file_list.GetSelectedItemCount()
        self.download_button.Enable(selected_count > 0)
        self.copy_button.Enable(selected_count > 0)
        self.delete_button.Enable(selected_count > 0)
        if selected_count == 1:
            idx = self.file_list.GetFirstSelected()
            item_type = self.file_list.GetItemText(idx, col=2)
            self.edit_button.Enable(item_type == "File")
        else: self.edit_button.Enable(False)

    def _put_paths_on_clipboard(self, local_paths):
        data = wx.FileDataObject()
        for path in local_paths: data.AddFile(path)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            self.status_text.SetLabel(f"Copied {len(local_paths)} item(s) to clipboard.")
        else:
            self.status_text.SetLabel("Error: Could not open clipboard.")

    def on_copy(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths: return
        if self.copy_temp_dir and os.path.exists(self.copy_temp_dir):
            shutil.rmtree(self.copy_temp_dir, ignore_errors=True)
        self.copy_temp_dir = tempfile.mkdtemp(prefix="teatype_copy_")
        self.progress_dialog = wx.ProgressDialog("Copying to Clipboard...", "", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
        self.Disable()
        worker = threading.Thread(target=self._copy_worker, args=(remote_paths, self.copy_temp_dir))
        worker.start()
        self.progress_dialog.Show()

    def _copy_worker(self, remote_paths, local_dest):
        local_paths = []
        try:
            for i, remote_path in enumerate(remote_paths):
                filename = os.path.basename(remote_path)
                local_path = os.path.join(local_dest, filename)
                local_paths.append(local_path)
                wx.CallAfter(self.progress_dialog.Update, 0, f"Downloading {filename} for copy ({i+1}/{len(remote_paths)})...")
                def progress_callback(transferred, total):
                    if self.progress_dialog:
                        percent = int(transferred / total * 100)
                        wx.CallAfter(self.progress_dialog.Update, percent)
                download_item(self.sftp, remote_path, local_path, progress_callback)
            wx.CallAfter(self._put_paths_on_clipboard, local_paths)
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Copy failed: {e}", "Error", wx.ICON_ERROR)
        finally:
            if self.progress_dialog: wx.CallAfter(self.progress_dialog.Destroy)
            wx.CallAfter(self.Enable)

    def on_upload(self, event):
        with wx.FileDialog(self, "Choose files or directories to upload",
                           style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.start_upload_thread(dlg.GetPaths())
    
    def start_upload_thread(self, local_paths):
        if not local_paths: return
        self.progress_dialog = wx.ProgressDialog("Uploading...", "", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
        self.Disable()
        worker = threading.Thread(target=self._upload_worker, args=(local_paths,))
        worker.start()
        self.progress_dialog.Show()

    def _upload_worker(self, local_paths):
        try:
            for i, local_path in enumerate(local_paths):
                filename = os.path.basename(local_path)
                remote_path = f"{self.current_path}/{filename}"
                wx.CallAfter(self.progress_dialog.Update, 0, f"Uploading {filename} ({i+1}/{len(local_paths)})...")
                def progress_callback(transferred, total):
                    if self.progress_dialog:
                        percent = int(transferred / total * 100)
                        wx.CallAfter(self.progress_dialog.Update, percent)
                upload_item(self.sftp, local_path, remote_path, progress_callback)
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Upload failed: {e}", "Error", wx.ICON_ERROR)
        finally:
            if self.progress_dialog: wx.CallAfter(self.progress_dialog.Destroy)
            wx.CallAfter(self.Enable)
            wx.CallAfter(self.populate_files)

    def on_download(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths: return
        with wx.DirDialog(self, "Choose download destination", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                local_dest = dlg.GetPath()
                self.progress_dialog = wx.ProgressDialog("Downloading...", "", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
                self.Disable()
                worker = threading.Thread(target=self._download_worker, args=(remote_paths, local_dest))
                worker.start()
                self.progress_dialog.Show()

    def _download_worker(self, remote_paths, local_dest):
        try:
            for i, remote_path in enumerate(remote_paths):
                filename = os.path.basename(remote_path)
                local_path = os.path.join(local_dest, filename)
                wx.CallAfter(self.progress_dialog.Update, 0, f"Downloading {filename} ({i+1}/{len(remote_paths)})...")
                def progress_callback(transferred, total):
                    if self.progress_dialog:
                        percent = int(transferred / total * 100)
                        wx.CallAfter(self.progress_dialog.Update, percent)
                download_item(self.sftp, remote_path, local_path, progress_callback)
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Download failed: {e}", "Error", wx.ICON_ERROR)
        finally:
            if self.progress_dialog: wx.CallAfter(self.progress_dialog.Destroy)
            wx.CallAfter(self.Enable)

    def on_delete(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths: return
        count = len(remote_paths)
        message = f"Are you sure you want to permanently delete {count} item(s)?"
        if count == 1:
            message = f"Are you sure you want to permanently delete '{os.path.basename(remote_paths[0])}'?"
        result = wx.MessageBox(message, "Confirm Deletion", wx.YES_NO | wx.ICON_WARNING)
        if result != wx.YES: return
        self.progress_dialog = wx.ProgressDialog("Deleting...", "", maximum=count, parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
        self.Disable()
        worker = threading.Thread(target=self._delete_worker, args=(remote_paths,))
        worker.start()
        self.progress_dialog.Show()

    def _delete_worker(self, remote_paths):
        try:
            for i, remote_path in enumerate(remote_paths):
                filename = os.path.basename(remote_path)
                wx.CallAfter(self.progress_dialog.Update, i, f"Deleting {filename}...")
                delete_item(self.sftp, remote_path)
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Deletion failed: {e}", "Error", wx.ICON_ERROR)
        finally:
            if self.progress_dialog: wx.CallAfter(self.progress_dialog.Destroy)
            wx.CallAfter(self.Enable)
            wx.CallAfter(self.populate_files)
    
    def go_to_parent_directory(self):
        if self.current_path != "/":
            parts = self.current_path.rstrip('/').split('/')
            self.current_path = '/'.join(parts[:-1]) or "/"
            self.populate_files()
            
    def get_selected_remote_paths(self):
        paths = []
        idx = -1
        while True:
            idx = self.file_list.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1: break
            name = self.file_list.GetItemText(idx)
            if self.current_path == "/": paths.append(f"/{name}")
            else: paths.append(f"{self.current_path}/{name}")
        return paths
        
    def populate_files(self):
        self.path_text.SetLabel(f"Path: {self.current_path}")
        self.file_list.DeleteAllItems()
        if self.current_path != "/":
            index = self.file_list.InsertItem(self.file_list.GetItemCount(), "..")
            self.file_list.SetItem(index, 2, "Parent Directory")
        try:
            for attr in self.sftp.listdir_attr(self.current_path):
                index = self.file_list.InsertItem(self.file_list.GetItemCount(), attr.filename)
                self.file_list.SetItem(index, 1, str(attr.st_size))
                file_mode = attr.st_mode
                if stat.S_ISDIR(file_mode): self.file_list.SetItem(index, 2, "Directory")
                else: self.file_list.SetItem(index, 2, "File")
        except Exception as e:
            wx.MessageBox(f"Could not list directory: {e}", "SFTP Error", wx.ICON_ERROR)
        self.on_selection_changed(None)
        
    def on_item_activated(self, event):
        item_text = event.GetText()
        item_type = self.file_list.GetItemText(event.GetIndex(), col=2)
        if item_type == "Directory":
            if self.current_path == "/": self.current_path += item_text
            else: self.current_path += f"/{item_text}"
            self.populate_files()
        elif item_type == "Parent Directory": self.go_to_parent_directory()
        elif item_type == "File": self.on_edit_button(None)
        
    def on_edit_button(self, event):
        remote_paths = self.get_selected_remote_paths()
        if remote_paths:
            self.edit_callback(remote_paths[0])
            # self.Close() <-- This line is removed to keep the browser open.

    def on_paste_upload(self):
        data = wx.FileDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
            if success: self.start_upload_thread(data.GetFilenames())