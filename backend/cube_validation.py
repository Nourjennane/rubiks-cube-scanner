# cube_validation.py
# Full Rubik's Cube solvability checks for a Kociemba-style facelet string.
#
# This module assumes the cube is given as a 54-character string using
# the standard face colors:
#   U, R, F, D, L, B
#
# Facelet order (indices 0–53):
#   U1..U9, R1..R9, F1..F9, D1..D9, L1..L9, B1..B9
#
# That matches the Kociemba Python package.

# ----------------------------------------------------------------------
# Helpers: mapping from facelet (U1, R3, etc.) to index in the 54-char string
# ----------------------------------------------------------------------

def _idx(face: str, pos: int) -> int:
    """Return index in cube_string for face (U,R,F,D,L,B) and position 1–9."""
    offsets = {"U": 0, "R": 9, "F": 18, "D": 27, "L": 36, "B": 45}
    return offsets[face] + (pos - 1)

# Corner positions (URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB)
# Each entry is a triple of indices into cube_string.
# Order and indices follow Kociemba's reference implementation.
corner_facelets = [
    (_idx("U", 9),  _idx("R", 1),  _idx("F", 3)),  # URF
    (_idx("U", 7),  _idx("F", 1),  _idx("L", 3)),  # UFL
    (_idx("U", 1),  _idx("L", 1),  _idx("B", 3)),  # ULB
    (_idx("U", 3),  _idx("B", 1),  _idx("R", 3)),  # UBR
    (_idx("D", 3),  _idx("F", 9),  _idx("R", 7)),  # DFR
    (_idx("D", 1),  _idx("L", 9),  _idx("F", 7)),  # DLF
    (_idx("D", 7),  _idx("B", 9),  _idx("L", 7)),  # DBL
    (_idx("D", 9),  _idx("R", 9),  _idx("B", 7)),  # DRB
]

# Edge positions (UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR)
edge_facelets = [
    (_idx("U", 6),  _idx("R", 2)),  # UR
    (_idx("U", 8),  _idx("F", 2)),  # UF
    (_idx("U", 4),  _idx("L", 2)),  # UL
    (_idx("U", 2),  _idx("B", 2)),  # UB
    (_idx("D", 6),  _idx("R", 8)),  # DR
    (_idx("D", 2),  _idx("F", 8)),  # DF
    (_idx("D", 4),  _idx("L", 8)),  # DL
    (_idx("D", 8),  _idx("B", 8)),  # DB
    (_idx("F", 6),  _idx("R", 4)),  # FR
    (_idx("F", 4),  _idx("L", 6)),  # FL
    (_idx("B", 6),  _idx("L", 4)),  # BL
    (_idx("B", 4),  _idx("R", 6)),  # BR
]

# Canonical cubie color definitions (like Kociemba's cornerColor / edgeColor)
corner_colors = [
    ["U", "R", "F"],  # URF
    ["U", "F", "L"],  # UFL
    ["U", "L", "B"],  # ULB
    ["U", "B", "R"],  # UBR
    ["D", "F", "R"],  # DFR
    ["D", "L", "F"],  # DLF
    ["D", "B", "L"],  # DBL
    ["D", "R", "B"],  # DRB
]

edge_colors = [
    ["U", "R"],  # UR
    ["U", "F"],  # UF
    ["U", "L"],  # UL
    ["U", "B"],  # UB
    ["D", "R"],  # DR
    ["D", "F"],  # DF
    ["D", "L"],  # DL
    ["D", "B"],  # DB
    ["F", "R"],  # FR
    ["F", "L"],  # FL
    ["B", "L"],  # BL
    ["B", "R"],  # BR
]


# ----------------------------------------------------------------------
# Orientation & parity helpers
# ----------------------------------------------------------------------

def check_corner_orientation(co):
    """
    Sum of corner orientations (0,1,2) must be 0 mod 3.
    """
    return sum(co) % 3 == 0


def check_edge_orientation(eo):
    """
    Sum of edge flips (0 or 1) must be 0 mod 2.
    """
    return sum(eo) % 2 == 0


def _permutation_parity(p):
    """
    Returns 0 for even permutation, 1 for odd.
    p is a list like [0,1,2,...] describing where each cubie went.
    """
    visited = set()
    parity = 0
    for i in range(len(p)):
        if i not in visited:
            cycle_len = 0
            j = i
            while j not in visited:
                visited.add(j)
                j = p[j]
                cycle_len += 1
            parity += cycle_len - 1
    return parity % 2


