console.log("APP JS LOADED");

// ---------------- DOM ----------------
const twisty      = document.getElementById("twisty");
const scrambleBtn = document.getElementById("scrambleBtn");

const playBtn     = document.getElementById("playBtn");
const resetBtn    = document.getElementById("resetBtn");

const displayStringBtn = document.getElementById("displayStringBtn");const cubeStringInput   = document.getElementById("cubeStringInput");

const moveList    = document.getElementById("moveList");
const themeToggle = document.getElementById("themeToggle");
const prevStepBtn = document.getElementById("prevStepBtn");
const nextStepBtn = document.getElementById("nextStepBtn");
const stepLabel   = document.getElementById("stepLabel");
const solveVirtualBtn = document.getElementById("solveVirtualBtn");
const solveExternalBtn = document.getElementById("solveExternalBtn");
// ---------------- LOGGER ----------------
function log(text) {
    console.log(text);
    moveList.textContent = text;
}

// ---------------- STATE ----------------

let scrambleAlg = "";
let solutionAlg = "";
let cubeModel   = null;
let solutionMoves = [];   // ["R", "U", "R'", ...]
let stepIndex = 0;        // current step (0 → solutionMoves.length)
let baseMode = "alg";          // "alg" | "serialized"
let baseSerialized = "";       // holds scanned cube state
let baseSetupAlg = "";         // holds scrambleAlg when using alg mode
const BACKEND_SOLVE_URL   = "http://127.0.0.1:8000/solve";
const BACKEND_SCAN_START = "http://127.0.0.1:8000/scan/start";

