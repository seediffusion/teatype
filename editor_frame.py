import wx
import os
import theme
from menu_mixin import SettingsMenuMixin

# --- NEW: Dialogs for Find and Replace functionality ---
class FindDialog(wx.Dialog):
    def __init__(self, parent, title):
        super(FindDialog, self).__init__(parent, title=title)
        self.parent = parent
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.find_text = wx.TextCtrl(panel)
        vbox.Add(wx.StaticText(panel, label="Find what:"), 0, wx.ALL, 5)
        vbox.Add(self.find_text, 0, wx.EXPAND|wx.ALL, 5)
        
        self.case_checkbox = wx.CheckBox(panel, label="Match case")
        vbox.Add(self.case_checkbox, 0, wx.ALL, 5)
        
        # --- FIX: Add a horizontal sizer for buttons ---
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        find_next_btn = wx.Button(panel, label="Find Next")
        close_btn = wx.Button(panel, label="Close", id=wx.ID_CANCEL) # Use standard Cancel ID
        hbox.Add(find_next_btn)
        hbox.Add(close_btn, 0, wx.LEFT, 5)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        panel.SetSizer(vbox)
        find_next_btn.Bind(wx.EVT_BUTTON, self.on_find_next)
        self.find_text.SetFocus()

    def on_find_next(self, event):
        self.parent.do_find(self.find_text.GetValue(), self.case_checkbox.IsChecked())

class ReplaceDialog(wx.Dialog):
    def __init__(self, parent, title):
        super(ReplaceDialog, self).__init__(parent, title=title)
        self.parent = parent
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(panel, label="Find what:"), 0, wx.ALL, 5)
        self.find_text = wx.TextCtrl(panel)
        vbox.Add(self.find_text, 0, wx.EXPAND|wx.ALL, 5)
        
        vbox.Add(wx.StaticText(panel, label="Replace with:"), 0, wx.ALL, 5)
        self.replace_text = wx.TextCtrl(panel)
        vbox.Add(self.replace_text, 0, wx.EXPAND|wx.ALL, 5)
        
        self.case_checkbox = wx.CheckBox(panel, label="Match case")
        vbox.Add(self.case_checkbox, 0, wx.ALL, 5)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        find_next_btn = wx.Button(panel, label="Find Next")
        replace_btn = wx.Button(panel, label="Replace")
        replace_all_btn = wx.Button(panel, label="Replace All")
        close_btn = wx.Button(panel, label="Close", id=wx.ID_CANCEL) # Use standard Cancel ID
        hbox.Add(find_next_btn)
        hbox.Add(replace_btn, 0, wx.LEFT, 5)
        hbox.Add(replace_all_btn, 0, wx.LEFT, 5)
        hbox.Add(close_btn, 0, wx.LEFT, 15) # Add extra space
        vbox.Add(hbox, 0, wx.EXPAND|wx.ALL, 5)

        panel.SetSizer(vbox)
        find_next_btn.Bind(wx.EVT_BUTTON, self.on_find_next)
        replace_btn.Bind(wx.EVT_BUTTON, self.on_replace)
        replace_all_btn.Bind(wx.EVT_BUTTON, self.on_replace_all)
        self.find_text.SetFocus()
        
    def on_find_next(self, event):
        self.parent.do_find(self.find_text.GetValue(), self.case_checkbox.IsChecked())
        
    def on_replace(self, event):
        self.parent.do_replace(self.find_text.GetValue(), self.replace_text.GetValue(), self.case_checkbox.IsChecked())
        
    def on_replace_all(self, event):
        self.parent.do_replace_all(self.find_text.GetValue(), self.replace_text.GetValue(), self.case_checkbox.IsChecked())


