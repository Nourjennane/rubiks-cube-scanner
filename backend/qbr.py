#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import os
import i18n
import kociemba

from fix_cube import fix_cube
from video import webcam
from config import config
from constants import ROOT_DIR, E_INCORRECTLY_SCANNED, E_ALREADY_SOLVED
import itertools
import kociemba

def reverse_algorithm(alg: str) -> str:
    moves = alg.strip().split()
    reversed_moves = []

    for m in reversed(moves):
        if m.endswith("2"):
            reversed_moves.append(m)       # R2 → R2
        elif m.endswith("'"):
            reversed_moves.append(m[0])    # R' → R
        else:
            reversed_moves.append(m + "'") # R → R'

    return " ".join(reversed_moves)

def rotate_face_cw_str(face9: str) -> str:
    # face9 is 9 chars, row-major
    f = list(face9)
    return "".join([
        f[6], f[3], f[0],
        f[7], f[4], f[1],
        f[8], f[5], f[2],
    ])

def rotate_face_n(face9: str, n: int) -> str:
    out = face9
    for _ in range(n % 4):
        out = rotate_face_cw_str(out)
    return out

def try_fix_by_rotating_faces_only(urfdlb54: str):
    """
    Keep the 6 faces in the same URFDLB slots (centers fixed),
    but try 0/90/180/270 rotation for each face.
    Return a solvable cube string or None.
    """
    U = urfdlb54[0:9]
    R = urfdlb54[9:18]
    F = urfdlb54[18:27]
    D = urfdlb54[27:36]
    L = urfdlb54[36:45]
    B = urfdlb54[45:54]

    faces = [U, R, F, D, L, B]

    for rots in itertools.product([0,1,2,3], repeat=6):  # 4^6 = 4096
        cand_faces = [rotate_face_n(face, r) for face, r in zip(faces, rots)]
        cand = "".join(cand_faces)
        try:
            kociemba.solve(cand)
            return cand, rots
        except Exception:
            pass

    return None, None
# ---------------- CENTER REMAP ----------------
def remap_scanner_to_standard_by_centers(cube: str) -> str:
    if len(cube) != 54:
        raise ValueError("Cube must be 54 chars")

    center_map = {
        cube[4]:  "U",
        cube[31]: "D",
        cube[22]: "F",
        cube[49]: "B",
        cube[13]: "R",
        cube[40]: "L",
    }

    if len(center_map) != 6:
        raise ValueError("Invalid centers")

    return "".join(center_map[c] for c in cube)

# ---------------- I18N ----------------
locale = config.get_setting('locale') or 'en'
config.set_setting('locale', locale)

i18n.load_path.append(os.path.join(ROOT_DIR, 'translations'))
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'json')
i18n.set('locale', locale)
i18n.set('fallback', 'en')

# ---------------- QBR ----------------
class Qbr:
    def __init__(self, normalize=False):
        self.normalize = normalize

    def run(self):
        raw = webcam.run()

        if isinstance(raw, int):
            self.print_E_and_exit(raw)

        print("\nRAW CUBE STRING:")
        print(raw)
        print("Length:", len(raw))

        mapped = remap_scanner_to_standard_by_centers(raw)
        fixed = mapped

        print("\n✅ FIXED / VALID CUBE STRING:")
        print(fixed)
        print("Length:", len(fixed))
        print("==============================\n")

        # If kociemba fails, try rotating faces only (common scan issue)
        try:
            solution = kociemba.solve(fixed)
        except Exception:
            alt, rots = try_fix_by_rotating_faces_only(fixed)
            if alt is None:
                print("❌ Still unsolvable even after trying all face rotations.")
                print("Cube string was:", fixed)
                return
            print("✅ Solvable after rotating some faces (rots URFDLB):", rots)
            fixed = alt
            solution = kociemba.solve(fixed)

        moves = solution.split()

        print(i18n.t('startingPosition'))
        print(i18n.t('moves', moves=len(moves)))
        print(i18n.t('solution', algorithm=solution))

        reversed_solution = reverse_algorithm(solution)
        print("Reversed solution (to scramble):")
        print(reversed_solution)

        if self.normalize:
            for i,m in enumerate(moves,1):
                print(f"{i}. {i18n.t(f'solveManual.{m}')}" )

    def print_E_and_exit(self, code):
        sys.exit(code)

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--normalize",action="store_true")
    Qbr(parser.parse_args().normalize).run()
