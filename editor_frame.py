import wx
import os
import theme
from menu_mixin import SettingsMenuMixin


class FindDialog(wx.Dialog):
    def __init__(self, parent, title="Find"):
        super(FindDialog, self).__init__(parent, title=title)
        self.parent = parent

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Find what
        vbox.Add(wx.StaticText(panel, label="Find what:"), 0, wx.ALL, 5)
        self.find_text = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.find_text, 0, wx.EXPAND | wx.ALL, 5)

        # Match case
        self.case_checkbox = wx.CheckBox(panel, label="Match &case")
        vbox.Add(self.case_checkbox, 0, wx.ALL, 5)

        # Direction
        dir_box = wx.StaticBox(panel, label="Direction")
        dir_sizer = wx.StaticBoxSizer(dir_box, wx.HORIZONTAL)
        self.direction_radio = wx.RadioBox(
            panel,
            choices=["Down", "Up"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.direction_radio.SetSelection(0)
        dir_sizer.Add(self.direction_radio, 1, wx.ALL, 5)
        vbox.Add(dir_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        find_next_btn = wx.Button(panel, wx.ID_OK, "&Find Next")
        close_btn = wx.Button(panel, wx.ID_CANCEL, "&Close")
        btn_sizer.Add(find_next_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(close_btn, 0)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        panel.SetSizer(vbox)
        self.Fit()
        self.find_text.SetFocus()

        find_next_btn.Bind(wx.EVT_BUTTON, self.on_find_next)
        self.find_text.Bind(wx.EVT_TEXT_ENTER, self.on_find_next)

        theme.apply_dark_theme(self)

    def on_find_next(self, event):
        direction = self.direction_radio.GetStringSelection().lower()
        self.parent.do_find(
            self.find_text.GetValue(),
            self.case_checkbox.IsChecked(),
            direction,
        )


class ReplaceDialog(wx.Dialog):
    def __init__(self, parent, title="Find and Replace"):
        super(ReplaceDialog, self).__init__(parent, title=title)
        self.parent = parent

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Find what
        vbox.Add(wx.StaticText(panel, label="Find what:"), 0, wx.ALL, 5)
        self.find_text = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.find_text, 0, wx.EXPAND | wx.ALL, 5)

        # Replace with
        vbox.Add(wx.StaticText(panel, label="Replace with:"), 0, wx.ALL, 5)
        self.replace_text = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.replace_text, 0, wx.EXPAND | wx.ALL, 5)

        # Match case
        self.case_checkbox = wx.CheckBox(panel, label="Match &case")
        vbox.Add(self.case_checkbox, 0, wx.ALL, 5)

        # Direction
        dir_box = wx.StaticBox(panel, label="Direction")
        dir_sizer = wx.StaticBoxSizer(dir_box, wx.HORIZONTAL)
        self.direction_radio = wx.RadioBox(
            panel,
            choices=["Down", "Up"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.direction_radio.SetSelection(0)
        dir_sizer.Add(self.direction_radio, 1, wx.ALL, 5)
        vbox.Add(dir_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        find_next_btn = wx.Button(panel, wx.ID_FIND, "&Find Next")
        replace_btn = wx.Button(panel, wx.ID_REPLACE, "&Replace")
        replace_all_btn = wx.Button(panel, wx.ID_ANY, "Replace &All")
        close_btn = wx.Button(panel, wx.ID_CANCEL, "&Close")
        for b in (find_next_btn, replace_btn, replace_all_btn, close_btn):
            btn_sizer.Add(b, 0, wx.RIGHT, 5)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        panel.SetSizer(vbox)
        self.Fit()
        self.find_text.SetFocus()

        find_next_btn.Bind(wx.EVT_BUTTON, self.on_find_next)
        replace_btn.Bind(wx.EVT_BUTTON, self.on_replace)
        replace_all_btn.Bind(wx.EVT_BUTTON, self.on_replace_all)
        self.find_text.Bind(wx.EVT_TEXT_ENTER, self.on_find_next)
        self.replace_text.Bind(wx.EVT_TEXT_ENTER, self.on_find_next)

        theme.apply_dark_theme(self)

    def on_find_next(self, event):
        direction = self.direction_radio.GetStringSelection().lower()
        self.parent.do_find(
            self.find_text.GetValue(),
            self.case_checkbox.IsChecked(),
            direction,
        )

    def on_replace(self, event):
        direction = self.direction_radio.GetStringSelection().lower()
        self.parent.do_replace(
            self.find_text.GetValue(),
            self.replace_text.GetValue(),
            self.case_checkbox.IsChecked(),
            direction,
        )

    def on_replace_all(self, event):
        self.parent.do_replace_all(
            self.find_text.GetValue(),
            self.replace_text.GetValue(),
            self.case_checkbox.IsChecked(),
        )


class EditorFrame(wx.Frame, SettingsMenuMixin):
    def __init__(self, parent, title, local_path, remote_path, sftp_client):
        wx.Frame.__init__(self, parent, title=title, size=(800, 600))
        SettingsMenuMixin.__init__(self)

        self.parent = parent  # main frame, used for notify_editor_closed
        self.local_path = local_path
        self.remote_path = remote_path
        self.sftp = sftp_client

        self.is_modified = False
        self.last_search_string = ""
        self.last_search_flags = 0
        self.last_search_direction = "down"

        # Text control
        self.text_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB | wx.TE_RICH2,
        )
        font = wx.Font(
            12,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.text_ctrl.SetFont(font)

        # Menu bar
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        save_item = file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S")
        close_item = file_menu.Append(wx.ID_CLOSE, "&Close\tCtrl+W")
        menu_bar.Append(file_menu, "&File")

        # Edit menu
        edit_menu = wx.Menu()
        undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z")
        redo_item = edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y")
        edit_menu.AppendSeparator()
        cut_item = edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X")
        copy_item = edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        paste_item = edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        edit_menu.AppendSeparator()
        select_all_item = edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        menu_bar.Append(edit_menu, "&Edit")

        # Search menu
        search_menu = wx.Menu()
        find_item = search_menu.Append(wx.ID_FIND, "&Find\tCtrl+F")
        find_next_item = search_menu.Append(wx.ID_ANY, "Find &Next\tF3")
        replace_item = search_menu.Append(wx.ID_REPLACE, "Find and &Replace\tCtrl+H")
        goto_item = search_menu.Append(wx.ID_ANY, "&Go To Line\tCtrl+G")
        menu_bar.Append(search_menu, "&Search")

        self.SetMenuBar(menu_bar)

        # SettingsMenuMixin already added Settings menu in its __init__

        # Status bar
        self.CreateStatusBar()
        self.SetStatusText(f"Editing: {self.remote_path}")

        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_close, close_item)

        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Undo(), undo_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Redo(), redo_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Cut(), cut_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Copy(), copy_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.Paste(), paste_item)
        self.Bind(wx.EVT_MENU, lambda e: self.text_ctrl.SelectAll(), select_all_item)

        self.Bind(wx.EVT_MENU, self.on_find, find_item)
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.do_find(
                self.last_search_string,
                bool(self.last_search_flags & wx.FR_MATCHCASE),
                self.last_search_direction,
            ),
            find_next_item,
        )
        self.Bind(wx.EVT_MENU, self.on_replace, replace_item)
        self.Bind(wx.EVT_MENU, self.on_go_to_line, goto_item)

        # Other bindings
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_text_modified)

        theme.apply_dark_theme(self)
        self.load_file_content()
        self.Show()

    # ------------- searching / replacing -------------

    def on_find(self, event):
        with FindDialog(self, "Find") as dlg:
            dlg.ShowModal()

    def on_replace(self, event):
        with ReplaceDialog(self, "Find and Replace") as dlg:
            dlg.ShowModal()

    def do_find(self, find_string, match_case, direction="down"):
        if not find_string:
            return

        self.last_search_string = find_string
        self.last_search_direction = direction
        self.last_search_flags = wx.FR_MATCHCASE if match_case else 0

        content = self.text_ctrl.GetValue()
        if not match_case:
            content_to_search = content.lower()
            needle = find_string.lower()
        else:
            content_to_search = content
            needle = find_string

        current_pos = self.text_ctrl.GetInsertionPoint()

        if direction == "down":
            start = current_pos
            idx = content_to_search.find(needle, start)
            if idx == -1:
                idx = content_to_search.find(needle, 0)
        else:
            start = 0
            before = content_to_search[:current_pos]
            idx = before.rfind(needle)
            if idx == -1:
                idx = content_to_search.rfind(needle)

        if idx == -1:
            wx.Bell()
            self.SetStatusText("Text not found.")
            return

        end = idx + len(find_string)
        self.text_ctrl.SetSelection(idx, end)
        self.text_ctrl.SetInsertionPoint(end)
        self.text_ctrl.ShowPosition(idx)
        self.SetStatusText(f"Found at position {idx}.")

    def do_replace(self, find_string, replace_string, match_case, direction="down"):
        if not find_string:
            return

        # If current selection matches, replace it; else find next
        selection = self.text_ctrl.GetStringSelection()
        if selection:
            if match_case:
                matches = (selection == find_string)
            else:
                matches = (selection.lower() == find_string.lower())
            if matches:
                start, end = self.text_ctrl.GetSelection()
                self.text_ctrl.Replace(start, end, replace_string)
                self.is_modified = True
                self.mark_modified_title()
        # Find next occurrence
        self.do_find(find_string, match_case, direction)

    def do_replace_all(self, find_string, replace_string, match_case):
        if not find_string:
            return

        content = self.text_ctrl.GetValue()
        if match_case:
            new_content = content.replace(find_string, replace_string)
        else:
            # Case-insensitive replace
            import re

            pattern = re.compile(re.escape(find_string), re.IGNORECASE)
            new_content = pattern.sub(replace_string, content)

        if new_content != content:
            self.text_ctrl.SetValue(new_content)
            self.is_modified = True
            self.mark_modified_title()
            self.SetStatusText("Replace All completed.")
        else:
            self.SetStatusText("No occurrences replaced.")

    def on_go_to_line(self, event):
        with wx.TextEntryDialog(
            self, "Enter line number:", "Go To Line"
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            try:
                line_no = int(dlg.GetValue())
            except ValueError:
                wx.MessageBox("Please enter a valid line number.", "Error", wx.ICON_ERROR)
                return

        if line_no < 1:
            line_no = 1

        # wx.TextCtrl doesn't expose line offsets directly; approximate by splitting
        content = self.text_ctrl.GetValue().splitlines(True)
        if not content:
            return

        index = 0
        for i in range(min(line_no - 1, len(content) - 1)):
            index += len(content[i])

        self.text_ctrl.SetInsertionPoint(index)
        self.text_ctrl.ShowPosition(index)
        self.SetStatusText(f"Moved to line {line_no}.")

    # ------------- file operations -------------

    def load_file_content(self):
        try:
            if os.path.exists(self.local_path):
                with open(self.local_path, "r", encoding="utf-8", errors="replace") as f:
                    self.text_ctrl.SetValue(f.read())
            else:
                self.text_ctrl.SetValue("")
            self.is_modified = False
            self.mark_modified_title()
        except Exception as e:
            wx.MessageBox(
                f"Failed to load file: {e}", "Error", wx.ICON_ERROR
            )
            self.text_ctrl.SetValue("")
            self.is_modified = False
            self.mark_modified_title()

    def on_text_modified(self, event):
        if not self.is_modified:
            self.is_modified = True
            self.mark_modified_title()
        event.Skip()

    def mark_modified_title(self):
        title = self.GetTitle()
        if self.is_modified:
            if not title.endswith(" *"):
                self.SetTitle(title + " *")
        else:
            if title.endswith(" *"):
                self.SetTitle(title[:-2])

    def on_save(self, event):
        # Save to local temp file first
        try:
            with open(self.local_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(self.text_ctrl.GetValue())
        except Exception as e:
            wx.MessageBox(
                f"Failed to save file locally: {e}", "Error", wx.ICON_ERROR
            )
            self.SetStatusText(f"Error saving file locally: {e}")
            return

        # Then upload to server
        try:
            self.sftp.put(self.local_path, self.remote_path)
            self.is_modified = False
            self.mark_modified_title()
            self.SetStatusText(f"Successfully saved: {self.remote_path}")
        except Exception as e:
            wx.MessageBox(
                f"Failed to save file to server: {e}", "SFTP Error", wx.ICON_ERROR
            )
            self.SetStatusText(f"Error saving file: {e}")

    def on_close(self, event):
        if self.is_modified:
            result = wx.MessageBox(
                "You have unsaved changes. Do you want to save them?",
                "Unsaved Changes",
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
            )
            if result == wx.YES:
                self.on_save(None)
                # If save failed, keep window open
                if self.is_modified:
                    return
            elif result == wx.CANCEL:
                return

        # Clean up temp file
        try:
            if os.path.exists(self.local_path):
                os.remove(self.local_path)
        except Exception as e:
            print(
                f"Warning: Could not delete temp file {self.local_path}: {e}"
            )

        # Inform main frame that this editor is closed
        if hasattr(self.parent, "notify_editor_closed"):
            try:
                self.parent.notify_editor_closed(self.remote_path)
            except Exception:
                # Don't crash if parent misbehaves
                pass

        self.Destroy()
