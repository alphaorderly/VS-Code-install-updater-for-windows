import os
import sys
import shutil
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QPushButton, QFileDialog, QHBoxLayout, QCheckBox,
                             QProgressBar, QTextEdit, QMessageBox)
from PySide6.QtCore import Slot, Qt

# Constants
INSIDER_CODE_FILE = 'Code - Insiders.exe'
CODE_FILE = 'Code.exe'
VSCODE_STABLE_URL = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-archive"
VSCODE_INSIDER_URL = "https://code.visualstudio.com/sha/download?build=insider&os=win32-x64-archive"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_state()
        self.setup_ui()
    
    def setup_window(self):
        """Configure window properties"""
        self.setWindowTitle("VS Code One-click Updater/Installer")
        self.setGeometry(100, 100, 800, 600)
    
    def setup_state(self):
        """Initialize application state variables"""
        self.folder_path = None
        self.is_insider = False
        self.is_portable = True
        self.is_operation_in_progress = False
        self.cancel_requested = False
        self.active_button = None
        self.other_button = None
        self.original_active_button_text = ""
    
    def setup_ui(self):
        """Set up the user interface components"""
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.central_widget.setLayout(self.main_layout)
        
        # Folder selector button
        self.setup_folder_selector()
        
        # Update button
        self.setup_update_button()
        
        # Install controls
        self.setup_install_widget()
        
        # Progress display
        self.setup_progress_widget()
    
    def setup_folder_selector(self):
        """Create folder selection button"""
        self.folder_path_selector = QPushButton("Select Folder")
        self.folder_path_selector.clicked.connect(self.select_folder)
        self.folder_path_selector.setFixedHeight(30)
        self.folder_path_selector.setStyleSheet("background-color: white; color: black; border-radius: 5px; padding: 5px; border: 1px solid #ccc;")
        self.main_layout.addWidget(self.folder_path_selector)
    
    def setup_update_button(self):
        """Create update button (initially hidden)"""
        self.update_button = QPushButton("Update")
        self.update_button.setFixedHeight(30)
        self.update_button.setVisible(False)
        self.update_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        self.update_button.clicked.connect(self.handle_update_button_click)
        self.main_layout.addWidget(self.update_button)
    
    def setup_install_widget(self):
        """Create install controls container and components"""
        self.install_widget = QWidget()
        self.install_widget.setVisible(False)
        
        self.install_layout = QVBoxLayout()
        self.install_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.install_layout.setContentsMargins(0, 0, 0, 0)
        self.install_layout.setSpacing(10)
        self.install_widget.setLayout(self.install_layout)
        
        # Checkbox container
        self.checkbox_layout = QHBoxLayout()
        self.checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Insider checkbox
        self.is_insider_checkbox = QCheckBox("Insider")
        self.is_insider_checkbox.setChecked(self.is_insider)
        self.is_insider_checkbox.clicked.connect(self.toggle_insider)
        
        # Portable checkbox
        self.is_portable_checkbox = QCheckBox("Portable")
        self.is_portable_checkbox.setChecked(self.is_portable)
        self.is_portable_checkbox.clicked.connect(self.toggle_portable)
        
        self.checkbox_layout.addWidget(self.is_insider_checkbox)
        self.checkbox_layout.addWidget(self.is_portable_checkbox)
        
        # Install button
        self.install_button = QPushButton("Install")
        self.install_button.setFixedHeight(30)
        self.install_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        self.install_button.clicked.connect(self.handle_install_button_click)
        
        self.install_layout.addLayout(self.checkbox_layout)
        self.install_layout.addWidget(self.install_button)
        
        self.main_layout.addWidget(self.install_widget)
    
    def setup_progress_widget(self):
        """Create progress display components"""
        self.progress_widget = QWidget()
        self.progress_layout = QVBoxLayout()
        self.progress_widget.setLayout(self.progress_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(self.progress_bar)
        
        # Progress text area
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_layout.addWidget(self.progress_text)
        
        self.main_layout.addWidget(self.progress_widget)
        self.progress_widget.setVisible(False)
    
    def handle_install_button_click(self):
        """Handle install button click event"""
        if self.is_operation_in_progress:
            self.request_cancellation()
        else:
            if not self.folder_path:
                self.show_progress_message("Please select a folder first.")
                return
            self.start_operation(is_install_operation=True)
    
    def handle_update_button_click(self):
        """Handle update button click event"""
        if self.is_operation_in_progress:
            self.request_cancellation()
        else:
            self.start_operation(is_install_operation=False)
    
    def request_cancellation(self):
        """Show confirmation dialog and handle cancellation request"""
        if self.is_operation_in_progress:
            reply = QMessageBox.warning(
                self, "Confirm Cancel",
                "Are you sure you want to cancel the current operation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_requested = True
                self.log_message("Cancellation requested by user...")
            else:
                self.log_message("Cancellation aborted by user.")
    
    def start_operation(self, is_install_operation):
        """Begin installation or update operation"""
        self.is_operation_in_progress = True
        self.cancel_requested = False
        
        # Setup UI for operation
        self.progress_widget.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_text.clear()
        
        operation_type = "Installing" if is_install_operation else "Updating"
        self.log_message(f"{operation_type} VS Code...")
        
        # Configure buttons
        if is_install_operation:
            self.active_button = self.install_button
            self.other_button = self.update_button
        else:
            self.active_button = self.update_button
            self.other_button = self.install_button
        
        self.original_active_button_text = self.active_button.text()
        self.active_button.setText("Cancel")
        
        # Disable controls during operation
        self.toggle_controls_enabled(False)
        
        # Perform operation
        success = self.perform_operation(is_install_operation)
        self.finish_operation(success)
    
    def toggle_controls_enabled(self, enabled):
        """Enable or disable UI controls"""
        self.folder_path_selector.setEnabled(enabled)
        self.is_insider_checkbox.setEnabled(enabled)
        self.is_portable_checkbox.setEnabled(enabled)
        if self.other_button:
            self.other_button.setEnabled(enabled)
    
    def perform_operation(self, is_install_operation):
        """Core download and installation logic"""
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "temp")
        
        try:
            # Prepare temp directory
            self.prepare_temp_dir(temp_dir)
            if self.cancel_requested:
                return False
            
            # Download VS Code
            temp_file = os.path.join(temp_dir, "vscode.zip")
            download_successful = self.download_vscode(temp_file)
            if not download_successful or self.cancel_requested:
                self.cleanup_temp_dir(temp_dir)
                return False
            
            # Extract archive
            extract_successful = self.extract_archive(temp_file, temp_dir)
            if not extract_successful or self.cancel_requested:
                self.cleanup_temp_dir(temp_dir)
                return False
            
            # Remove zip file
            try:
                os.remove(temp_file)
                self.log_message("Temporary zip file removed.")
            except Exception as e:
                self.log_message(f"Warning: Could not remove temporary zip file: {e}")
            
            # Move files to installation directory
            move_successful = self.move_files_to_install_dir(temp_dir)
            if not move_successful or self.cancel_requested:
                self.cleanup_temp_dir(temp_dir)
                return False
            
            # Clean up temp directory
            self.cleanup_temp_dir(temp_dir)
            if self.cancel_requested:
                return False
            
            # Create data folder for portable mode if needed
            if is_install_operation and self.is_portable:
                self.create_portable_data_folder()
                if self.cancel_requested:
                    return False
            
            self.progress_bar.setValue(100)
            self.log_message("Operation successful!")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_message(f"NETWORK ERROR: {e}. Please check your internet connection.")
            self.cleanup_temp_dir(temp_dir)
            return False
        except Exception as e:
            self.log_message(f"AN UNEXPECTED ERROR OCCURRED: {e}")
            self.cleanup_temp_dir(temp_dir)
            return False
    
    def prepare_temp_dir(self, temp_dir):
        """Create clean temporary directory"""
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.log_message(f"Notice: Could not clean up pre-existing temp directory: {e}")
        
        try:
            os.makedirs(temp_dir)
        except Exception as e:
            self.log_message(f"ERROR: Could not create temp directory: {e}")
            return False
        
        return True
    
    def download_vscode(self, temp_file):
        """Download VS Code archive"""
        self.log_message("Downloading VS Code...")
        
        # Determine download URL based on version
        download_url = VSCODE_INSIDER_URL if self.is_insider else VSCODE_STABLE_URL
        
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested:
                        self.log_message("Download cancelled.")
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((bytes_downloaded / total_size) * 50)
                            self.progress_bar.setValue(progress)
                            QApplication.processEvents()
            
            self.progress_bar.setValue(50)
            self.log_message("Download complete.")
            return True
            
        except Exception as e:
            self.log_message(f"Download error: {e}")
            return False
    
    def extract_archive(self, temp_file, temp_dir):
        """Extract downloaded archive"""
        self.log_message("Extracting files...")
        
        try:
            shutil.unpack_archive(temp_file, temp_dir)
            self.progress_bar.setValue(75)
            self.log_message("Extraction complete.")
            return True
        except Exception as e:
            self.log_message(f"EXTRACTION ERROR: {e}")
            return False
    
    def move_files_to_install_dir(self, temp_dir):
        """Move files from temp directory to installation directory"""
        self.log_message("Moving files to installation directory...")
        
        try:
            items = os.listdir(temp_dir)
            total_items = len(items)
            items_moved = 0
            
            for item in items:
                if self.cancel_requested:
                    self.log_message("File moving cancelled during operation.")
                    return False
                
                source = os.path.join(temp_dir, item)
                destination = os.path.join(self.folder_path, item)
                
                if os.path.isdir(source):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, destination)
                
                items_moved += 1
                if total_items > 0:
                    progress = 75 + int((items_moved / total_items) * 20)
                    self.progress_bar.setValue(progress)
                    QApplication.processEvents()
            
            self.progress_bar.setValue(95)
            self.log_message("File move complete.")
            return True
            
        except PermissionError as pe:
            self.log_message(f"PERMISSION ERROR during file move: {pe}. VS Code might be running or files are locked. Please close VS Code and try again.")
            return False
        except shutil.Error as se:
            self.log_message(f"FILE OPERATION ERROR during file move: {se}. Please check permissions or if VS Code is running.")
            return False
        except Exception as e:
            self.log_message(f"UNEXPECTED ERROR during file move: {e}.")
            return False
    
    def cleanup_temp_dir(self, temp_dir):
        """Remove temporary directory"""
        self.log_message("Cleaning up temporary directory...")
        
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            self.log_message("Temporary directory cleaned up.")
            return True
        except Exception as e:
            self.log_message(f"Warning: Error during final temporary directory cleanup: {e}")
            return False
    
    def create_portable_data_folder(self):
        """Create data folder for portable mode"""
        self.log_message("Creating 'data' folder for portable mode...")
        
        data_path = os.path.join(self.folder_path, "data")
        try:
            if not os.path.exists(data_path):
                os.makedirs(data_path)
            self.log_message("'data' folder created/ensured.")
            return True
        except PermissionError as e:
            self.log_message(f"Warning: PERMISSION ERROR creating 'data' folder: {e}. Check permissions.")
            return False
        except Exception as e:
            self.log_message(f"Warning: Error creating 'data' folder: {e}.")
            return False
    
    def finish_operation(self, success):
        """Complete the operation and reset UI state"""
        # Restore button states
        if self.active_button:
            self.active_button.setText(self.original_active_button_text)
        
        # Re-enable controls
        self.toggle_controls_enabled(True)
        
        # Reset operation state
        self.is_operation_in_progress = False
        self.active_button = None
        self.other_button = None
        
        if self.cancel_requested:
            self.log_message("Operation officially cancelled by user.")
            self.progress_bar.setValue(0)
        elif success:
            self.log_message("Installation/Update complete! Resetting UI.")
            self.progress_bar.setValue(100)
            self.reset_ui_to_initial_state()
        else:
            self.log_message("Operation failed. Check logs above for details.")
    
    def reset_ui_to_initial_state(self):
        """Reset UI to initial state after successful operation"""
        self.log_message("Resetting UI to initial state...")
        
        # Reset state variables
        self.folder_path = None
        self.folder_path_selector.setText("Select Folder")
        self.is_insider = False
        self.is_portable = True
        
        # Reset checkboxes
        self.is_insider_checkbox.setChecked(self.is_insider)
        self.is_portable_checkbox.setChecked(self.is_portable)
        
        # Reset visibility
        self.update_button.setVisible(False)
        self.install_widget.setVisible(False)
        self.progress_widget.setVisible(False)
        self.progress_bar.setValue(0)
        
        self.log_message("UI Reset. Select a folder to begin or check logs.")
    
    def show_progress_message(self, message):
        """Display a message in the progress area and show it"""
        self.progress_text.setText(message)
        self.progress_widget.setVisible(True)
        QApplication.processEvents()
    
    def log_message(self, message):
        """Add a log message to the progress text area"""
        self.progress_text.append(message)
        QApplication.processEvents()
    
    @Slot()
    def select_folder(self):
        """Handle folder selection button click"""
        if self.is_operation_in_progress:
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.folder_path_selector.setText(folder)
            self.detect_existing_installation(folder)
    
    def detect_existing_installation(self, folder):
        """Detect if a VS Code installation already exists in the selected folder"""
        try:
            files = os.listdir(folder)
            
            is_update_scenario = False
            if INSIDER_CODE_FILE in files:
                self.is_insider = True
                is_update_scenario = True
            elif CODE_FILE in files:
                self.is_insider = False
                is_update_scenario = True
            
            # Update checkbox to match detected version
            self.is_insider_checkbox.setChecked(self.is_insider)
            
            # Show appropriate UI based on detection
            if is_update_scenario:
                self.install_widget.setVisible(False)
                self.update_button.setVisible(True)
                self.show_progress_message(f"VS Code {'Insider ' if self.is_insider else ''}detected. Ready to update.")
            else:
                self.install_widget.setVisible(True)
                self.update_button.setVisible(False)
                self.show_progress_message("No VS Code installation detected. Ready to install.")
                
        except Exception as e:
            self.show_progress_message(f"Error reading folder contents: {e}")
    
    @Slot()
    def toggle_insider(self):
        """Toggle Insider version checkbox"""
        if self.is_operation_in_progress:
            return
        self.is_insider = not self.is_insider
        self.is_insider_checkbox.setChecked(self.is_insider)
    
    @Slot()
    def toggle_portable(self):
        """Toggle Portable mode checkbox"""
        if self.is_operation_in_progress:
            return
        self.is_portable = not self.is_portable
        self.is_portable_checkbox.setChecked(self.is_portable)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()