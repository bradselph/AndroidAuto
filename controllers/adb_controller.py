import subprocess
import os
import time
import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class AdbController(QObject):
    """Controller for ADB operations with Android devices"""
    
    def __init__(self, device_id=None):
        super().__init__()
        self.device_id = device_id
        self.scrcpy_process = None
        self.adb_path = self._find_adb_path()
        self.screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp_screenshot.png")
    
    def _find_adb_path(self):
        """Attempt to find ADB in common locations or PATH"""
        # Check if adb is in PATH
        try:
            subprocess.run(['adb', '--version'], capture_output=True, check=False)
            return 'adb'
        except (FileNotFoundError, subprocess.SubprocessError):
            # Check common installation locations
            common_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'android-sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Android', 'android-sdk', 'platform-tools', 'adb.exe')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            # Default to 'adb' and hope for the best
            return 'adb'
    
    def get_devices(self):
        """Get list of connected devices"""
        result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, check=False)
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        for line in lines:
            if line and "\tdevice" in line:
                devices.append(line.split('\t')[0])
        return devices
    
    def is_device_connected(self, device_id=None):
        """Check if specific device is connected"""
        device_to_check = device_id or self.device_id
        if not device_to_check:
            return False
        
        devices = self.get_devices()
        return device_to_check in devices
    
    def start_scrcpy(self, output_file=None, no_display=False):
        """Start scrcpy for screen mirroring"""
        cmd = ['scrcpy']
        if self.device_id:
            cmd.extend(['-s', self.device_id])
        if output_file:
            cmd.extend(['--record', output_file])
        if no_display:
            cmd.extend(['--no-display'])
        
        try:
            self.scrcpy_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            print(f"Error starting scrcpy: {e}")
            return False
    
    def stop_scrcpy(self):
        """Stop scrcpy process"""
        if self.scrcpy_process:
            self.scrcpy_process.terminate()
            try:
                self.scrcpy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.scrcpy_process.kill()
            self.scrcpy_process = None
    
    def adb_command(self, command, shell=False):
        """Run generic ADB command"""
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(['-s', self.device_id])
        
        if shell:
            cmd.extend(['shell'] + command)
        else:
            cmd.extend(command)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print(f"ADB command error: {result.stderr}")
                return None
            return result.stdout.strip()
        except subprocess.SubprocessError as e:
            print(f"Error executing ADB command: {e}")
            return None
    
    def tap(self, x, y):
        """Tap at coordinates"""
        return self.adb_command(['input', 'tap', str(int(x)), str(int(y))], shell=True)
    
    def swipe(self, x1, y1, x2, y2, duration=300):
        """Swipe from (x1,y1) to (x2,y2)"""
        return self.adb_command(
            ['input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(duration)],
            shell=True
        )
    
    def long_press(self, x, y, duration=500):
        """Long press at coordinates"""
        # Simulate long press with a swipe that doesn't move
        return self.swipe(x, y, x, y, duration)
    
    def key_event(self, keycode):
        """Send key event"""
        return self.adb_command(['input', 'keyevent', str(keycode)], shell=True)
    
    def text_input(self, text):
        """Input text"""
        # Replace spaces with %s for ADB
        safe_text = text.replace(' ', '%s').replace("'", "\\'").replace('"', '\\"')
        return self.adb_command(['input', 'text', safe_text], shell=True)
    
    def take_screenshot(self):
        """Capture screenshot and return as OpenCV image"""
        # Delete previous screenshot if it exists
        if os.path.exists(self.screenshot_path):
            try:
                os.remove(self.screenshot_path)
            except OSError:
                pass
                
        # Capture screenshot on device
        self.adb_command(['screencap', '-p', '/sdcard/screenshot.png'], shell=True)
        
        # Pull screenshot to computer
        self.adb_command(['pull', '/sdcard/screenshot.png', self.screenshot_path])
        
        # Delete screenshot from device
        self.adb_command(['rm', '/sdcard/screenshot.png'], shell=True)
        
        # Check if screenshot was pulled successfully
        if os.path.exists(self.screenshot_path):
            try:
                return cv2.imread(self.screenshot_path)
            except Exception as e:
                print(f"Error reading screenshot: {e}")
                return None
        return None
    
    def get_device_dimensions(self):
        """Get device screen dimensions"""
        output = self.adb_command(['wm', 'size'], shell=True)
        if output:
            # Parse output like "Physical size: 1080x2340"
            try:
                dimensions = output.split(': ')[1].split('x')
                width = int(dimensions[0])
                height = int(dimensions[1])
                return width, height
            except (IndexError, ValueError):
                pass
        return None, None
    
    def restart_adb_server(self):
        """Restart ADB server"""
        subprocess.run([self.adb_path, 'kill-server'], check=False)
        time.sleep(1)
        subprocess.run([self.adb_path, 'start-server'], check=False)
        time.sleep(2)
        return True


class ScreenCaptureThread(QThread):
    """Thread for continuous screen capture"""
    update_frame = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)
    
    def __init__(self, adb_controller, interval=0.2):
        super().__init__()
        self.adb_controller = adb_controller
        self.interval = interval
        self.running = False
    
    def run(self):
        self.running = True
        failures = 0
        
        while self.running:
            try:
                frame = self.adb_controller.take_screenshot()
                if frame is not None:
                    self.update_frame.emit(frame)
                    failures = 0
                else:
                    failures += 1
                    if failures >= 3:
                        self.error.emit("Failed to capture screenshot multiple times")
                        failures = 0
            except Exception as e:
                self.error.emit(f"Error in screen capture: {str(e)}")
                failures += 1
            
            # Sleep between captures
            time.sleep(self.interval)
    
    def stop(self):
        self.running = False
        self.wait()