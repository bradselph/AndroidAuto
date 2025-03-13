import os
import time
import threading
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize, QEvent
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QListWidget, QTabWidget, QGroupBox, 
                            QLineEdit, QSpinBox, QCheckBox, QFileDialog, QMessageBox,
                            QListWidgetItem, QMenu, QAction, QSplitter, QDialog,
                            QFormLayout, QDialogButtonBox, QRadioButton, QButtonGroup)

from controllers.adb_controller import AdbController, ScreenCaptureThread
from controllers.action_recorder import ActionRecorder, ActionType
from controllers.action_player import ActionPlayer
from controllers.opencv_processor import OpenCVProcessor
from ui.screen_widget import ScreenWidget
from ui.themes import ThemeManager
from utils.config_manager import ConfigManager
from utils.logger import Logger

class AddActionDialog(QDialog):
    """Dialog for adding a new action"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Action")
        self.resize(400, 300)
        
        self.action_type = ActionType.TAP
        self.action_data = {}
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Action type selection
        type_group = QGroupBox("Action Type")
        type_layout = QVBoxLayout()
        
        self.action_group = QButtonGroup(self)
        
        # Add all action types
        for action_type in ActionType:
            radio = QRadioButton(action_type.value.capitalize())
            self.action_group.addButton(radio)
            type_layout.addWidget(radio)
            
            # Set tap as default
            if action_type == ActionType.TAP:
                radio.setChecked(True)
        
        self.action_group.buttonClicked.connect(self.on_action_type_changed)
        type_group.setLayout(type_layout)
        
        # Action parameters (will be updated based on action type)
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        
        # Setup parameters for tap (default)
        self.setup_tap_params()
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(type_group)
        layout.addWidget(self.params_group)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_action_type_changed(self, button):
        # Clear existing parameters
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        
        # Get selected action type
        action_name = button.text().lower()
        for action_type in ActionType:
            if action_type.value == action_name:
                self.action_type = action_type
                break
        
        # Setup parameters for the selected action type
        if self.action_type == ActionType.TAP:
            self.setup_tap_params()
        elif self.action_type == ActionType.SWIPE:
            self.setup_swipe_params()
        elif self.action_type == ActionType.WAIT:
            self.setup_wait_params()
        elif self.action_type == ActionType.KEY:
            self.setup_key_params()
        elif self.action_type == ActionType.TEXT:
            self.setup_text_params()
        elif self.action_type == ActionType.LONG_PRESS:
            self.setup_long_press_params()
        elif self.action_type == ActionType.TEMPLATE_MATCH:
            self.setup_template_match_params()
    
    def setup_tap_params(self):
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        
        self.params_layout.addRow("X:", self.x_spin)
        self.params_layout.addRow("Y:", self.y_spin)
    
    def setup_swipe_params(self):
        self.x1_spin = QSpinBox()
        self.x1_spin.setRange(0, 9999)
        self.y1_spin = QSpinBox()
        self.y1_spin.setRange(0, 9999)
        self.x2_spin = QSpinBox()
        self.x2_spin.setRange(0, 9999)
        self.y2_spin = QSpinBox()
        self.y2_spin.setRange(0, 9999)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(50, 5000)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" ms")
        
        self.params_layout.addRow("Start X:", self.x1_spin)
        self.params_layout.addRow("Start Y:", self.y1_spin)
        self.params_layout.addRow("End X:", self.x2_spin)
        self.params_layout.addRow("End Y:", self.y2_spin)
        self.params_layout.addRow("Duration:", self.duration_spin)
    
    def setup_wait_params(self):
        self.wait_spin = QSpinBox()
        self.wait_spin.setRange(100, 60000)
        self.wait_spin.setValue(1000)
        self.wait_spin.setSuffix(" ms")
        
        self.params_layout.addRow("Duration:", self.wait_spin)
    
    def setup_key_params(self):
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Enter keycode (e.g., 4 for BACK)")
        
        self.params_layout.addRow("Keycode:", self.key_edit)
    
    def setup_text_params(self):
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Enter text to input")
        
        self.params_layout.addRow("Text:", self.text_edit)
    
    def setup_long_press_params(self):
        self.lp_x_spin = QSpinBox()
        self.lp_x_spin.setRange(0, 9999)
        self.lp_y_spin = QSpinBox()
        self.lp_y_spin.setRange(0, 9999)
        self.lp_duration_spin = QSpinBox()
        self.lp_duration_spin.setRange(300, 5000)
        self.lp_duration_spin.setValue(500)
        self.lp_duration_spin.setSuffix(" ms")
        
        self.params_layout.addRow("X:", self.lp_x_spin)
        self.params_layout.addRow("Y:", self.lp_y_spin)
        self.params_layout.addRow("Duration:", self.lp_duration_spin)
    
    def setup_template_match_params(self):
        self.template_path_edit = QLineEdit()
        self.template_path_edit.setReadOnly(True)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_template)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.template_path_edit)
        path_layout.addWidget(self.browse_btn)
        
        self.wait_check = QCheckBox("Wait for template")
        self.wait_check.setChecked(True)
        
        self.max_wait_spin = QSpinBox()
        self.max_wait_spin.setRange(1, 60)
        self.max_wait_spin.setValue(10)
        self.max_wait_spin.setSuffix(" sec")
        
        self.tap_check = QCheckBox("Tap when found")
        self.tap_check.setChecked(True)
        
        self.params_layout.addRow("Template:", path_layout)
        self.params_layout.addRow("", self.wait_check)
        self.params_layout.addRow("Max wait:", self.max_wait_spin)
        self.params_layout.addRow("", self.tap_check)
    
    def browse_template(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Template Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if filename:
            self.template_path_edit.setText(filename)
    
    def get_action_data(self):
        """Get action type and data based on user input"""
        if self.action_type == ActionType.TAP:
            return ActionType.TAP, {
                'x': self.x_spin.value(),
                'y': self.y_spin.value()
            }
        
        elif self.action_type == ActionType.SWIPE:
            return ActionType.SWIPE, {
                'x1': self.x1_spin.value(),
                'y1': self.y1_spin.value(),
                'x2': self.x2_spin.value(),
                'y2': self.y2_spin.value(),
                'duration': self.duration_spin.value()
            }
        
        elif self.action_type == ActionType.WAIT:
            return ActionType.WAIT, {
                'duration': self.wait_spin.value()
            }
        
        elif self.action_type == ActionType.KEY:
            try:
                keycode = int(self.key_edit.text())
                return ActionType.KEY, {'keycode': keycode}
            except ValueError:
                return None, None
        
        elif self.action_type == ActionType.TEXT:
            return ActionType.TEXT, {
                'text': self.text_edit.text()
            }
        
        elif self.action_type == ActionType.LONG_PRESS:
            return ActionType.LONG_PRESS, {
                'x': self.lp_x_spin.value(),
                'y': self.lp_y_spin.value(),
                'duration': self.lp_duration_spin.value()
            }
        
        elif self.action_type == ActionType.TEMPLATE_MATCH:
            template_path = self.template_path_edit.text()
            if not template_path:
                return None, None
                
            return ActionType.TEMPLATE_MATCH, {
                'template_path': template_path,
                'wait': self.wait_check.isChecked(),
                'max_wait': self.max_wait_spin.value(),
                'tap': self.tap_check.isChecked()
            }
        
        return None, None
    
    def accept(self):
        action_type, action_data = self.get_action_data()
        if action_type is None:
            QMessageBox.warning(self, "Invalid Input", "Please fill all required fields correctly.")
            return
        
        self.action_type = action_type
        self.action_data = action_data
        super().accept()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android Automation Tool")
        self.setMinimumSize(1200, 800)
        
        # Initialize controllers
        self.adb_controller = AdbController()
        self.opencv_processor = OpenCVProcessor(self.adb_controller)
        self.action_recorder = ActionRecorder()
        self.action_player = ActionPlayer(self.adb_controller, self.opencv_processor)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Initialize logger
        self.logger = Logger()
        
        # State variables
        self.capture_thread = None
        self.is_recording = False
        self.is_playing = False
        self.is_connected = False
        self.last_coord = None
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize UI
        self.init_ui()
        
        # Load configuration
        self.load_config()
        
        # Connect signals
        self.connect_signals()
        
        # Set initial theme
        self.apply_theme(self.theme_combo.currentText())
        
        # Start timers
        self.init_timers()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget with layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout with splitter
        main_layout = QHBoxLayout(self.central_widget)
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Control panel (left side)
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)
        
        # Device connection group
        self.init_device_group()
        
        # Recording controls group
        self.init_recording_group()
        
        # Playback controls group
        self.init_playback_group()
        
        # Settings group
        self.init_settings_group()
        
        # Add stretch to push groups to the top
        self.control_layout.addStretch()
        
        # Right panel with vertical splitter
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_layout.addWidget(self.right_splitter)
        
        # Screen display area
        self.init_screen_display()
        
        # Tabs for actions, templates, logs
        self.init_tabs()
        
        # Add panels to main splitter
        self.main_splitter.addWidget(self.control_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([300, 900])
        self.right_splitter.setSizes([600, 200])
    
    def init_device_group(self):
        """Initialize device connection group"""
        device_group = QGroupBox("Device Connection")
        device_layout = QVBoxLayout()
        
        # Device selection
        device_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.connect_btn = QPushButton("Connect")
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.connect_btn)
        
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        device_layout.addLayout(buttons_layout)
        
        device_group.setLayout(device_layout)
        self.control_layout.addWidget(device_group)
    
    def init_recording_group(self):
        """Initialize recording controls group"""
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        # Recording buttons
        self.record_btn = QPushButton("Start Recording")
        self.stop_record_btn = QPushButton("Stop Recording")
        recording_layout.addWidget(self.record_btn)
        recording_layout.addWidget(self.stop_record_btn)
        
        # Add action button
        self.add_action_btn = QPushButton("Add Action")
        recording_layout.addWidget(self.add_action_btn)
        
        # Save/load buttons
        buttons_layout = QHBoxLayout()
        self.save_recording_btn = QPushButton("Save")
        self.load_recording_btn = QPushButton("Load")
        buttons_layout.addWidget(self.save_recording_btn)
        buttons_layout.addWidget(self.load_recording_btn)
        recording_layout.addLayout(buttons_layout)
        
        recording_group.setLayout(recording_layout)
        self.control_layout.addWidget(recording_group)
    
    def init_playback_group(self):
        """Initialize playback controls group"""
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout()
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(10, 500)
        self.speed_spin.setValue(100)
        self.speed_spin.setSuffix("%")
        speed_layout.addWidget(self.speed_spin)
        
        # Playback buttons
        buttons_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_play_btn = QPushButton("Stop")
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.stop_play_btn)
        
        # Loop playback
        self.loop_check = QCheckBox("Loop playback")
        
        playback_layout.addLayout(speed_layout)
        playback_layout.addLayout(buttons_layout)
        playback_layout.addWidget(self.loop_check)
        
        playback_group.setLayout(playback_layout)
        self.control_layout.addWidget(playback_group)
    
    def init_settings_group(self):
        """Initialize settings group"""
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addWidget(self.theme_combo)
        
        # OpenCV processing
        self.opencv_check = QCheckBox("Enable OpenCV Processing")
        self.opencv_check.setChecked(True)
        
        # Capture interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Capture Interval:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 2000)
        self.interval_spin.setValue(200)
        self.interval_spin.setSuffix(" ms")
        interval_layout.addWidget(self.interval_spin)
        
        settings_layout.addLayout(theme_layout)
        settings_layout.addWidget(self.opencv_check)
        settings_layout.addLayout(interval_layout)
        
        settings_group.setLayout(settings_layout)
        self.control_layout.addWidget(settings_group)
    
    def init_screen_display(self):
        """Initialize screen display area"""
        display_group = QGroupBox("Device Screen")
        display_layout = QVBoxLayout()
        
        # Custom screen widget for handling mouse events
        self.screen_widget = ScreenWidget(self.adb_controller)
        
        display_layout.addWidget(self.screen_widget)
        display_group.setLayout(display_layout)
        
        self.right_splitter.addWidget(display_group)
    
    def init_tabs(self):
        """Initialize tabs for actions, templates, logs"""
        self.tabs = QTabWidget()
        
        # Actions tab
        self.actions_tab = QWidget()
        actions_layout = QVBoxLayout()
        
        self.actions_list = QListWidget()
        self.actions_list.setContextMenuPolicy(Qt.CustomContextMenu)
        
        actions_layout.addWidget(QLabel("Recorded Actions:"))
        actions_layout.addWidget(self.actions_list)
        
        action_buttons_layout = QHBoxLayout()
        self.clear_actions_btn = QPushButton("Clear All")
        self.edit_action_btn = QPushButton("Edit Selected")
        self.remove_action_btn = QPushButton("Remove Selected")
        action_buttons_layout.addWidget(self.clear_actions_btn)
        action_buttons_layout.addWidget(self.edit_action_btn)
        action_buttons_layout.addWidget(self.remove_action_btn)
        
        actions_layout.addLayout(action_buttons_layout)
        self.actions_tab.setLayout(actions_layout)
        
        # Templates tab
        self.templates_tab = QWidget()
        templates_layout = QVBoxLayout()
        
        self.templates_list = QListWidget()
        self.templates_list.setContextMenuPolicy(Qt.CustomContextMenu)
        
        templates_layout.addWidget(QLabel("Saved Templates:"))
        templates_layout.addWidget(self.templates_list)
        
        template_buttons_layout = QHBoxLayout()
        self.create_template_btn = QPushButton("Create New")
        self.remove_template_btn = QPushButton("Remove")
        template_buttons_layout.addWidget(self.create_template_btn)
        template_buttons_layout.addWidget(self.remove_template_btn)
        
        templates_layout.addLayout(template_buttons_layout)
        self.templates_tab.setLayout(templates_layout)
        
        # Logs tab
        self.logs_tab = QWidget()
        logs_layout = QVBoxLayout()
        
        self.logs_list = QListWidget()
        
        logs_layout.addWidget(QLabel("Application Logs:"))
        logs_layout.addWidget(self.logs_list)
        
        logs_buttons_layout = QHBoxLayout()
        self.clear_logs_btn = QPushButton("Clear Logs")
        logs_buttons_layout.addWidget(self.clear_logs_btn)
        
        logs_layout.addLayout(logs_buttons_layout)
        self.logs_tab.setLayout(logs_layout)
        
        # Add tabs
        self.tabs.addTab(self.actions_tab, "Actions")
        self.tabs.addTab(self.templates_tab, "Templates")
        self.tabs.addTab(self.logs_tab, "Logs")
        
        self.right_splitter.addWidget(self.tabs)
    
    def init_timers(self):
        """Initialize timers"""
        # Timer for updating UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(500)  # Update every 500ms
    
    def connect_signals(self):
        """Connect signals to slots"""
        # Device connection
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.connect_btn.clicked.connect(self.connect_device)
        
        # Recording
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.add_action_btn.clicked.connect(self.add_action)
        self.save_recording_btn.clicked.connect(self.save_recording)
        self.load_recording_btn.clicked.connect(self.load_recording)
        
        # Playback
        self.play_btn.clicked.connect(self.play_actions)
        self.stop_play_btn.clicked.connect(self.stop_playback)
        
        # Action list
        self.actions_list.customContextMenuRequested.connect(self.show_actions_context_menu)
        self.clear_actions_btn.clicked.connect(self.clear_actions)
        self.edit_action_btn.clicked.connect(self.edit_selected_action)
        self.remove_action_btn.clicked.connect(self.remove_selected_action)
        
        # Templates
        self.templates_list.customContextMenuRequested.connect(self.show_templates_context_menu)
        self.create_template_btn.clicked.connect(self.create_template)
        self.remove_template_btn.clicked.connect(self.remove_template)
        
        # Logs
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        
        # Settings
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.opencv_check.stateChanged.connect(self.toggle_opencv)
        
        # Screen widget
        self.screen_widget.tap_event.connect(self.on_screen_tap)
        self.screen_widget.swipe_event.connect(self.on_screen_swipe)
        self.screen_widget.long_press_event.connect(self.on_screen_long_press)
        
        # Action player
        self.action_player.playback_started.connect(lambda: self.log("Playback started"))
        self.action_player.playback_completed.connect(lambda: self.log("Playback completed"))
        self.action_player.playback_error.connect(self.log)
        self.action_player.action_started.connect(self.on_action_started)
        self.action_player.action_completed.connect(self.on_action_completed)
    
    def refresh_devices(self):
        """Refresh list of connected devices"""
        self.device_combo.clear()
        devices = self.adb_controller.get_devices()
        self.device_combo.addItems(devices)
        
        if devices:
            self.log(f"Found {len(devices)} device(s)")
        else:
            self.log("No devices found")
    
    def connect_device(self):
        """Connect to selected device"""
        if not self.device_combo.currentText():
            self.log("No device selected")
            return
        
        # If already connected, disconnect first
        if self.is_connected:
            self.disconnect_device()
        
        device_id = self.device_combo.currentText()
        self.adb_controller.device_id = device_id
        
        # Start screen capture thread
        try:
            if self.capture_thread and self.capture_thread.isRunning():
                self.capture_thread.stop()
                self.capture_thread.wait()
            
            self.capture_thread = ScreenCaptureThread(
                self.adb_controller, 
                self.interval_spin.value() / 1000.0
            )
            self.capture_thread.update_frame.connect(self.on_frame_update)
            self.capture_thread.error.connect(self.log)
            self.capture_thread.start()
            
            self.is_connected = True
            self.log(f"Connected to device: {device_id}")
            
            # Get device dimensions
            width, height = self.adb_controller.get_device_dimensions()
            if width and height:
                self.log(f"Device screen size: {width}x{height}")
                self.screen_widget.set_device_dimensions(width, height)
        
        except Exception as e:
            self.log(f"Error connecting to device: {str(e)}")
    
    def disconnect_device(self):
        """Disconnect from current device"""
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread.wait()
        
        self.adb_controller.device_id = None
        self.is_connected = False
        self.screen_widget.clear()
        self.log("Disconnected from device")
    
    def on_frame_update(self, frame):
        """Handle new frame from capture thread"""
        # Process with OpenCV if enabled
        if self.opencv_check.isChecked():
            frame = self.opencv_processor.process_frame(frame)
        
        # Update screen display
        self.screen_widget.update_frame(frame)
    
    def start_recording(self):
        """Start recording actions"""
        if not self.is_connected:
            self.log("Cannot start recording: No device connected")
            return
        
        self.action_recorder.start_recording()
        self.is_recording = True
        self.log("Recording started")
    
    def stop_recording(self):
        """Stop recording actions"""
        if not self.is_recording:
            return
            
        self.action_recorder.stop_recording()
        self.is_recording = False
        self.log("Recording stopped")
        
        # Update actions list
        self.update_actions_list()
    
    def add_action(self):
        """Add a custom action"""
        dialog = AddActionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            action_type = dialog.action_type
            action_data = dialog.action_data
            
            # Add action to recorder
            action_index = self.action_recorder.add_action(action_type, action_data)
            if action_index >= 0:
                self.log(f"Added action: {action_type.value}")
                self.update_actions_list()
    
    def save_recording(self):
        """Save recorded actions to file"""
        if not self.action_recorder.actions:
            self.log("No actions to save")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Actions", "", "JSON Files (*.json)"
        )
        if filename:
            if self.action_recorder.save_actions(filename):
                self.log(f"Saved {len(self.action_recorder.actions)} actions to {filename}")
            else:
                self.log(f"Failed to save actions to {filename}")
    
    def load_recording(self):
        """Load actions from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Actions", "", "JSON Files (*.json)"
        )
        if filename:
            if self.action_recorder.load_actions(filename):
                self.action_player.load_actions(self.action_recorder.actions)
                self.update_actions_list()
                self.log(f"Loaded {len(self.action_recorder.actions)} actions from {filename}")
            else:
                self.log(f"Failed to load actions from {filename}")
    
    def play_actions(self):
        """Play recorded actions"""
        if not self.action_recorder.actions:
            self.log("No actions to play")
            return
        
        if not self.is_connected:
            self.log("Cannot play actions: No device connected")
            return
        
        self.action_player.load_actions(self.action_recorder.actions)
        speed_factor = self.speed_spin.value() / 100.0
        
        # Start playback in action player
        if self.action_player.play(speed_factor):
            self.is_playing = True
            self.log(f"Playing {len(self.action_recorder.actions)} actions at {speed_factor}x speed")
        else:
            self.log("Failed to start playback")
    
    def stop_playback(self):
        """Stop action playback"""
        if self.action_player.stop():
            self.is_playing = False
            self.log("Playback stopped")
    
    def on_screen_tap(self, x, y, device_x, device_y):
        """Handle tap on screen widget"""
        if self.is_recording:
            # Add tap action to recorder
            self.action_recorder.add_tap(device_x, device_y)
            self.log(f"Recorded tap at ({device_x}, {device_y})")
        
        # Send tap to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.tap(device_x, device_y)
    
    def on_screen_swipe(self, start_x, start_y, end_x, end_y, device_start_x, device_start_y, device_end_x, device_end_y, duration):
        """Handle swipe on screen widget"""
        if self.is_recording:
            # Add swipe action to recorder
            self.action_recorder.add_swipe(device_start_x, device_start_y, device_end_x, device_end_y, duration)
            self.log(f"Recorded swipe from ({device_start_x}, {device_start_y}) to ({device_end_x}, {device_end_y})")
        
        # Send swipe to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.swipe(device_start_x, device_start_y, device_end_x, device_end_y, duration)
    
    def on_screen_long_press(self, x, y, device_x, device_y, duration):
        """Handle long press on screen widget"""
        if self.is_recording:
            # Add long press action to recorder
            self.action_recorder.add_long_press(device_x, device_y, duration)
            self.log(f"Recorded long press at ({device_x}, {device_y}) for {duration}ms")
        
        # Send long press to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.long_press(device_x, device_y, duration)
    
    def on_action_started(self, index, action):
        """Handle action playback start"""
        # Highlight the action in the list
        if 0 <= index < self.actions_list.count():
            self.actions_list.setCurrentRow(index)
            
            # Log the action
            action_type = action.get('type', '')
            self.log(f"Executing: {self.action_recorder.get_action_description(action)}")
    
    def on_action_completed(self, index):
        """Handle action playback completion"""
        pass
    
    def update_actions_list(self):
        """Update the actions list widget"""
        self.actions_list.clear()
        
        for action in self.action_recorder.actions:
            description = self.action_recorder.get_action_description(action)
            self.actions_list.addItem(description)
    
    def clear_actions(self):
        """Clear all recorded actions"""
        if not self.action_recorder.actions:
            return
            
        reply = QMessageBox.question(
            self, "Clear Actions", 
            "Are you sure you want to clear all actions?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.action_recorder.clear_actions()
            self.actions_list.clear()
            self.log("All actions cleared")
    
    def edit_selected_action(self):
        """Edit the selected action"""
        selected_items = self.actions_list.selectedItems()
        if not selected_items:
            self.log("No action selected")
            return
        
        selected_index = self.actions_list.row(selected_items[0])
        if selected_index < 0 or selected_index >= len(self.action_recorder.actions):
            return
        
        # Get the action to edit
        action = self.action_recorder.actions[selected_index]
        action_type_str = action.get('type', '')
        action_data = action.get('data', {})
        
        # Find the corresponding ActionType
        action_type = None
        for at in ActionType:
            if at.value == action_type_str:
                action_type = at
                break
        
        if action_type is None:
            self.log(f"Unknown action type: {action_type_str}")
            return
        
        # Create and configure the edit dialog
        dialog = AddActionDialog(self)
        
        # Set the dialog to show the action type
        for button in dialog.action_group.buttons():
            if button.text().lower() == action_type_str:
                button.setChecked(True)
                dialog.on_action_type_changed(button)  # Update params
                break
        
        # Set the dialog fields based on action data
        if action_type == ActionType.TAP:
            dialog.x_spin.setValue(action_data.get('x', 0))
            dialog.y_spin.setValue(action_data.get('y', 0))
        
        elif action_type == ActionType.SWIPE:
            dialog.x1_spin.setValue(action_data.get('x1', 0))
            dialog.y1_spin.setValue(action_data.get('y1', 0))
            dialog.x2_spin.setValue(action_data.get('x2', 0))
            dialog.y2_spin.setValue(action_data.get('y2', 0))
            dialog.duration_spin.setValue(action_data.get('duration', 300))
        
        elif action_type == ActionType.WAIT:
            dialog.wait_spin.setValue(action_data.get('duration', 1000))
        
        elif action_type == ActionType.KEY:
            dialog.key_edit.setText(str(action_data.get('keycode', '')))
        
        elif action_type == ActionType.TEXT:
            dialog.text_edit.setText(action_data.get('text', ''))
        
        elif action_type == ActionType.LONG_PRESS:
            dialog.lp_x_spin.setValue(action_data.get('x', 0))
            dialog.lp_y_spin.setValue(action_data.get('y', 0))
            dialog.lp_duration_spin.setValue(action_data.get('duration', 500))
        
        elif action_type == ActionType.TEMPLATE_MATCH:
            dialog.template_path_edit.setText(action_data.get('template_path', ''))
            dialog.wait_check.setChecked(action_data.get('wait', True))
            dialog.max_wait_spin.setValue(action_data.get('max_wait', 10))
            dialog.tap_check.setChecked(action_data.get('tap', True))
        
        # Show the dialog
        if dialog.exec_() == QDialog.Accepted:
            new_action_type = dialog.action_type
            new_action_data = dialog.action_data
            
            # Update the action
            self.action_recorder.actions[selected_index] = {
                'type': new_action_type.value,
                'data': new_action_data,
                'timestamp': action.get('timestamp', time.time()),
                'time_offset': action.get('time_offset', 0)
            }
            
            self.update_actions_list()
            self.log(f"Action {selected_index} updated")
    
    def remove_selected_action(self):
        """Remove the selected action"""
        selected_items = self.actions_list.selectedItems()
        if not selected_items:
            self.log("No action selected")
            return
        
        selected_index = self.actions_list.row(selected_items[0])
        if self.action_recorder.remove_action(selected_index):
            self.update_actions_list()
            self.log(f"Removed action at index {selected_index}")
    
    def show_actions_context_menu(self, position):
        """Show context menu for actions list"""
        menu = QMenu()
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.edit_selected_action)
        
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_action)
        
        menu.addAction(edit_action)
        menu.addAction(remove_action)
        
        if self.actions_list.count() > 0:
            menu.exec_(self.actions_list.mapToGlobal(position))
    
    def create_template(self):
        """Create a new template from screen selection"""
        if not self.is_connected or self.screen_widget.selected_region is None:
            self.log("Select a region on the screen first")
            return
        
        # Get selected region
        region = self.screen_widget.selected_region
        device_region = self.screen_widget.get_device_coordinates_rect(region)
        
        # Prompt for template name
        template_name, ok = QFileDialog.getSaveFileName(
            self, "Save Template", self.templates_dir, "PNG Files (*.png)"
        )
        
        if ok and template_name:
            # Create the template
            if self.opencv_processor.create_template(device_region, template_name):
                self.log(f"Template created: {os.path.basename(template_name)}")
                self.refresh_templates()
            else:
                self.log("Failed to create template")
    
    def remove_template(self):
        """Remove selected template"""
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            self.log("No template selected")
            return
        
        template_name = selected_items[0].text()
        template_path = os.path.join(self.templates_dir, template_name)
        
        try:
            if os.path.exists(template_path):
                os.remove(template_path)
                self.refresh_templates()
                self.log(f"Template removed: {template_name}")
            else:
                self.log(f"Template not found: {template_name}")
        except Exception as e:
            self.log(f"Error removing template: {str(e)}")
    
    def refresh_templates(self):
        """Refresh templates list"""
        self.templates_list.clear()
        
        if os.path.exists(self.templates_dir):
            templates = [f for f in os.listdir(self.templates_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            for template in templates:
                self.templates_list.addItem(template)
    
    def show_templates_context_menu(self, position):
        """Show context menu for templates list"""
        menu = QMenu()
        
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_template)
        
        use_action = QAction("Use in Action", self)
        use_action.triggered.connect(self.use_template_in_action)
        
        menu.addAction(use_action)
        menu.addAction(remove_action)
        
        if self.templates_list.count() > 0:
            menu.exec_(self.templates_list.mapToGlobal(position))
    
    def use_template_in_action(self):
        """Add a template matching action using the selected template"""
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            self.log("No template selected")
            return
        
        template_name = selected_items[0].text()
        template_path = os.path.join(self.templates_dir, template_name)
        
        if os.path.exists(template_path):
            # Create a dialog to configure the template action
            dialog = AddActionDialog(self)
            
            # Find and select the template_match radio button
            for button in dialog.action_group.buttons():
                if button.text().lower() == ActionType.TEMPLATE_MATCH.value:
                    button.setChecked(True)
                    dialog.on_action_type_changed(button)
                    break
            
            # Set the template path
            dialog.template_path_edit.setText(template_path)
            
            if dialog.exec_() == QDialog.Accepted:
                action_type = dialog.action_type
                action_data = dialog.action_data
                
                # Add action to recorder
                action_index = self.action_recorder.add_action(action_type, action_data)
                if action_index >= 0:
                    self.log(f"Added template action: {template_name}")
                    self.update_actions_list()
    
    def clear_logs(self):
        """Clear the logs list"""
        self.logs_list.clear()
    
    def log(self, message):
        """Add a message to the logs"""
        if isinstance(message, str):
            timestamp = time.strftime("%H:%M:%S")
            self.logs_list.addItem(f"[{timestamp}] {message}")
            self.logs_list.scrollToBottom()
            
            # Also write to logger
            self.logger.log(message)
    
    def apply_theme(self, theme_name):
        """Apply the selected theme"""
        self.theme_manager.apply_theme(self, theme_name)
    
    def toggle_opencv(self, state):
        """Toggle OpenCV processing"""
        enabled = state == Qt.Checked
        self.screen_widget.set_opencv_enabled(enabled)
    
    def load_config(self):
        """Load application configuration"""
        config = self.config_manager.load_config()
        
        # Apply configuration
        if config:
            if 'theme' in config and config['theme'] in ["Light", "Dark", "System"]:
                self.theme_combo.setCurrentText(config['theme'])
            
            if 'capture_interval' in config:
                self.interval_spin.setValue(config['capture_interval'])
            
            if 'opencv_enabled' in config:
                self.opencv_check.setChecked(config['opencv_enabled'])
            
            if 'templates_dir' in config and os.path.exists(config['templates_dir']):
                self.templates_dir = config['templates_dir']
            
            self.refresh_templates()
    
    def save_config(self):
        """Save application configuration"""
        config = {
            'theme': self.theme_combo.currentText(),
            'capture_interval': self.interval_spin.value(),
            'opencv_enabled': self.opencv_check.isChecked(),
            'templates_dir': self.templates_dir
        }
        
        self.config_manager.save_config(config)
    
    def update_ui_state(self):
        """Update UI based on current state"""
        # Connection state
        connected = self.is_connected
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        
        # Recording state
        recording = self.is_recording
        self.record_btn.setEnabled(connected and not recording and not self.is_playing)
        self.stop_record_btn.setEnabled(connected and recording)
        self.add_action_btn.setEnabled(not recording and not self.is_playing)
        
        # Playback state
        playing = self.is_playing
        self.play_btn.setEnabled(connected and not recording and not playing and len(self.action_recorder.actions) > 0)
        self.stop_play_btn.setEnabled(connected and playing)
        
        # Action editing
        has_actions = len(self.action_recorder.actions) > 0
        self.save_recording_btn.setEnabled(has_actions and not recording and not playing)
        self.load_recording_btn.setEnabled(not recording and not playing)
        self.clear_actions_btn.setEnabled(has_actions and not recording and not playing)
        
        has_selection = len(self.actions_list.selectedItems()) > 0
        self.edit_action_btn.setEnabled(has_selection and not recording and not playing)
        self.remove_action_btn.setEnabled(has_selection and not recording and not playing)
        
        # Template management
        has_region = self.screen_widget.selected_region is not None
        self.create_template_btn.setEnabled(connected and has_region)
        
        has_template = len(self.templates_list.selectedItems()) > 0
        self.remove_template_btn.setEnabled(has_template)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop any running threads
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread.wait()
        
        # Stop playback
        if self.is_playing:
            self.action_player.stop()
        
        # Save configuration
        self.save_config()
        
        # Accept the event
        event.accept()