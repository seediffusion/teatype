# --- START OF FILE menu_mixin.py ---

import wx
import speech

class SettingsMenuMixin:
    def __init__(self):
        # --- FIX: Renamed config name ---
        self.config = wx.Config("Teatype")
        self._setup_settings_menu()

    # ... (The rest of the file is unchanged) ...
    def _setup_settings_menu(self):
        menu_bar = self.GetMenuBar()
        if not menu_bar:
            menu_bar = wx.MenuBar()
        settings_menu = wx.Menu()
        self.speak_output_item = settings_menu.AppendCheckItem(
            wx.ID_ANY,
            "&Speak Terminal Output",
            "Read terminal output aloud using a screen reader"
        )
        menu_bar.Append(settings_menu, "&Settings")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.on_toggle_speak_output, self.speak_output_item)
        self.load_settings()
    def on_toggle_speak_output(self, event):
        is_enabled = self.speak_output_item.IsChecked()
        speech.set_speak_enabled(is_enabled)
        self.config.WriteBool("/Settings/SpeakOutput", is_enabled)
        self.config.Flush()
    def load_settings(self):
        speak_enabled = self.config.ReadBool("/Settings/SpeakOutput", True)
        self.speak_output_item.Check(speak_enabled)
        speech.set_speak_enabled(speak_enabled)