class EditorFrame(wx.Frame, SettingsMenuMixin):
    def __init__(self, parent, title, local_path, remote_path, sftp_client):
        super(EditorFrame, self).__init__(parent, title=title, size=(800, 600))
        self.local_path, self.remote_path, self.sftp = local_path, remote_path, sftp_client
        self.parent, self.is_modified = parent, False
        self.last_search_string, self.last_search_flags = "", 0
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB | wx.TE_RICH2)
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.text_ctrl.SetFont(font)
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        save_item = file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S")
        close_item = file_menu.Append(wx.ID_CLOSE, "&Close\tCtrl+W")
        edit_menu = wx.Menu()
        undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z")
        redo_item = edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y")
        edit_menu.AppendSeparator()
        cut_item = edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X")
        copy_item = edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        paste_item = edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        search_menu = wx.Menu()
        find_item = search_menu.Append(wx.ID_FIND, "&Find\tCtrl+F")
        replace_item = search_menu.Append(wx.ID_REPLACE, "Find and &Replace\tCtrl+H")
        goto_item = search_menu.Append(wx.ID_ANY, "&Go To Line\tCtrl+G")
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(edit_menu, "&Edit")
        menu_bar.Append(search_menu, "&Search")
        self.SetMenuBar(menu_bar)
        SettingsMenuMixin.__init__(self)
        self.CreateStatusBar()
        self.SetStatusText(f"Editing: {self.remote_path}")
        self.Bind(wx.EVT_MENU, self.on_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_close, close_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Undo(), undo_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Redo(), redo_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Cut(), cut_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Copy(), copy_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Paste(), paste_item)
        self.Bind(wx.EVT_MENU, self.on_find, find_item)
        self.Bind(wx.EVT_MENU, self.on_replace, replace_item)
        self.Bind(wx.EVT_MENU, self.on_go_to_line, goto_item)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_text_modified)
        theme.apply_dark_theme(self)
        self.load_file_content()
        self.Show()

    def on_find(self, event):
        with FindDialog(self, "Find") as dlg:
            dlg.ShowModal()
    def on_replace(self, event):
        with ReplaceDialog(self, "Find and Replace") as dlg:
            dlg.ShowModal()
    def do_find(self, find_string, match_case):
        self.last_search_string = find_string
        flags = wx.FR_DOWN
        if match_case: flags |= wx.FR_MATCHCASE
        self.last_search_flags = flags
        content = self.text_ctrl.GetValue()
        start = self.text_ctrl.GetInsertionPoint()
        if not match_case:
            content = content.lower()
            find_string = find_string.lower()
        pos = content.find(find_string, start)
        if pos == -1: pos = content.find(find_string, 0)
        if pos != -1:
            self.text_ctrl.SetSelection(pos, pos + len(find_string))
            self.text_ctrl.SetFocus()
        else:
            wx.MessageBox(f"'{find_string}' not found.", "Find", wx.ICON_INFORMATION)
    def do_replace(self, find_string, replace_string, match_case):
        start, end = self.text_ctrl.GetSelection()
        selected_text = self.text_ctrl.GetStringSelection()
        compare_text = selected_text if match_case else selected_text.lower()
        compare_find = find_string if match_case else find_string.lower()
        if compare_text == compare_find:
            self.text_ctrl.Replace(start, end, replace_string)
        self.do_find(find_string, match_case)
    def do_replace_all(self, find_string, replace_string, match_case):
        content = self.text_ctrl.GetValue()
        if match_case:
            new_content = content.replace(find_string, replace_string)
        else:
            import re
            new_content = re.sub(find_string, replace_string, content, flags=re.IGNORECASE)
        self.text_ctrl.SetValue(new_content)
    def on_go_to_line(self, event):
        line_count = self.text_ctrl.GetNumberOfLines()
        with wx.NumberEntryDialog(self, f"Enter line number (1-{line_count})", "Go To Line", "Go To Line", 1, 1, line_count) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                line_num = dlg.GetValue() - 1
                pos = self.text_ctrl.XYToPosition(0, line_num)
                self.text_ctrl.SetInsertionPoint(pos)
                self.text_ctrl.SetFocus()
    def load_file_content(self):
        try:
            with open(self.local_path, 'r', encoding='utf-8') as f: self.text_ctrl.SetValue(f.read())
            self.is_modified = False
        except Exception as e:
            wx.MessageBox(f"Failed to read temporary file: {e}", "Error", wx.ICON_ERROR)
            self.Close()
    def on_text_modified(self, event):
        if not self.is_modified:
            self.is_modified = True
            self.SetTitle(self.GetTitle() + " *")
    def on_save(self, event):
        try:
            content = self.text_ctrl.GetValue()
            with open(self.local_path, 'w', encoding='utf-8') as f: f.write(content)
            self.SetStatusText(f"Uploading to {self.remote_path}...")
            self.sftp.put(self.local_path, self.remote_path)
            self.is_modified = False
            self.SetTitle(self.GetTitle().rstrip(" *"))
            self.SetStatusText(f"Successfully saved: {self.remote_path}")
        except Exception as e:
            wx.MessageBox(f"Failed to save file to server: {e}", "SFTP Error", wx.ICON_ERROR)
            self.SetStatusText(f"Error saving file: {e}")
    def on_close(self, event):
        if self.is_modified:
            result = wx.MessageBox("You have unsaved changes. Do you want to save before closing?", "Unsaved Changes", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            if result == wx.YES:
                self.on_save(None)
                if self.is_modified: return
            elif result == wx.CANCEL: return
        try:
            if os.path.exists(self.local_path): os.remove(self.local_path)
        except Exception as e: print(f"Warning: Could not delete temp file {self.local_path}: {e}")
        self.parent.notify_editor_closed(self.remote_path)
        self.Destroy()