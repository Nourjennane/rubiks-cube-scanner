# backend/constants.py

from pathlib import Path
import os 
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# ===============================
# UI / Visualization constants
# ===============================

# Placeholder color (used before calibration)
COLOR_PLACEHOLDER = (128, 128, 128)

# Cube color palette (BGR for OpenCV)
CUBE_PALETTE = {
    'U': (255, 255, 255),   # white
    'D': (0, 255, 255),     # yellow
    'F': (0, 255, 0),       # green
    'B': (255, 0, 0),       # blue
    'R': (0, 0, 255),       # red
    'L': (0, 165, 255),     # orange
}

# Locales supported by UI
LOCALES = {
    "en": "EN"
}

# Text rendering
TEXT_SIZE = 20

# OpenCV drawing colors
STICKER_CONTOUR_COLOR = (0, 255, 0)  # green


# ===============================
# Keyboard controls (OpenCV)
# ===============================

CALIBRATE_MODE_KEY = ord('c')     # press 'c' to calibrate
SWITCH_LANGUAGE_KEY = ord('l')    # press 'l' to switch language
EXIT_KEY = ord('q')


# ===============================
# Error codes
# ===============================

E_INCORRECTLY_SCANNED = 1
E_ALREADY_SOLVED = 2

# ===============================
# Sticker layout (pixel values)
# ===============================

STICKER_AREA_TILE_SIZE = 40
STICKER_AREA_TILE_GAP = 6
STICKER_AREA_OFFSET = 20

MINI_STICKER_AREA_TILE_SIZE = 18
MINI_STICKER_AREA_TILE_GAP = 4
MINI_STICKER_AREA_OFFSET = 10