// ---------------- HELPERS ----------------
function applyMovesToScannedCube(pastedReversedSolution) {
    if (!baseSerialized) {
        log("No scanned cube loaded.");
        return;
    }

    // Reset cube to scanned state
    twisty.setAttribute("experimental-setup-serialized", baseSerialized);
    twisty.setAttribute("experimental-setup-alg", "");
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    // Apply moves
    solutionMoves = moves
        .trim()
        .replace(/[’‘`]/g, "'")
        .split(/\s+/);

    solutionAlg = solutionMoves.join(" ");
    stepIndex = solutionMoves.length;

    twisty.setAttribute("alg", solutionAlg);
    updateStepLabel();

    log("Applied reversed solution to scanned cube ✅");
}
function loadExternalCubeFromURFDLB(raw54) {
    const s = raw54.trim().toUpperCase().replace(/[^URFDLB]/g, "");

    if (s.length !== 54) {
        log("❌ Paste a 54-character cube string using only U R F D L B.");
        return;
    }

    // store it for Solve External
    baseMode = "serialized";
    baseSerialized = s;
    baseSetupAlg = "";

    // show it in 3D
    twisty.setAttribute("experimental-setup-serialized", baseSerialized);
    twisty.setAttribute("experimental-setup-alg", "");
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    // keep a model too (optional but useful)
    cubeModel = new Cube(baseSerialized);

    solutionMoves = [];
    solutionAlg = "";
    stepIndex = 0;
    updateStepLabel();

    log("External cube loaded ✅ Now click Solve Pasted / Scanned Cube.");
}
function updateStepLabel() {
    stepLabel.textContent = solutionMoves.length
        ? `Step ${stepIndex} / ${solutionMoves.length}`
        : "";
}

function renderCurrentStep() {
    const partial = solutionMoves.slice(0, stepIndex).join(" ");

    twisty.setAttribute("alg", partial);
    twisty.jumpToStart?.();

    updateStepLabel();
}
function reverseAlgorithm(alg) {
    if (!alg) return "";

    return alg
        .trim()
        .split(/\s+/)
        .reverse()
        .map(m => {
            if (m.endsWith("2")) return m;        // R2 stays R2
            if (m.endsWith("'")) return m[0];     // R' → R
            return m + "'";                       // R → R'
        })
        .join(" ");
}
// 🔑 LOCK ORIENTATION: U on top, F in front
// 🔑 LOCK ORIENTATION: U on top, R in front (red front)
// 🔒 FULL ORIENTATION LOCK (all 6 centers)
function rotateCubeToCanonical(cube) {
    const rotations = [
        "", "x", "x2", "x'",
        "y", "y2", "y'",
        "z", "z2", "z'",
        "x y", "x y2", "x y'",
        "x' y", "x' y2", "x' y'",
        "x2 y", "x2 y2", "x2 y'",
        "x z", "x z2", "x z'",
        "x' z", "x' z2", "x' z'",
        "y z", "y z2", "y z'",
        "y' z", "y' z2", "y' z'",
        "x y z", "x y z2", "x y z'",
        "x' y z", "x' y z2", "x' y z'"
    ];

    for (const r of rotations) {
        const test = cube.clone();
        if (r) test.move(r);

        const s = test.asString();

        // URFDLB centers must match exactly
        if (
            s[4]  === "U" && // white
            s[13] === "R" && // red
            s[22] === "F" && // green
            s[31] === "D" && // yellow
            s[40] === "L" && // orange
            s[49] === "B"    // blue
        ) {
            if (r) cube.move(r);
            return;
        }
    }

    console.error("❌ Could not canonicalize cube orientation");
}

// 🔑 CENTER-BASED CANONICALIZATION
function remapByCenters(urfdlb) {
    const centers = {
        U: urfdlb[4],
        R: urfdlb[13],
        F: urfdlb[22],
        D: urfdlb[31],
        L: urfdlb[40],
        B: urfdlb[49],
    };

    const map = {};
    for (const f in centers) {
        map[centers[f]] = f;
    }

    return urfdlb.split("").map(c => map[c]).join("");
}

function normalizeCubeString(raw) {
    return raw.toUpperCase().replace(/[^URFDLB]/g, "");
}

function hasValidFaceCounts(s) {
    const c = {U:0,R:0,F:0,D:0,L:0,B:0};
    for (const x of s) c[x]++;
    return Object.values(c).every(v => v === 9);
}

function cubeStringToDict(facelets) {
    return {
        U: facelets.slice(0,9).split(""),
        R: facelets.slice(9,18).split(""),
        F: facelets.slice(18,27).split(""),
        D: facelets.slice(27,36).split(""),
        L: facelets.slice(36,45).split(""),
        B: facelets.slice(45,54).split("")
    };
}

// ---------------- LOAD MOVES ----------------
function loadCubeFromMoves(movesRaw) {
    const moves = movesRaw
        .trim()
        .replace(/[’‘`]/g, "'")
        .replace(/\s+/g, " ");

    if (!moves) {
        log("❌ Please paste a move sequence.");
        return;
    }

    try {
        // ✅ IMPORTANT: switch twisty to ALG mode by REMOVING serialized attribute
        twisty.removeAttribute("experimental-setup-serialized");

        // Always start from solved cube if none exists
        if (!cubeModel) {
            cubeModel = new Cube();
            scrambleAlg = "";
        }

        // Apply moves to logical cube
        cubeModel.move(moves);

        // Keep full history so it accumulates
        scrambleAlg = scrambleAlg ? `${scrambleAlg} ${moves}` : moves;
        baseMode = "alg";
        baseSetupAlg = scrambleAlg;
        baseSerialized = "";
        // ✅ Render by ALG (setup-alg)
        twisty.setAttribute("experimental-setup-alg", scrambleAlg);
        twisty.setAttribute("alg", "");
        twisty.jumpToStart?.();

        solutionAlg = "";

        log("Moves applied ✅");

    } catch (e) {
        console.error(e);
        log("❌ Invalid move sequence.");
    }
}

// ✅ YOU WERE MISSING THESE → input box "does nothing" without them
displayStringBtn.onclick = () => {
    loadCubeFromMoves(cubeStringInput.value);
};

cubeStringInput.addEventListener("paste", () => {
    setTimeout(() => {
        loadCubeFromMoves(cubeStringInput.value);
    }, 0);
});

// ---------------- SCRAMBLE ----------------
function randomScramble(n=20) {
    const m=["R","R'","R2","L","L'","L2","U","U'","U2","D","D'","D2","F","F'","F2","B","B'","B2"];
    return Array.from({length:n},()=>m[Math.floor(Math.random()*m.length)]).join(" ");
}

