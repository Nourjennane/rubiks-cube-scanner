#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ts=4 sw=4 et
import cv2
from backend import color_processing 
from backend.config import config
from backend.helpers import get_next_locale
from backend.color_processing import color_detector
import i18n
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from backend.constants import (
    COLOR_PLACEHOLDER,
    LOCALES,
    ROOT_DIR,
    CUBE_PALETTE,
    MINI_STICKER_AREA_TILE_SIZE,
    MINI_STICKER_AREA_TILE_GAP,
    MINI_STICKER_AREA_OFFSET,
    STICKER_AREA_TILE_SIZE,
    STICKER_AREA_TILE_GAP,
    STICKER_AREA_OFFSET,
    STICKER_CONTOUR_COLOR,
    CALIBRATE_MODE_KEY,
    SWITCH_LANGUAGE_KEY,
    TEXT_SIZE,
    E_INCORRECTLY_SCANNED,
    E_ALREADY_SOLVED
)
# ============================================================
# ✅ FACE ORIENTATION NORMALIZATION (ROTATIONS ONLY)
# ============================================================
# ============================================================
# ✅ DETECTED COLOR NAME -> REAL CUBE COLOR NAME
# (based on what you observed on centers)
# ============================================================

class Webcam:

    def __init__(self):
        print('Starting webcam... (this might take a while, please be patient)')
        # Force internal MacBook camera
        self.cam = None
        self.finished = False
        for i in range(5):  # try camera indices 0..4
            cam = cv2.VideoCapture(i)
            if cam.isOpened():
                ret, frame = cam.read()
                if ret and frame is not None:
                    self.cam = cam
                    print(f"Using camera index {i}")
                    break
                cam.release()

        if self.cam is None:
            raise RuntimeError("No valid camera found")
        print('Webcam successfully started')

        self.colors_to_calibrate = ['green', 'red', 'blue', 'orange', 'white', 'yellow']
        self.average_sticker_colors = {}
        self.result_state = {}
        


        self.snapshot_state = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]
        self.preview_state  = [(255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255),
                               (255,255,255), (255,255,255), (255,255,255)]

        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.calibrate_mode = False
        self.calibrated_colors = {}
        self.current_color_to_calibrate_index = 0
        self.done_calibrating = False

    def draw_stickers(self, stickers, offset_x, offset_y):
        """Draws the given stickers onto the given frame."""
        index = -1
        for row in range(3):
            for col in range(3):
                index += 1
                x1 = (offset_x + STICKER_AREA_TILE_SIZE * col) + STICKER_AREA_TILE_GAP * col
                y1 = (offset_y + STICKER_AREA_TILE_SIZE * row) + STICKER_AREA_TILE_GAP * row
                x2 = x1 + STICKER_AREA_TILE_SIZE
                y2 = y1 + STICKER_AREA_TILE_SIZE

                # shadow
                cv2.rectangle(
                    self.frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 0),
                    -1
                )

                # foreground color
                cv2.rectangle(
                    self.frame,
                    (x1 + 1, y1 + 1),
                    (x2 - 1, y2 - 1),
                    color_processing.get_prominent_color(stickers[index]),
                    -1
                )

    def draw_preview_stickers(self):
        """Draw the current preview state onto the given frame."""
        self.draw_stickers(self.preview_state, STICKER_AREA_OFFSET, STICKER_AREA_OFFSET)

    def draw_snapshot_stickers(self):
        """Draw the current snapshot state onto the given frame."""
        y = STICKER_AREA_TILE_SIZE * 3 + STICKER_AREA_TILE_GAP * 2 + STICKER_AREA_OFFSET * 2
        self.draw_stickers(self.snapshot_state, STICKER_AREA_OFFSET, y)

    def find_contours(self, dilatedFrame):
        """Find the contours of a 3x3x3 cube."""
        contours, hierarchy = cv2.findContours(
            dilatedFrame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        final_contours = []

        # ------------------------------------------------------------
        # Step 1/4: filter square-ish contours
        # ------------------------------------------------------------
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                (x, y, w, h) = cv2.boundingRect(approx)
                ratio = w / float(h)

                if (
                    0.8 <= ratio <= 1.2
                    and 30 <= w <= 60
                    and area / (w * h) > 0.4
                ):
                    final_contours.append((x, y, w, h))

        if len(final_contours) < 9:
            return []

        # ------------------------------------------------------------
        # Step 2/4: find contour cluster with 9 neighbors
        # ------------------------------------------------------------
        contour_neighbors = {}
        for index, (x, y, w, h) in enumerate(final_contours):
            contour_neighbors[index] = []
            cx = x + w / 2
            cy = y + h / 2
            radius = 1.5

            neighbor_positions = [
                (cx - w * radius, cy - h * radius),
                (cx,              cy - h * radius),
                (cx + w * radius, cy - h * radius),
                (cx - w * radius, cy),
                (cx,              cy),
                (cx + w * radius, cy),
                (cx - w * radius, cy + h * radius),
                (cx,              cy + h * radius),
                (cx + w * radius, cy + h * radius),
            ]

            for (x2, y2, w2, h2) in final_contours:
                for (px, py) in neighbor_positions:
                    if (
                        x2 < px < x2 + w2 and
                        y2 < py < y2 + h2
                    ):
                        contour_neighbors[index].append((x2, y2, w2, h2))

        found = False
        for neighbors in contour_neighbors.values():
            if len(neighbors) == 9:
                final_contours = neighbors
                found = True
                break

        if not found:
            return []

        # ------------------------------------------------------------
        # ✅ FINAL FIX — STABLE 3×3 ORDERING (NO BUCKETING)
        # ------------------------------------------------------------
        # Sort by Y (top → bottom)
        final_contours.sort(key=lambda c: c[1])

        # Split into rows and sort each by X (left → right)
        row1 = sorted(final_contours[0:3], key=lambda c: c[0])
        row2 = sorted(final_contours[3:6], key=lambda c: c[0])
        row3 = sorted(final_contours[6:9], key=lambda c: c[0])

        sorted_contours = row1 + row2 + row3

        if len(sorted_contours) != 9:
            return []

        return sorted_contours
        # ============================================================

    def scanned_successfully(self):
        """Validate if the user scanned 9 colors for each side."""
        color_count = {}
        for side, preview in self.result_state.items():
            for bgr in preview:
                key = str(bgr)
                if key not in color_count:
                    color_count[key] = 1
                else:
                    color_count[key] = color_count[key] + 1
        invalid_colors = [k for k, v in color_count.items() if v != 9]
        return len(invalid_colors) == 0

    def draw_contours(self, contours):
        """Draw contours onto the given frame."""
        if self.calibrate_mode:
            # Only show the center piece contour.
            (x, y, w, h) = contours[4]
            cv2.rectangle(self.frame, (x, y), (x + w, y + h), STICKER_CONTOUR_COLOR, 2)
        else:
            for index, (x, y, w, h) in enumerate(contours):
                cv2.rectangle(self.frame, (x, y), (x + w, y + h), STICKER_CONTOUR_COLOR, 2)

    def update_preview_state(self, contours):
        max_average_rounds = 14

        for index, (x, y, w, h) in enumerate(contours):

            # 🔒 Tight ROI (CRITICAL)
            pad_y = int(h * 0.30)
            pad_x = int(w * 0.30)

            roi = self.frame[
                y + pad_y : y + h - pad_y,
                x + pad_x : x + w - pad_x
            ]

            if roi.size == 0:
                continue

            roi_blur = cv2.GaussianBlur(roi, (5, 5), 0)
            avg_bgr = color_detector.get_dominant_color(roi_blur)
            closest = color_detector.get_closest_color(avg_bgr)
           

            # ❌ Reject uncertain colors
            if closest['color_name'] is None:
                continue

            if index not in self.average_sticker_colors:
                self.average_sticker_colors[index] = []

            self.average_sticker_colors[index].append(closest['bgr'])
            if len(self.average_sticker_colors[index]) > max_average_rounds:
                self.average_sticker_colors[index].pop(0)

            votes = {}
            for bgr in self.average_sticker_colors[index]:
                k = str(bgr)
                votes[k] = votes.get(k, 0) + 1

            most_common_color = max(votes, key=votes.get)
            self.preview_state[index] = eval(most_common_color)


    def update_snapshot_state(self):
        detected_color = color_detector.get_closest_color(
            self.preview_state[4]
        )['color_name']

        if detected_color is None:
            print("❌ Center uncertain — hold still")
            return

        # ❌ Reject duplicate face
        if detected_color in self.result_state:
            print(f"❌ Face '{detected_color}' already scanned")
            return

        # 🔒 Require ALL 9 stickers to be reasonably stable
        unstable = 0
        for i in range(9):
            hist = self.average_sticker_colors.get(i, [])
            if len(hist) < 4:
                unstable += 1
                continue

            votes = {}
            for c in hist:
                k = str(c)
                votes[k] = votes.get(k, 0) + 1

            if max(votes.values()) < 3:
                unstable += 1

        # allow ONE unstable sticker (corner glare, reflection)
        if unstable > 1:
            print(f"❌ Too many unstable stickers ({unstable})")
            return

        # ✅ Store RAW face exactly as seen
        self.snapshot_state = list(self.preview_state)
        self.result_state[detected_color] = list(self.preview_state)

        # reset averaging for next face
        self.average_sticker_colors = {}

        print(f"✅ Stored face: {detected_color}")

        if len(self.result_state) == 6:
            print("🎉 All faces scanned")
            self.finished = True

    def get_font(self, size):
        return ImageFont.load_default()

    def render_text(self, text, pos, color=(255, 255, 255), size=TEXT_SIZE, anchor='lt'):
        """
        Render text with a shadow using the pillow module.
        """
        font = self.get_font(size)

        # Convert opencv frame (np.array) to PIL Image array.
        frame = Image.fromarray(self.frame)

        # Draw the text onto the image.
        draw = ImageDraw.Draw(frame)
        draw.text(pos, text, font=font, fill=color, anchor=anchor,
                  stroke_width=1, stroke_fill=(0, 0, 0))

        # Convert the pillow frame back to a numpy array.
        self.frame = np.array(frame)

    def get_text_size(self, text, size=TEXT_SIZE):
        """Get text size based on the default freetype2 loaded font."""
        return self.get_font(size).getsize(text)

    def draw_scanned_sides(self):
        """Display how many sides are scanned by the user."""
        text = i18n.t('scannedSides', num=len(self.result_state.keys()))
        self.render_text(text, (20, self.height - 20), anchor='lb')

    def draw_current_color_to_calibrate(self):
        """Display the current side's color that needs to be calibrated."""
        offset_y = 20
        font_size = int(TEXT_SIZE * 1.25)
        if self.done_calibrating:
            messages = [
                i18n.t('calibratedSuccessfully'),
                i18n.t('quitCalibrateMode', keyValue=CALIBRATE_MODE_KEY),
            ]
            for index, text in enumerate(messages):
                _, textsize_height = self.get_text_size(text, font_size)
                y = offset_y + (textsize_height + 10) * index
                self.render_text(text, (int(self.width / 2), y), size=font_size, anchor='mt')
        else:
            current_color = self.colors_to_calibrate[self.current_color_to_calibrate_index]
            text = i18n.t('currentCalibratingSide.{}'.format(current_color))
            self.render_text(text, (int(self.width / 2), offset_y), size=font_size, anchor='mt')

    def draw_calibrated_colors(self):
        """Display all the colors that are calibrated while in calibrate mode."""
        offset_y = 20
        for index, (color_name, color_bgr) in enumerate(self.calibrated_colors.items()):
            x1 = 90
            y1 = int(offset_y + STICKER_AREA_TILE_SIZE * index)
            x2 = x1 + STICKER_AREA_TILE_SIZE
            y2 = y1 + STICKER_AREA_TILE_SIZE

            # shadow
            cv2.rectangle(
                self.frame,
                (x1, y1),
                (x2, y2),
                (0, 0, 0),
                -1
            )

            # foreground
            cv2.rectangle(
                self.frame,
                (x1 + 1, y1 + 1),
                (x2 - 1, y2 - 1),
                tuple([int(c) for c in color_bgr]),
                -1
            )
            self.render_text(i18n.t(color_name), (20, y1 + STICKER_AREA_TILE_SIZE / 2 - 3), anchor='lm')

    def reset_calibrate_mode(self):
        """Reset calibrate mode variables."""
        self.calibrated_colors = {}
        self.current_color_to_calibrate_index = 0
        self.done_calibrating = False

    def draw_current_language(self):
        text = '{}: {}'.format(
            i18n.t('language'),
            LOCALES[config.get_setting('locale')]
        )
        offset = 20
        self.render_text(text, (self.width - offset, offset), anchor='rt')

    def draw_2d_cube_state(self):
        # 🔧 Renderer global orientation fix (x2 rotation)
        
        """
        Create a 2D cube state visualization and draw the self.result_state.
        """
        grid = {
            'U': [1, 0],
            'L': [0, 1],
            'F': [1, 1],
            'R': [2, 1],
            'B': [3, 1],
            'D': [1, 2],
        }

        side_offset = MINI_STICKER_AREA_TILE_GAP * 3
        side_size = MINI_STICKER_AREA_TILE_SIZE * 3 + MINI_STICKER_AREA_TILE_GAP * 2
        offset_x = self.width - (side_size * 4) - (side_offset * 3) - MINI_STICKER_AREA_OFFSET
        offset_y = self.height - (side_size * 3) - (side_offset * 2) - MINI_STICKER_AREA_OFFSET

        for side, (grid_x, grid_y) in grid.items():
            mapped_side = side
            index = -1
            for row in range(3):
                for col in range(3):
                    index += 1
                    x1 = int(
                        (offset_x + MINI_STICKER_AREA_TILE_SIZE * col) +
                        (MINI_STICKER_AREA_TILE_GAP * col) +
                        ((side_size + side_offset) * grid_x)
                    )
                    y1 = int(
                        (offset_y + MINI_STICKER_AREA_TILE_SIZE * row) +
                        (MINI_STICKER_AREA_TILE_GAP * row) +
                        ((side_size + side_offset) * grid_y)
                    )
                    x2 = int(x1 + MINI_STICKER_AREA_TILE_SIZE)
                    y2 = int(y1 + MINI_STICKER_AREA_TILE_SIZE)

                    foreground_color = COLOR_PLACEHOLDER
                    if mapped_side in self.result_state:
                        foreground_color = color_processing.get_prominent_color(
                            self.result_state[mapped_side][index]
                        )
                    cv2.rectangle(self.frame, (x1, y1), (x2, y2), (0, 0, 0), -1)
                    cv2.rectangle(self.frame, (x1 + 1, y1 + 1), (x2 - 1, y2 - 1), foreground_color, -1)

    def get_result_notation(self):
        """
        Build a Kociemba-compatible cube string in URFDLB order.
        Assumes result_state keys are already U R F D L B.
        """

        FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']

        # Map center colors → face letters
        COLOR_TO_FACE = {
            'white':  'U',
            'yellow': 'D',
            'green':  'F',
            'blue':   'B',
            'red':    'R',
            'orange': 'L'
        }

        cube_string = ""

        for face in FACE_ORDER:
            stickers = self.result_state[face]

            for bgr in stickers:
                color_name = color_detector.get_closest_color(bgr)['color_name']
                cube_string += color_name

        return cube_string

    def state_already_solved(self):
        for side in self.result_state.keys():
            center_bgr = self.result_state[side][4]
            for bgr in self.result_state[side]:
                if center_bgr != bgr:
                    return False
        return True

    def run(self):
        """
        Open up the webcam and present the user with the Qbr user interface.
        Returns a string of the scanned state in rubik's cube notation.
        """
        while not self.finished:
            _, frame = self.cam.read()
            self.frame = frame
            key = cv2.waitKey(10) & 0xff

            if key == 27:
                break

            if not self.calibrate_mode:
                if key == 32:
                    self.update_snapshot_state()

                if key == SWITCH_LANGUAGE_KEY:
                    next_locale = get_next_locale(config.get_setting('locale'))
                    config.set_setting('locale', next_locale)
                    i18n.set('locale', next_locale)

            if key == CALIBRATE_MODE_KEY:
                self.reset_calibrate_mode()
                self.calibrate_mode = not self.calibrate_mode

            grayFrame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            blurredFrame = cv2.blur(grayFrame, (3, 3))
            cannyFrame = cv2.Canny(blurredFrame, 30, 60, 3)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilatedFrame = cv2.dilate(cannyFrame, kernel)

            contours = self.find_contours(dilatedFrame)
            if len(contours) == 9:
                self.draw_contours(contours)
                if not self.calibrate_mode:
                    self.update_preview_state(contours)
                elif key == 32 and self.done_calibrating is False:
                    current_color = self.colors_to_calibrate[self.current_color_to_calibrate_index]
                    (x, y, w, h) = contours[4]
                    roi = self.frame[y+7:y+h-7, x+14:x+w-14]
                    avg_bgr = color_detector.get_dominant_color(roi)
                    self.calibrated_colors[current_color] = avg_bgr
                    self.current_color_to_calibrate_index += 1
                    self.done_calibrating = self.current_color_to_calibrate_index == len(self.colors_to_calibrate)
                    if self.done_calibrating:
                        color_detector.set_cube_color_pallete(self.calibrated_colors)
                        config.set_setting(CUBE_PALETTE, color_detector.cube_color_palette)

            if self.calibrate_mode:
                self.draw_current_color_to_calibrate()
                self.draw_calibrated_colors()
            else:
                self.draw_current_language()
                self.draw_preview_stickers()
                self.draw_snapshot_stickers()
                self.draw_scanned_sides()
                self.draw_2d_cube_state()

            cv2.imshow("Qbr - Rubik's cube solver", self.frame)

        self.cam.release()
        cv2.destroyAllWindows()

        if len(self.result_state.keys()) != 6:
            return E_INCORRECTLY_SCANNED

        if not self.scanned_successfully():
            return E_INCORRECTLY_SCANNED

        if self.state_already_solved():
            return E_ALREADY_SOLVED

        return self.get_result_notation()


webcam = Webcam()