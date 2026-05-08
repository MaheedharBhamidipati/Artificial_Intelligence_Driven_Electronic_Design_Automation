# 🚀 Backend – AI EDA Tool

## 📌 Overview

The `backend` folder is the core processing engine of the AI EDA Tool platform.

It contains all major modules responsible for:

- RTL parsing
- AI-assisted code analysis
- Simulation
- Verification
- Schematic generation
- PPA estimation
- Timing analysis
- FPGA support
- Synthesis automation

This backend is designed to automate modern semiconductor design workflows using Artificial Intelligence and open-source EDA tools.

---

# 📂 Folder Structure

```bash
backend/
│
├── ai/
├── fpga/
├── ppa/
├── rtl_parser_engine/
├── schematic/
├── simulation/
├── sta/
├── static/
├── synthesis/
├── truth/
├── uploads/
├── utils/
├── verification/
├── Visualization/
│
├── __init__.py
├── main.py
└── verilog_simulator.py

⚡ Backend Modules
🧠 ai/

Contains AI-powered modules for:

RTL analysis
Error detection
Code correction
Design classification
AI-assisted optimization
HDL understanding
🖥️ fpga/

Handles FPGA-oriented workflows including:

FPGA synthesis support
Resource estimation
FPGA deployment preparation
Bitstream-related utilities
📊 ppa/

Responsible for:

Power estimation
Performance estimation
Area analysis
RTL-level PPA prediction
🔍 rtl_parser_engine/

Core RTL parser responsible for:

Verilog parsing
Module extraction
Port detection
Signal analysis
Syntax structure identification
🧩 schematic/

Generates RTL schematics using:

Yosys
Graphviz
SVG rendering

Supports printable schematic visualization.

▶️ simulation/

Simulation-related utilities:

Icarus Verilog integration
Simulation automation
Waveform generation
GTKWave support
⏱️ sta/

Static Timing Analysis module for:

Delay estimation
Timing path analysis
Critical path identification
🎨 static/

Contains static assets such as:

CSS
JavaScript
Images
UI resources
⚙️ synthesis/

Handles synthesis workflows using:

Yosys
Netlist generation
RTL elaboration
Gate-level conversion
📋 truth/

Generates truth tables for:

Combinational circuits
Logic verification
Functional validation
📤 uploads/

Temporary storage for:

Uploaded RTL files
User-generated design files
Simulation inputs
🛠️ utils/

Contains reusable helper utilities and shared functions used across the backend.

✅ verification/

Verification engine supporting:

Testbench generation
Functional verification
Simulation validation
Output checking
📈 Visualization/

Responsible for:

Design visualization
Graph rendering
Interactive RTL display
UI-based analysis outputs
🛠️ Technologies Used
Languages
Python
Verilog HDL
Frameworks
Flask
Jinja2
EDA Tools
Yosys
Icarus Verilog
GTKWave
Graphviz
OSS CAD Suite
▶️ Running the Backend
1️⃣ Activate OSS CAD Suite
environment.bat
2️⃣ Run Backend Server
python main.py
🎯 Objectives

The backend aims to provide:

Intelligent RTL understanding
Automated verification
Faster debugging workflows
AI-assisted semiconductor design automation
Research-oriented EDA experimentation
🔮 Future Improvements
Formal verification support
AI-generated RTL
Timing diagram generation
Physical design integration
GDSII workflow support
ML-based optimization engine
👨‍💻 Author

Maheedhar Bhamidipati
VLSI Design | FPGA | AI-EDA Research

📜 License

This project is intended for educational, research, and development purposes.
