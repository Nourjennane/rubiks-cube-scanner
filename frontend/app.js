console.log("APP JS LOADED");

// ---------------- DOM ----------------
const resetVirtualBtn = document.getElementById("resetVirtualBtn");
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
console.log("moveList element =", moveList);

moveList.style.whiteSpace = "pre-wrap";
moveList.style.maxHeight = "200px";
moveList.style.overflowY = "auto";
moveList.style.display = "block";
// ---------------- LOGGER ----------------
function log(text) {
  console.log(text);
  // moveList.textContent = text;  // ❌ remove this line
}

// ---------------- STATE ----------------
let solutionAlg = "";
let isPlaying = false;
let playTimer = null;
let playedAlg = "";   // moves already applied
let currentSetupAlg = "";
let scrambleAlg = "";
let cubeModel   = null;
let solutionMoves = [];   // ["R", "U", "R'", ...]
let stepIndex = 0;        // current step (0 → solutionMoves.length)
let baseSetupAlg = "";         // holds scrambleAlg when using alg mode
const BACKEND_SOLVE_URL   = "http://127.0.0.1:8000/solve";
const BACKEND_SCAN_START = "http://127.0.0.1:8000/scan/start";

// ---------------- HELPERS ----------------
function cubeDictToString(cubeDict) {
  return [
    ...cubeDict.U,
    ...cubeDict.R,
    ...cubeDict.F,
    ...cubeDict.D,
    ...cubeDict.L,
    ...cubeDict.B
  ].join("");
}

function unlockForPlayback() {
  twisty.removeAttribute("experimental-setup-alg");
}
function showSolution() {
  if (!solutionMoves.length) {
    moveList.textContent = "";
    return;
  }
  moveList.textContent = solutionMoves.join(" ");
}

function invertMove(m) {
  if (m.endsWith("2")) return m;
  if (m.endsWith("'")) return m.slice(0, -1);
  return m + "'";
}


function enterStepModeFromSetupAlg(setupAlg) {
  currentSetupAlg = setupAlg;
  playedAlg = "";                // 🔑 reset played moves

  twisty.setAttribute("experimental-setup-alg", setupAlg);
  twisty.setAttribute("alg", "");  // no auto-play
  twisty.jumpToStart?.();
}


