# solver_hsv.py
import kociemba

# -------------------------------------------------
# PURE SOLVER (NO CAMERA, NO CALLBACK CHEATS)
# -------------------------------------------------

def solve_cube(cube_string: str):
    """
    Solve a Rubik's cube given a 54-character cube string
    in URFDLB order.

    Raises ValueError if cube is invalid.
    """

    if not isinstance(cube_string, str):
        raise ValueError("Cube string must be a string")

    if len(cube_string) != 54:
        raise ValueError("Cube string must be exactly 54 characters")

    allowed = set("URFDLB")
    if any(c not in allowed for c in cube_string):
        raise ValueError("Cube string contains invalid characters")

    # Color count check (9 of each)
    for c in allowed:
        if cube_string.count(c) != 9:
            raise ValueError(f"Invalid cube: {c} appears {cube_string.count(c)} times")

    try:
        solution = kociemba.solve(cube_string)
    except Exception as e:
        raise ValueError(f"Kociemba failed: {e}")

    return solution.split()