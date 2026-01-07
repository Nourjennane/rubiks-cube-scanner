from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List

from solver import solve_cube
from cube_validation import is_cube_solvable

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FACE_ORDER = ["U", "R", "F", "D", "L", "B"]

COLOR_TO_FACE = {
    # full names
    "WHITE": "U",
    "YELLOW": "D",
    "GREEN": "F",
    "BLUE": "B",
    "RED": "R",
    "ORANGE": "L",
    # single-letter colors
    "W": "U",
    "Y": "D",
    "G": "F",
    "B": "B",
    "R": "R",
    "O": "L",
    # already facelets
    "U": "U",
    "R": "R",
    "F": "F",
    "D": "D",
    "L": "L",
    "B": "B",
}

class CubeRequest(BaseModel):
    cube: Dict[str, List[str]]

def normalize_cube_to_facelets(cube: Dict[str, List[str]]) -> str:
    # Require faces U,R,F,D,L,B
    for f in FACE_ORDER:
        if f not in cube:
            raise ValueError(f"Missing face '{f}' in cube payload.")
        if len(cube[f]) != 9:
            raise ValueError(f"Face '{f}' must have 9 stickers.")

    out = []
    for f in FACE_ORDER:
        for s in cube[f]:
            key = str(s).strip().upper()
            if key not in COLOR_TO_FACE:
                raise ValueError(f"Unknown sticker value: {s}")
            out.append(COLOR_TO_FACE[key])

    facelets = "".join(out)

    # quick count check
    for ch in "URFDLB":
        if facelets.count(ch) != 9:
            raise ValueError(
                f"Bad counts: {ch} appears {facelets.count(ch)} times (must be 9)."
            )

    return facelets

@app.post("/solve")
def solve(req: CubeRequest):
    try:
        cube_string = normalize_cube_to_facelets(req.cube)  # ALWAYS URFDLB
        is_cube_solvable(cube_string)
        moves = solve_cube(cube_string)
        return {"moves": moves}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})