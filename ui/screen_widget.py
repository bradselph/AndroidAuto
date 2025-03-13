from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor, QMouseEvent

class ScreenWidget(QLabel):
    """Custom widget for displaying and interacting with device screen"""
    
    # Signals
    tap_event = pyqtSignal(int, int, int, int)  # x, y, device_x, device_y
    swipe_event = pyqtSignal(int, int, int, int, int, int, int, int, int)  # start_x, start_y, end_x, end_y, device_start_x, device_start_y, device_end_x, device_end_y, duration
    long_press_event = pyqtSignal(int, int, int, int, int)  # x, y, device_x, device_y, duration
    
    def __init__(self, adb_controller):
        super().__init__()
        self.adb_controller = adb_controller
        
        # Set widget properties
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 400)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        self.setText("No device connected")
        
        # State variables
        self.current_frame = None
        self.scaled_pixmap = None
        self.device_width = 0
        self.device_height = 0
        self.actual_width = 0
        self.actual_height = 0
        self.offset_x = 0
        self.offset_y = 0
        
        # Mouse tracking
        self.setMouseTracking(True)
        self.mouse_pressed = False
        self.press_pos = None
        self.press_time = None
        self.last_pos = None
        self.long_press_threshold = 500  # ms
        
        # Selection
        self.selecting = False
        self.selection_start = None
        self.selected_region = None
        
        # OpenCV
        self.opencv_enabled = True
    
    def update_frame(self, frame):
        """Update the displayed frame"""
        if frame is None:
            return
        
        self.current_frame = frame
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        # Convert to QImage and QPixmap
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Update widget size if needed
        if self.device_width == 0 or self.device_height == 0:
            self.device_width = width
            self.device_height = height
        
        # Adjust pixmap to widget size
        self.update_scaled_pixmap(pixmap)
        
        # Update display
        self.update()
    
    def update_scaled_pixmap(self, pixmap=None):
        """Scale the pixmap to fit the widget while maintaining aspect ratio"""
        if pixmap is None and self.current_frame is not None:
            # Recreate pixmap from current frame
            height, width, channel = self.current_frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(self.current_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
        elif pixmap is None:
            return
        
        # Calculate scaling to fit widget
        widget_size = self.size()
        scaled_pixmap = pixmap.scaled(widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Calculate offset for centered pixmap
        self.offset_x = (widget_size.width() - scaled_pixmap.width()) // 2
        self.offset_y = (widget_size.height() - scaled_pixmap.height()) // 2
        
        # Store actual displayed size
        self.actual_width = scaled_pixmap.width()
        self.actual_height = scaled_pixmap.height()
        
        self.scaled_pixmap = scaled_pixmap
    
    def clear(self):
        """Clear the display"""
        self.current_frame = None
        self.scaled_pixmap = None
        self.setText("No device connected")
        self.update()
    
    def set_device_dimensions(self, width, height):
        """Set the actual device screen dimensions"""
        self.device_width = width
        self.device_height = height
    
    def set_opencv_enabled(self, enabled):
        """Enable or disable OpenCV processing"""
        self.opencv_enabled = enabled
    
    def get_device_coordinates(self, x, y):
        """Convert widget coordinates to device coordinates"""
        if self.actual_width == 0 or self.actual_height == 0:
            return 0, 0
        
        # Adjust for offset
        x -= self.offset_x
        y -= self.offset_y
        
        # Ensure coordinates are within the actual image area
        if x < 0 or x >= self.actual_width or y < 0 or y >= self.actual_height:
            return None, None
        
        # Scale to device coordinates
        device_x = int(x * self.device_width / self.actual_width)
        device_y = int(y * self.device_height / self.actual_height)
        
        return device_x, device_y
    
    def get_device_coordinates_rect(self, rect):
        """Convert widget rectangle to device rectangle"""
        x1, y1 = self.get_device_coordinates(rect.left(), rect.top())
        x2, y2 = self.get_device_coordinates(rect.right(), rect.bottom())
        
        if x1 is None or x2 is None:
            return None
        
        return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    
    def paintEvent(self, event):
        """Custom paint event to display the screen and selections"""
        if self.scaled_pixmap is None:
            # Fall back to default label behavior
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        
        # Draw the screen image
        painter.drawPixmap(self.offset_x, self.offset_y, self.scaled_pixmap)
        
        # Draw selection rectangle if selecting or a region is selected
        if self.selecting and self.selection_start is not None and self.last_pos is not None:
            rect = QRect(self.selection_start, self.last_pos).normalized()
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
            painter.drawRect(rect)
        
        elif self.selected_region is not None:
            painter.setPen(QPen(QColor(0, 255, 0), 2, Qt.SolidLine))
            painter.drawRect(self.selected_region)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if self.scaled_pixmap is not None:
            self.update_scaled_pixmap()
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if self.scaled_pixmap is None or event.button() != Qt.LeftButton:
            return
        
        self.mouse_pressed = True
        self.press_pos = event.pos()
        self.last_pos = event.pos()
        self.press_time = event.timestamp()
        
        # Check if Control key is held for selection mode
        if event.modifiers() & Qt.ControlModifier:
            self.selecting = True
            self.selection_start = event.pos()
            self.selected_region = None
            self.setCursor(Qt.CrossCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if not self.mouse_pressed:
            return
        
        self.last_pos = event.pos()
        
        if self.selecting:
            # Update selection rectangle
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if not self.mouse_pressed or event.button() != Qt.LeftButton:
            return
        
        release_time = event.timestamp()
        duration = release_time - self.press_time
        
        if self.selecting:
            # Finalize selection
            self.selecting = False
            self.selected_region = QRect(self.selection_start, event.pos()).normalized()
            self.setCursor(Qt.ArrowCursor)
            self.update()
        
        else:
            # Calculate device coordinates
            press_device_x, press_device_y = self.get_device_coordinates(self.press_pos.x(), self.press_pos.y())
            release_device_x, release_device_y = self.get_device_coordinates(event.pos().x(), event.pos().y())
            
            if press_device_x is None or release_device_x is None:
                self.mouse_pressed = False
                return
            
            # Check for tap, long press, or swipe
            distance = ((event.pos().x() - self.press_pos.x()) ** 2 + 
                        (event.pos().y() - self.press_pos.y()) ** 2) ** 0.5
            
            if distance < 10:  # Small movement, consider as tap or long press
                if duration > self.long_press_threshold:
                    # Long press
                    self.long_press_event.emit(
                        self.press_pos.x(), self.press_pos.y(),
                        press_device_x, press_device_y,
                        duration
                    )
                else:
                    # Tap
                    self.tap_event.emit(
                        self.press_pos.x(), self.press_pos.y(),
                        press_device_x, press_device_y
                    )
            else:
                # Swipe
                self.swipe_event.emit(
                    self.press_pos.x(), self.press_pos.y(),
                    event.pos().x(), event.pos().y(),
                    press_device_x, press_device_y,
                    release_device_x, release_device_y,
                    duration
                )
        
        self.mouse_pressed = False
        self.press_pos = None
        self.last_pos = None