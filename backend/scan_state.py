FACE_ORDER = ["U", "R", "F", "D", "L", "B"]

scan_data = {f: None for f in FACE_ORDER}

def reset_scan():
    for f in scan_data:
        scan_data[f] = None

def store_face(face, colors):
    if face not in scan_data:
        raise ValueError("Invalid face")
    if len(colors) != 9:
        raise ValueError("Face must have 9 stickers")
    scan_data[face] = colors

def scan_complete():
    return all(scan_data[f] is not None for f in scan_data)

def get_scanned_cube():
    if not scan_complete():
        raise ValueError("Scan incomplete")
    return scan_data.copy()