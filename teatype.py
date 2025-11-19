import wx
import json
import os
import paramiko
import threading
import queue
import time
import re
import shutil
import tempfile
from dialogs import AddServerDialog, FileBrowserDialog
from editor_frame import EditorFrame
from security import (
    store_password, get_password, delete_password,
    store_passphrase, get_passphrase, delete_passphrase
)
import theme
from menu_mixin import SettingsMenuMixin
from server_panel import ServerPanel
from terminal_panel import TerminalPanel

SERVERS_FILE = "servers.json"
ANSI_ESCAPE_RE = re.compile(r'(\x1B\[[0-?]*[ -/]*[@-~]|\x1B\].*?(\x07|\x1B\\))')

class MainFrame(wx.Frame, SettingsMenuMixin):
    def __init__(self):
        super().__init__(None, title="Teatype", size=(800, 600))
        SettingsMenuMixin.__init__(self)
        
        self.servers = []
        self.load_servers()
        
        # --- FIX: Create a sizer for the frame and add the Simplebook to it ---
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.book = wx.Simplebook(self)
        sizer.Add(self.book, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.server_panel = ServerPanel(self.book)
        self.terminal_panel = TerminalPanel(self.book)
        self.book.AddPage(self.server_panel, "Servers")
        self.book.AddPage(self.terminal_panel, "Terminal")
        
        self.ssh_client = None
        self.ssh_channel = None
        self.sftp_client = None
        self.command_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.ssh_thread = None
        self.temp_dir = None
        self.open_files = set()
        self.sftp_last_path = None
        self.current_server_info = None

        self.Bind(wx.EVT_CLOSE, self.on_close_app)
        
        theme.apply_dark_theme(self)
        self.Centre()
        self.Show()

    def on_close_app(self, event):
        self.disconnect(app_closing=True)
        self.Destroy()

    def get_servers(self):
        return self.servers

    def add_server(self, data):
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
        self.server_panel.populate_list()

    def edit_server(self, index):
        original_server = self.servers[index]
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
                        updated_server["has_passphrase"] = False
                
                self.servers[index] = updated_server
                self.save_servers()
                self.server_panel.populate_list()

    def remove_server(self, index):
        server_to_remove = self.servers[index]
        if server_to_remove.get("password_stored", False):
            auth_method = server_to_remove.get("auth_method", "password")
            if auth_method == "password":
                delete_password(server_name=server_to_remove["name"], host=server_to_remove["host"], user=server_to_remove["user"])
            else:
                delete_passphrase(server_name=server_to_remove["name"], host=server_to_remove["host"], user=server_to_remove["user"])
        self.servers.pop(index)
        self.save_servers()
        self.server_panel.populate_list()
                
    def connect_to_server(self, index):
        server_info = self.servers[index].copy()
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
        
        self.current_server_info = server_info
        self.sftp_last_path = self.current_server_info.get("last_path")
        
        self.SetTitle(f"Teatype - {server_info['name']}")
        self.terminal_panel.clear_output()
        self.book.SetSelection(1)
        
        self.ssh_thread = threading.Thread(target=self.ssh_worker, args=(connect_kwargs,))
        self.ssh_thread.daemon = True
        self.ssh_thread.start()

    def disconnect(self, app_closing=False):
        if self.ssh_thread and self.ssh_thread.is_alive():
            self.stop_event.set()
            if not app_closing:
                self.ssh_thread.join(timeout=2)
        
        if self.current_server_info and self.sftp_last_path:
            self.update_server_last_path(self.current_server_info['name'], self.sftp_last_path)

        self.cleanup_session()
        self.book.SetSelection(0)
        self.SetTitle("Teatype")
        self.server_panel.populate_list()

    def cleanup_session(self):
        if self.sftp_client: self.sftp_client.close()
        if self.ssh_client: self.ssh_client.close()
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Warning: Could not remove temp directory {self.temp_dir}: {e}")
        self.ssh_client, self.ssh_channel, self.sftp_client = None, None, None
        self.stop_event.clear()
        self.temp_dir = None
        self.open_files.clear()
        self.current_server_info = None

    def send_command(self, command):
        if self.ssh_channel:
            self.command_queue.put(command)
    
    def on_browse_files(self, event):
        if self.sftp_client:
            with FileBrowserDialog(self, self.sftp_client, self.open_file_for_edit, initial_path=self.sftp_last_path) as dlg:
                dlg.ShowModal()
                self.sftp_last_path = dlg.get_current_path()
    
    def open_file_for_edit(self, remote_path):
        if remote_path in self.open_files:
            wx.MessageBox(f"This file is already open for editing.", "Already Open", wx.ICON_INFORMATION)
            return
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="teatype_")
        try:
            local_filename = remote_path.replace('/', '_')
            local_path = os.path.join(self.temp_dir, local_filename)
            self.sftp_client.get(remote_path, local_path)
            self.open_files.add(remote_path)
            title = f"Editing {os.path.basename(remote_path)} from {self.current_server_info['name']}"
            EditorFrame(self, title, local_path, remote_path, self.sftp_client)
        except Exception as e:
            wx.MessageBox(f"Failed to open file for editing: {e}", "SFTP Error", wx.ICON_ERROR)
    
    def notify_editor_closed(self, remote_path):
        if remote_path in self.open_files:
            self.open_files.remove(remote_path)

    def ssh_worker(self, connect_kwargs):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            wx.CallAfter(self.terminal_panel.append_output, f"Connecting to {connect_kwargs['hostname']}...\n")
            self.ssh_client.connect(**connect_kwargs, timeout=10)
            
            stdin, stdout, stderr = self.ssh_client.exec_command('pwd')
            home_dir = stdout.read().decode('utf-8').strip()
            if home_dir and not self.sftp_last_path:
                self.sftp_last_path = home_dir

            self.ssh_channel = self.ssh_client.invoke_shell(term='xterm')
            self.sftp_client = self.ssh_client.open_sftp()
            wx.CallAfter(self.terminal_panel.append_output, "Connection established.\n")
            wx.CallAfter(self.terminal_panel.set_focus_on_input)

            while not self.stop_event.is_set():
                if not self.ssh_channel:
                    break
                
                if self.ssh_channel.exit_status_ready(): break 
                if self.ssh_channel.recv_ready():
                    data = self.ssh_channel.recv(4096).decode('utf-8', 'ignore')
                    data_no_ansi = ANSI_ESCAPE_RE.sub('', data)
                    fully_clean_data = "".join(c for c in data_no_ansi if c.isprintable() or c in ('\n', '\t'))
                    if fully_clean_data:
                        wx.CallAfter(self.terminal_panel.append_output, fully_clean_data)
                try:
                    command = self.command_queue.get_nowait()
                    self.ssh_channel.sendall(command)
                except queue.Empty: pass
                time.sleep(0.05)
        except Exception as e:
            wx.CallAfter(self.terminal_panel.append_output, f"\n--- ERROR ---\n{str(e)}\n")
            wx.CallAfter(wx.MessageBox, f"SSH Connection Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
        finally:
            wx.CallAfter(self.disconnect)

    def update_server_last_path(self, server_name, last_path):
        for server in self.servers:
            if server.get("name") == server_name:
                server["last_path"] = last_path
                self.save_servers()
                break

    def load_servers(self):
        if os.path.exists(SERVERS_FILE):
            try:
                with open(SERVERS_FILE, "r") as f: self.servers = json.load(f)
            except json.JSONDecodeError: self.servers = []
        else: self.servers = []
        
    def save_servers(self):
        with open(SERVERS_FILE, "w") as f: json.dump(self.servers, f, indent=4)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()