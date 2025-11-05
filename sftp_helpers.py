import os
import stat
import wx

def upload_item(sftp, local_path, remote_path, progress_callback):
    # ... (unchanged) ...
    if os.path.isdir(local_path):
        try: sftp.mkdir(remote_path)
        except IOError: pass
        for item in os.listdir(local_path):
            upload_item(sftp, os.path.join(local_path, item), f"{remote_path}/{item}", progress_callback)
    else:
        sftp.put(local_path, remote_path, callback=progress_callback)

def download_item(sftp, remote_path, local_path, progress_callback):
    # ... (unchanged) ...
    remote_attrs = sftp.lstat(remote_path)
    if stat.S_ISDIR(remote_attrs.st_mode):
        os.makedirs(local_path, exist_ok=True)
        for item in sftp.listdir(remote_path):
            download_item(sftp, f"{remote_path}/{item}", os.path.join(local_path, item), progress_callback)
    else:
        sftp.get(remote_path, local_path, callback=progress_callback)

# --- NEW: Recursive deletion function ---
def delete_item(sftp, remote_path):
    """
    Deletes a remote file or directory recursively.
    """
    try:
        attrs = sftp.lstat(remote_path)
        if stat.S_ISDIR(attrs.st_mode):
            # It's a directory, delete its contents first
            for item in sftp.listdir(remote_path):
                delete_item(sftp, f"{remote_path}/{item}")
            # Then delete the empty directory
            sftp.rmdir(remote_path)
        else:
            # It's a file, just remove it
            sftp.remove(remote_path)
    except Exception as e:
        # Pass the error up to be handled by the GUI
        raise IOError(f"Failed to delete {remote_path}: {e}")