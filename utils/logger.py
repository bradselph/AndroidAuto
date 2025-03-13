import os
import time
import datetime

class Logger:
    """Simple logging utility"""
    
    def __init__(self):
        self.logs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"))
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create a new log file for this session
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.logs_dir, f"log_{self.session_id}.txt")
    
    def log(self, message):
        """Log a message to file"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to log: {e}")
    
    def get_logs(self, max_lines=100):
        """Read the most recent log entries"""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Return the last max_lines lines
            return lines[-max_lines:]
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []