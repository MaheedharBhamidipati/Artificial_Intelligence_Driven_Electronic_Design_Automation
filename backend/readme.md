# 🚀 Backend – AIDEA (Artificial Intelligence Driven Electronic Design Automation)

## 📌 Overview

The **backend** is the computational core of **AIDEA (Artificial Intelligence Driven Electronic Design Automation)**. It powers the complete RTL-to-analysis workflow by integrating AI-driven design understanding with open-source Electronic Design Automation (EDA) tools.

The backend is responsible for parsing RTL, generating simulations, performing synthesis, conducting timing analysis, creating schematics, estimating PPA metrics, verifying functionality, and producing comprehensive engineering reports.

Designed with a modular architecture, it enables scalable development, easy maintenance, and seamless integration of new AI models and EDA capabilities.

---

## ✨ Core Features

- 🧠 AI-Assisted RTL Analysis
- 📖 RTL Parsing & Structural Analysis
- 🛠️ Automatic Testbench Generation
- ▶️ Functional Simulation
- 📊 Waveform Generation
- 🧩 RTL Schematic Generation
- ⚙️ Logic Synthesis
- 📈 Static Timing Analysis (STA)
- 📋 Truth Table Generation
- 🔄 Finite State Machine (FSM) Extraction
- 🖥️ FPGA Flow Support
- 📐 Physical Design Visualization
- 🔋 Power Estimation
- 📏 Area Estimation
- ⚡ Performance Analysis
- ✅ Functional Verification
- 📑 Automatic PDF Report Generation

---

# 📂 Backend Folder Structure

```text
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
├── visualization/
│
├── __init__.py
├── main.py
└── verilog_simulator.py
```

---

# 📦 Backend Modules

## 🧠 AI (`ai/`)

Provides Artificial Intelligence capabilities for RTL understanding and design analysis.

### Features

- RTL explanation
- AI-based code analysis
- Error detection
- RTL quality assessment
- Logic classification
- Design summarization
- Optimization suggestions
- AI-assisted debugging

---

## 🖥️ FPGA (`fpga/`)

Implements FPGA-specific design flows.

### Features

- FPGA synthesis preparation
- Resource utilization estimation
- Device compatibility checks
- FPGA implementation support
- Bitstream preparation utilities

---

## 📊 PPA (`ppa/`)

Performs RTL-level Power, Performance, and Area estimation.

### Features

- Power estimation
- Area prediction
- Performance estimation
- Design complexity metrics
- Resource utilization analysis

---

## 🔍 RTL Parser Engine (`rtl_parser_engine/`)

The primary RTL processing engine responsible for analyzing Verilog HDL.

### Features

- Verilog parsing
- Syntax tree generation
- Module extraction
- Port detection
- Signal identification
- Parameter extraction
- Wire and register analysis
- Instance detection
- RTL hierarchy construction

---

## 🧩 Schematic (`schematic/`)

Automatically generates RTL schematics from Verilog designs.

### Features

- RTL netlist generation
- Yosys integration
- Graphviz rendering
- SVG export
- High-resolution schematic generation
- Printable schematic visualization

---

## ▶️ Simulation (`simulation/`)

Handles functional simulation of RTL designs.

### Features

- Automatic testbench execution
- Icarus Verilog integration
- Simulation automation
- VCD waveform generation
- GTKWave compatibility
- Simulation result parsing

---

## ⏱️ Static Timing Analysis (`sta/`)

Performs timing analysis for synthesized designs.

### Features

- Critical path identification
- Delay estimation
- Slack calculation
- Timing path extraction
- Timing report generation
- Timing visualization

---

## 🎨 Static (`static/`)

Stores frontend resources used by the backend.

### Includes

- CSS files
- JavaScript
- Images
- Icons
- Fonts
- UI assets

---

## ⚙️ Synthesis (`synthesis/`)

Responsible for RTL synthesis using open-source EDA tools.

### Features

- RTL elaboration
- Logic synthesis
- Netlist generation
- Gate-level conversion
- Cell statistics
- Logic depth estimation
- Resource reporting

---

## 📋 Truth (`truth/`)

Generates functional truth tables and logic behavior.

### Features

- Combinational truth tables
- Functional validation
- Logic verification
- Input-output mapping
- Boolean behavior analysis

---

## 📤 Uploads (`uploads/`)

Temporary workspace for uploaded user files.

### Stores

- RTL files
- Testbenches
- Generated netlists
- Simulation inputs
- Intermediate design files

---

## 🛠️ Utils (`utils/`)

Contains reusable helper functions shared across backend modules.

### Includes

- File utilities
- Parser helpers
- Logging utilities
- Common algorithms
- Report helpers
- Data conversion utilities

---

## ✅ Verification (`verification/`)

Responsible for validating RTL functionality.

### Features

- Automatic testbench generation
- Functional verification
- Output comparison
- Result validation
- Simulation checking
- Verification summaries

---

## 📈 Visualization (`visualization/`)

Generates graphical outputs for design analysis.

### Features

- RTL visualization
- Timing graphs
- FSM diagrams
- Interactive charts
- Physical design visualization
- Analysis dashboards

---

# 🔄 Backend Workflow

```text
RTL Design
      │
      ▼
RTL Parsing
      │
      ▼
AI RTL Analysis
      │
      ▼
Testbench Generation
      │
      ▼
Simulation
      │
      ▼
Synthesis
      │
      ▼
Truth Table / FSM Extraction
      │
      ▼
Timing Analysis
      │
      ▼
PPA Estimation
      │
      ▼
Verification
      │
      ▼
Engineering Report Generation
```

---

# 🛠️ Technologies Used

## Programming Languages

- Python
- Verilog HDL

---

## Backend Framework

- Flask
- Jinja2

---

## AI Technologies

- Large Language Models (LLMs)
- Prompt Engineering
- AI-Assisted RTL Analysis

---

## Open-Source EDA Tools

- Yosys
- ABC
- Icarus Verilog
- GTKWave
- Graphviz
- OSS CAD Suite

---

## Python Libraries

- PyVerilog
- Pandas
- NumPy
- NetworkX
- Matplotlib
- ReportLab

---

# ▶️ Running the Backend

## 1. Activate OSS CAD Suite

```bash
environment.bat
```

---

## 2. Navigate to Backend

```bash
cd backend
```

---

## 3. Start the Backend Server

```bash
python main.py
```

---

# 🎯 Project Objectives

The backend is designed to provide:

- Intelligent RTL understanding
- AI-assisted design analysis
- Automated simulation workflows
- Automatic synthesis
- Functional verification
- Timing-aware design analysis
- Physical design visualization
- Automated engineering documentation
- Faster RTL debugging
- Semiconductor design automation

---

# 🔮 Future Enhancements

Planned improvements include:

- Formal verification
- AI-generated RTL
- SystemVerilog support
- OpenROAD integration
- Floorplanning automation
- Placement visualization
- Routing visualization
- Clock Tree Synthesis (CTS)
- Static Power Analysis
- Dynamic Power Analysis
- Congestion Analysis
- GDSII generation
- ML-driven optimization
- Multi-clock domain analysis
- Design-for-Test (DFT) support

---

# 👨‍💻 Author

**Maheedhar Bhamidipati**

*M.Tech VLSI Design Engineer | FPGA Developer | AI-EDA Researcher*

---

# 📜 License

This project is intended for educational, research, and development purposes.

---

## © AIDEA – Artificial Intelligence Driven Electronic Design Automation

*Design Intelligent • Verify Automatically • Analyze Efficiently • Optimize Performance • Visualize Everything*
