import wx
import stat
import os
import threading
import tempfile
import shutil
import math

import theme
import speech
from sftp_helpers import (
    upload_item,
    download_item,
    delete_item,
    count_remote_items,
    count_local_items,
    TransferCancelledError,
)


def human_readable_size(size_bytes: int) -> str:
    """Convert a size in bytes to a human-readable string."""
    try:
        size_bytes = int(size_bytes)
    except (TypeError, ValueError):
        return "?"

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    try:
        i = int(math.floor(math.log(size_bytes, 1024)))
        i = min(i, len(size_name) - 1)
        p = math.pow(1024, i)
        s = round(size_bytes / p, 1)
        return f"{s} {size_name[i]}"
    except Exception:
        return str(size_bytes)


class AddServerDialog(wx.Dialog):
    """
    Dialog for adding or editing an SSH server definition.

    get_data() returns a dict with keys:
      - name, host, port, user
      - auth_method: "password" or "key"
      - password_stored: bool
      - password (optional, for password auth)
      - key_path, passphrase (optional, for key auth)
    """

    def __init__(self, parent, title="Add SSH Server", server_to_edit=None):
        super(AddServerDialog, self).__init__(parent, title=title, size=(400, 420))

        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # Server name
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self.panel, label="Server &Name:"), 0, wx.RIGHT, 8)
        self.name = wx.TextCtrl(self.panel)
        hbox1.Add(self.name, 1)
        self.vbox.Add(hbox1, 0, wx.EXPAND | wx.ALL, 10)

        # Hostname
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(self.panel, label="&Hostname/IP:"), 0, wx.RIGHT, 8)
        self.host = wx.TextCtrl(self.panel)
        hbox2.Add(self.host, 1)
        self.vbox.Add(hbox2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Port
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(wx.StaticText(self.panel, label="&Port:"), 0, wx.RIGHT, 8)
        self.port = wx.TextCtrl(self.panel, value="22")
        hbox3.Add(self.port, 1)
        self.vbox.Add(hbox3, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Username
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(wx.StaticText(self.panel, label="&Username:"), 0, wx.RIGHT, 8)
        self.username = wx.TextCtrl(self.panel)
        hbox4.Add(self.username, 1)
        self.vbox.Add(hbox4, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Auth method
        auth_methods = ["Password", "SSH Key"]
        hbox_auth = wx.BoxSizer(wx.HORIZONTAL)
        hbox_auth.Add(wx.StaticText(self.panel, label="Auth &Method:"), 0, wx.RIGHT, 8)
        self.auth_choice = wx.Choice(self.panel, choices=auth_methods)
        self.auth_choice.SetSelection(0)
        hbox_auth.Add(self.auth_choice, 1)
        self.vbox.Add(hbox_auth, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Password auth controls
        self.password_sizer = wx.BoxSizer(wx.VERTICAL)
        hbox_pass = wx.BoxSizer(wx.HORIZONTAL)
        hbox_pass.Add(wx.StaticText(self.panel, label="&Password:"), 0, wx.RIGHT, 8)
        self.password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.password.SetHint("Leave blank to keep unchanged")
        hbox_pass.Add(self.password, 1)
        self.password_sizer.Add(
            hbox_pass, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10
        )
        self.store_password_cb = wx.CheckBox(
            self.panel, label="&Store password securely"
        )
        self.password_sizer.Add(self.store_password_cb, 0, wx.LEFT | wx.BOTTOM, 10)
        self.vbox.Add(self.password_sizer, 0, wx.EXPAND)

        # Key auth controls
        self.key_sizer = wx.BoxSizer(wx.VERTICAL)
        hbox_key_path = wx.BoxSizer(wx.HORIZONTAL)
        hbox_key_path.Add(
            wx.StaticText(self.panel, label="Private &Key:"), 0, wx.RIGHT, 8
        )
        self.key_path = wx.TextCtrl(self.panel)
        hbox_key_path.Add(self.key_path, 1, wx.RIGHT, 5)
        browse_btn = wx.Button(self.panel, label="&Browse...")
        hbox_key_path.Add(browse_btn)
        self.key_sizer.Add(
            hbox_key_path, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10
        )

        hbox_passphrase = wx.BoxSizer(wx.HORIZONTAL)
        hbox_passphrase.Add(
            wx.StaticText(self.panel, label="Pass&phrase:"), 0, wx.RIGHT, 8
        )
        self.passphrase = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.passphrase.SetHint("Leave blank to keep unchanged")
        hbox_passphrase.Add(self.passphrase, 1)
        self.key_sizer.Add(
            hbox_passphrase, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10
        )

        self.store_passphrase_cb = wx.CheckBox(
            self.panel, label="Store passphrase &securely"
        )
        self.key_sizer.Add(self.store_passphrase_cb, 0, wx.LEFT | wx.BOTTOM, 10)
        self.vbox.Add(self.key_sizer, 0, wx.EXPAND)

        # Buttons
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_button = wx.Button(self.panel, id=wx.ID_OK, label="&OK")
        cancel_button = wx.Button(self.panel, id=wx.ID_CANCEL, label="&Cancel")
        hbox_buttons.Add(self.ok_button)
        hbox_buttons.Add(cancel_button, 0, wx.LEFT, 5)
        self.vbox.Add(hbox_buttons, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.SetSizer(self.vbox)

        # Events
        self.auth_choice.Bind(wx.EVT_CHOICE, self.on_auth_method_change)
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_key)
        self.password.Bind(wx.EVT_TEXT, self.on_credential_change)
        self.passphrase.Bind(wx.EVT_TEXT, self.on_credential_change)

        if server_to_edit:
            self.SetTitle("Edit SSH Server")
            self.ok_button.SetLabel("&Save")
            self.populate_fields(server_to_edit)
            self.on_auth_method_change(None)
        else:
            self.on_auth_method_change(None)

        theme.apply_dark_theme(self)
        self.name.SetFocus()

    def populate_fields(self, server: dict):
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
            has_cred = bool(self.password.GetValue())
            self.store_password_cb.Enable(has_cred)
            if not has_cred:
                self.store_password_cb.SetValue(False)
        else:
            has_cred = bool(self.passphrase.GetValue())
            self.store_passphrase_cb.Enable(has_cred)
            if not has_cred:
                self.store_passphrase_cb.SetValue(False)
        if event:
            event.Skip()

    def on_auth_method_change(self, event):
        is_password = self.auth_choice.GetStringSelection() == "Password"
        self.vbox.Show(self.password_sizer, is_password, recursive=True)
        self.vbox.Show(self.key_sizer, not is_password, recursive=True)
        self.on_credential_change(None)
        self.panel.Layout()

    def on_browse_key(self, event):
        with wx.FileDialog(
            self,
            "Open SSH private key",
            wildcard="All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            self.key_path.SetValue(dlg.GetPath())

    def get_data(self) -> dict:
        is_password = self.auth_choice.GetStringSelection() == "Password"
        data = {
            "name": self.name.GetValue(),
            "host": self.host.GetValue(),
            "port": int(self.port.GetValue() or 22),
            "user": self.username.GetValue(),
            "auth_method": "password" if is_password else "key",
            "password_stored": (
                self.store_password_cb.GetValue()
                if is_password
                else self.store_passphrase_cb.GetValue()
            ),
        }
        if data["auth_method"] == "password":
            data["password"] = self.password.GetValue()
        else:
            data["key_path"] = self.key_path.GetValue()
            data["passphrase"] = self.passphrase.GetValue()
        return data


class FileBrowserDialog(wx.Dialog):
    """
    SFTP file browser dialog with inline progress bar for long operations
    and an Alt+Shift+P hotkey to speak the current progress/status.
    """

    def __init__(self, parent, sftp_client, edit_callback, initial_path=None):
        super(FileBrowserDialog, self).__init__(
            parent, title="Teaview", size=(640, 540)
        )

        self.sftp = sftp_client
        self.edit_callback = edit_callback
        self.current_path = initial_path or "/"

        self.cancel_flag = threading.Event()
        self.copy_temp_dir = None
        self.worker_thread = None

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.path_text = wx.StaticText(panel, label=f"Path: {self.current_path}")
        vbox.Add(self.path_text, 0, wx.ALL | wx.EXPAND, 5)

        self.file_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.file_list.InsertColumn(0, "Name", width=260)
        self.file_list.InsertColumn(1, "Size", width=120)
        self.file_list.InsertColumn(2, "Type", width=120)
        vbox.Add(self.file_list, 1, wx.ALL | wx.EXPAND, 5)

        # Buttons row
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_button = wx.Button(panel, label="&Upload")
        self.new_button = wx.Button(panel, label="&New...")
        self.download_button = wx.Button(panel, label="Down&load")
        self.copy_button = wx.Button(panel, label="C&opy")
        self.edit_button = wx.Button(panel, label="&Edit")
        self.delete_button = wx.Button(panel, label="&Delete")
        close_button = wx.Button(panel, id=wx.ID_CANCEL, label="&Close")

        for btn in (
            self.upload_button,
            self.new_button,
            self.download_button,
            self.copy_button,
            self.edit_button,
            self.delete_button,
        ):
            hbox_buttons.Add(btn, 0, wx.RIGHT, 5)
        hbox_buttons.AddStretchSpacer()
        hbox_buttons.Add(close_button, 0)
        vbox.Add(hbox_buttons, 0, wx.ALL | wx.EXPAND, 5)

        # Status and progress area
        self.status_text = wx.StaticText(panel, label=" ")
        vbox.Add(self.status_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        self.progress_panel = wx.Panel(panel)
        progress_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_label = wx.StaticText(self.progress_panel, label="")
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100)
        self.progress_cancel_btn = wx.Button(self.progress_panel, label="&Cancel")
        self.progress_cancel_btn.Enable(False)
        progress_sizer.Add(
            self.progress_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )
        progress_sizer.Add(
            self.progress_gauge, 2, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )
        progress_sizer.Add(self.progress_cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        self.progress_panel.SetSizer(progress_sizer)
        vbox.Add(self.progress_panel, 0, wx.ALL | wx.EXPAND, 5)
        self.progress_panel.Hide()

        panel.SetSizer(vbox)

        # Bind events
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # Global-ish key handler inside this dialog
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)

        self.file_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)
        self.file_list.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        self.upload_button.Bind(wx.EVT_BUTTON, self.on_upload)
        self.new_button.Bind(wx.EVT_BUTTON, self.on_new)
        self.download_button.Bind(wx.EVT_BUTTON, self.on_download)
        self.copy_button.Bind(wx.EVT_BUTTON, self.on_copy)
        self.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_button)
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete)
        self.progress_cancel_btn.Bind(wx.EVT_BUTTON, self.on_progress_cancel)

        theme.apply_dark_theme(self)
        self.populate_files()

    # ------------- progress helpers -------------

    def _begin_progress(self, total: int, message: str):
        if total <= 0:
            total = 1
        self.progress_gauge.SetRange(total)
        self.progress_gauge.SetValue(0)
        self.progress_label.SetLabel(message)
        self.progress_cancel_btn.Enable(True)
        self.progress_panel.Show()
        self.Layout()
        self.cancel_flag.clear()
        self.status_text.SetLabel(message)

    def _update_progress(self, done: int, message: str):
        if not self.progress_panel.IsShown():
            return
        total = self.progress_gauge.GetRange()
        if total <= 0:
            total = 1
        done = max(0, min(done, total))
        self.progress_gauge.SetValue(done)
        self.progress_label.SetLabel(message)
        self.status_text.SetLabel(message)

    def _end_progress(self, refresh: bool = False, final_message=None):
        self.progress_panel.Hide()
        self.progress_gauge.SetValue(0)
        self.progress_label.SetLabel("")
        self.progress_cancel_btn.Enable(False)
        self.Layout()
        if refresh:
            self.populate_files()
        if final_message:
            self.status_text.SetLabel(final_message)

    def on_progress_cancel(self, event):
        if not self.cancel_flag.is_set():
            self.cancel_flag.set()
            self.status_text.SetLabel("Cancelling operation...")
            speech.speak("Cancelling operation", interrupt=True)

    def _run_worker(self, target, *args):
        self.cancel_flag.clear()
        t = threading.Thread(target=target, args=args)
        t.daemon = True
        self.worker_thread = t
        t.start()

    # ------------- accessibility / hotkey -------------

    def announce_progress(self):
        """Speak the current progress or status (Alt+Shift+P)."""
        if self.progress_panel.IsShown():
            msg = self.progress_label.GetLabel()
            if not msg:
                msg = "Transfer in progress."
        else:
            msg = self.status_text.GetLabel() or "No transfer in progress."
        speech.speak(msg, interrupt=True)

    def on_char_hook(self, event: wx.KeyEvent):
        keycode = event.GetKeyCode()
        if event.AltDown() and event.ShiftDown() and keycode in (ord("P"), ord("p")):
            self.announce_progress()
        else:
            event.Skip()

    # ------------- UI helpers -------------

    def get_current_path(self) -> str:
        return self.current_path

    def on_activate(self, event):
        if event.GetActive():
            self.populate_files()
        event.Skip()

    def populate_files(self):
        self.path_text.SetLabel(f"Path: {self.current_path}")
        self.file_list.DeleteAllItems()

        if self.current_path != "/":
            idx = self.file_list.InsertItem(self.file_list.GetItemCount(), "..")
            self.file_list.SetItem(idx, 2, "Parent Directory")

        try:
            for attr in self.sftp.listdir_attr(self.current_path):
                idx = self.file_list.InsertItem(
                    self.file_list.GetItemCount(), attr.filename
                )
                self.file_list.SetItem(idx, 1, human_readable_size(attr.st_size))
                mode = attr.st_mode
                if stat.S_ISDIR(mode):
                    self.file_list.SetItem(idx, 2, "Directory")
                else:
                    self.file_list.SetItem(idx, 2, "File")
        except Exception as e:
            wx.MessageBox(
                f"Could not list directory: {e}", "SFTP Error", wx.ICON_ERROR
            )
            self.current_path = "/"

        self.on_selection_changed(None)

    def on_close(self, event):
        if self.worker_thread and self.worker_thread.is_alive():
            self.cancel_flag.set()
        if self.copy_temp_dir and os.path.exists(self.copy_temp_dir):
            try:
                shutil.rmtree(self.copy_temp_dir)
            except Exception:
                pass
        self.Destroy()

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_BACK:
            self.go_to_parent_directory()
        elif keycode == wx.WXK_DELETE:
            wx.CallAfter(self.on_delete, None)
        elif event.ControlDown() and keycode == ord("V"):
            wx.CallAfter(self.on_paste_upload)
        elif event.ControlDown() and keycode == ord("C"):
            wx.CallAfter(self.on_copy, None)
        else:
            event.Skip()

    def on_selection_changed(self, event):
        count = self.file_list.GetSelectedItemCount()
        self.download_button.Enable(count > 0)
        self.copy_button.Enable(count > 0)
        self.delete_button.Enable(count > 0)

        if count == 1:
            idx = self.file_list.GetFirstSelected()
            item_type = self.file_list.GetItemText(idx, 2)
            self.edit_button.Enable(item_type == "File")
        else:
            self.edit_button.Enable(False)

        if event:
            event.Skip()

    def go_to_parent_directory(self):
        if self.current_path != "/":
            parts = self.current_path.rstrip("/").split("/")
            self.current_path = "/".join(parts[:-1]) or "/"
            self.populate_files()

    def get_selected_remote_paths(self):
        paths = []
        idx = -1
        while True:
            idx = self.file_list.GetNextItem(
                idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED
            )
            if idx == -1:
                break
            name = self.file_list.GetItemText(idx)
            if name == "..":
                continue
            if self.current_path == "/":
                paths.append(f"/{name}")
            else:
                paths.append(f"{self.current_path}/{name}")
        return paths

    def on_item_activated(self, event):
        idx = event.GetIndex()
        name = self.file_list.GetItemText(idx)
        item_type = self.file_list.GetItemText(idx, 2)
        if name == ".." or item_type == "Parent Directory":
            self.go_to_parent_directory()
        elif item_type == "Directory":
            if self.current_path == "/":
                self.current_path = f"/{name}"
            else:
                self.current_path = f"{self.current_path}/{name}"
            self.populate_files()
        elif item_type == "File":
            self.on_edit_button(None)

    def on_edit_button(self, event):
        paths = self.get_selected_remote_paths()
        if paths:
            self.edit_callback(paths[0])

    # -------------- Clipboard copy / paste --------------

    def _put_paths_on_clipboard(self, local_paths):
        data = wx.FileDataObject()
        for p in local_paths:
            data.AddFile(p)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            msg = f"Copied {len(local_paths)} item(s) to clipboard."
            self.status_text.SetLabel(msg)
            speech.speak(msg, interrupt=False)
        else:
            self.status_text.SetLabel("Error: could not open clipboard.")
            speech.speak("Error: could not open clipboard.", interrupt=True)

    def on_paste_upload(self):
        data = wx.FileDataObject()
        if wx.TheClipboard.Open():
            ok = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        else:
            ok = False
        if not ok:
            return
        local_paths = data.GetFilenames()
        if not local_paths:
            return
        self.status_text.SetLabel("Preparing to upload clipboard files...")
        self._run_worker(self._upload_worker, local_paths)

    # -------------- Copy from remote to clipboard (download to temp) --------------

    def on_copy(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths:
            return
        self.status_text.SetLabel("Preparing to copy files...")
        self._run_worker(self._copy_worker, remote_paths)

    def _copy_worker(self, remote_paths):
        try:
            if self.copy_temp_dir and os.path.exists(self.copy_temp_dir):
                shutil.rmtree(self.copy_temp_dir, ignore_errors=True)
            self.copy_temp_dir = tempfile.mkdtemp(prefix="teatype_copy_")

            total = 0
            for p in remote_paths:
                total += count_remote_items(self.sftp, p, self.cancel_flag)
            wx.CallAfter(self._begin_progress, total, "Starting copy...")
            done = [0]

            def file_cb(path):
                done[0] += 1
                wx.CallAfter(
                    self._update_progress,
                    done[0],
                    f"Copying: {os.path.basename(path)}",
                )

            local_paths = []
            for remote_path in remote_paths:
                if self.cancel_flag.is_set():
                    raise TransferCancelledError("Copy cancelled")
                name = os.path.basename(remote_path)
                local_path = os.path.join(self.copy_temp_dir, name)
                local_paths.append(local_path)
                download_item(
                    self.sftp,
                    remote_path,
                    local_path,
                    file_cb,
                    self.cancel_flag,
                )

            if not self.cancel_flag.is_set():
                wx.CallAfter(self._put_paths_on_clipboard, local_paths)
                wx.CallAfter(self._end_progress, False, "Copy complete.")
            else:
                wx.CallAfter(self._end_progress, False, "Copy cancelled.")
        except TransferCancelledError:
            wx.CallAfter(self._end_progress, False, "Copy cancelled.")
        except Exception as e:
            wx.CallAfter(
                wx.MessageBox, f"Copy failed: {e}", "Error", wx.ICON_ERROR
            )
            wx.CallAfter(self._end_progress, False, "Copy failed.")

    # -------------- Upload --------------

    def on_upload(self, event):
        with wx.FileDialog(
            self,
            "Choose files to upload",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            local_paths = dlg.GetPaths()
        self.status_text.SetLabel("Preparing to upload...")
        self._run_worker(self._upload_worker, local_paths)

    def _upload_worker(self, local_paths):
        try:
            total = 0
            for p in local_paths:
                total += count_local_items(p, self.cancel_flag)
            wx.CallAfter(self._begin_progress, total, "Starting upload...")
            done = [0]

            def file_cb(path):
                done[0] += 1
                wx.CallAfter(
                    self._update_progress,
                    done[0],
                    f"Uploading: {os.path.basename(path)}",
                )

            for local_path in local_paths:
                if self.cancel_flag.is_set():
                    raise TransferCancelledError("Upload cancelled")
                name = os.path.basename(local_path)
                if self.current_path == "/":
                    remote_path = f"/{name}"
                else:
                    remote_path = f"{self.current_path}/{name}"
                upload_item(
                    self.sftp,
                    local_path,
                    remote_path,
                    file_cb,
                    self.cancel_flag,
                )

            if not self.cancel_flag.is_set():
                wx.CallAfter(self._end_progress, True, "Upload complete.")
            else:
                wx.CallAfter(self._end_progress, False, "Upload cancelled.")
        except TransferCancelledError:
            wx.CallAfter(self._end_progress, False, "Upload cancelled.")
        except Exception as e:
            wx.CallAfter(
                wx.MessageBox, f"Upload failed: {e}", "Error", wx.ICON_ERROR
            )
            wx.CallAfter(self._end_progress, False, "Upload failed.")

    # -------------- Download --------------

    def on_download(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths:
            return
        with wx.DirDialog(self, "Choose download destination") as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            dest = dlg.GetPath()
        self.status_text.SetLabel("Preparing to download...")
        self._run_worker(self._download_worker, remote_paths, dest)

    def _download_worker(self, remote_paths, dest):
        try:
            total = 0
            for p in remote_paths:
                total += count_remote_items(self.sftp, p, self.cancel_flag)
            wx.CallAfter(self._begin_progress, total, "Starting download...")
            done = [0]

            def file_cb(path):
                done[0] += 1
                wx.CallAfter(
                    self._update_progress,
                    done[0],
                    f"Downloading: {os.path.basename(path)}",
                )

            for remote_path in remote_paths:
                if self.cancel_flag.is_set():
                    raise TransferCancelledError("Download cancelled")
                name = os.path.basename(remote_path)
                local_path = os.path.join(dest, name)
                download_item(
                    self.sftp,
                    remote_path,
                    local_path,
                    file_cb,
                    self.cancel_flag,
                )

            if not self.cancel_flag.is_set():
                wx.CallAfter(self._end_progress, False, "Download complete.")
            else:
                wx.CallAfter(self._end_progress, False, "Download cancelled.")
        except TransferCancelledError:
            wx.CallAfter(self._end_progress, False, "Download cancelled.")
        except Exception as e:
            wx.CallAfter(
                wx.MessageBox, f"Download failed: {e}", "Error", wx.ICON_ERROR
            )
            wx.CallAfter(self._end_progress, False, "Download failed.")

    # -------------- Delete --------------

    def on_delete(self, event):
        remote_paths = self.get_selected_remote_paths()
        if not remote_paths:
            return
        count = len(remote_paths)
        if count == 1:
            msg = (
                "Are you sure you want to permanently delete "
                f"'{os.path.basename(remote_paths[0])}'?"
            )
        else:
            msg = (
                f"Are you sure you want to permanently delete {count} item(s)?"
            )
        res = wx.MessageBox(msg, "Confirm Deletion", wx.YES_NO | wx.ICON_WARNING)
        if res != wx.YES:
            return
        self.status_text.SetLabel("Deleting selected items...")
        self._run_worker(self._delete_worker, remote_paths)

    def _delete_worker(self, remote_paths):
        try:
            total = len(remote_paths)
            wx.CallAfter(self._begin_progress, total, "Starting deletion...")
            for i, remote_path in enumerate(remote_paths):
                if self.cancel_flag.is_set():
                    raise TransferCancelledError("Delete cancelled")
                name = os.path.basename(remote_path)
                wx.CallAfter(
                    self._update_progress,
                    i + 1,
                    f"Deleting: {name}",
                )
                delete_item(self.sftp, remote_path)
            if not self.cancel_flag.is_set():
                wx.CallAfter(self._end_progress, True, "Delete complete.")
            else:
                wx.CallAfter(self._end_progress, True, "Delete cancelled.")
        except TransferCancelledError:
            wx.CallAfter(self._end_progress, True, "Delete cancelled.")
        except Exception as e:
            wx.CallAfter(
                wx.MessageBox, f"Deletion failed: {e}", "Error", wx.ICON_ERROR
            )
            wx.CallAfter(self._end_progress, True, "Deletion failed.")

    # -------------- New file / directory --------------

    def on_new(self, event):
        menu = wx.Menu()
        dir_item = menu.Append(wx.ID_ANY, "&Directory")
        file_item = menu.Append(wx.ID_ANY, "&File")
        self.Bind(wx.EVT_MENU, self.on_new_directory, dir_item)
        self.Bind(wx.EVT_MENU, self.on_new_file, file_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_new_directory(self, event):
        with wx.TextEntryDialog(
            self, "Enter name for the new directory:", "Create Directory"
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            name = dlg.GetValue().strip()
        if not name:
            return
        if self.current_path == "/":
            remote_path = f"/{name}"
        else:
            remote_path = f"{self.current_path}/{name}"
        try:
            self.sftp.mkdir(remote_path)
            self.populate_files()
        except Exception as e:
            wx.MessageBox(
                f"Failed to create directory: {e}", "Error", wx.ICON_ERROR
            )

    def on_new_file(self, event):
        with wx.TextEntryDialog(
            self, "Enter name for the new file:", "Create File"
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            name = dlg.GetValue().strip()
        if not name:
            return
        if self.current_path == "/":
            remote_path = f"/{name}"
        else:
            remote_path = f"{self.current_path}/{name}"
        try:
            with self.sftp.open(remote_path, "w"):
                pass
            self.populate_files()
        except Exception as e:
            wx.MessageBox(f"Failed to create file: {e}", "Error", wx.ICON_ERROR)