def check_parity(corner_perm, edge_perm):
    """
    Corners and edges must have the SAME parity (both even or both odd).
    Otherwise the cube state is unsolvable.
    """
    return _permutation_parity(corner_perm) == _permutation_parity(edge_perm)


# ----------------------------------------------------------------------
# Extract corners / edges, permutations & orientations from cube_string
# ----------------------------------------------------------------------

def extract_corners(cube_string):
    """
    From a 54-character cube_string, compute:
      - cp: corner permutation (list of 8 ints, each in 0..7)
      - co: corner orientation (list of 8 ints, each in {0,1,2})

    Algorithm mirrors Kociemba's FaceCube -> CubieCube conversion.
    """
    cp = [None] * 8  # which cubie is in each corner position
    co = [0] * 8     # orientation for each corner

    for i in range(8):  # for each corner position
        # find which of the 3 facelets is on U or D
        ori = 0
        for o in range(3):
            c = cube_string[corner_facelets[i][o]]
            if c == "U" or c == "D":
                ori = o
                break

        # the other two colors (in order) relative to that orientation
        c1 = cube_string[corner_facelets[i][(ori + 1) % 3]]
        c2 = cube_string[corner_facelets[i][(ori + 2) % 3]]

        # find which canonical corner cubie matches these two colors
        found = False
        for j in range(8):
            if c1 == corner_colors[j][1] and c2 == corner_colors[j][2]:
                cp[i] = j
                co[i] = ori % 3
                found = True
                break

        if not found:
            raise ValueError(f"Invalid corner cubie colors at corner position {i}")

    # Ensure cp is a proper permutation of 0..7
    if sorted(cp) != list(range(8)):
        raise ValueError("Corner permutation is invalid – duplicate or missing corner.")

    return cp, co


def extract_edges(cube_string):
    """
    From a 54-character cube_string, compute:
      - ep: edge permutation (list of 12 ints, each in 0..11)
      - eo: edge orientation (list of 12 ints, each in {0,1})

    Mirrors Kociemba's FaceCube -> CubieCube edge extraction.
    """
    ep = [None] * 12  # which cubie is in each edge position
    eo = [0] * 12     # orientation for each edge

    for i in range(12):  # for each edge position
        c0 = cube_string[edge_facelets[i][0]]
        c1 = cube_string[edge_facelets[i][1]]
        found = False

        for j in range(12):
            # orientation 0: colors match in the same order
            if c0 == edge_colors[j][0] and c1 == edge_colors[j][1]:
                ep[i] = j
                eo[i] = 0
                found = True
                break

            # orientation 1: colors reversed
            if c0 == edge_colors[j][1] and c1 == edge_colors[j][0]:
                ep[i] = j
                eo[i] = 1
                found = True
                break

        if not found:
            raise ValueError(f"Invalid edge cubie colors at edge position {i}")

    # Ensure ep is a proper permutation of 0..11
    if sorted(ep) != list(range(12)):
        raise ValueError("Edge permutation is invalid – duplicate or missing edge.")

    return ep, eo


# ----------------------------------------------------------------------
# Public API: main solvability check
# ----------------------------------------------------------------------

def is_cube_solvable(cube_string: str) -> bool:
    """
    Full Rubik's Cube solvability test for a 54-character facelet string.

    Raises:
        ValueError with an explanation if the cube is not solvable.

    Returns:
        True if the cube passes all checks.
    """

    if len(cube_string) != 54:
        raise ValueError("Cube string must have length 54.")

    # Extract cubie-level representation
    cp, co = extract_corners(cube_string)
    ep, eo = extract_edges(cube_string)

    # Corner orientation sum must be 0 mod 3
    if not check_corner_orientation(co):
        raise ValueError("Corner orientation invalid — cube is unsolvable.")

    # Edge orientation sum must be 0 mod 2
    if not check_edge_orientation(eo):
        raise ValueError("Edge orientation invalid — cube is unsolvable.")

    # Parity of corners and edges must match
    if not check_parity(cp, ep):
        raise ValueError("Corner and edge permutation parity do not match — cube is unsolvable.")

    # If we reach here, all checks passed
    return True
































