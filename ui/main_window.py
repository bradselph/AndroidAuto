import os
import time
import threading
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize, QEvent, QDateTime, QTime
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QColor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QListWidget, QTabWidget, QGroupBox, 
                            QLineEdit, QSpinBox, QCheckBox, QFileDialog, QMessageBox,
                            QListWidgetItem, QMenu, QAction, QSplitter, QDialog,
                            QFormLayout, QDialogButtonBox, QRadioButton, QButtonGroup,
                            QDateTimeEdit, QTimeEdit, QDoubleSpinBox)
from controllers.adb_controller import AdbController, ScreenCaptureThread, DeviceManager
from controllers.action_recorder import ActionRecorder, ActionType
from controllers.action_player import ActionPlayer
from controllers.opencv_processor import OpenCVProcessor
from controllers.scheduler import TaskScheduler, ScheduleType
from controllers.condition_checker import ConditionChecker, ConditionType
from ui.screen_widget import ScreenWidget
from ui.themes import ThemeManager
from utils.config_manager import ConfigManager
from utils.logger import Logger

class AddActionDialog(QDialog):

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

    def __init__(self, config_manager=None, driver_manager=None):
        super().__init__()
        self.setWindowTitle("Android Automation Tool")
        self.setMinimumSize(1200, 800)
        
        # Initialize managers
        self.config_manager = config_manager or ConfigManager()
        self.driver_manager = driver_manager or DriverManager(self.config_manager)

        # Initialize controllers
        adb_path = self.driver_manager.get_adb_path()
        self.adb_controller = AdbController(None)
        self.adb_controller.adb_path = adb_path
        self.device_manager = DeviceManager(self.driver_manager)
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

        # Check for drivers
        self.check_drivers()

        self.task_scheduler = TaskScheduler(self.action_player, self.logger)
        self.task_scheduler.start()

        # Update UI
        self.refresh_devices()
        self.update_scheduled_tasks_list()

    def init_ui(self):
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
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        # Recording buttons
        self.record_btn = QPushButton("Start Recording")
        self.stop_record_btn = QPushButton("Stop Recording")
        recording_layout.addWidget(self.record_btn)
        recording_layout.addWidget(self.stop_record_btn)
        
        # Add action buttons
        action_buttons_layout = QHBoxLayout()
        self.add_action_btn = QPushButton("Add Action")
        self.add_conditional_btn = QPushButton("Add Conditional")
        action_buttons_layout.addWidget(self.add_action_btn)
        action_buttons_layout.addWidget(self.add_conditional_btn)
        recording_layout.addLayout(action_buttons_layout)

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
        
        # Action delay control
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Action Delay:"))
        self.action_delay_spin = QSpinBox()
        self.action_delay_spin.setRange(0, 5000)
        self.action_delay_spin.setValue(0)
        self.action_delay_spin.setSuffix(" ms")
        delay_layout.addWidget(self.action_delay_spin)

        # Playback buttons
        buttons_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_play_btn = QPushButton("Stop")
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.stop_play_btn)
        
        # Loop playback
        self.loop_check = QCheckBox("Loop playback")
        
        playback_layout.addLayout(speed_layout)
        playback_layout.addLayout(delay_layout)
        playback_layout.addLayout(buttons_layout)
        playback_layout.addWidget(self.loop_check)

        playback_group.setLayout(playback_layout)
        self.control_layout.addWidget(playback_group)

    def init_settings_group(self):
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
        self.interval_spin.setRange(10, 2000)
        self.interval_spin.setValue(200)
        self.interval_spin.setSuffix(" ms")
        interval_layout.addWidget(self.interval_spin)
        
        settings_layout.addLayout(theme_layout)
        settings_layout.addWidget(self.opencv_check)
        settings_layout.addLayout(interval_layout)
        
        settings_group.setLayout(settings_layout)
        self.control_layout.addWidget(settings_group)
    
    def init_screen_display(self):
        display_group = QGroupBox("Device Screen")
        display_layout = QVBoxLayout()
        
        # Custom screen widget for handling mouse events
        self.screen_widget = ScreenWidget(self.adb_controller)
        
        display_layout.addWidget(self.screen_widget)
        display_group.setLayout(display_layout)
        
        self.right_splitter.addWidget(display_group)
    
    def init_tabs(self):
        self.tabs = QTabWidget()
        
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

        self.scheduler_tab = QWidget()
        scheduler_layout = QVBoxLayout()

        self.scheduled_tasks_list = QListWidget()
        self.scheduled_tasks_list.setContextMenuPolicy(Qt.CustomContextMenu)

        scheduler_layout.addWidget(QLabel("Scheduled Tasks:"))
        scheduler_layout.addWidget(self.scheduled_tasks_list)

        scheduler_buttons_layout = QHBoxLayout()
        self.add_scheduled_task_btn = QPushButton("Add Task")
        self.remove_scheduled_task_btn = QPushButton("Remove Task")
        self.enable_task_btn = QPushButton("Enable/Disable")
        scheduler_buttons_layout.addWidget(self.add_scheduled_task_btn)
        scheduler_buttons_layout.addWidget(self.remove_scheduled_task_btn)
        scheduler_buttons_layout.addWidget(self.enable_task_btn)

        scheduler_layout.addLayout(scheduler_buttons_layout)
        self.scheduler_tab.setLayout(scheduler_layout)

        self.tabs.addTab(self.scheduler_tab, "Scheduler")

        self.tabs.addTab(self.actions_tab, "Actions")
        self.tabs.addTab(self.templates_tab, "Templates")
        self.tabs.addTab(self.logs_tab, "Logs")
        
        self.right_splitter.addWidget(self.tabs)
    
    def init_timers(self):
        # Timer for updating UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(500)  # Update every 500ms
    
    def connect_signals(self):
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

        # Conditional action
        self.add_conditional_btn.clicked.connect(self.add_conditional_action)

        # Scheduler buttons
        self.add_scheduled_task_btn.clicked.connect(self.add_scheduled_task)
        self.remove_scheduled_task_btn.clicked.connect(self.remove_scheduled_task)
        self.enable_task_btn.clicked.connect(self.toggle_scheduled_task)


    def refresh_devices(self):
        self.device_combo.clear()
        devices = self.adb_controller.get_devices()
        self.device_combo.addItems(devices)
        
        if devices:
            self.log(f"Found {len(devices)} device(s)")
        else:
            self.log("No devices found")
    
    def connect_device(self):
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

    def check_drivers(self):
        driver_status = self.driver_manager.check_drivers()

        if not driver_status['adb']:
            reply = QMessageBox.question(
                    self, "ADB Not Found",
                    "ADB platform tools are not found in the drivers directory. Would you like to download them now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.log("Downloading ADB platform tools...")
                success, message = self.driver_manager.download_adb()
                self.log(message)

                if success:
                    adb_path = self.driver_manager.get_adb_path()
                    self.adb_controller.adb_path = adb_path
                    self.device_manager.adb_path = adb_path

        if not driver_status['scrcpy']:
            reply = QMessageBox.question(
                    self, "scrcpy Not Found",
                    "scrcpy is not found in the drivers directory. Would you like to download it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.log("Downloading scrcpy...")
                success, message = self.driver_manager.download_scrcpy()
                self.log(message)

    def disconnect_device(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread.wait()
        
        self.adb_controller.device_id = None
        self.is_connected = False
        self.screen_widget.clear()
        self.log("Disconnected from device")
    
    def on_frame_update(self, frame):
        # Process with OpenCV if enabled
        if self.opencv_check.isChecked():
            frame = self.opencv_processor.process_frame(frame)
        
        # Update screen display
        self.screen_widget.update_frame(frame)
    
    def start_recording(self):
        if not self.is_connected:
            self.log("Cannot start recording: No device connected")
            return
        
        self.action_recorder.start_recording()
        self.is_recording = True
        self.log("Recording started")
    
    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.action_recorder.stop_recording()
        self.is_recording = False
        self.log("Recording stopped")
        
        # Update actions list
        self.update_actions_list()
    
    def add_action(self):
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
        if self.action_player.stop():
            self.is_playing = False
            self.log("Playback stopped")
    
    def on_screen_tap(self, x, y, device_x, device_y):
        if self.is_recording:
            # Add tap action to recorder
            self.action_recorder.add_tap(device_x, device_y)
            self.log(f"Recorded tap at ({device_x}, {device_y})")
        
        # Send tap to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.tap(device_x, device_y)
    
    def on_screen_swipe(self, start_x, start_y, end_x, end_y, device_start_x, device_start_y, device_end_x, device_end_y, duration):
        if self.is_recording:
            # Add swipe action to recorder
            self.action_recorder.add_swipe(device_start_x, device_start_y, device_end_x, device_end_y, duration)
            self.log(f"Recorded swipe from ({device_start_x}, {device_start_y}) to ({device_end_x}, {device_end_y})")
        
        # Send swipe to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.swipe(device_start_x, device_start_y, device_end_x, device_end_y, duration)
    
    def on_screen_long_press(self, x, y, device_x, device_y, duration):
        if self.is_recording:
            # Add long press action to recorder
            self.action_recorder.add_long_press(device_x, device_y, duration)
            self.log(f"Recorded long press at ({device_x}, {device_y}) for {duration}ms")
        
        # Send long press to device if connected
        if self.is_connected and not self.is_playing:
            self.adb_controller.long_press(device_x, device_y, duration)
    
    def on_action_started(self, index, action):
        if 0 <= index < self.actions_list.count():
            self.actions_list.setCurrentRow(index)
            
            # Log the action
            action_type = action.get('type', '')
            self.log(f"Executing: {self.action_recorder.get_action_description(action)}")
    
    def on_action_completed(self, index):
        pass
    
    def update_actions_list(self):
        self.actions_list.clear()
        
        for action in self.action_recorder.actions:
            description = self.action_recorder.get_action_description(action)
            self.actions_list.addItem(description)
    
    def clear_actions(self):
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
        selected_items = self.actions_list.selectedItems()
        if not selected_items:
            self.log("No action selected")
            return
        
        selected_index = self.actions_list.row(selected_items[0])
        if self.action_recorder.remove_action(selected_index):
            self.update_actions_list()
            self.log(f"Removed action at index {selected_index}")
    
    def show_actions_context_menu(self, position):
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
        if not self.is_connected or self.screen_widget.selected_region is None:
            self.log("Select a region on the screen first")
            return

        region = self.screen_widget.selected_region
        device_region = self.screen_widget.get_device_coordinates_rect(region)
        
        template_name, ok = QFileDialog.getSaveFileName(
            self, "Save Template", self.templates_dir, "PNG Files (*.png)"
        )
        
        if ok and template_name:
            if self.opencv_processor.create_template(device_region, template_name):
                self.log(f"Template created: {os.path.basename(template_name)}")
                self.refresh_templates()
            else:
                self.log("Failed to create template")
    
    def remove_template(self):
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
        self.templates_list.clear()
        
        if os.path.exists(self.templates_dir):
            templates = [f for f in os.listdir(self.templates_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            for template in templates:
                self.templates_list.addItem(template)
    
    def show_templates_context_menu(self, position):
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
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            self.log("No template selected")
            return
        
        template_name = selected_items[0].text()
        template_path = os.path.join(self.templates_dir, template_name)
        
        if os.path.exists(template_path):
            dialog = AddActionDialog(self)
            
            for button in dialog.action_group.buttons():
                if button.text().lower() == ActionType.TEMPLATE_MATCH.value:
                    button.setChecked(True)
                    dialog.on_action_type_changed(button)
                    break
            
            dialog.template_path_edit.setText(template_path)
            
            if dialog.exec_() == QDialog.Accepted:
                action_type = dialog.action_type
                action_data = dialog.action_data
                
                action_index = self.action_recorder.add_action(action_type, action_data)
                if action_index >= 0:
                    self.log(f"Added template action: {template_name}")
                    self.update_actions_list()
    
    def clear_logs(self):
        self.logs_list.clear()
    
    def log(self, message):
        if isinstance(message, str):
            timestamp = time.strftime("%H:%M:%S")
            self.logs_list.addItem(f"[{timestamp}] {message}")
            self.logs_list.scrollToBottom()
            
            self.logger.log(message)
    
    def apply_theme(self, theme_name):
        self.theme_manager.apply_theme(self, theme_name)
    
    def toggle_opencv(self, state):
        enabled = state == Qt.Checked
        self.screen_widget.set_opencv_enabled(enabled)
    
    def load_config(self):
        config = self.config_manager.load_config()
        
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
        config = {
            'theme': self.theme_combo.currentText(),
            'capture_interval': self.interval_spin.value(),
            'opencv_enabled': self.opencv_check.isChecked(),
            'templates_dir': self.templates_dir
        }
        
        self.config_manager.save_config(config)
    
    def update_ui_state(self):
        connected = self.is_connected
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        
        recording = self.is_recording
        self.record_btn.setEnabled(connected and not recording and not self.is_playing)
        self.stop_record_btn.setEnabled(connected and recording)
        self.add_action_btn.setEnabled(not recording and not self.is_playing)
        
        playing = self.is_playing
        self.play_btn.setEnabled(connected and not recording and not playing and len(self.action_recorder.actions) > 0)
        self.stop_play_btn.setEnabled(connected and playing)
        
        has_actions = len(self.action_recorder.actions) > 0
        self.save_recording_btn.setEnabled(has_actions and not recording and not playing)
        self.load_recording_btn.setEnabled(not recording and not playing)
        self.clear_actions_btn.setEnabled(has_actions and not recording and not playing)
        
        has_selection = len(self.actions_list.selectedItems()) > 0
        self.edit_action_btn.setEnabled(has_selection and not recording and not playing)
        self.remove_action_btn.setEnabled(has_selection and not recording and not playing)
        
        has_region = self.screen_widget.selected_region is not None
        self.create_template_btn.setEnabled(connected and has_region)
        
        has_template = len(self.templates_list.selectedItems()) > 0
        self.remove_template_btn.setEnabled(has_template)
    
    def closeEvent(self, event):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread.wait()
        
        if self.is_playing:
            self.action_player.stop()
        
        self.save_config()
        
        event.accept()

    def update_scheduled_tasks_list(self):
        self.scheduled_tasks_list.clear()

        for task in self.task_scheduler.get_tasks():
            name = task.get('name', 'Unnamed')
            schedule_type = task.get('schedule_type', '')
            enabled = task.get('enabled', False)

            display = f"{'✓' if enabled else '✗'} {name} ({schedule_type})"

            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, task)

            if not enabled:
                item.setForeground(QColor(150, 150, 150))

            self.scheduled_tasks_list.addItem(item)

    def add_scheduled_task(self):
        if not self.action_recorder.actions:
            self.log("No actions to schedule")
            return

        dialog = ScheduleTaskDialog(self, self.action_recorder.actions)
        if dialog.exec_() == QDialog.Accepted:
            task_data = dialog.task_data

            self.task_scheduler.add_task(
                    task_data['name'],
                    self.action_recorder.actions,
                    task_data['schedule_type'],
                    task_data['schedule_data'],
                    task_data['enabled'],
                    task_data['speed_factor']
            )

            self.update_scheduled_tasks_list()
            self.log(f"Added scheduled task: {task_data['name']}")

    def remove_scheduled_task(self):
        selected_items = self.scheduled_tasks_list.selectedItems()
        if not selected_items:
            self.log("No task selected")
            return

        selected_index = self.scheduled_tasks_list.row(selected_items[0])
        if self.task_scheduler.remove_task(selected_index):
            self.update_scheduled_tasks_list()
            self.log("Task removed")
        else:
            self.log("Failed to remove task")

    def toggle_scheduled_task(self):
        selected_items = self.scheduled_tasks_list.selectedItems()
        if not selected_items:
            self.log("No task selected")
            return

        selected_index = self.scheduled_tasks_list.row(selected_items[0])
        tasks = self.task_scheduler.get_tasks()

        if 0 <= selected_index < len(tasks):
            task = tasks[selected_index]
            task['enabled'] = not task.get('enabled', False)

            self.task_scheduler.update_task(selected_index, task)
            self.update_scheduled_tasks_list()
            self.log(f"Task {task['name']} {'enabled' if task['enabled'] else 'disabled'}")

    def add_conditional_action(self):
        if not self.is_connected:
            self.log("Cannot add conditional: No device connected")
            return

        dialog = AddConditionalActionDialog(self, self.action_recorder, self.opencv_processor)
        if dialog.exec_() == QDialog.Accepted:
            condition = dialog.condition
            then_actions = dialog.then_actions
            else_actions = dialog.else_actions

            self.action_recorder.add_conditional_action(condition, then_actions, else_actions)
            self.update_actions_list()
            self.log(f"Added conditional action with {len(then_actions)} 'then' actions and {len(else_actions)} 'else' actions")

class ScheduleTaskDialog(QDialog):

    def __init__(self, parent=None, actions=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule Task")
        self.resize(500, 400)

        self.actions = actions or []
        self.task_data = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Task Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)

        type_group = QGroupBox("Schedule Type")
        type_layout = QVBoxLayout()

        self.type_group = QButtonGroup(self)

        self.one_time_radio = QRadioButton("One Time")
        self.type_group.addButton(self.one_time_radio)
        type_layout.addWidget(self.one_time_radio)

        self.daily_radio = QRadioButton("Daily")
        self.type_group.addButton(self.daily_radio)
        type_layout.addWidget(self.daily_radio)

        self.weekly_radio = QRadioButton("Weekly")
        self.type_group.addButton(self.weekly_radio)
        type_layout.addWidget(self.weekly_radio)

        self.interval_radio = QRadioButton("Interval")
        self.type_group.addButton(self.interval_radio)
        type_layout.addWidget(self.interval_radio)

        self.one_time_radio.setChecked(True)

        type_group.setLayout(type_layout)

        self.params_group = QGroupBox("Schedule Parameters")
        self.params_layout = QVBoxLayout()
        self.params_group.setLayout(self.params_layout)

        self.setup_one_time_params()

        self.type_group.buttonClicked.connect(self.on_schedule_type_changed)

        self.enabled_check = QCheckBox("Enable Schedule")
        self.enabled_check.setChecked(True)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(10, 500)
        self.speed_spin.setValue(100)
        self.speed_spin.setSuffix("%")
        speed_layout.addWidget(self.speed_spin)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(name_layout)
        layout.addWidget(type_group)
        layout.addWidget(self.params_group)
        layout.addWidget(self.enabled_check)
        layout.addLayout(speed_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_schedule_type_changed(self, button):
        self.clear_params_layout()

        if button == self.one_time_radio:
            self.setup_one_time_params()
        elif button == self.daily_radio:
            self.setup_daily_params()
        elif button == self.weekly_radio:
            self.setup_weekly_params()
        elif button == self.interval_radio:
            self.setup_interval_params()

    def clear_params_layout(self):
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def setup_one_time_params(self):
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.datetime_edit.setCalendarPopup(True)

        self.params_layout.addWidget(QLabel("Date and Time:"))
        self.params_layout.addWidget(self.datetime_edit)

    def setup_daily_params(self):
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime().addSecs(3600))

        self.params_layout.addWidget(QLabel("Time:"))
        self.params_layout.addWidget(self.time_edit)

    def setup_weekly_params(self):
        self.days_layout = QVBoxLayout()

        self.days_checks = {}
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            check = QCheckBox(day.capitalize())
            self.days_checks[day] = check
            self.days_layout.addWidget(check)

        self.weekly_time_edit = QTimeEdit()
        self.weekly_time_edit.setTime(QTime.currentTime().addSecs(3600))

        self.params_layout.addWidget(QLabel("Days:"))
        self.params_layout.addLayout(self.days_layout)
        self.params_layout.addWidget(QLabel("Time:"))
        self.params_layout.addWidget(self.weekly_time_edit)

    def setup_interval_params(self):
        hours_layout = QHBoxLayout()
        hours_layout.addWidget(QLabel("Hours:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 999)
        self.hours_spin.setValue(1)
        hours_layout.addWidget(self.hours_spin)

        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(QLabel("Minutes:"))
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(0)
        minutes_layout.addWidget(self.minutes_spin)

        self.params_layout.addLayout(hours_layout)
        self.params_layout.addLayout(minutes_layout)

    def get_schedule_data(self):
        if self.one_time_radio.isChecked():
            return ScheduleType.ONE_TIME, {
                    'datetime': self.datetime_edit.dateTime().toString(Qt.ISODate)
            }

        elif self.daily_radio.isChecked():
            return ScheduleType.DAILY, {
                    'time': self.time_edit.time().toString('HH:mm')
            }

        elif self.weekly_radio.isChecked():
            selected_days = []
            for day, check in self.days_checks.items():
                if check.isChecked():
                    selected_days.append(day)

            return ScheduleType.WEEKLY, {
                    'days': selected_days,
                    'time': self.weekly_time_edit.time().toString('HH:mm')
            }

        elif self.interval_radio.isChecked():
            return ScheduleType.INTERVAL, {
                    'hours':   self.hours_spin.value(),
                    'minutes': self.minutes_spin.value()
            }

        return None, {}

    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a task name.")
            return

        schedule_type, schedule_data = self.get_schedule_data()

        if schedule_type == ScheduleType.WEEKLY and not any(self.days_checks.values()):
            QMessageBox.warning(self, "Invalid Input", "Please select at least one day of the week.")
            return

        if schedule_type == ScheduleType.INTERVAL and self.hours_spin.value() == 0 and self.minutes_spin.value() == 0:
            QMessageBox.warning(self, "Invalid Input", "Please set a non-zero interval.")
            return

        self.task_data = {
                'name':          name,
                'schedule_type': schedule_type,
                'schedule_data': schedule_data,
                'enabled':       self.enabled_check.isChecked(),
                'speed_factor':  self.speed_spin.value() / 100.0
        }

        super().accept()

class AddConditionalActionDialog(QDialog):

    def __init__(self, parent=None, action_recorder=None, opencv_processor=None):
        super().__init__(parent)
        self.setWindowTitle("Add Conditional Action")
        self.resize(600, 500)

        self.action_recorder = action_recorder
        self.opencv_processor = opencv_processor

        self.condition = {}
        self.then_actions = []
        self.else_actions = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        condition_group = QGroupBox("Condition")
        condition_layout = QVBoxLayout()

        condition_type_layout = QHBoxLayout()
        condition_type_layout.addWidget(QLabel("Type:"))

        self.condition_combo = QComboBox()
        for cond_type in ConditionType:
            self.condition_combo.addItem(cond_type.value.replace('_', ' ').title(), cond_type.value)

        condition_type_layout.addWidget(self.condition_combo)
        condition_layout.addLayout(condition_type_layout)

        self.condition_params_layout = QVBoxLayout()
        condition_layout.addLayout(self.condition_params_layout)

        condition_group.setLayout(condition_layout)

        then_group = QGroupBox("Then Actions")
        then_layout = QVBoxLayout()

        self.then_list = QListWidget()
        then_buttons_layout = QHBoxLayout()
        self.add_then_btn = QPushButton("Add Action")
        self.remove_then_btn = QPushButton("Remove")
        then_buttons_layout.addWidget(self.add_then_btn)
        then_buttons_layout.addWidget(self.remove_then_btn)

        then_layout.addWidget(self.then_list)
        then_layout.addLayout(then_buttons_layout)
        then_group.setLayout(then_layout)

        else_group = QGroupBox("Else Actions")
        else_layout = QVBoxLayout()

        self.else_list = QListWidget()
        else_buttons_layout = QHBoxLayout()
        self.add_else_btn = QPushButton("Add Action")
        self.remove_else_btn = QPushButton("Remove")
        else_buttons_layout.addWidget(self.add_else_btn)
        else_buttons_layout.addWidget(self.remove_else_btn)

        else_layout.addWidget(self.else_list)
        else_layout.addLayout(else_buttons_layout)
        else_group.setLayout(else_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(condition_group)
        layout.addWidget(then_group)
        layout.addWidget(else_group)
        layout.addWidget(button_box)

        self.setLayout(layout)

        self.condition_combo.currentIndexChanged.connect(self.update_condition_params)
        self.add_then_btn.clicked.connect(lambda: self.add_action(True))
        self.remove_then_btn.clicked.connect(lambda: self.remove_action(True))
        self.add_else_btn.clicked.connect(lambda: self.add_action(False))
        self.remove_else_btn.clicked.connect(lambda: self.remove_action(False))

        self.update_condition_params(0)

    def update_condition_params(self, index):
        self.clear_condition_params()

        condition_type = self.condition_combo.currentData()

        if condition_type == ConditionType.TEMPLATE_PRESENT.value or condition_type == ConditionType.TEMPLATE_ABSENT.value:
            self.setup_template_condition_params()

        elif condition_type == ConditionType.COLOR_PRESENT.value:
            self.setup_color_condition_params()

        elif condition_type == ConditionType.PIXEL_COLOR.value:
            self.setup_pixel_condition_params()

    def clear_condition_params(self):
        while self.condition_params_layout.count():
            item = self.condition_params_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    while layout.count():
                        sub_item = layout.takeAt(0)
                        sub_widget = sub_item.widget()
                        if sub_widget:
                            sub_widget.deleteLater()

    def setup_template_condition_params(self):
        path_layout = QHBoxLayout()
        self.template_path_edit = QLineEdit()
        self.template_path_edit.setReadOnly(True)

        self.browse_template_btn = QPushButton("Browse...")
        self.browse_template_btn.clicked.connect(self.browse_template)

        path_layout.addWidget(self.template_path_edit)
        path_layout.addWidget(self.browse_template_btn)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Threshold:"))

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setValue(0.8)
        self.threshold_spin.setSingleStep(0.05)

        threshold_layout.addWidget(self.threshold_spin)

        self.condition_params_layout.addWidget(QLabel("Template Image:"))
        self.condition_params_layout.addLayout(path_layout)
        self.condition_params_layout.addLayout(threshold_layout)

    def setup_color_condition_params(self):
        hsv_min_layout = QHBoxLayout()
        hsv_min_layout.addWidget(QLabel("Min HSV:"))

        self.h_min_spin = QSpinBox()
        self.h_min_spin.setRange(0, 179)
        self.s_min_spin = QSpinBox()
        self.s_min_spin.setRange(0, 255)
        self.v_min_spin = QSpinBox()
        self.v_min_spin.setRange(0, 255)

        hsv_min_layout.addWidget(QLabel("H:"))
        hsv_min_layout.addWidget(self.h_min_spin)
        hsv_min_layout.addWidget(QLabel("S:"))
        hsv_min_layout.addWidget(self.s_min_spin)
        hsv_min_layout.addWidget(QLabel("V:"))
        hsv_min_layout.addWidget(self.v_min_spin)

        hsv_max_layout = QHBoxLayout()
        hsv_max_layout.addWidget(QLabel("Max HSV:"))

        self.h_max_spin = QSpinBox()
        self.h_max_spin.setRange(0, 179)
        self.h_max_spin.setValue(179)
        self.s_max_spin = QSpinBox()
        self.s_max_spin.setRange(0, 255)
        self.s_max_spin.setValue(255)
        self.v_max_spin = QSpinBox()
        self.v_max_spin.setRange(0, 255)
        self.v_max_spin.setValue(255)

        hsv_max_layout.addWidget(QLabel("H:"))
        hsv_max_layout.addWidget(self.h_max_spin)
        hsv_max_layout.addWidget(QLabel("S:"))
        hsv_max_layout.addWidget(self.s_max_spin)
        hsv_max_layout.addWidget(QLabel("V:"))
        hsv_max_layout.addWidget(self.v_max_spin)

        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel("Min Area:"))

        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(10, 100000)
        self.min_area_spin.setValue(100)

        area_layout.addWidget(self.min_area_spin)

        self.condition_params_layout.addLayout(hsv_min_layout)
        self.condition_params_layout.addLayout(hsv_max_layout)
        self.condition_params_layout.addLayout(area_layout)

    def setup_pixel_condition_params(self):
        coords_layout = QHBoxLayout()
        coords_layout.addWidget(QLabel("X:"))

        self.pixel_x_spin = QSpinBox()
        self.pixel_x_spin.setRange(0, 9999)

        coords_layout.addWidget(self.pixel_x_spin)
        coords_layout.addWidget(QLabel("Y:"))

        self.pixel_y_spin = QSpinBox()
        self.pixel_y_spin.setRange(0, 9999)

        coords_layout.addWidget(self.pixel_y_spin)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color (BGR):"))

        self.b_spin = QSpinBox()
        self.b_spin.setRange(0, 255)
        self.g_spin = QSpinBox()
        self.g_spin.setRange(0, 255)
        self.r_spin = QSpinBox()
        self.r_spin.setRange(0, 255)

        color_layout.addWidget(QLabel("B:"))
        color_layout.addWidget(self.b_spin)
        color_layout.addWidget(QLabel("G:"))
        color_layout.addWidget(self.g_spin)
        color_layout.addWidget(QLabel("R:"))
        color_layout.addWidget(self.r_spin)

        # Tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Tolerance:"))

        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 128)
        self.tolerance_spin.setValue(10)

        tolerance_layout.addWidget(self.tolerance_spin)

        self.condition_params_layout.addLayout(coords_layout)
        self.condition_params_layout.addLayout(color_layout)
        self.condition_params_layout.addLayout(tolerance_layout)

    def browse_template(self):
        filename, _ = QFileDialog.getOpenFileName(
                self, "Select Template Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if filename:
            self.template_path_edit.setText(filename)

    def add_action(self, is_then_branch):
        dialog = AddActionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            action_type = dialog.action_type
            action_data = dialog.action_data

            action = {
                    'type':        action_type.value,
                    'data':        action_data,
                    'timestamp':   time.time(),
                    'time_offset': 0
            }

            if is_then_branch:
                self.then_actions.append(action)
                self.then_list.addItem(self.action_recorder.get_action_description(action))
            else:
                self.else_actions.append(action)
                self.else_list.addItem(self.action_recorder.get_action_description(action))

    def remove_action(self, is_then_branch):
        list_widget = self.then_list if is_then_branch else self.else_list
        actions_list = self.then_actions if is_then_branch else self.else_actions

        selected_items = list_widget.selectedItems()
        if not selected_items:
            return

        selected_index = list_widget.row(selected_items[0])
        if 0 <= selected_index < len(actions_list):
            actions_list.pop(selected_index)
            list_widget.takeItem(selected_index)

    def get_condition_data(self):
        condition_type = self.condition_combo.currentData()

        if condition_type == ConditionType.TEMPLATE_PRESENT.value or condition_type == ConditionType.TEMPLATE_ABSENT.value:
            template_path = self.template_path_edit.text()
            if not template_path:
                return None

            return {
                    'type': condition_type,
                    'data': {
                            'template_path': template_path,
                            'threshold':     self.threshold_spin.value()
                    }
            }

        elif condition_type == ConditionType.COLOR_PRESENT.value:
            return {
                    'type': condition_type,
                    'data': {
                            'color_range': [
                                    [self.h_min_spin.value(), self.s_min_spin.value(), self.v_min_spin.value()],
                                    [self.h_max_spin.value(), self.s_max_spin.value(), self.v_max_spin.value()]
                            ],
                            'min_area':    self.min_area_spin.value()
                    }
            }

        elif condition_type == ConditionType.PIXEL_COLOR.value:
            return {
                    'type': condition_type,
                    'data': {
                            'x':         self.pixel_x_spin.value(),
                            'y':         self.pixel_y_spin.value(),
                            'color':     [self.b_spin.value(), self.g_spin.value(), self.r_spin.value()],
                            'tolerance': self.tolerance_spin.value()
                    }
            }

        return None

    def accept(self):
        condition = self.get_condition_data()
        if condition is None:
            QMessageBox.warning(self, "Invalid Condition", "Please fill all required condition fields.")
            return

        if not self.then_actions:
            QMessageBox.warning(self, "Missing Actions", "Please add at least one action to the 'Then' branch.")
            return

        self.condition = condition

        super().accept()