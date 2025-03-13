import cv2
import numpy as np
import time
import os
from PyQt5.QtCore import QObject, pyqtSignal

class OpenCVProcessor(QObject):
    """Handles OpenCV image processing operations"""
    
    template_found = pyqtSignal(str, tuple)  # template_path, (x, y, w, h)
    
    def __init__(self, adb_controller):
        super().__init__()
        self.adb_controller = adb_controller
        self.last_frame = None
        self.template_cache = {}  # Cache for loaded templates
    
    def process_frame(self, frame):
        """Process a frame with OpenCV operations"""
        if frame is None:
            return None
        
        # Store the last processed frame
        self.last_frame = frame.copy()
        
        # Apply any general processing here
        return frame
    
    def load_template(self, template_path):
        """Load a template image with caching"""
        if template_path in self.template_cache:
            return self.template_cache[template_path]
        
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return None
        
        try:
            template = cv2.imread(template_path)
            if template is not None:
                self.template_cache[template_path] = template
            return template
        except Exception as e:
            print(f"Error loading template: {e}")
            return None
    
    def find_template(self, template_path, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
        """Find a template in the current frame"""
        if self.last_frame is None:
            return None
        
        template = self.load_template(template_path)
        if template is None:
            return None
        
        # Ensure both images are the same format
        if len(self.last_frame.shape) != len(template.shape):
            if len(self.last_frame.shape) == 3:
                template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
            else:
                self.last_frame = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        
        # Run template matching
        result = cv2.matchTemplate(self.last_frame, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # For TM_CCOEFF_NORMED, we want max value
        if method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]:
            if max_val < threshold:
                return None
            h, w = template.shape[:2]
            match = (max_loc[0], max_loc[1], w, h)
            self.template_found.emit(template_path, match)
            return match
        # For TM_SQDIFF_NORMED, we want min value
        else:
            if 1.0 - min_val < threshold:
                return None
            h, w = template.shape[:2]
            match = (min_loc[0], min_loc[1], w, h)
            self.template_found.emit(template_path, match)
            return match
    
    def wait_for_template(self, template_path, timeout=10, check_interval=0.5, threshold=0.8):
        """Wait for a template to appear on screen"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Take a new screenshot
            frame = self.adb_controller.take_screenshot()
            if frame is not None:
                self.last_frame = frame
                
                # Try to find the template
                match = self.find_template(template_path, threshold)
                if match:
                    return match
            
            # Wait before next check
            time.sleep(check_interval)
        
        # Timeout reached
        return None
    
    def highlight_match(self, frame, match, color=(0, 255, 0), thickness=2):
        """Draw a rectangle around a match"""
        if frame is None or match is None:
            return frame
        
        result = frame.copy()
        x, y, w, h = match
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        return result
    
    def find_color(self, color_range, min_area=100):
        """Find regions of a specific color in the current frame"""
        if self.last_frame is None:
            return None
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2HSV)
        
        # Create a mask for the color range
        lower_bound = np.array(color_range[0])
        upper_bound = np.array(color_range[1])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        
        if not valid_contours:
            return None
        
        # Return the largest contour
        largest_contour = max(valid_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        return (x, y, w, h)
    
    def detect_text_area(self, min_area=500):
        """Detect areas that may contain text"""
        if self.last_frame is None:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio
        text_areas = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h
                
                # Text typically has a reasonable aspect ratio
                if 0.2 < aspect_ratio < 15:
                    text_areas.append((x, y, w, h))
        
        return text_areas
    
    def create_template(self, region, filename):
        """Create a template from a region of the current frame"""
        if self.last_frame is None:
            return False
        
        x, y, w, h = region
        template = self.last_frame[y:y+h, x:x+w]
        
        try:
            cv2.imwrite(filename, template)
            # Add to template cache
            self.template_cache[filename] = template
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False