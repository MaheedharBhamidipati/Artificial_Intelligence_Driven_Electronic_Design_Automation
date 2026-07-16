# 🎨 Frontend – AI EDA Tool

## 📌 Overview

The `frontend` folder contains the complete user interface layer of the AI EDA Tool platform.

It is responsible for providing:

- Interactive RTL analysis interface
- File upload functionality
- Schematic visualization
- AI-generated output display
- Simulation result visualization
- User-friendly semiconductor design workflow interaction

The frontend acts as the bridge between users and the backend AI-EDA processing engine.

---

# 📂 Folder Structure


-----
⚡ Frontend Modules
🧩 components/

Contains reusable UI components such as:

Navigation bars
RTL upload panels
Result cards
Analysis sections
Schematic viewers
Truth table displays
Simulation output panels

These components improve modularity and UI scalability.

📄 pages/

Contains application pages including:

Home page
RTL analysis page
Simulation page
Schematic visualization page
Verification dashboard
PPA analysis page

Each page represents a major workflow in the AI EDA Tool platform.

🔗 services/

Handles communication between frontend and backend.

Responsibilities include:

API calls
Backend request handling
Upload requests
Simulation requests
AI analysis requests
Result fetching
🖼️ SchematicCanvas.js

Responsible for:

Rendering generated schematics
Interactive schematic visualization
Zoom and display controls
SVG schematic handling

This module enables RTL schematic viewing directly within the web application.

🚀 Features
✅ RTL Upload Interface
Upload Verilog HDL files
Drag-and-drop support
File validation
✅ AI Analysis Dashboard

Displays:

RTL summaries
Error reports
AI suggestions
Optimization hints
✅ Schematic Visualization
Interactive RTL schematics
SVG rendering
Printable design visualization
✅ Simulation Results
Output waveform display
Simulation logs
Functional verification results
✅ Responsive UI

Designed for:

Desktop systems
Research workflows
Semiconductor engineering applications
🛠️ Technologies Used
Frontend Technologies
React.js
JavaScript
HTML5
CSS3
Visualization
SVG Rendering
Canvas-based visualization
API Communication
REST APIs
Flask backend integration
▶️ Running the Frontend
1️⃣ Install Dependencies
npm install
2️⃣ Start Development Server
npm start
🌐 Default Local Server
http://localhost:3000
🎯 Objectives

The frontend aims to provide:

Clean semiconductor workflow visualization
Easy RTL interaction
AI-assisted debugging experience
Interactive design exploration
Modern EDA user experience
🔮 Future Enhancements
Dark mode UI
Real-time waveform viewer
Interactive gate-level editing
RTL drag-and-drop editor
AI chat assistant integration
Live synthesis monitoring
FPGA dashboard support
👨‍💻 Author

Maheedhar Bhamidipati
VLSI Design | FPGA | AI-EDA Research

📜 License

This project is intended for educational, research, and development purposes.
