import os
import platform
import subprocess
import shutil
import zipfile
import requests


class DriverManager:

    def __init__(self, config_manager):
        self.config_manager = config_manager

        self.drivers_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "drivers"
        ))

        self.adb_dir = os.path.join(self.drivers_dir, "adb")
        self.scrcpy_dir = os.path.join(self.drivers_dir, "scrcpy")

        os.makedirs(self.drivers_dir, exist_ok=True)
        os.makedirs(self.scrcpy_dir, exist_ok=True)

        self.system = platform.system()

        if self.system == "Windows":
            self.adb_exec = "adb.exe"
            self.scrcpy_exec = "scrcpy.exe"
        else:
            self.adb_exec = "adb"
            self.scrcpy_exec = "scrcpy"

        self.adb_path = os.path.join(self.scrcpy_dir, self.adb_exec)
        self.scrcpy_path = os.path.join(self.scrcpy_dir, self.scrcpy_exec)

    def check_drivers(self):
        adb_installed = os.path.exists(self.adb_path)
        scrcpy_installed = os.path.exists(self.scrcpy_path)

        return {
                "adb":    adb_installed,
                "scrcpy": scrcpy_installed
        }

    def download_adb(self):
        if os.path.exists(os.path.join(self.scrcpy_dir, self.adb_exec)):
            self.adb_path = os.path.join(self.scrcpy_dir, self.adb_exec)
            return True, "ADB found in scrcpy directory"

        url = None

        if self.system == "Windows":
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        if not url:
            return False, "Unsupported operating system"

        try:
            temp_file = os.path.join(self.drivers_dir, "platform-tools.zip")

            print(f"Downloading ADB from {url}")
            response = requests.get(url, stream=True)

            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(self.drivers_dir)

            platform_tools_dir = os.path.join(self.drivers_dir, "platform-tools")

            for item in os.listdir(platform_tools_dir):
                s = os.path.join(platform_tools_dir, item)
                d = os.path.join(self.adb_dir, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
                else:
                    shutil.copytree(s, d, dirs_exist_ok=True)

            os.remove(temp_file)
            shutil.rmtree(platform_tools_dir)

            return True, "ADB installed successfully"

        except Exception as e:
            return False, f"Failed to install ADB: {str(e)}"

    def download_scrcpy(self):
        url = None

        if self.system == "Windows":
            url = "https://github.com/Genymobile/scrcpy/releases/download/v3.1/scrcpy-win64-v3.1.zip"

        if not url:
            return False, "Automatic installation not supported for this OS. Please install scrcpy manually."

        try:
            temp_file = os.path.join(self.drivers_dir, "scrcpy.zip")

            print(f"Downloading scrcpy from {url}")
            response = requests.get(url, stream=True)

            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(self.scrcpy_dir)

            os.remove(temp_file)

            if os.path.exists(os.path.join(self.scrcpy_dir, self.adb_exec)):
                self.adb_path = os.path.join(self.scrcpy_dir, self.adb_exec)

            return True, "scrcpy installed successfully"

        except Exception as e:
            return False, f"Failed to install scrcpy: {str(e)}"

    def get_adb_path(self):
        scrcpy_adb_path = os.path.join(self.scrcpy_dir, self.adb_exec)
        if os.path.exists(scrcpy_adb_path):
            return scrcpy_adb_path

        if os.path.exists(self.adb_path):
            return self.adb_path

        try:
            if self.system == "Windows":
                result = subprocess.run(['where', 'adb'], capture_output=True, text=True, check=False)
            else:
                result = subprocess.run(['which', 'adb'], capture_output=True, text=True, check=False)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[0]

        except Exception:
            pass

        return "adb"

    def get_scrcpy_path(self):
        if os.path.exists(self.scrcpy_path):
            return self.scrcpy_path

        try:
            if self.system == "Windows":
                result = subprocess.run(['where', 'scrcpy'], capture_output=True, text=True, check=False)
            else:
                result = subprocess.run(['which', 'scrcpy'], capture_output=True, text=True, check=False)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[0]

        except Exception:
            pass

        return "scrcpy"
