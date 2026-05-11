<p align="center">
  <img src="Images/AIEDA.png" width="100%">
</p>

<h1 align="center">AIDEA</h1>

<p align="center">
Artificial Intelligence Driven Electronic Design Automation Platform
</p>



# ⚡ AI-Driven EDA Tool for RTL Analysis & Verification

> An AI-powered Electronic Design Automation (EDA) assistant that automates Verilog analysis, debugging, and simulation using a **local LLM (Ollama)** with a **Flask-based backend pipeline**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Verilog](https://img.shields.io/badge/Verilog-RTL-orange?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey?style=flat-square&logo=flask)
![Ollama](https://img.shields.io/badge/LLM-Ollama-purple?style=flat-square)
![ModelSim](https://img.shields.io/badge/Simulator-ModelSim-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow?style=flat-square)

---

## 🚀 Overview

This project bridges the gap between **AI-based code understanding** and **hardware verification workflows**. Traditional EDA tools require significant manual effort for debugging, testbench authoring, and result interpretation. This tool automates that pipeline end-to-end — from Verilog upload to AI-generated circuit insights.

Unlike general-purpose AI code assistants, this tool is purpose-built for RTL:

- 🧠 **AI-based RTL analysis** — LLM-powered syntax and logic error detection with fix suggestions
- 🔁 **Simulation feedback loop** — AI-generated fixes are validated through ModelSim simulation iteratively
- 🖥️ **Fully local execution** — runs offline using Ollama; no cloud dependency or data upload
- 📊 **Waveform + diagram output** — VCD waveform generation and circuit visualization in one pipeline

---

## 🧩 Architecture

```
Local HTML  (Upload & Display)
      ↓
Flask Local Server  (Pipeline Orchestration)
      ↓
Ollama (LLM Analysis) + ModelSim (Simulation Engine)
      ↓
Results returned to UI  (Logs / Waveforms / Diagrams / AI Explanation)
```

---

## ⚙️ Tech Stack

| Component | Technology |
|---|---|
| Backend orchestration | Python 3.10+ |
| Frontend UI | Streamlit |
| Server pipeline | Flask |
| AI / LLM engine | Ollama (local, offline) |
| Simulation engine | ModelSim / Icarus Verilog |
| Hardware design input | Verilog (.v) |
| Waveform format | VCD (Value Change Dump) |

---

## 📁 Project Structure

```
AI_EDA_TOOL/
├── app/
│   ├── templates/
│   ├── app.py                  # Flask app entry point
│   └── app.txt
├── backend/
│   ├── ai/
│   │   ├── ai_engine.py        # LLM prompt + response handler
│   │   └── analyzer.py         # Waveform pattern analysis
│   ├── parser/
│   │   ├── verilog_parser.py   # Module/port/gate extraction
│   │   ├── fsm_generator.py    # Sequential logic → FSM
│   │   ├── netlist_visualizer.py
│   │   └── diagram.py
│   ├── simulation/
│   │   ├── simulator.py        # ModelSim/Icarus simulation runner
│   │   └── tb_generator.py     # Auto testbench generation
│   ├── ppa/
│   │   └── ppa_analyzer.py     # Power-Performance-Area estimation
│   ├── truth/
│   │   └── truth_table.py      # Logic truth table generator
│   └── utils/
│       └── cleaner.py
├── static/                     # circuit.png, fsm.png, style.css
├── runs/                       # design.v, tb.v, wave.vcd, out.vvp
├── Verilog codes/              # Sample RTL: adders, gates, full_adder
└── models/
```

---

## 🔄 Workflow

```
1. Upload Verilog (.v) file via Streamlit UI
       ↓
2. Parser extracts modules, ports, gates, FSM (if sequential)
       ↓
3. Structured prompt sent to Ollama LLM
       ↓
4. AI performs:
     • Syntax error detection
     • Logical issue identification
     • Code correction with explanation
     • Top-module extraction
       ↓
5. Auto-generated testbench (tb.v) passed to ModelSim
       ↓
6. Simulation produces VCD waveform + logs
       ↓
7. AI Analysis Engine interprets waveform patterns
       ↓
8. Results displayed: waveform viewer, truth table, PPA estimate, AI explanation
```

---

## ✨ Features

### Currently Implemented
- ✅ Verilog file upload via UI
- ✅ AI-based syntax and logical error detection (Ollama)
- ✅ Code correction suggestions with explanations
- ✅ Automatic testbench generation
- ✅ ModelSim simulation + VCD waveform extraction
- ✅ GTKWave-compatible waveform output
- ✅ Truth table generation
- ✅ Circuit diagram visualization
- ✅ Log output display in UI

### Roadmap
- 🔄 Automatic testbench generation (in progress)
- 🔄 Multi-module and multi-file design support
- 🔄 Improved LLM prompt engineering for synthesizability
- 🔄 Real-time waveform visualization in browser
- 🔄 Integration with open-source tools (Yosys, GTKWave embedded)
- 🔄 Coverage-driven feedback loop (in progress)
- 🔄 FSM extraction for sequential designs
- 🔄 PPA (Power, Performance, Area) estimation (in progress)
- 🔄 Full RTL-to-GDSII flow exploration (in progress)

---

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- ModelSim or Icarus Verilog installed and on system PATH

### Installation

```bash
# Clone the repository
git clone https://github.com/MaheedharBhamidipati/AI-Driven-EDA-Tool-for-RTL-Analysis-Verification.git
cd AI-Driven-EDA-Tool-for-RTL-Analysis-Verification

# Install dependencies
pip install -r requirements.txt

# Start Ollama server (in a separate terminal)
ollama serve

# Pull the LLM model (phi3 recommended for hardware tasks)
ollama pull phi3

# Run the Flask application
cd app
python app.py
```

The app will be available at `http://127.0.0.1:5000`

---

## 💡 Key Innovation

This tool implements an **AI + Simulation feedback loop** — a concept now central to commercial AI-EDA platforms. The flow:

1. LLM analyzes RTL and suggests a fix
2. Fix is compiled and simulated automatically
3. Simulation output is fed back to the AI analysis engine
4. Human-readable explanation of circuit behavior is generated

This positions the tool as an early prototype of the AI-augmented EDA workflows being explored by industry (Cadence JedAI, Synopsys.ai, etc.).

---

## 🎥 Demo

| Demo | Link |
|---|---|
| Basic model working | [Watch on Google Drive](https://drive.google.com/file/d/1xPqQAtJI0-7rtnDBuFz3Sr7tOk_hUEli/view?usp=sharing) |
| EDA Toolkit with waveform & logic visualization | Available in repo (`Verilog EDA Toolkit with Waveform & Logic Visualization Video.mp4`) |

---

## 🧠 Future Scope

- ML-trained models for fault detection and design optimization suggestions
- Integration with Yosys for open-source synthesis
- FPGA deployment pipeline (RTL → bitstream)
- Performance benchmarking against commercial EDA tool baselines
- Multi-language support (VHDL input)

---

## 👨‍💻 Author

**V N S S S R Maheedhar Bhamidipati**  
M.Tech VLSI Design | Amrita Vishwa Vidyapeetham, Bengaluru (2025)  
FPGA · UVM · SystemVerilog · AI for Hardware

[![LinkedIn](https://img.shields.io/badge/LinkedIn-maheedhar--bhamidipati-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/maheedhar-bhamidipati)
[![GitHub](https://img.shields.io/badge/GitHub-MaheedharBhamidipati-black?style=flat-square&logo=github)](https://github.com/MaheedharBhamidipati)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-brightgreen?style=flat-square)](https://maheedhar-bhamidipati-portfolio.netlify.app/)

---
