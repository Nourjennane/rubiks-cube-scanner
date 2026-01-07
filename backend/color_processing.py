# backend/color_processing.py
import numpy as np
from backend.constants import CUBE_PALETTE


def _dist(a, b):
    # a,b are (b,g,r)
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


class ColorDetector:
    def __init__(self):
        # default palette = constants palette
        self.cube_color_palette = dict(CUBE_PALETTE)

    def set_cube_color_pallete(self, calibrated_colors: dict):
        """
        QBR calls this after calibration.
        calibrated_colors example:
          {"green": (b,g,r), "red": (b,g,r), ...}
        """
        self.cube_color_palette = dict(calibrated_colors)

    def get_dominant_color(self, bgr_image):
        """
        Input: OpenCV ROI image (H,W,3) BGR
        Output: (b,g,r) ints
        """
        if bgr_image is None or getattr(bgr_image, "size", 0) == 0:
            return (0, 0, 0)

        # mean over H,W
        b = int(np.mean(bgr_image[:, :, 0]))
        g = int(np.mean(bgr_image[:, :, 1]))
        r = int(np.mean(bgr_image[:, :, 2]))
        return (b, g, r)

    def get_prominent_color(self, sticker_pixels):
        """
        In your UI you sometimes pass already-averaged BGR tuple.
        If it's a list of pixels, average them.
        """
        if isinstance(sticker_pixels, tuple) and len(sticker_pixels) == 3:
            return sticker_pixels

        if isinstance(sticker_pixels, list) and len(sticker_pixels) > 0:
            p0 = sticker_pixels[0]
            if isinstance(p0, int):
                # already [b,g,r]
                if len(sticker_pixels) >= 3:
                    return (int(sticker_pixels[0]), int(sticker_pixels[1]), int(sticker_pixels[2]))
                return (0, 0, 0)

            # list of (b,g,r)
            b = int(sum(p[0] for p in sticker_pixels) / len(sticker_pixels))
            g = int(sum(p[1] for p in sticker_pixels) / len(sticker_pixels))
            r = int(sum(p[2] for p in sticker_pixels) / len(sticker_pixels))
            return (b, g, r)

        return (0, 0, 0)

    def get_closest_color(self, color_bgr, palette=None):
        """
        Output must be a dict because your video.py does:
          closest['color_name']
          closest['color_bgr']
          closest['bgr']
        """
        if palette is None:
            palette = self.cube_color_palette

        # palette MUST be dict: { "green": (b,g,r), ... }
        if not isinstance(palette, dict):
            palette = self.cube_color_palette

        closest_name = min(palette.keys(), key=lambda k: _dist(color_bgr, palette[k]))
        closest_bgr = palette[closest_name]

        return {
            "color_name": closest_name,
            "color_bgr": closest_bgr,  # ✅ what your code expects later
            "bgr": closest_bgr,        # ✅ you also use closest['bgr']
        }


# ✅ This is what your video.py imports
color_detector = ColorDetector()

# keep this too since you call color_processing.get_prominent_color(...)
def get_prominent_color(x):
    return color_detector.get_prominent_color(x)