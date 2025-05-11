import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout, QCheckBox, QProgressBar, QTextEdit, QMessageBox
from PySide6.QtCore import Slot, Qt
import shutil
import requests
import sys # Add sys import


INSIDER_CODE_FILE = 'Code - Insiders.exe'
CODE_FILE = 'Code.exe'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VS Code One-click Updater/Installer")
        self.setGeometry(100, 100, 800, 600)

        self.folderPath = None

        self.isInsider = False
        self.isPortable = True

        self.is_operation_in_progress = False
        self.cancel_requested = False
        self.active_button = None
        self.other_button = None
        self.original_active_button_text = ""

        self.initUI()

    def initUI(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.centralWidget.setLayout(self.main_layout)

        self.folderPathSelector = QPushButton("Select Folder" if not self.folderPath else self.folderPath)
        self.folderPathSelector.clicked.connect(self.selectFolder)
        self.folderPathSelector.setFixedHeight(30)
        self.folderPathSelector.setStyleSheet("background-color: white; color: black; border-radius: 5px; padding: 5px; border: 1px solid #ccc;")
        self.main_layout.addWidget(self.folderPathSelector)

        ### UPDATE BUTTON ###
        self.updateButton = QPushButton("Update")
        self.updateButton.setFixedHeight(30)
        self.updateButton.setVisible(False)
        self.updateButton.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        self.updateButton.clicked.connect(self.handle_update_button_click) # Changed

        self.main_layout.addWidget(self.updateButton)


        ### INSTALL LAYOUT ###

        self.installWidget = QWidget()
        self.installWidget.setVisible(False) # Initially hidden

        self.install_layout = QVBoxLayout()
        self.install_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.install_layout.setContentsMargins(0, 0, 0, 0)
        self.install_layout.setSpacing(10)

        self.installWidget.setLayout(self.install_layout)

        self.checkbox_layout = QHBoxLayout()
        self.checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.isInsiderCheckbox = QCheckBox("Insider")
        self.isInsiderCheckbox.setCheckable(True)
        self.isInsiderCheckbox.setChecked(self.isInsider)
        self.isInsiderCheckbox.clicked.connect(self.toggleInsider)

        self.isPortableCheckbox = QCheckBox("Portable")
        self.isPortableCheckbox.setCheckable(True)
        self.isPortableCheckbox.setChecked(self.isPortable)
        self.isPortableCheckbox.clicked.connect(self.togglePortable)

        self.checkbox_layout.addWidget(self.isInsiderCheckbox)
        self.checkbox_layout.addWidget(self.isPortableCheckbox)

        self.installButton = QPushButton("Install")
        self.installButton.setFixedHeight(30)
        self.installButton.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        self.installButton.clicked.connect(self.handle_install_button_click) # Changed

        self.install_layout.addLayout(self.checkbox_layout)
        self.install_layout.addWidget(self.installButton)

        self.main_layout.addWidget(self.installWidget)

        ### Progress Box ###
        self.progressWidget = QWidget()
        self.progressLayout = QVBoxLayout()
        self.progressWidget.setLayout(self.progressLayout)

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressLayout.addWidget(self.progressBar)

        self.progressText = QTextEdit()
        self.progressText.setReadOnly(True)
        self.progressLayout.addWidget(self.progressText)

        self.main_layout.addWidget(self.progressWidget)
        self.progressWidget.setVisible(False) # Initially hidden

    def handle_install_button_click(self):
        if self.is_operation_in_progress:
            self.request_cancellation()
        else:
            if not self.folderPath:
                self.progressText.setText("Please select a folder first.")
                self.progressWidget.setVisible(True)
                return
            self.start_operation(is_install_operation=True)

    def handle_update_button_click(self):
        if self.is_operation_in_progress:
            self.request_cancellation()
        else:
            # folderPath should exist if update button is visible
            self.start_operation(is_install_operation=False)

    def request_cancellation(self):
        if self.is_operation_in_progress:
            reply = QMessageBox.warning(self, "Confirm Cancel",
                                        "Are you sure you want to cancel the current operation?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_requested = True
                self.progressText.append("Cancellation requested by user...")
                QApplication.processEvents()
            else:
                self.progressText.append("Cancellation aborted by user.")
                QApplication.processEvents()

    def start_operation(self, is_install_operation):
        self.is_operation_in_progress = True
        self.cancel_requested = False
        
        self.progressWidget.setVisible(True)
        self.progressBar.setValue(0)
        self.progressText.clear()
        self.progressText.append(f"{'Installing' if is_install_operation else 'Updating'} VS Code...")
        QApplication.processEvents()

        if is_install_operation:
            self.active_button = self.installButton
            self.other_button = self.updateButton
        else:
            self.active_button = self.updateButton
            self.other_button = self.installButton
        
        self.original_active_button_text = self.active_button.text()
        self.active_button.setText("Cancel")

        self.folderPathSelector.setEnabled(False)
        self.isInsiderCheckbox.setEnabled(False)
        self.isPortableCheckbox.setEnabled(False)
        self.other_button.setEnabled(False) # Disable the other action button

        # Run the core logic in a separate thread or use QTimer to avoid freezing, 
        # for now, direct call with processEvents
        success = self._perform_download_and_extract_core(is_install_operation)
        self._finalize_operation(success, self.cancel_requested, is_install_operation)

    def _perform_download_and_extract_core(self, is_install_operation):
        # Corrected temp_dir calculation:
        # temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "temp")
        
        try:
            # Initial cleanup of temp_dir
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e_initial_cleanup:
                    self.progressText.append(f"Notice: Could not clean up pre-existing temp directory: {e_initial_cleanup}")
                    QApplication.processEvents()
                    # Not returning False, as os.makedirs might still succeed or handle it.
            
            os.makedirs(temp_dir) # Ensure temp_dir is created for subsequent operations

            temp_file = os.path.join(temp_dir, "vscode.zip")

            if self.isInsider:
                install_url = "https://code.visualstudio.com/sha/download?build=insider&os=win32-x64-archive"
            else:
                install_url = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-archive"

            self.progressText.append("Downloading VS Code...")
            QApplication.processEvents() 

            response = requests.get(install_url, stream=True)
            response.raise_for_status() # Check for HTTP errors
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested:
                        self.progressText.append("Download cancelled.")
                        if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                        return False
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((bytes_downloaded / total_size) * 50) 
                            self.progressBar.setValue(progress)
                            QApplication.processEvents()

            if self.cancel_requested: # Check again after loop
                self.progressText.append("Download cancelled.")
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False

            self.progressBar.setValue(50) 
            self.progressText.append("Download complete.")
            self.progressText.append("Extracting files...")
            QApplication.processEvents()

            try:
                shutil.unpack_archive(temp_file, temp_dir)
            except Exception as e_unpack:
                self.progressText.append(f"EXTRACTION ERROR: {e_unpack}")
                QApplication.processEvents()
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False # Critical failure

            if self.cancel_requested:
                self.progressText.append("Extraction cancelled.")
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            self.progressBar.setValue(75) 
            self.progressText.append("Extraction complete.")
            QApplication.processEvents()

            try:
                os.remove(temp_file)
                self.progressText.append("Temporary zip file removed.")
            except Exception as e_remove_zip:
                self.progressText.append(f"Warning: Could not remove temporary zip file: {e_remove_zip}")
            QApplication.processEvents()


            self.progressText.append("Moving files to installation directory...")
            QApplication.processEvents()
            items = os.listdir(temp_dir)
            total_items = len(items)
            items_moved = 0
            try:
                for item in items:
                    if self.cancel_requested:
                        self.progressText.append("File moving cancelled during operation.")
                        if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                        return False
                    s = os.path.join(temp_dir, item)
                    d = os.path.join(self.folderPath, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
                    items_moved += 1
                    if total_items > 0:
                        progress = 75 + int((items_moved / total_items) * 20) 
                        self.progressBar.setValue(progress)
                        QApplication.processEvents()
            except PermissionError as pe:
                self.progressText.append(f"PERMISSION ERROR during file move: {pe}. VS Code might be running or files are locked. Please close VS Code and try again.")
                QApplication.processEvents()
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            except shutil.Error as se:
                self.progressText.append(f"FILE OPERATION ERROR during file move: {se}. Please check permissions or if VS Code is running.")
                QApplication.processEvents()
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            except Exception as e_move:
                self.progressText.append(f"UNEXPECTED ERROR during file move: {e_move}.")
                QApplication.processEvents()
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            if self.cancel_requested: # Final check after move loop
                self.progressText.append("File moving cancelled.")
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
                return False

            self.progressBar.setValue(95)
            self.progressText.append("File move complete.")
            QApplication.processEvents()

            self.progressText.append("Cleaning up temporary directory...")
            QApplication.processEvents()
            try:
                if os.path.exists(temp_dir): # Ensure it exists before trying to remove
                    shutil.rmtree(temp_dir)
                self.progressText.append("Temporary directory cleaned up.")
            except Exception as e_final_cleanup:
                self.progressText.append(f"Warning: Error during final temporary directory cleanup: {e_final_cleanup}")
            QApplication.processEvents()


            if is_install_operation and self.isPortable and not self.cancel_requested:
                self.progressText.append("Creating 'data' folder for portable mode...")
                QApplication.processEvents()
                data_path = os.path.join(self.folderPath, "data")
                try:
                    if not os.path.exists(data_path):
                        os.makedirs(data_path)
                    self.progressText.append("'data' folder created/ensured.")
                except PermissionError as pe_data:
                    self.progressText.append(f"Warning: PERMISSION ERROR creating 'data' folder: {pe_data}. Check permissions.")
                except Exception as e_data:
                    self.progressText.append(f"Warning: Error creating 'data' folder: {e_data}.")
                QApplication.processEvents()
            
            if self.cancel_requested: 
                 self.progressText.append("Operation cancelled before final step.")
                 # temp_dir should have been cleaned up by earlier cancel checks
                 return False

            self.progressBar.setValue(100)
            self.progressText.append("Core operation successful!")
            QApplication.processEvents()
            return True

        except requests.exceptions.RequestException as e:
            self.progressText.append(f"NETWORK ERROR: {e}. Please check your internet connection.")
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        except Exception as e:
            self.progressText.append(f"AN UNEXPECTED ERROR OCCURRED: {e}")
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir): shutil.rmtree(temp_dir, ignore_errors=True)
            return False

    def _finalize_operation(self, success, cancelled, is_install_op):
        if self.active_button: # Ensure active_button was set
            self.active_button.setText(self.original_active_button_text)
        
        self.folderPathSelector.setEnabled(True)
        self.isInsiderCheckbox.setEnabled(True)
        self.isPortableCheckbox.setEnabled(True)
        if self.other_button: # Ensure other_button was set
            self.other_button.setEnabled(True) 

        self.is_operation_in_progress = False
        self.active_button = None # Reset
        self.other_button = None # Reset

        if cancelled:
            self.progressText.append("Operation officially cancelled by user.")
            self.progressBar.setValue(0) 
            # Optionally hide progressWidget after a delay or keep it
        elif success:
            self.progressText.append("Installation/Update complete! Resetting UI.")
            self.progressBar.setValue(100)
            self._reset_ui_to_initial_state()
        else: # Failed, not cancelled
            self.progressText.append("Operation failed. Check logs above for details.")
            # Keep progressWidget visible with the error message
        QApplication.processEvents()


    def _reset_ui_to_initial_state(self):
        self.progressText.append("Resetting UI to initial state...")
        QApplication.processEvents()

        self.folderPath = None
        self.folderPathSelector.setText("Select Folder")
        
        self.isInsider = False # Default
        self.isPortable = True # Default
        
        self.isInsiderCheckbox.setChecked(self.isInsider)
        self.isPortableCheckbox.setChecked(self.isPortable)

        self.updateButton.setVisible(False)
        self.installWidget.setVisible(False) # Ensure install widget is hidden on reset
        
        # Hide progress after a short delay or immediately
        # For now, hide immediately as part of reset
        self.progressWidget.setVisible(False) 
        self.progressBar.setValue(0)
        # self.progressText.clear() # Or keep logs until next operation

        self.progressText.append("UI Reset. Select a folder to begin or check logs.")
        QApplication.processEvents()

    @Slot()
    def selectFolder(self):
        if self.is_operation_in_progress: return # Don't allow folder change during operation

        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folderPath = folder
            self.folderPathSelector.setText(folder)
            files = os.listdir(folder)

            is_update_scenario = False
            if INSIDER_CODE_FILE in files:
                self.isInsider = True
                is_update_scenario = True
            elif CODE_FILE in files:
                self.isInsider = False
                is_update_scenario = True
            
            self.isInsiderCheckbox.setChecked(self.isInsider) # Reflect detected version

            if is_update_scenario:
                self.installWidget.setVisible(False)
                self.updateButton.setVisible(True)
                self.progressText.setText(f"VS Code {'Insider ' if self.isInsider else ''}detected. Ready to update.")
            else:
                self.installWidget.setVisible(True)
                self.updateButton.setVisible(False)
                self.progressText.setText("No VS Code installation detected. Ready to install.")
            
            self.progressWidget.setVisible(True) # Show status message
            # self.isUpdate = is_update_scenario # Redundant if using button visibility

    @Slot()
    def toggleInsider(self):
        if self.is_operation_in_progress: return
        self.isInsider = not self.isInsider
        self.isInsiderCheckbox.setChecked(self.isInsider)

    @Slot()
    def togglePortable(self):
        if self.is_operation_in_progress: return
        self.isPortable = not self.isPortable
        self.isPortableCheckbox.setChecked(self.isPortable)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()