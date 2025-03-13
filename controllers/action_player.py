import time
import os
import threading
from PyQt5.QtCore import QObject, pyqtSignal
from controllers.action_recorder import ActionType

class ActionPlayer(QObject):
    """Plays back recorded actions on the device"""
    
    action_started = pyqtSignal(int, dict)  # Index, action data
    action_completed = pyqtSignal(int)  # Index
    playback_started = pyqtSignal()
    playback_completed = pyqtSignal()
    playback_error = pyqtSignal(str)
    
    def __init__(self, adb_controller, opencv_processor=None):
        super().__init__()
        self.adb_controller = adb_controller
        self.opencv_processor = opencv_processor
        self.actions = []
        self.playing = False
        self.current_index = -1
        self.play_thread = None
        self.stop_event = threading.Event()
    
    def load_actions(self, actions):
        """Load actions to be played"""
        self.actions = actions
    
    def play(self, speed_factor=1.0, start_index=0):
        """Play actions with speed adjustment"""
        if not self.actions or self.playing or start_index >= len(self.actions):
            return False
        
        # Reset stop event
        self.stop_event.clear()
        
        # Start playback in a separate thread
        self.play_thread = threading.Thread(
            target=self._play_thread, 
            args=(speed_factor, start_index)
        )
        self.play_thread.daemon = True
        self.play_thread.start()
        return True
    
    def _play_thread(self, speed_factor, start_index):
        """Thread function for action playback"""
        self.playing = True
        self.playback_started.emit()
        
        try:
            prev_time_offset = 0
            
            for i in range(start_index, len(self.actions)):
                # Check if playback has been stopped
                if self.stop_event.is_set():
                    break
                
                self.current_index = i
                action = self.actions[i]
                
                # Emit signal that action is starting
                self.action_started.emit(i, action)
                
                # Wait appropriate time between actions
                if i > start_index and 'time_offset' in action:
                    current_time_offset = action['time_offset']
                    delay = (current_time_offset - prev_time_offset) / speed_factor
                    if delay > 0:
                        time.sleep(delay)
                    prev_time_offset = current_time_offset
                
                # Execute the action
                success = self._execute_action(action)
                
                # Emit signal that action is complete
                self.action_completed.emit(i)
                
                if not success:
                    self.playback_error.emit(f"Failed to execute action: {action.get('type')}")
                    break
        
        except Exception as e:
            self.playback_error.emit(f"Error during playback: {str(e)}")
        
        finally:
            self.playing = False
            self.current_index = -1
            self.playback_completed.emit()
    
    def stop(self):
        """Stop playback"""
        if self.playing:
            self.stop_event.set()
            if self.play_thread:
                self.play_thread.join(timeout=5.0)
            return True
        return False
    
    def _execute_action(self, action):
        """Execute a single action"""
        action_type = action.get('type', '')
        data = action.get('data', {})
        
        try:
            if action_type == ActionType.TAP.value:
                return self.adb_controller.tap(data.get('x', 0), data.get('y', 0)) is not None
            
            elif action_type == ActionType.SWIPE.value:
                return self.adb_controller.swipe(
                    data.get('x1', 0), data.get('y1', 0),
                    data.get('x2', 0), data.get('y2', 0),
                    data.get('duration', 300)
                ) is not None
            
            elif action_type == ActionType.WAIT.value:
                time.sleep(data.get('duration', 1) / 1000.0)  # Convert ms to seconds
                return True
            
            elif action_type == ActionType.KEY.value:
                return self.adb_controller.key_event(data.get('keycode', '')) is not None
            
            elif action_type == ActionType.TEXT.value:
                return self.adb_controller.text_input(data.get('text', '')) is not None
            
            elif action_type == ActionType.LONG_PRESS.value:
                return self.adb_controller.long_press(
                    data.get('x', 0), 
                    data.get('y', 0), 
                    data.get('duration', 500)
                ) is not None
            
            elif action_type == ActionType.TEMPLATE_MATCH.value:
                if self.opencv_processor is None:
                    self.playback_error.emit("Template matching requested but OpenCV processor not available")
                    return False
                
                template_path = data.get('template_path', '')
                if not os.path.exists(template_path):
                    self.playback_error.emit(f"Template file not found: {template_path}")
                    return False
                
                # Wait for template to appear if requested
                if data.get('wait', True):
                    max_wait = data.get('max_wait', 10)  # seconds
                    result = self.opencv_processor.wait_for_template(
                        template_path, 
                        timeout=max_wait
                    )
                    
                    if not result:
                        return False
                
                # Find template and tap if requested
                match = self.opencv_processor.find_template(template_path)
                if match and data.get('tap', False):
                    cx, cy = match[0] + match[2] // 2, match[1] + match[3] // 2
                    return self.adb_controller.tap(cx, cy) is not None
                
                return match is not None
            
            else:
                self.playback_error.emit(f"Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            self.playback_error.emit(f"Error executing action: {str(e)}")
            return False