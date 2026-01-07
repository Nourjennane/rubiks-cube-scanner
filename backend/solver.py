import kociemba

def solve_cube(cube_string: str):
    """
    Solve a Rubik's Cube given a 54-character facelet string.
    Returns a list of moves.
    """
    try:
        solution = kociemba.solve(cube_string)
        return solution.split()
    except Exception as e:
        raise ValueError(f"Invalid cube state: {e}")