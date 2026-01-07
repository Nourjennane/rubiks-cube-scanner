# 🧩🤖 Rubik’s Cube Scanner & Solver

An end-to-end **Rubik’s Cube scanner and solver** built using **computer vision**, **algorithmic validation**, and an **interactive 3D web interface**.

This project takes a **real physical Rubik’s Cube**, scans it using a camera, reconstructs its exact state, checks whether the configuration is physically valid, computes a solution, and visualizes the solving process step by step in the browser.

The goal is not just to solve the cube — but to build a **robust, modular, and realistic perception-to-solution pipeline**, handling real-world noise and ambiguity.

---

## 🚀 What this project does

✅ Scans a real Rubik’s Cube using a camera  
🎨 Detects sticker colors using HSV color processing  
🧠 Reconstructs the full cube state from scanned faces  
🔍 Validates physical solvability (edges, corners, parity)  
🧮 Computes a valid solving sequence  
🧊 Animates the solution on a 3D cube in the browser  

---

## 🏗️ System architecture

The project is split into **two clearly separated layers**.

### 🐍 Backend (Python)

Handles all computation and reasoning:
- 📷 Camera access and video frame capture  
- 🎨 Color detection and normalization  
- 🧩 Face and cube reconstruction  
- ⚠️ Physical cube validation  
- 🤖 Solving algorithm computation  

### 🌐 Frontend (Web)

Handles visualization and user interaction:
- 🧊 Interactive 3D Rubik’s Cube  
- ▶️ Step-by-step solution playback  
- ⏮️⏭️ Manual step navigation  
- 🔄 Reset and replay controls  

This separation keeps the system **clean, testable, and extensible**.

---

## 🔁 Processing pipeline

```
Camera input
    ↓
Color detection (HSV)
    ↓
Face reconstruction
    ↓
Cube state reconstruction
    ↓
Physical validation
    ↓
Solution computation
    ↓
3D visualization
```

Each stage is independent, making debugging and future improvements straightforward.

---

## 🧰 Tech stack

### Backend
- 🐍 Python 3  
- 📷 OpenCV  
- 🔢 NumPy  
- 🧠 Custom cube validation & solving logic  

### Frontend
- 🌐 HTML  
- 🎨 CSS  
- ⚙️ JavaScript  
- 🧊 Twisty Player (3D cube visualization)  

---

## 📁 Project structure

```
RubiksBackend/
├── backend/
│   ├── main.py              # Backend entry point
│   ├── scanner.py           # Camera scanning logic
│   ├── video.py             # Video capture utilities
│   ├── color_processing.py  # HSV color detection
│   ├── cube_format.py       # Cube data formatting
│   ├── cube_validation.py   # Physical feasibility checks
│   ├── solver.py            # Solving algorithm
│   ├── reorder.py           # Face reordering logic
│   ├── solver_hsv.py        # Experimental solver variant
│   └── scan_state.py        # Scan state handling
│
├── frontend/
│   ├── index.html           # Web interface
│   ├── app.js               # Frontend logic
│   ├── style.css            # Styling
│   └── libs/                # 3D visualization libraries
│
└── README.md
```

---

## ▶️ Running the project locally

### 🐍 Backend

From the project root:
```
cd backend
python main.py
```

This starts the backend responsible for scanning and solving.

### 🌐 Frontend

Open `frontend/index.html` directly in your browser  
(or serve it with a local HTTP server).

---

## 🎥 Demo

A short demo video demonstrates:
- 📷 Scanning a real cube  
- 🧮 Computing a solution  
- 🧊 Playing the solution step by step on the 3D cube  

📹 *Demo video link coming soon.*

---

## 🎯 Motivation

This project was built to explore the intersection of:
- 👁️ Computer vision applied to physical objects  
- 🧩 Constraint-based validation problems  
- 🤖 Algorithmic reasoning  
- 🌐 Full-stack system integration  

Real-world cube scanning introduces noise, lighting issues, and ambiguity — a major focus of the project was making the system **robust, not just correct**.

---

## 🔮 Possible improvements

✨ More robust color detection under difficult lighting  
⚡ Faster multi-face scanning  
📱 Mobile camera support  
📉 Solution move count optimization  
📤 Exporting solutions in standard cube notation formats  

---

## 👩‍💻 Author

**Nour Jennane**  

GitHub: https://github.com/Nourjennane  

---

🧠✨ Built with curiosity, iteration, and a lot of debugging.
