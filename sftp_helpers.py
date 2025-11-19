import os
import stat
import wx

class TransferCancelledError(Exception):
    """Custom exception for clean cancellation of transfers."""
    pass

def count_remote_items(sftp, path, cancel_flag=None):
    """Recursively counts the number of files in a remote path."""
    if cancel_flag and cancel_flag.is_set():
        raise TransferCancelledError("Operation cancelled by user during file count.")
    count = 0
    attrs = sftp.lstat(path)
    if stat.S_ISDIR(attrs.st_mode):
        for item in sftp.listdir(path):
            count += count_remote_items(sftp, f"{path}/{item}", cancel_flag)
    else:
        count = 1
    return count

def count_local_items(path, cancel_flag=None):
    """Recursively counts the number of files in a local path."""
    if cancel_flag and cancel_flag.is_set():
        raise TransferCancelledError("Operation cancelled by user during file count.")
    count = 0
    if os.path.isdir(path):
        for item in os.listdir(path):
            count += count_local_items(os.path.join(path, item), cancel_flag)
    else:
        count = 1
    return count

def upload_item(sftp, local_path, remote_path, file_processed_callback, cancel_flag):
    """
    Uploads a local file or directory recursively, calling a callback for each file.
    """
    if cancel_flag.is_set():
        raise TransferCancelledError("Upload cancelled by user.")
    if os.path.isdir(local_path):
        try:
            sftp.mkdir(remote_path)
        except IOError:
            pass
        for item in os.listdir(local_path):
            upload_item(sftp, os.path.join(local_path, item), f"{remote_path}/{item}", file_processed_callback, cancel_flag)
    else:
        file_processed_callback(local_path)
        sftp.put(local_path, remote_path)

def download_item(sftp, remote_path, local_path, file_processed_callback, cancel_flag):
    """
    Downloads a remote file or directory recursively, calling a callback for each file.
    """
    if cancel_flag.is_set():
        raise TransferCancelledError("Download cancelled by user.")
    remote_attrs = sftp.lstat(remote_path)
    if stat.S_ISDIR(remote_attrs.st_mode):
        os.makedirs(local_path, exist_ok=True)
        for item in sftp.listdir(remote_path):
            download_item(sftp, f"{remote_path}/{item}", os.path.join(local_path, item), file_processed_callback, cancel_flag)
    else:
        file_processed_callback(remote_path)
        sftp.get(remote_path, local_path)

def delete_item(sftp, remote_path):
    """
    Deletes a remote file or directory recursively.
    """
    try:
        attrs = sftp.lstat(remote_path)
        if stat.S_ISDIR(attrs.st_mode):
            for item in sftp.listdir(remote_path):
                delete_item(sftp, f"{remote_path}/{item}")
            sftp.rmdir(remote_path)
        else:
            sftp.remove(remote_path)
    except Exception as e:
        raise IOError(f"Failed to delete {remote_path}: {e}")