# reorder.py
# Reorder scanner output into canonical URFDLB face order

def reorder_faces_to_urfdlb(state: str) -> str:
    """
    Takes a 54-char cube string coming from the scanner
    and reorders faces into canonical URFDLB order.

    ASSUMPTION (for now, to get you unstuck):
    - state already contains exactly 9 of each letter
    - center stickers identify faces
    """

    if len(state) != 54:
        raise ValueError(f"Expected 54 chars, got {len(state)}")

    # Split into 6 faces of 9 stickers EACH
    faces = [state[i:i+9] for i in range(0, 54, 9)]

    # Identify faces by their center sticker (index 4)
    by_center = {}
    for face in faces:
        center = face[4]
        by_center[center] = face

    # Canonical mapping
    try:
        U = by_center["U"]  # white
        R = by_center["R"]  # red
        F = by_center["F"]  # green
        D = by_center["D"]  # yellow
        L = by_center["L"]  # orange
        B = by_center["B"]  # blue
    except KeyError as e:
        raise ValueError(f"Missing face with center {e}")

    # Return in URFDLB order
    return U + R + F + D + L + B