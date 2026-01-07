import math

calibration = {}

def calibrate_face(face: str, rgb: tuple):
    calibration[face] = rgb

def _dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

def map_color(rgb: tuple):
    if not calibration:
        raise ValueError("Calibration not set")

    return min(calibration, key=lambda f: _dist(rgb, calibration[f]))

def map_face_colors(rgb_list):
    return [map_color(rgb) for rgb in rgb_list]