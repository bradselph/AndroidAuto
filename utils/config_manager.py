import json
import os

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config"))
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            return self.get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return self.get_default_config()
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            'theme': 'System',
            'capture_interval': 200,
            'opencv_enabled': True,
            'templates_dir': os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "resources", 
                "templates"
            ))
        }