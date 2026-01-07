# fix_cube.py
# Whole-cube rotation search (24 orientations) + strong physical validation diagnostics
# PLUS: per-face 0/90/180/270 rotation search (physics-safe) to fix scanning face-rotation mismatches
# Input/Output: facelet string in URFDLB order (len 54), letters must be U R F D L B.

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
from itertools import product


# ----------------------------
# Facelet helpers (URFDLB)
# ----------------------------
BASE = {"U": 0, "R": 9, "F": 18, "D": 27, "L": 36, "B": 45}

def face_slice(cube: str, face: str) -> str:
    b = BASE[face]
    return cube[b:b+9]

def set_face(cube: str, face: str, new9: str) -> str:
    b = BASE[face]
    return cube[:b] + new9 + cube[b+9:]

def rot_face_cw(f: str) -> str:
    return (
        f[6] + f[3] + f[0] +
        f[7] + f[4] + f[1] +
        f[8] + f[5] + f[2]
    )

def rot_face_ccw(f: str) -> str:
    return (
        f[2] + f[5] + f[8] +
        f[1] + f[4] + f[7] +
        f[0] + f[3] + f[6]
    )

def rot_face_180(f: str) -> str:
    return f[::-1]


# ----------------------------
# Whole-cube rotations (x,y,z)
# ----------------------------
# These are physical cube rotations in space.
def rot_x(c: str) -> str:
    U, R, F, D, L, B = (face_slice(c, x) for x in "URFDLB")

    newU = F
    newF = D
    newD = rot_face_180(B)
    newB = rot_face_180(U)

    newR = rot_face_cw(R)
    newL = rot_face_ccw(L)

    out = c
    out = set_face(out, "U", newU)
    out = set_face(out, "R", newR)
    out = set_face(out, "F", newF)
    out = set_face(out, "D", newD)
    out = set_face(out, "L", newL)
    out = set_face(out, "B", newB)
    return out

def rot_y(c: str) -> str:
    U, R, F, D, L, B = (face_slice(c, x) for x in "URFDLB")

    newF = L
    newR = F
    newB = R
    newL = B

    newU = rot_face_cw(U)
    newD = rot_face_ccw(D)

    out = c
    out = set_face(out, "U", newU)
    out = set_face(out, "R", newR)
    out = set_face(out, "F", newF)
    out = set_face(out, "D", newD)
    out = set_face(out, "L", newL)
    out = set_face(out, "B", newB)
    return out

def rot_z(c: str) -> str:
    U, R, F, D, L, B = (face_slice(c, x) for x in "URFDLB")

    newU = rot_face_cw(R)   # R -> U
    newR = rot_face_cw(D)   # D -> R
    newD = rot_face_cw(L)   # L -> D
    newL = rot_face_cw(U)   # U -> L

    newF = rot_face_cw(F)
    newB = rot_face_ccw(B)

    out = c
    out = set_face(out, "U", newU)
    out = set_face(out, "R", newR)
    out = set_face(out, "F", newF)
    out = set_face(out, "D", newD)
    out = set_face(out, "L", newL)
    out = set_face(out, "B", newB)
    return out

def all_24_orientations(c: str) -> List[str]:
    if len(c) != 54:
        return []
    seen = {c}
    q = [c]
    while q:
        cur = q.pop(0)
        for nxt in (rot_x(cur), rot_y(cur), rot_z(cur)):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return list(seen)  # should be 24


# ----------------------------
# Per-face rotation search (physics-safe)
# ----------------------------
def face_rotations_4(face9: str) -> List[str]:
    """All 4 in-plane rotations of a 3x3 face."""
    r0 = face9
    r1 = rot_face_cw(r0)
    r2 = rot_face_cw(r1)
    r3 = rot_face_cw(r2)
    return [r0, r1, r2, r3]

