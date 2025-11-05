import accessible_output2.outputs

# --- NEW: Global flag to control speech output ---
SPEAK_ENABLED = True

speaker = accessible_output2.outputs.auto.Auto()

# --- NEW: Function to set the state of speech output ---
def set_speak_enabled(enabled: bool):
    """Globally enables or disables screen reader output."""
    global SPEAK_ENABLED
    SPEAK_ENABLED = enabled

def speak(text, interrupt=True):
    """Speaks the given text if speech is enabled."""
    # --- The gatekeeper check ---
    if not SPEAK_ENABLED:
        return
    
    speaker.speak(text, interrupt=interrupt)