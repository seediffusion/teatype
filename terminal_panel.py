import wx
import os
from collections import deque
from speech import speak

class TerminalPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_book = parent
        
        # --- FIX: Get a reference to the main application frame ---
        self.main_frame = self.GetTopLevelParent()
        
        self.command_history = deque(maxlen=25)
        self.history_index = -1
        self.current_command = ""

        sizer = wx.BoxSizer(wx.VERTICAL)

        output_label = wx.StaticText(self, label="&Server Output:")
        sizer.Add(output_label, 0, wx.LEFT | wx.TOP, 5)
        self.output_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.output_ctrl.SetFont(font)
        sizer.Add(self.output_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_files_btn = wx.Button(self, label="&Browse Files (SFTP)")
        self.disconnect_btn = wx.Button(self, label="&Disconnect")
        hbox.Add(self.browse_files_btn)
        hbox.Add(self.disconnect_btn, 0, wx.LEFT, 5)
        sizer.Add(hbox, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
        
        input_label = wx.StaticText(self, label="&Command Input:")
        sizer.Add(input_label, 0, wx.LEFT, 5)
        self.input_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.input_ctrl.SetFont(font)
        sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.SetSizer(sizer)
        
        self.output_ctrl.SetBackgroundColour(wx.BLACK)
        self.output_ctrl.SetForegroundColour(wx.WHITE)
        self.input_ctrl.SetBackgroundColour(wx.BLACK)
        self.input_ctrl.SetForegroundColour(wx.WHITE)
        
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_command_enter)
        self.input_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.browse_files_btn.Bind(wx.EVT_BUTTON, self.on_browse_files)
        self.disconnect_btn.Bind(wx.EVT_BUTTON, lambda e: self.main_frame.disconnect())

    def on_browse_files(self, event):
        # --- FIX: Call on_browse_files on the correct object ---
        self.main_frame.on_browse_files(event)

    def on_command_enter(self, event):
        if not wx.GetKeyState(wx.WXK_SHIFT):
            command = self.input_ctrl.GetValue()
            if command:
                self.command_history.append(command)
            self.history_index = -1
            self.current_command = ""
            # --- FIX: Call send_command on the correct object ---
            self.main_frame.send_command(command + '\n')
            self.input_ctrl.Clear()
        else:
            current_pos = self.input_ctrl.GetInsertionPoint()
            self.input_ctrl.WriteText('\n')
            self.input_ctrl.SetInsertionPoint(current_pos + 1)
            
    def on_key_down(self, event):
        key_code = event.GetKeyCode()
        is_ctrl_down = event.ControlDown()
        
        if key_code == wx.WXK_UP:
            if self.history_index == -1:
                self.current_command = self.input_ctrl.GetValue()
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                idx = -1 - self.history_index
                self.input_ctrl.SetValue(self.command_history[idx])
                self.input_ctrl.SetInsertionPointEnd()
        elif key_code == wx.WXK_DOWN:
            if self.history_index > 0:
                self.history_index -= 1
                idx = -1 - self.history_index
                self.input_ctrl.SetValue(self.command_history[idx])
                self.input_ctrl.SetInsertionPointEnd()
            elif self.history_index == 0:
                self.history_index = -1
                self.input_ctrl.SetValue(self.current_command)
                self.input_ctrl.SetInsertionPointEnd()
        elif is_ctrl_down and key_code == ord('D'):
            self.main_frame.send_command('\x04')
        elif is_ctrl_down and key_code == ord('C'):
            self.main_frame.send_command('\x03')
        else:
            event.Skip()

    def append_output(self, text):
        self.output_ctrl.AppendText(text)
        clean_text = text.strip()
        if clean_text:
            speak(clean_text, interrupt=False)

    def clear_output(self):
        self.output_ctrl.Clear()
        
    def set_focus_on_input(self):
        self.input_ctrl.SetFocus()