def cube_with_face_rotations(raw: str, rots: Tuple[int,int,int,int,int,int]) -> str:
    """Apply per-face rotations to URFDLB faces of the cube string."""
    U = face_slice(raw, "U")
    R = face_slice(raw, "R")
    F = face_slice(raw, "F")
    D = face_slice(raw, "D")
    L = face_slice(raw, "L")
    B = face_slice(raw, "B")

    Uv = face_rotations_4(U)[rots[0]]
    Rv = face_rotations_4(R)[rots[1]]
    Fv = face_rotations_4(F)[rots[2]]
    Dv = face_rotations_4(D)[rots[3]]
    Lv = face_rotations_4(L)[rots[4]]
    Bv = face_rotations_4(B)[rots[5]]

    out = raw
    out = set_face(out, "U", Uv)
    out = set_face(out, "R", Rv)
    out = set_face(out, "F", Fv)
    out = set_face(out, "D", Dv)
    out = set_face(out, "L", Lv)
    out = set_face(out, "B", Bv)
    return out


# ----------------------------
# Cubie validation (Kociemba mapping)
# ----------------------------
# Corner positions: URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB
CORNER_FACELETS = [
    (("U", 8), ("R", 0), ("F", 2)),  # URF
    (("U", 6), ("F", 0), ("L", 2)),  # UFL
    (("U", 0), ("L", 0), ("B", 2)),  # ULB
    (("U", 2), ("B", 0), ("R", 2)),  # UBR
    (("D", 2), ("F", 8), ("R", 6)),  # DFR
    (("D", 0), ("L", 8), ("F", 6)),  # DLF
    (("D", 6), ("B", 8), ("L", 6)),  # DBL
    (("D", 8), ("R", 8), ("B", 6)),  # DRB
]

# Edge positions: UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR
EDGE_FACELETS = [
    (("U", 5), ("R", 1)),  # UR
    (("U", 7), ("F", 1)),  # UF
    (("U", 3), ("L", 1)),  # UL
    (("U", 1), ("B", 1)),  # UB
    (("D", 5), ("R", 7)),  # DR
    (("D", 1), ("F", 7)),  # DF
    (("D", 3), ("L", 7)),  # DL
    (("D", 7), ("B", 7)),  # DB
    (("F", 5), ("R", 3)),  # FR
    (("F", 3), ("L", 5)),  # FL
    (("B", 5), ("L", 3)),  # BL
    (("B", 3), ("R", 5)),  # BR
]

LEGAL_CORNERS = [
    tuple("URF"), tuple("UFL"), tuple("ULB"), tuple("UBR"),
    tuple("DFR"), tuple("DLF"), tuple("DBL"), tuple("DRB"),
]
LEGAL_EDGES = [
    tuple("UR"), tuple("UF"), tuple("UL"), tuple("UB"),
    tuple("DR"), tuple("DF"), tuple("DL"), tuple("DB"),
    tuple("FR"), tuple("FL"), tuple("BL"), tuple("BR"),
]

def get_facelet(cube: str, face: str, idx: int) -> str:
    return cube[BASE[face] + idx]

def corner_colors(cube: str, pos: int) -> Tuple[str, str, str]:
    a, b, c = CORNER_FACELETS[pos]
    return (
        get_facelet(cube, a[0], a[1]),
        get_facelet(cube, b[0], b[1]),
        get_facelet(cube, c[0], c[1]),
    )

def edge_colors(cube: str, pos: int) -> Tuple[str, str]:
    a, b = EDGE_FACELETS[pos]
    return (
        get_facelet(cube, a[0], a[1]),
        get_facelet(cube, b[0], b[1]),
    )

def parity_of_perm(p: List[int]) -> int:
    visited = [False] * len(p)
    swaps_parity = 0
    for i in range(len(p)):
        if visited[i]:
            continue
        j = i
        cycle = []
        while not visited[j]:
            visited[j] = True
            cycle.append(j)
            j = p[j]
        if len(cycle) > 0:
            swaps_parity ^= ((len(cycle) - 1) % 2)
    return swaps_parity  # 0 even, 1 odd


@dataclass
class ValidationResult:
    ok: bool
    reason: str
    bad_corners: List[Tuple[int, Tuple[str, str, str]]]
    bad_edges: List[Tuple[int, Tuple[str, str]]]
    counts: Optional[dict] = None
    corner_twist_sum_mod3: Optional[int] = None
    edge_flip_sum_mod2: Optional[int] = None
    corner_parity: Optional[int] = None
    edge_parity: Optional[int] = None

    def score(self) -> int:
        # lower is better
        return len(self.bad_corners) * 10 + len(self.bad_edges) * 10 + (0 if self.ok else 100)


