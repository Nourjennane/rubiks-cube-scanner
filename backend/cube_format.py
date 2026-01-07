FACE_ORDER = ["U", "R", "F", "D", "L", "B"]

def validate_cube_format(cube: dict):
    if not isinstance(cube, dict):
        raise ValueError("Cube must be a dictionary.")

    for face in FACE_ORDER:
        if face not in cube:
            raise ValueError(f"Missing face {face}")
        if len(cube[face]) != 9:
            raise ValueError(f"Face {face} must have 9 stickers")

def validate_colors(cube: dict):
    all_stickers = []
    for face in FACE_ORDER:
        all_stickers.extend(cube[face])

    counts = {c: all_stickers.count(c) for c in set(all_stickers)}
    if len(counts) != 6:
        raise ValueError("Cube must have exactly 6 colors")

    for c, n in counts.items():
        if n != 9:
            raise ValueError(f"Color {c} appears {n} times")

def cube_to_string(cube: dict) -> str:
    """
    cube contains faces in SCAN ORDER:
    1: Green
    2: Red
    3: Blue
    4: Orange
    5: White
    6: Yellow
    """

    # Map scanned faces → solver faces (URFDLB)
    remapped = {
        "U": cube["White"],
        "R": cube["Red"],
        "F": cube["Green"],
        "D": cube["Yellow"],
        "L": cube["Orange"],
        "B": cube["Blue"],
    }

    return (
        "".join(remapped["U"]) +
        "".join(remapped["R"]) +
        "".join(remapped["F"]) +
        "".join(remapped["D"]) +
        "".join(remapped["L"]) +
        "".join(remapped["B"])
    )