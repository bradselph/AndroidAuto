import subprocess
import os
import time
import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class AdbController(QObject):

    def __init__(self, device_id=None):
        super().__init__()
        self.device_id = device_id
        self.scrcpy_process = None
        self.adb_path = self._find_adb_path()
        self.screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp_screenshot.png")
    
    def _find_adb_path(self):
        try:
            subprocess.run(['adb', '--version'], capture_output=True, check=False)
            return 'adb'
        except (FileNotFoundError, subprocess.SubprocessError):
            common_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'android-sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Android', 'android-sdk', 'platform-tools', 'adb.exe')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            return 'adb'
    
    def get_devices(self):
        result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, check=False)
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        for line in lines:
            if line and "\tdevice" in line:
                devices.append(line.split('\t')[0])
        return devices
    
    def is_device_connected(self, device_id=None):
        device_to_check = device_id or self.device_id
        if not device_to_check:
            return False
        
        devices = self.get_devices()
        return device_to_check in devices
    
    def start_scrcpy(self, output_file=None, no_display=False):
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
        if self.scrcpy_process:
            self.scrcpy_process.terminate()
            try:
                self.scrcpy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.scrcpy_process.kill()
            self.scrcpy_process = None
    
    def adb_command(self, command, shell=False):
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
        return self.adb_command(['input', 'tap', str(int(x)), str(int(y))], shell=True)
    
    def swipe(self, x1, y1, x2, y2, duration=300):
        return self.adb_command(
            ['input', 'swipe', str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(duration)],
            shell=True
        )
    
    def long_press(self, x, y, duration=500):
        return self.swipe(x, y, x, y, duration)
    
    def key_event(self, keycode):
        return self.adb_command(['input', 'keyevent', str(keycode)], shell=True)
    
    def text_input(self, text):
        safe_text = text.replace(' ', '%s').replace("'", "\\'").replace('"', '\\"')
        return self.adb_command(['input', 'text', safe_text], shell=True)
    
    def take_screenshot(self):
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(['shell', 'screencap', '-p'])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            screenshot_data, error = process.communicate()

            if process.returncode != 0 or not screenshot_data:
                print(f"Screenshot capture error: {error.decode('utf-8', errors='ignore')}")
                return None

            if os.name == 'nt':
                screenshot_data = screenshot_data.replace(b'\r\n', b'\n')

            nparr = np.frombuffer(screenshot_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    def get_device_dimensions(self):
        output = self.adb_command(['wm', 'size'], shell=True)
        if output:
            try:
                dimensions = output.split(': ')[1].split('x')
                width = int(dimensions[0])
                height = int(dimensions[1])
                return width, height
            except (IndexError, ValueError):
                pass
        return None, None
    
    def restart_adb_server(self):
        subprocess.run([self.adb_path, 'kill-server'], check=False)
        time.sleep(1)
        subprocess.run([self.adb_path, 'start-server'], check=False)
        time.sleep(2)
        return True


class ScreenCaptureThread(QThread):
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
            
            time.sleep(self.interval)
    
    def stop(self):
        self.running = False
        self.wait()

class DeviceManager:

    def __init__(self, driver_manager=None):
        self.driver_manager = driver_manager
        self.adb_path = driver_manager.get_adb_path() if driver_manager else 'adb'
        self.devices = {}

    def refresh_devices(self):
        result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, check=False)

        if result.returncode != 0:
            return []

        lines = result.stdout.strip().split('\n')[1:]

        device_ids = []
        for line in lines:
            if line and "\tdevice" in line:
                device_id = line.split('\t')[0]
                device_ids.append(device_id)

                if device_id not in self.devices:
                    self.devices[device_id] = AdbController(device_id, self.adb_path)

        disconnected = [d for d in self.devices.keys() if d not in device_ids]
        for device_id in disconnected:
            del self.devices[device_id]

        return device_ids

    def get_device(self, device_id):
        if device_id in self.devices:
            return self.devices[device_id]

        if self.is_device_connected(device_id):
            self.devices[device_id] = AdbController(device_id, self.adb_path)
            return self.devices[device_id]

        return None

    def is_device_connected(self, device_id):
        device_ids = self.refresh_devices()
        return device_id in device_ids

    def restart_adb_server(self):
        subprocess.run([self.adb_path, 'kill-server'], check=False)
        time.sleep(1)
        subprocess.run([self.adb_path, 'start-server'], check=False)
        time.sleep(2)

        self.refresh_devices()
        return True