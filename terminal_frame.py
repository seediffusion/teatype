# --- START OF FILE terminal_frame.py ---

import wx
import paramiko
import threading
import queue
import time
import re
import os
import tempfile
import shutil
from speech import speak
import theme
from dialogs import FileBrowserDialog
from editor_frame import EditorFrame
from menu_mixin import SettingsMenuMixin

ANSI_ESCAPE_RE = re.compile(r'(\x1B\[[0-?]*[ -/]*[@-~]|\x1B\].*?(\x07|\x1B\\))')

class TerminalFrame(wx.Frame, SettingsMenuMixin):
    def __init__(self, parent, server_info, connect_kwargs):
        self.server_info = server_info
        self.connect_kwargs = connect_kwargs
        title = f"Teatype - {server_info['name']} ({server_info['user']}@{server_info['host']})"
        super(TerminalFrame, self).__init__(parent, title=title, size=(800, 600))
        SettingsMenuMixin.__init__(self)
        self.sftp_client = None
        self.temp_dir = tempfile.mkdtemp(prefix="teatype_")
        self.open_files = set()
        self.sftp_last_path = self.server_info.get("last_path")
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        output_label = wx.StaticText(panel, label="&Server Output:")
        sizer.Add(output_label, 0, wx.LEFT | wx.TOP, 5)
        self.output_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.output_ctrl.SetFont(font)
        sizer.Add(self.output_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_files_btn = wx.Button(panel, label="&Browse Files (SFTP)")
        self.browse_files_btn.Disable()
        hbox.Add(self.browse_files_btn)
        sizer.Add(hbox, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        input_label = wx.StaticText(panel, label="&Command Input:")
        sizer.Add(input_label, 0, wx.LEFT, 5)
        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.input_ctrl.SetFont(font)
        sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel.SetSizer(sizer)
        theme.apply_dark_theme(self)
        self.output_ctrl.SetBackgroundColour(wx.BLACK)
        self.output_ctrl.SetForegroundColour(wx.WHITE)
        self.input_ctrl.SetBackgroundColour(wx.BLACK)
        self.input_ctrl.SetForegroundColour(wx.WHITE)
        self.ssh_client = None
        self.ssh_channel = None
        self.command_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.Bind(wx.EVT_TEXT_ENTER, self.on_command_enter, self.input_ctrl)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.input_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.browse_files_btn.Bind(wx.EVT_BUTTON, self.on_browse_files)
        self.input_ctrl.SetFocus()
        self.start_ssh_thread()
        self.Show()

    def on_browse_files(self, event):
        if self.sftp_client:
            with FileBrowserDialog(self, self.sftp_client, self.open_file_for_edit, initial_path=self.sftp_last_path) as dlg:
                dlg.ShowModal()
                self.sftp_last_path = dlg.get_current_path()
    
    def open_file_for_edit(self, remote_path):
        if remote_path in self.open_files:
            wx.MessageBox(f"This file is already open for editing.", "Already Open", wx.ICON_INFORMATION)
            return
        try:
            local_filename = remote_path.replace('/', '_')
            local_path = os.path.join(self.temp_dir, local_filename)
            self.sftp_client.get(remote_path, local_path)
            self.open_files.add(remote_path)
            title = f"Editing {os.path.basename(remote_path)} from {self.server_info['name']}"
            EditorFrame(self, title, local_path, remote_path, self.sftp_client)
        except Exception as e:
            wx.MessageBox(f"Failed to open file for editing: {e}", "SFTP Error", wx.ICON_ERROR)
    
    def notify_editor_closed(self, remote_path):
        if remote_path in self.open_files:
            self.open_files.remove(remote_path)

    def on_close(self, event):
        try:
            if os.path.exists(self.temp_dir): shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Warning: Could not remove temp directory {self.temp_dir}: {e}")
        
        if self.Parent and self.sftp_last_path:
            self.Parent.update_server_last_path(self.server_info['name'], self.sftp_last_path)

        self.stop_event.set()
        if self.ssh_thread and self.ssh_thread.is_alive():
            self.ssh_thread.join(timeout=2)
        if self.sftp_client: self.sftp_client.close()
        if self.ssh_client: self.ssh_client.close()
        self.Destroy()
        
    def on_key_down(self, event):
        key_code = event.GetKeyCode()
        is_ctrl_down = event.ControlDown()
        if is_ctrl_down and key_code == ord('D'):
            if self.ssh_channel: self.command_queue.put('\x04')
            return
        elif is_ctrl_down and key_code == ord('C'):
            if self.ssh_channel: self.command_queue.put('\x03')
            return
        event.Skip()
        
    def start_ssh_thread(self):
        self.ssh_thread = threading.Thread(target=self.ssh_worker)
        self.ssh_thread.daemon = True
        self.ssh_thread.start()
        
    def on_command_enter(self, event):
        if not wx.GetKeyState(wx.WXK_SHIFT):
            if self.ssh_channel:
                command = self.input_ctrl.GetValue()
                self.command_queue.put(command + '\n')
            self.input_ctrl.Clear()
        else:
            current_pos = self.input_ctrl.GetInsertionPoint()
            self.input_ctrl.WriteText('\n')
            self.input_ctrl.SetInsertionPoint(current_pos + 1)
            
    def append_output(self, text):
        self.output_ctrl.AppendText(text)
        clean_text_for_speech = text.strip()
        if clean_text_for_speech:
            speak(clean_text_for_speech, interrupt=False)
            
    def filter_control_characters(self, text: str) -> str:
        return "".join(c for c in text if c.isprintable() or c in ('\n', '\t'))
        
    def ssh_worker(self):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            wx.CallAfter(self.append_output, f"Connecting to {self.connect_kwargs['hostname']}...\n")
            self.ssh_client.connect(**self.connect_kwargs, timeout=10)
            
            # --- FIX: Get the home directory reliably ---
            # Use exec_command for a single, non-interactive command
            stdin, stdout, stderr = self.ssh_client.exec_command('pwd')
            home_dir = stdout.read().decode('utf-8').strip()
            if home_dir and not self.sftp_last_path:
                self.sftp_last_path = home_dir

            self.ssh_channel = self.ssh_client.invoke_shell(term='xterm')
            self.sftp_client = self.ssh_client.open_sftp()

            wx.CallAfter(self.append_output, "Connection established.\n")
            wx.CallAfter(self.browse_files_btn.Enable)
            
            while not self.stop_event.is_set():
                if self.ssh_channel.exit_status_ready(): break 
                if self.ssh_channel.recv_ready():
                    data = self.ssh_channel.recv(4096).decode('utf-8', 'ignore')
                    data_no_ansi = ANSI_ESCAPE_RE.sub('', data)
                    fully_clean_data = self.filter_control_characters(data_no_ansi)
                    if fully_clean_data:
                        wx.CallAfter(self.append_output, fully_clean_data)
                try:
                    command = self.command_queue.get_nowait()
                    self.ssh_channel.sendall(command)
                except queue.Empty: pass
                time.sleep(0.05)
        except Exception as e:
            wx.CallAfter(self.append_output, f"\n--- ERROR ---\n{str(e)}\n")
            wx.CallAfter(wx.MessageBox, f"SSH Connection Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
        finally:
            if self.sftp_client: self.sftp_client.close()
            if self.ssh_client: self.ssh_client.close()
            if not self.IsBeingDeleted():
                wx.CallAfter(self.Close)