scrambleBtn.onclick = () => {
    scrambleAlg = randomScramble();

    cubeModel = new Cube();
    cubeModel.move(scrambleAlg);

    // 🔒 VIRTUAL MODE = ALG BASE
    twisty.removeAttribute("experimental-setup-serialized");
    twisty.setAttribute("experimental-setup-alg", scrambleAlg);
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    solutionMoves = [];
    solutionAlg = "";
    stepIndex = 0;
    updateStepLabel();

    log("Scramble:\n" + scrambleAlg);
};

// ---------------- SOLVE ----------------
// 🔁 MOVE REMAP: solver coords → real-life hand coords
const MOVE_REMAP = {
    "R": "F",
    "R'": "F'",
    "R2": "F2",

    "F": "L",
    "F'": "L'",
    "F2": "L2",

    "L": "B",
    "L'": "B'",
    "L2": "B2",

    "B": "R",
    "B'": "R'",
    "B2": "R2",

    "U": "U",
    "U'": "U'",
    "U2": "U2",

    "D": "D",
    "D'": "D'",
    "D2": "D2",
};
solveVirtualBtn.onclick = async () => {
    if (!scrambleAlg) {
        log("No virtual scramble to solve.");
        return;
    }

    // Rebuild cube from scramble (logic only)
    const cube = new Cube();
    cube.move(scrambleAlg);

    const res = await fetch(BACKEND_SOLVE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            cube: cubeStringToDict(cube.asString())
        })
    });

    const data = await res.json();

    solutionMoves = data.moves;
    solutionAlg = solutionMoves.join(" ");
    stepIndex = 0;

    // 🔥 CRITICAL: re-assert scramble as base
    twisty.removeAttribute("experimental-setup-serialized");
    twisty.setAttribute("experimental-setup-alg", scrambleAlg);
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    updateStepLabel();
    log("Solution (virtual cube):\n" + solutionAlg);
};

solveExternalBtn.onclick = () => {

    // 🔑 FIRST: lock current cube if not already scanned
    if (!baseSerialized && cubeModel) {
        baseSerialized = cubeModel.asString();
        baseMode = "serialized";
    }

    // ❌ NOW check
    if (!baseSerialized) {
        log("❌ No scanned cube loaded.");
        return;
    }

    const pasted = cubeStringInput.value
        .trim()
        .replace(/[’‘`]/g, "'");

    if (!pasted) {
        log("❌ Paste the reversed solution moves.");
        return;
    }

    const realSolution = reverseAlgorithm(pasted);

    solutionMoves = realSolution.split(/\s+/);
    solutionAlg   = solutionMoves.join(" ");
    stepIndex = 0;

    twisty.setAttribute("experimental-setup-serialized", baseSerialized);
    twisty.setAttribute("experimental-setup-alg", "");
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    updateStepLabel();
    log("Solution (from reversed input):\n" + solutionAlg);
};

nextStepBtn.onclick = () => {
    if (!solutionMoves.length) return;
    stepIndex = Math.min(stepIndex + 1, solutionMoves.length);
    renderCurrentStep();
};

prevStepBtn.onclick = () => {
    if (!solutionMoves.length) return;
    stepIndex = Math.max(stepIndex - 1, 0);
    renderCurrentStep();
};
// ---------------- PLAY ----------------
playBtn.onclick = () => {
    if (!solutionAlg) return;
    twisty.jumpToStart();
    twisty.play();
};

// ---------------- RESET ----------------
resetBtn.onclick = () => {
    cubeModel = null;
    scrambleAlg = "";
    solutionAlg = "";

    // 1️⃣ clear alg FIRST
    twisty.setAttribute("alg", "");

    // 2️⃣ defer setup change to next tick (VERY IMPORTANT)
    setTimeout(() => {
        twisty.setAttribute("experimental-setup-serialized", baseSerialized);
        twisty.setAttribute("experimental-setup-alg", "");
        twisty.jumpToStart?.();
    }, 0);

    log("Reset.");
};



// ---------------- THEME ----------------
document.body.classList.add("apple-light");
themeToggle.onclick = () => {
    document.body.classList.toggle("apple-dark");
    document.body.classList.toggle("apple-light");
};