# --- START OF FILE security.py ---

import keyring

# --- FIX: Renamed service name ---
SERVICE_NAME = "Teatype"

# ... (The rest of the file is unchanged) ...
def _get_keyring_username(server_name, host, user):
    return f"{user}@{host} ({server_name})"
def _get_keyring_key_identifier(server_name, host, user):
    return f"{user}@{host} ({server_name}) [SSH Key]"
def store_password(server_name, host, user, password):
    if not password: return
    username = _get_keyring_username(server_name, host, user)
    keyring.set_password(SERVICE_NAME, username, password)
def get_password(server_name, host, user):
    username = _get_keyring_username(server_name, host, user)
    return keyring.get_password(SERVICE_NAME, username)
def delete_password(server_name, host, user):
    try:
        username = _get_keyring_username(server_name, host, user)
        keyring.delete_password(SERVICE_NAME, username)
    except keyring.errors.PasswordDeleteError: pass
def store_passphrase(server_name, host, user, passphrase):
    username = _get_keyring_key_identifier(server_name, host, user)
    keyring.set_password(SERVICE_NAME, username, passphrase)
def get_passphrase(server_name, host, user):
    username = _get_keyring_key_identifier(server_name, host, user)
    return keyring.get_password(SERVICE_NAME, username)
def delete_passphrase(server_name, host, user):
    try:
        username = _get_keyring_key_identifier(server_name, host, user)
        keyring.delete_password(SERVICE_NAME, username)
    except keyring.errors.PasswordDeleteError: pass