function updateStepLabel() {
    stepLabel.textContent = solutionMoves.length
        ? `Step ${stepIndex} / ${solutionMoves.length}`
        : "";
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
    cubeModel = new Cube();
    cubeModel.move(moves);

    // 🔑 THIS IS THE KEY LINE
    scrambleAlg = moves;

    solutionMoves = [];
    solutionAlg = "";
    stepIndex = 0;
    isPlaying = false;

    twisty.removeAttribute("experimental-setup-serialized");
    twisty.setAttribute("experimental-setup-alg", scrambleAlg);
    twisty.setAttribute("alg", "");
    twisty.jumpToStart?.();

    updateStepLabel();
    log("Moves applied:\n" + scrambleAlg);

  } catch (e) {
    console.error(e);
    log("❌ Invalid move sequence.");
  }
}
resetVirtualBtn.onclick = () => {
  console.log("♻️ Reset Virtual Cube");

  // 🧠 Reset internal state
  scrambleAlg = "";
  solutionAlg = "";
  solutionMoves = [];
  stepIndex = 0;
  playedAlg = "";
  isPlaying = false;
  currentSetupAlg = "";
  cubeModel = new Cube(); // solved cube

  // 🧼 Reset UI
  moveList.textContent = "No solution yet.";
  stepLabel.textContent = "";

  // 🧊 SAFE Twisty reset (NO attribute removal)
  twisty.setAttribute("experimental-setup-alg", "");
  twisty.setAttribute("alg", "");
  twisty.jumpToStart?.();

  console.log("✅ Cube fully reset (solved, stable)");
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
  // 1️⃣ Generate scramble
  scrambleAlg = randomScramble();

  // 2️⃣ Update logical cube (optional but good practice)
  cubeModel = new Cube();
  cubeModel.move(scrambleAlg);

  // 3️⃣ Clear any existing solution state
  solutionMoves = [];
  stepIndex = 0;
  updateStepLabel();

  // 4️⃣ SHOW scrambled cube and FREEZE it
  enterStepModeFromSetupAlg(scrambleAlg);

  // 5️⃣ Log
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
  if (!scrambleAlg || !scrambleAlg.trim()) {
    log("❌ No virtual scramble to solve.");
    return;
  }

  console.log("🧠 SOLVE VIRTUAL CLICKED");
  console.log("ScrambleAlg =", scrambleAlg);

  // 1️⃣ Build logical cube from scramble
  const cube = new Cube();
  cube.move(scrambleAlg);

  // 2️⃣ Convert to 54-char URFDLB string
  const cubeString = cube.asString();
  console.log("📤 Sending cube string:", cubeString, cubeString.length);

  // 3️⃣ Send to backend solver
  const res = await fetch(BACKEND_SOLVE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cube: cubeString })
  });

  const data = await res.json();

  if (!res.ok) {
    console.error("❌ Solve failed:", data);
    log("❌ Error while solving virtual cube.");
    return;
  }

  // 4️⃣ Extract solution moves
  if (Array.isArray(data.moves)) {
    solutionMoves = data.moves;
  } else if (typeof data.moves === "string") {
    solutionMoves = data.moves.trim().split(/\s+/);
  } else {
    log("❌ Invalid solver response.");
    return;
  }

  solutionAlg = solutionMoves.join(" ");
  console.log("✅ Solution:", solutionAlg);

  // 5️⃣ SHOW solution in UI
  moveList.textContent = solutionAlg;

  // 🔑 🔑 🔑 THIS WAS MISSING
  // Give Twisty an animation timeline
  twisty.setAttribute("alg", solutionAlg);

  // 6️⃣ Reset cube to scrambled state (static setup)
  currentSetupAlg = scrambleAlg;
  playedAlg = "";
  stepIndex = 0;
  isPlaying = false;

  twisty.removeAttribute("experimental-setup-serialized");
  twisty.setAttribute("experimental-setup-alg", scrambleAlg);
  twisty.jumpToStart?.();

  updateStepLabel();
  log("✅ Virtual cube ready — press ▶ to animate.");
};
solveExternalBtn.onclick = () => {
  const pasted = cubeStringInput.value
    .trim()
    .replace(/[’‘`]/g, "'")
    .replace(/\s+/g, " ");

  if (!pasted) {
    log("❌ Paste reversed solution.");
    return;
  }

  // 1️⃣ This is the scramble that produced the scanned cube
  const setupAlg = pasted;

  // 2️⃣ Compute the REAL solution (inverse of pasted)
  solutionMoves = reverseAlgorithm(setupAlg).split(/\s+/);
  solutionAlg   = solutionMoves.join(" ");

  // 3️⃣ Reset state
  stepIndex = 0;
  isPlaying = false;

  // 4️⃣ ENTER STEP MODE (static, safe)
  currentSetupAlg = setupAlg;
  twisty.removeAttribute("experimental-setup-serialized");
  twisty.setAttribute("experimental-setup-alg", setupAlg);
  twisty.setAttribute("alg", "");
  twisty.jumpToStart?.();

  // 5️⃣ Update UI
  updateStepLabel();
  showSolution();

  log("✅ Scanned cube ready. Use ▶ / ◀ or ▶▶ Play.");
};

nextStepBtn.onclick = () => {
  isPlaying = false;
  if (stepIndex >= solutionMoves.length) return;

  const move = solutionMoves[stepIndex];
  playedAlg = playedAlg ? `${playedAlg} ${move}` : move;

  twisty.setAttribute("alg", playedAlg);

  stepIndex++;
  updateStepLabel();
};

prevStepBtn.onclick = () => {
  isPlaying = false;
  if (stepIndex <= 0) return;

  stepIndex--;
  playedAlg = solutionMoves.slice(0, stepIndex).join(" ");

  twisty.setAttribute("alg", playedAlg);
  updateStepLabel();
};
// ---------------- PLAY ----------------
playBtn.onclick = () => {
  twisty.play();
};


// ---------------- RESET ----------------
resetBtn.onclick = () => {
  isPlaying = false;
  stepIndex = 0;
  playedAlg = "";

  if (currentSetupAlg) enterStepModeFromSetupAlg(currentSetupAlg);

  updateStepLabel();
  log("Reset.");
};

// ---------------- THEME ----------------
document.body.classList.add("apple-light");
themeToggle.onclick = () => {
    document.body.classList.toggle("apple-dark");
    document.body.classList.toggle("apple-light");
};