def validate_cube(cube: str) -> ValidationResult:
    if len(cube) != 54:
        return ValidationResult(False, "Length != 54", [], [], counts=None)

    letters = "URFDLB"
    counts = {ch: cube.count(ch) for ch in letters}
    if any(counts[ch] != 9 for ch in letters):
        return ValidationResult(False, f"Bad counts: {counts}", [], [], counts=counts)

    # corners
    legal_corner_sets = [set(x) for x in LEGAL_CORNERS]
    corner_perm = [-1] * 8
    corner_ori = [0] * 8
    bad_corners = []

    for i in range(8):
        cols = corner_colors(cube, i)
        s = set(cols)
        if s not in legal_corner_sets:
            bad_corners.append((i, cols))
            continue
        piece_idx = next(j for j, cc in enumerate(LEGAL_CORNERS) if set(cc) == s)
        corner_perm[i] = piece_idx

        # corner twist: where is U or D within the triplet
        if cols[0] in ("U", "D"):
            corner_ori[i] = 0
        elif cols[1] in ("U", "D"):
            corner_ori[i] = 1
        else:
            corner_ori[i] = 2

    # edges
    legal_edge_sets = [set(x) for x in LEGAL_EDGES]
    edge_perm = [-1] * 12
    edge_ori = [0] * 12
    bad_edges = []

    for i in range(12):
        cols = edge_colors(cube, i)
        s = set(cols)
        if s not in legal_edge_sets:
            bad_edges.append((i, cols))
            continue
        piece_idx = next(j for j, ee in enumerate(LEGAL_EDGES) if set(ee) == s)
        edge_perm[i] = piece_idx

        a, b = cols
        (f1, _), (f2, _) = EDGE_FACELETS[i]

        if "U" in s or "D" in s:
            if (a in ("U", "D") and f1 in ("U", "D")) or (b in ("U", "D") and f2 in ("U", "D")):
                edge_ori[i] = 0
            else:
                edge_ori[i] = 1
        else:
            if (a in ("F", "B") and f1 in ("F", "B")) or (b in ("F", "B") and f2 in ("F", "B")):
                edge_ori[i] = 0
            else:
                edge_ori[i] = 1

    if bad_corners or bad_edges:
        return ValidationResult(
            False,
            "Some corner/edge color SETS are impossible (at least 1 sticker is wrong).",
            bad_corners,
            bad_edges,
            counts=counts
        )

    # duplicates check
    if len(set(corner_perm)) != 8:
        return ValidationResult(False, "Duplicate corner cubie detected.", [], [], counts=counts)
    if len(set(edge_perm)) != 12:
        return ValidationResult(False, "Duplicate edge cubie detected.", [], [], counts=counts)

    twist = sum(corner_ori) % 3
    flip = sum(edge_ori) % 2
    if twist != 0:
        return ValidationResult(
            False,
            "Corner twist sum invalid (one corner is twisted in scan).",
            [], [],
            counts=counts,
            corner_twist_sum_mod3=twist,
            edge_flip_sum_mod2=flip
        )
    if flip != 0:
        return ValidationResult(
            False,
            "Edge flip sum invalid (one edge is flipped in scan).",
            [], [],
            counts=counts,
            corner_twist_sum_mod3=twist,
            edge_flip_sum_mod2=flip
        )

    cpar = parity_of_perm(corner_perm)
    epar = parity_of_perm(edge_perm)
    if cpar != epar:
        return ValidationResult(
            False,
            "Parity mismatch (two cubies swapped OR one sticker wrong).",
            [], [],
            counts=counts,
            corner_twist_sum_mod3=twist,
            edge_flip_sum_mod2=flip,
            corner_parity=cpar,
            edge_parity=epar
        )

    return ValidationResult(
        True,
        "OK",
        [], [],
        counts=counts,
        corner_twist_sum_mod3=twist,
        edge_flip_sum_mod2=flip,
        corner_parity=cpar,
        edge_parity=epar
    )

