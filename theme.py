import wx

# Define our dark theme colors
DARK_BACKGROUND = wx.Colour(45, 45, 45)
DARK_FOREGROUND = wx.Colour(240, 240, 240)
DARK_TEXT_CTRL_BACKGROUND = wx.Colour(60, 60, 60)
DARK_LIST_CTRL_BACKGROUND = wx.Colour(55, 55, 55)

def is_dark_mode():
    """Checks if the operating system is in dark mode."""
    return wx.SystemSettings.GetAppearance().IsDark()

def apply_dark_theme_to_widget(widget):
    """Applies dark theme colors to a single widget based on its type."""
    if isinstance(widget, (wx.Frame, wx.Dialog, wx.Panel)):
        widget.SetBackgroundColour(DARK_BACKGROUND)
        widget.SetForegroundColour(DARK_FOREGROUND)
    
    elif isinstance(widget, wx.ListCtrl):
        widget.SetBackgroundColour(DARK_LIST_CTRL_BACKGROUND)
        widget.SetForegroundColour(DARK_FOREGROUND)
        widget.SetTextColour(DARK_FOREGROUND)

    elif isinstance(widget, wx.TextCtrl):
        # We handle the special terminal output/input fields separately
        if widget.IsSingleLine():
            widget.SetBackgroundColour(DARK_TEXT_CTRL_BACKGROUND)
            widget.SetForegroundColour(DARK_FOREGROUND)

    # *** FIX: wx.CheckBox has been REMOVED from this line. ***
    # We will let the OS handle the theme for checkboxes to preserve accessibility.
    elif isinstance(widget, (wx.StaticText, wx.Button)):
        widget.SetBackgroundColour(DARK_BACKGROUND)
        widget.SetForegroundColour(DARK_FOREGROUND)
        
    else:
        # For other controls, at least try to set the basic colors
        try:
            widget.SetBackgroundColour(DARK_BACKGROUND)
            widget.SetForegroundColour(DARK_FOREGROUND)
        except Exception:
            # Not all widgets support this (e.g., Sizers), so we ignore errors
            pass


def apply_dark_theme(top_level_window):
    """
    Recursively applies a dark theme to a top-level window and all its children
    if the OS is in dark mode.
    """
    if not is_dark_mode():
        return

    # Apply to the top-level window itself
    apply_dark_theme_to_widget(top_level_window)

    # Recursively apply to all children
    for child in top_level_window.GetChildren():
        apply_dark_theme_to_widget(child)
        if hasattr(child, "GetChildren"):
            apply_dark_theme(child) # Recurse into panels and other containers