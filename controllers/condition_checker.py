import numpy as np
import cv2
import os
from enum import Enum


class ConditionType(Enum):
    TEMPLATE_PRESENT = "template_present"
    TEMPLATE_ABSENT = "template_absent"
    COLOR_PRESENT = "color_present"
    PIXEL_COLOR = "pixel_color"


class ConditionChecker:

    def __init__(self, opencv_processor):
        self.opencv_processor = opencv_processor

    def check_condition(self, condition):
        if not condition or 'type' not in condition:
            return False

        condition_type = condition['type']
        data = condition.get('data', {})

        if condition_type == ConditionType.TEMPLATE_PRESENT.value:
            return self._check_template_present(data)

        elif condition_type == ConditionType.TEMPLATE_ABSENT.value:
            return not self._check_template_present(data)

        elif condition_type == ConditionType.COLOR_PRESENT.value:
            return self._check_color_present(data)

        elif condition_type == ConditionType.PIXEL_COLOR.value:
            return self._check_pixel_color(data)

        return False

    def _check_template_present(self, data):
        template_path = data.get('template_path', '')
        threshold = data.get('threshold', 0.8)

        if not os.path.exists(template_path):
            return False

        match = self.opencv_processor.find_template(
                template_path,
                threshold=threshold
        )

        return match is not None

    def _check_color_present(self, data):
        color_range = data.get('color_range', None)
        min_area = data.get('min_area', 100)

        if not color_range or len(color_range) != 2:
            return False

        color_match = self.opencv_processor.find_color(
                color_range,
                min_area=min_area
        )

        return color_match is not None

    def _check_pixel_color(self, data):
        x = data.get('x', 0)
        y = data.get('y', 0)
        color = data.get('color', [0, 0, 0])
        tolerance = data.get('tolerance', 10)

        if not self.opencv_processor.last_frame is not None:
            return False

        frame = self.opencv_processor.last_frame

        if y >= frame.shape[0] or x >= frame.shape[1]:
            return False

        pixel_color = frame[y, x]

        for i in range(min(len(pixel_color), len(color))):
            if abs(int(pixel_color[i]) - int(color[i])) > tolerance:
                return False

        return True