def remap_urfdlb_by_center_colors(cube: str) -> str:
    """
    Enforce standard cube convention:
    U = White, F = Green, R = Red,
    L = Orange, B = Blue, D = Yellow
    Input and output are 54-char URFDLB strings.
    """

    if len(cube) != 54:
        raise ValueError("Cube string must be 54 characters")

    # Centers (fixed indices in URFDLB)
    centers = {
        cube[4]:  "U",  # Up center
        cube[22]: "F",  # Front center
        cube[13]: "R",  # Right center
        cube[40]: "L",  # Left center
        cube[49]: "B",  # Back center
        cube[31]: "D",  # Down center
    }

    # Ensure we have exactly 6 unique centers
    if len(centers) != 6:
        raise ValueError(f"Invalid centers detected: {centers}")

    # Remap all stickers
    try:
        return "".join(centers[c] for c in cube)
    except KeyError as e:
        raise ValueError(f"Unknown sticker color {e} in cube string")
# ----------------------------
# Public API: fix_cube(raw)
# ----------------------------
def fix_cube(raw: str) -> str:
    raw = raw.strip()

    # quick sanity
    if len(raw) != 54:
        raise ValueError(f"RAW string length must be 54, got {len(raw)}")

    allowed = set("URFDLB")
    if any(ch not in allowed for ch in raw):
        bad = sorted(set([ch for ch in raw if ch not in allowed]))
        raise ValueError(f"RAW contains invalid letters: {bad} (allowed: URFDLB only)")

    # 0) First try: 24 orientations only (fast)
    best: Optional[Tuple[str, ValidationResult]] = None
    for c in all_24_orientations(raw):
        diag = validate_cube(c)
        if diag.ok:
            return c
        if best is None or diag.score() < best[1].score():
            best = (c, diag)

    # 1) Physics-safe rescue: per-face rotations (4^6) + 24 orientations
    best2: Optional[Tuple[str, ValidationResult]] = best
    for rots in product(range(4), repeat=6):
        rotated = cube_with_face_rotations(raw, rots)  # URFDLB rotated in-plane
        for c in all_24_orientations(rotated):
            diag = validate_cube(c)
            if diag.ok:
                return c
            if best2 is None or diag.score() < best2[1].score():
                best2 = (c, diag)

    # If none valid, print BEST diagnostic (closest)
    _, d = best2  # type: ignore

    lines = []
    lines.append("Cube scan is NOT physically valid (after trying per-face rotations + 24 whole-cube orientations).")
    lines.append(f"Reason: {d.reason}")
    if d.counts:
        lines.append(f"Counts: {d.counts}")

    if d.corner_twist_sum_mod3 is not None or d.edge_flip_sum_mod2 is not None:
        if d.corner_twist_sum_mod3 is not None:
            lines.append(f"corner_twist_sum mod 3 = {d.corner_twist_sum_mod3}")
        if d.edge_flip_sum_mod2 is not None:
            lines.append(f"edge_flip_sum mod 2 = {d.edge_flip_sum_mod2}")

    if d.corner_parity is not None and d.edge_parity is not None:
        lines.append(f"corner_parity = {d.corner_parity}, edge_parity = {d.edge_parity}")

    if d.bad_corners:
        lines.append("\nBad corners (pos -> seen letters at URF/UFL/... positions):")
        for pos, cols in d.bad_corners:
            lines.append(f"  corner#{pos}: {cols}")

    if d.bad_edges:
        lines.append("\nBad edges (pos -> seen letters at UR/UF/... positions):")
        for pos, cols in d.bad_edges:
            lines.append(f"  edge#{pos}: {cols}")

    lines.append("\nLikely causes:")
    lines.append("- 1 sticker misread (most common)")
    lines.append("- a face captured at an angle -> wrong sticker index ordering on that face")
    lines.append("- scanning order mismatch (wrong face assigned to U/R/F/D/L/B)")
    lines.append("- cube color classification threshold needs recalibration")

    raise ValueError("\n".join(lines))


# ----------------------------
# CLI quick test
# ----------------------------
if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    if not raw:
        print("Usage: python fix_cube.py <RAW_54_CHAR_STRING>")
        sys.exit(1)

    print("RAW:", raw)
    print("Length:", len(raw))
    fixed = fix_cube(raw)
    print("\nFIXED STRING:")
    print(fixed)
    print("Length:", len(fixed))