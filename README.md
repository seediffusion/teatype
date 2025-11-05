# Teatype, the accessible TTY with speed and ease, by Seediffusion!

## Introduction

Teatype is a portable, light-weight, powerful SSH client designed with sightless sysadmins in mind. Unlike many SSH clients, such as PuTTY, Bitvise and XTerm, Teatype doesn't run in a terminal. Instead, it features a graphical TTY interface, with one textbox for entering commands and another showing a line-by-line view of command output. This helps to eliminate a lot of the problems screen reader users might face when using standard terminals, such as parts of the output being cut off or announced weirdly or not being able to see all the output of a very long process, even with a maximised window.

## Full disclosure

A large language model (LLM), specifically Google Gemini 2.5 Pro, was used to write this program. However, rest assured that the program has been thurroughly tested to ensure that it is as stable and reliable as possible.

## What is SSH?

SSH stands for Secure Shell. It is a way of interacting with a computer by sending terminal commands over a local network or the internet using a secure, encrypted connection. SSH client and server software is available for all major computer operating systems, including Unix, Linux, MacOS and Windows, with the most popular SSH solution being the free and open source OpenSSH.
As well as remotely controlling a system via terminal commands, SSH also allows you to view, upload and download files via SFTP, which is the SSH File Transfer Protocol.

## Teatype features

* A simple, minimalist UI.
* Includes clear screen reader labelling for all UI elements, such as textboxes, buttons, dropdown menus and checkboxes.
* The program can be controlled entirely via keyboard shortcuts.
* Includes an easy-to-use graphical TTY interface with one textbox for entering commands and another for viewing command output line by line. Use the Tab key to switch between the fields and the arrow keys to view their contents.
* Supports the operating system's dark mode setting and adds a dark theme acordingly.
* Multi-line commands with indentations are supported.
* Screen readers will automatically read command output by default.
* Both password and SSH key authentication is supported.
* Control + C (signal interrupt) and Control + D (end of transmission) are supported.
* An SFTP file browser and editor is included.

## Download and installation

### From source

Here are the instructions for running Teatype from its source code on Windows.

1.  Ensure you have Python installed.
    * [Download Python 3.13 (64-bit)](https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe)
    * [Download Python 3.13 (32-bit)](https://www.python.org/ftp/python/3.13.9/python-3.13.9.exe)
    * [Download Python 3.8 (64-bit) for Windows 7](https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe)
    * [Download Python 3.8 (32-bit) for Windows 7](https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe)
2.  Download and install Git for Windows.
    * [Download the latest Git for Windows](https://github.com/git-for-windows/git/releases/download/v2.51.2.windows.1/Git-2.51.2-64-bit.exe)
    * [Download Git for Windows 7](GitWindows7.exe)
3.  Press Windows + R, type `cmd`, and hit Enter to open a command prompt.
4.  Clone this repository with git.
    ```
    git clone https://github.com/seediffusion/Teatype.git
    ```
5.  Create a virtual environment. This creates a separate workspace for the project's dependencies, isolated from your main Python install.
    ```
    cd Teatype
    python -m venv venv
    ```
6.  Activate the virtual environment.
    ```
    venv\scripts\activate
    ```
7.  To avoid library installation errors, ensure you have the highest versions of pip, setuptools and wheel.
    ```
    python -m pip install --upgrade pip setuptools wheel
    ```
8.  Install the required libraries.
    ```
    pip install -r requirements.txt
    ```
9. Finally, you should now be able to run the program.
    ```
    python teatype.py
    ```

### Compiled

If you don't wanna mess with all that fancy dev stuff, you can simply [download the latest pre-compiled binary](https://github.com/seediffusion/Teatype/releases/latest/download/teatype.zip). This release works on both 32 and 64-bit versions of Windows 7 and higher.
Since Teatype is a portable program, everything the program needs to run is stored inside a single folder. all you have to do is extract the Teatype.zip file to a location of your choice using [7-Zip](https://7-zip.org) or your favourite zip archiver.
To start the program, simply launch the teatype.exe file. If Windows isn't set up to show file extensions, you won't see the .exe part.

## The server manager

When you launch Teatype for the first time, you will be greeted with the Server Manager. This is the central hub where all your saved SSH server connections are stored.

### Adding a server

1. Click the add button or press Alt + A to bring up the add server dialog.
2. Enter a memorable name for the server.
3. Enter the server's hostname or IP address.
4. Enter the SSH port. The default is 22.
5. Enter the username for your account on the server.
6. In the auth method dropdown, choose either password or SSH key.
7. If you chose password, simply enter your account password. Otherwise, browse to your OpenSSH private key file and enter a passphrase if you have one set for the SSH key.
8. Check the box to securely store your password or SSH key passphrase. Note: if you use a screen reader and Windows is in dark mode, this checkbox will be seen as a button.
9. Click the add button to save the server to the list.

### Connecting to a server

Press Enter on a server in the list, hit the Connect button or press Alt + C to log into the server and display the graphical TTY.

### Editing a server

Click the edit button on a server or press Alt + E. This brings up a dialog similar to the add server dialog, but you can makes changes to a server's details as needed. Hit save when you're done.

### Deleting a server

Hit the remove button on a server or press Alt + R, then hit yes to confirm the deletion.

## The TTY

Upon connecting and logging into a server, the  graphical TTY view will open  and you will be focused on the command input text field. Pressing tab in this window will switch between the command input field and the server output log. Simply use your screen reader's standard text reading keys to view the contents of the log.

* Press Enter to execute a command.
* Press Shift + Enter to create a new line for long commands that require multiple lines.
* Press Control + C to send an interrupt signal and stop a running foreground process.
* Press Control + D to send an end-of-transmission signal. If you're not in any interactive shell sessions, such as an SQL prompt or similar, this will log you out of the server.

## The file browser

Clicking the browse files button in the TTY view will open a file browser window. This allows you to view, edit, upload and download files and folders via SFTP. When you arrow up and down through the list, Teatype will show you the name of the item, the item's size, and whether it is a file or a directory (folder). Press Enter to go into a folder, and Backspace to go back to the parent folder.

### Editing files

Editing files is as simple as pressing Enter on a file to have it open in a text editor view. From here, you can just use your standard reading keys to view and edit the file like you would in a normal text editor like Notepad. Use Control + S to save the file, Control + F to find, Control + H to find and replace, Control + G to go to a specific line number, and Control + W to close the editor.

### Uploading files and folders

There are 2 ways of uploading files and folders to your server.

* You can copy the file or folder from your local machine and paste it into the file browser in Teatype.
* You can hit the upload button to browse your local machine for a file to upload.

### Downloading files and folders

* Copy the file or folder from the file browser and paste it someone in your local file system.
* Click the download button and choose where to save the file or folder on your machine.

## Disabling screen reader feedback

If you're sighted and don't want to hear server output spoken by a screen reader, both the server manager and TTY windows have a settings bar where you can turn it off. This is also useful in situations where you have a very long process running and you want to do other things without having to hear the screen reader blabbing on.

## Supporting Seediffusion
Teatype is completely free of charge, but donations and contributions are appreciated, as they help keep Seediffusion alive and support the development of present and future Seediffusion projects. Here are the ways you can give your support:

*   [Ko-Fi](https://ko-fi.com/seediffusion)
*   [Patreon](https://patreon.com/seediffusion)

If you can't give financial support, sharing around also helps. :)

*   [Visit the Seediffusion website](https://seediffusion.cc)
*   [Follow Seediffusion on Mastodon](https://vee.seedy.cc/@seediffusion)
*   [Email Seediffusion](mailto:"seedy@thecubed.cc")