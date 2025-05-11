# VS Code One-click Updater/Installer

A simple Python-based GUI application to easily download, install, or update Visual Studio Code (Stable or Insiders builds) on Windows. It also supports setting up a portable installation.

## Features

- **Download and Install/Update:** Fetches the latest version of VS Code (Stable or Insiders) and installs or updates it in the selected directory.
- **Portable Mode:** Option to create a portable version of VS Code by automatically creating the `data` directory.
- **Automatic Detection:** Detects existing VS Code installations (Stable or Insiders based on `Code.exe` or `Code - Insiders.exe`) in the selected folder and offers to update.
- **User-Friendly GUI:** Provides a simple interface built with PySide6 to select options and monitor progress.
- **Cancel Operation:** Allows cancellation of the download or installation process.
- **Progress Indication:** Shows download and extraction progress.

## Requirements

The application is built using Python and PySide6. The following packages are used (see `requirements.txt` for specific versions):

- PySide6
- requests

For building the executable, `PyInstaller` is used.

## How to Run/Build

### Running from Source

1.  **Clone the repository or download the source files.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the main script:**
    ```bash
    python main.py
    ```

### Building the Executable

The project includes an `install.bat` script and a `VSUpdater.spec` file for building a standalone executable using PyInstaller.

1.  **Ensure PyInstaller is installed:**
    ```bash
    pip install pyinstaller
    ```
2.  **Run the build script:**
    Open a command prompt or PowerShell in the project directory and run:
    ```bash
    .\install.bat
    ```
    This will create a standalone executable (`VSUpdater.exe`) in a `dist` folder. The `--uac-admin` flag in the spec file ensures the application requests administrator privileges, which are often needed for writing to Program Files or other protected locations.

## Usage

1.  **Run the application** (`VSUpdater.exe` if built, or `python main.py`).
2.  **Select Folder:**
    - Click the "Select Folder" button to choose the directory where you want to install VS Code or where an existing installation is located.
3.  **Installation/Update Options:**
    - If no VS Code installation is detected in the selected folder, the "Install" section will appear.
        - **Insider:** Check this box if you want to install the Insiders build of VS Code.
        - **Portable:** Check this box if you want the installation to be portable (creates a `data` subfolder).
        - Click **Install**.
    - If a VS Code installation (Stable or Insiders) is detected, the "Update" button will appear.
        - The application will automatically detect if it's an Insiders or Stable version.
        - Click **Update**.
4.  **Progress Monitoring:**
    - The progress bar and text area will show the status of the download, extraction, and file moving operations.
5.  **Cancel:**
    - During an operation, the "Install" or "Update" button will change to "Cancel". Clicking it will prompt for confirmation to stop the current operation.
6.  **Completion:**
    - Upon successful completion, a message will be displayed, and the UI will reset for another operation.
    - If an error occurs, details will be shown in the progress text area.

## Notes

- The application creates a temporary folder named `temp` in the same directory as the executable (or `main.py` if run from source) for downloading and extracting files. This folder is cleaned up after the operation.
- Administrator privileges might be required for installing/updating in certain system directories (e.g., `C:\Program Files`). The bundled executable (built with `VSUpdater.spec`) requests these privileges by default.
