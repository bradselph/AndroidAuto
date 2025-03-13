import json
import time
from enum import Enum

class ActionType(Enum):
    TAP = "tap"
    SWIPE = "swipe"
    WAIT = "wait"
    KEY = "key"
    TEXT = "text"
    LONG_PRESS = "long_press"
    TEMPLATE_MATCH = "template_match"

class ActionRecorder:
    """Records and manages user actions for playback"""
    
    def __init__(self):
        self.actions = []
        self.recording = False
        self.start_time = None
        self.file_path = None
    
    def start_recording(self):
        """Start a new recording session"""
        self.actions = []
        self.recording = True
        self.start_time = time.time()
    
    def stop_recording(self):
        """Stop the current recording session"""
        self.recording = False
    
    def add_action(self, action_type, data):
        """Add an action to the recording"""
        if self.recording:
            current_time = time.time()
            time_offset = current_time - self.start_time if self.start_time else 0
            
            action = {
                'type': action_type.value if isinstance(action_type, ActionType) else action_type,
                'data': data,
                'timestamp': current_time,
                'time_offset': time_offset
            }
            self.actions.append(action)
            return len(self.actions) - 1  # Return index of added action
        return -1
    
    def add_tap(self, x, y):
        """Add a tap action"""
        return self.add_action(ActionType.TAP, {'x': x, 'y': y})
    
    def add_swipe(self, x1, y1, x2, y2, duration=300):
        """Add a swipe action"""
        return self.add_action(ActionType.SWIPE, {
            'x1': x1, 'y1': y1, 
            'x2': x2, 'y2': y2, 
            'duration': duration
        })
    
    def add_wait(self, duration):
        """Add a wait action"""
        return self.add_action(ActionType.WAIT, {'duration': duration})
    
    def add_key_event(self, keycode):
        """Add a key event action"""
        return self.add_action(ActionType.KEY, {'keycode': keycode})
    
    def add_text_input(self, text):
        """Add a text input action"""
        return self.add_action(ActionType.TEXT, {'text': text})
    
    def add_long_press(self, x, y, duration=500):
        """Add a long press action"""
        return self.add_action(ActionType.LONG_PRESS, {'x': x, 'y': y, 'duration': duration})
    
    def add_template_match(self, template_path, wait=True, max_wait=10, tap=True):
        """Add a template matching action"""
        return self.add_action(ActionType.TEMPLATE_MATCH, {
            'template_path': template_path,
            'wait': wait,
            'max_wait': max_wait,
            'tap': tap
        })
    
    def remove_action(self, index):
        """Remove an action by index"""
        if 0 <= index < len(self.actions):
            self.actions.pop(index)
            return True
        return False
    
    def move_action(self, from_index, to_index):
        """Move an action from one position to another"""
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)
            return True
        return False
    
    def save_actions(self, filename):
        """Save actions to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'version': '1.0',
                    'timestamp': time.time(),
                    'actions': self.actions
                }, f, indent=4)
            self.file_path = filename
            return True
        except Exception as e:
            print(f"Error saving actions: {e}")
            return False
    
    def load_actions(self, filename):
        """Load actions from a JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
                # Check if the file has the expected format
                if 'actions' in data:
                    self.actions = data['actions']
                    self.file_path = filename
                    return True
                else:
                    # Try to interpret the file as a direct array of actions
                    if isinstance(data, list):
                        self.actions = data
                        self.file_path = filename
                        return True
            return False
        except Exception as e:
            print(f"Error loading actions: {e}")
            return False
    
    def clear_actions(self):
        """Clear all actions"""
        self.actions = []
        
    def get_action_description(self, action):
        """Get a human-readable description of an action"""
        action_type = action.get('type', '')
        data = action.get('data', {})
        
        if action_type == ActionType.TAP.value:
            return f"Tap at ({data.get('x', 0)}, {data.get('y', 0)})"
        
        elif action_type == ActionType.SWIPE.value:
            return f"Swipe from ({data.get('x1', 0)}, {data.get('y1', 0)}) to ({data.get('x2', 0)}, {data.get('y2', 0)})"
        
        elif action_type == ActionType.WAIT.value:
            return f"Wait for {data.get('duration', 0)} ms"
        
        elif action_type == ActionType.KEY.value:
            return f"Key event: {data.get('keycode', '')}"
        
        elif action_type == ActionType.TEXT.value:
            return f"Text input: {data.get('text', '')}"
        
        elif action_type == ActionType.LONG_PRESS.value:
            return f"Long press at ({data.get('x', 0)}, {data.get('y', 0)}) for {data.get('duration', 500)} ms"
        
        elif action_type == ActionType.TEMPLATE_MATCH.value:
            template = data.get('template_path', '').split('/')[-1]
            action_str = f"Find template: {template}"
            if data.get('tap', False):
                action_str += " and tap"
            return action_str
        
        else:
            return f"Unknown action: {action_type}"