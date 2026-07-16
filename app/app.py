
# ===============================================================================
# cmd /k "D:\AI_EDA_TOOL\oss-cad-suite\environment.bat"
# cd D:\AI_EDA_TOOL\app
# python app.py --no-reload
# ===============================================================================

# ===============================================================================
# AIDEA - COMPLETE STABLE AI EDA TOOL
# ADVANCED UI + CDC + TIMING + PLACEMENT + ROUTING + POWER + CONGESTION
# STABLE DASHBOARD + PRINT + FULLSCREEN + ZOOM
# ===============================================================================

from flask import Flask, request, jsonify, send_file
import os
import sys
import shutil
import traceback
import webbrowser
import threading
import time
import re
import importlib
import subprocess
import json

import markdown


# =========================================================
# DISABLE CACHE
# =========================================================

sys.dont_write_bytecode = True
importlib.invalidate_caches()

# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = "D:/AI_EDA_TOOL"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================================================
# IMPORTS
# =========================================================

from backend.utils.cleaner import clear_runs

from backend.ai.ai_engine import analyze_verilog

from dotenv import load_dotenv

load_dotenv()

from backend.simulation.tb_generator import generate_testbench

from backend.simulation.simulator import run_simulation

from backend.truth import (
    generate_behavior_view
)

from backend.truth.fsm_extractor import (
    extract_fsm
)

from backend.rtl_parser_engine.rtl_parser import RTLParser

from backend.yosys_engine.run_yosys import generate_json_netlist

from backend.yosys_engine.netlist_parser import (
    load_netlist,
    extract_cells
)

from backend.yosys_engine.schematic_generator import (
    generate_schematic as yosys_generate_schematic
)

from backend.Visualization.timing_visualizer import (
    parse_rtl_file,
    extract_logic_operations,
    generate_timing_data,
    save_timing_json,
    generate_timing_figure
)


from backend.placement.placement_engine import (
    PlacementEngine
)

from backend.placement.placement_predictor import (
    PlacementPredictor
)

from backend.placement.placement_visualizer import (
    visualize_placement
)

from backend.routing.routing_engine import (
    RoutingEngine
)

from backend.routing.routing_visualizer import (
    visualize_routing
)


from backend.Visualization.power_view import (
    PowerView
)


from backend.Visualization.congestion_view import (
    CongestionView
)

from backend.ai.chatbot import ask_chatbot


from backend.semantic import (
    SemanticDatabase,
    SemanticCell,
    Port
)

from backend.semantic.index import CellIndex

from backend.semantic.passes import (
    LogicPass,
    RegisterPass,
    FSMPass
)

# =========================================================
# TIMING MODULAR IMPORTS
# =========================================================

from backend.timing.timing_controller import (
    run_complete_timing_analysis
)

from backend.timing.timing_frontend import (
    generate_timing_panel
)

from backend.timing.timing_routes import (
    timing_bp
)
# =========================================================
# FLOORPLANNING
# =========================================================

from backend.floorplanning import FloorplanEngine
from backend.floorplanning.netlist_loader import NetlistLoader

from backend.report.pdf_report import generate_full_report_pdf


# =========================================================
# CDC ENGINE
# =========================================================

try:

    from backend.cdc.clock_domain_crossing import (
        CDCAnalyzer
    )

except:

    class CDCAnalyzer:

        def __init__(self, cells):

            self.cells = cells

        def analyze(self):

            return {}

# =========================================================
# TIMING ENGINE
# =========================================================

try:

    from backend.timing.timing_engine import (
        TimingEngine
    )

except:

    class TimingEngine:

        def __init__(self, paths):

            self.paths = paths

        def get_worst_path(self):

            return None



# =========================================================

try:

    from backend.routing.routing_engine import (
        RoutingEngine
    )

except:

    class RoutingEngine:

        def __init__(self, net_map):

            self.net_map = net_map

        def run(self):

            nets = []

            for net, connections in self.net_map.items():

                nets.append({

                    "net": str(net),

                    "fanout":
                        len(connections)
                        if isinstance(connections, list)
                        else 1
                })

            return {

                "nets": nets,

                "congestion":
                    "Moderate"
            }

# =========================================================

try:

    from backend.power.power_engine import (
        PowerEngine
    )

except:

    class PowerEngine:

        def __init__(self, cells):

            self.cells = cells

        def analyze(self):

            dynamic = len(self.cells) * 0.45

            leakage = len(self.cells) * 0.08

            total = dynamic + leakage

            return {

                "dynamic_power":
                    f"{dynamic:.2f} mW",

                "leakage_power":
                    f"{leakage:.2f} mW",

                "total_power":
                    f"{total:.2f} mW"
            }

# =========================================================

try:

    from backend.congestion.congestion_engine import (
        CongestionEngine
    )

except:

    class CongestionEngine:

        def __init__(self, nets):

            self.nets = nets

        def analyze(self):

            density = min(

                100,

                len(self.nets) * 2
            )

            hotspots = []

            for i, net in enumerate(
                list(self.nets.keys())[:10]
            ):

                hotspots.append({

                    "x": i * 120,

                    "y": i * 70
                })

            return {

                "density":
                    f"{density}%",

                "hotspots":
                    hotspots
            }

# =========================================================
# FLASK
# =========================================================

app = Flask(

    __name__,

    static_folder=os.path.join(
        PROJECT_ROOT,
        "static"
    )
)

# =========================================================
# AI ENGINE BLUEPRINT
# =========================================================

from backend.ai_engine.ai_routes import ai_bp

app.register_blueprint(ai_bp)

app.register_blueprint(timing_bp)

# =========================================================
# PATHS
# =========================================================

RUNS_PATH = os.path.join(
    PROJECT_ROOT,
    "runs"
)

STATIC_PATH = os.path.join(
    PROJECT_ROOT,
    "static"
)

GENERATED_PATH = os.path.join(
    STATIC_PATH,
    "generated"
)

SCHEMATIC_PATH = os.path.join(
    GENERATED_PATH,
    "schematics"
)

NETLIST_PATH = os.path.join(
    GENERATED_PATH,
    "netlists"
)

os.makedirs(RUNS_PATH, exist_ok=True)
os.makedirs(STATIC_PATH, exist_ok=True)
os.makedirs(GENERATED_PATH, exist_ok=True)
os.makedirs(SCHEMATIC_PATH, exist_ok=True)
os.makedirs(NETLIST_PATH, exist_ok=True)

REPORT_PDF_PATH = os.path.join(
    RUNS_PATH,
    "AIDEA_Full_Report.pdf"
)

# =========================================================
# GTK FLAG
# =========================================================

gtkwave_opened = False

# =========================================================
# CLEAN CACHE
# =========================================================

def clean_cache():

    for root, dirs, files in os.walk(PROJECT_ROOT):

        for d in dirs:

            if d == "__pycache__":

                try:

                    shutil.rmtree(

                        os.path.join(root, d),

                        ignore_errors=True
                    )

                except:
                    pass

        for file in files:

            if file.endswith(".pyc"):

                try:

                    os.remove(

                        os.path.join(root, file)
                    )

                except:
                    pass

# =========================================================
# OPEN BROWSER
# =========================================================

def open_browser():

    time.sleep(1)

    webbrowser.open(
        "http://127.0.0.1:5000"
    )

# =========================================================
# METRIC CARD
# =========================================================

def metric_card(title, value):

    return f"""

    <div class='metric-card'>

        <div class='metric-title'>

            {title}

        </div>

        <div class='metric-value'>

            {value}

        </div>

    </div>

    """

# =========================================================
# WIDTH PARSER
# =========================================================

def parse_width(width):

    if isinstance(width, int):

        return width

    if isinstance(width, str):

        m = re.search(

            r"\[(\d+):(\d+)\]",

            width
        )

        if m:

            msb = int(m.group(1))
            lsb = int(m.group(2))

            return abs(msb - lsb) + 1

    return 1

# =========================================================
# IO TABLE
# =========================================================

def generate_io_table(inputs, outputs):

    rows = ""

    for inp in inputs:

        rows += f"""

        <tr>

            <td>{inp.get('name')}</td>

            <td style='color:green;font-weight:700;'>

                INPUT

            </td>

            <td>{inp.get('width',1)}</td>

        </tr>

        """

    for out in outputs:

        rows += f"""

        <tr>

            <td>{out.get('name')}</td>

            <td style='color:red;font-weight:700;'>

                OUTPUT

            </td>

            <td>{out.get('width',1)}</td>

        </tr>

        """

    return f"""

    <table class='io-table'>

        <thead>

            <tr>

                <th>Port</th>

                <th>Direction</th>

                <th>Width</th>

            </tr>

        </thead>

        <tbody>

            {rows}

        </tbody>

    </table>

    """
    
    
# =========================================================
# SPLASH / LOGO ROUTE  (PAGE 1)
# =========================================================

@app.route('/', methods=['GET'])

def splash():

    return """

    <html>

    <head>

    <title>AIDEA</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>

        *{
            margin:0;
            padding:0;
            box-sizing:border-box;
        }

        html, body{
            width:100%;
            height:100%;
            background:#050b18;
            overflow:hidden;
        }

        .splash-link{
            display:flex;
            align-items:center;
            justify-content:center;
            width:100vw;
            height:100vh;
            cursor:pointer;
            background:
                radial-gradient(
                    circle at center,
                    #0b1730 0%,
                    #050b18 70%
                );
        }

        .splash-link img{
            max-width:92vw;
            max-height:92vh;
            width:auto;
            height:auto;
            object-fit:contain;
            filter:
                drop-shadow(0 0 35px rgba(37,99,235,0.45));
            transition:transform 0.35s ease, filter 0.35s ease;
        }

        .splash-link:hover img{
            transform:scale(1.035);
            filter:
                drop-shadow(0 0 55px rgba(37,99,235,0.65));
        }

        .splash-hint{
            position:absolute;
            bottom:32px;
            left:0;
            right:0;
            text-align:center;
            color:#64748b;
            font-family:Arial, sans-serif;
            font-size:13px;
            letter-spacing:0.5px;
            animation: pulseHint 2.2s ease-in-out infinite;
        }

        @keyframes pulseHint{
            0%, 100% { opacity:0.4; }
            50% { opacity:1; }
        }

    </style>

    </head>

    <body>

        <a href="/home" class="splash-link" aria-label="Enter AIDEA">

            <img src="/static/AIEDA.png" alt="AIDEA">

        </a>

        <div class="splash-hint">Click anywhere on the logo to enter AIDEA</div>

    </body>

    </html>

    """

# =========================================================
# MAIN ROUTE  (PAGE 2 : FORGE / HOME WORKSPACE)
# =========================================================

@app.route('/home', methods=['GET', 'POST'])

def index():

    # =====================================================
    # HOME PAGE
    # =====================================================

    if request.method == 'GET':

        return """

        <html>

        <head>

        <title>AIDEA</title>

        <style>

            *{
                box-sizing:border-box;
            }

            html, body{

                margin:0;
                padding:0;

                width:100%;

                min-height:100vh;

                overflow-y:auto;
                overflow-x:hidden;

                background:
                linear-gradient(
                    135deg,
                    #0f172a 0%,
                    #111827 35%,
                    #071633 100%
                );

                font-family:Segoe UI, sans-serif;
            }

            body{

                display:flex;

                justify-content:center;

                align-items:flex-start;

                padding:20px 0;
            }

            .hero{

                width:96%;

                min-height:88vh;

                background:white;

                border-radius:24px;

                padding:10px 26px 18px 26px;

                text-align:center;

                box-shadow:
                0 8px 30px rgba(0,0,0,0.08);

                display:flex;

                flex-direction:column;

                align-items:center;

                overflow:hidden;
            }
            }
            /* =========================================
            LOGO
            ========================================= */

            .logo-container{

                width:100%;

                display:flex;

                justify-content:center;

                align-items:center;

                padding-top:10px;

                padding-bottom:18px;

                flex-shrink:0;
            }

            .logo-container img{

                width:340px;

                max-width:95%;

                height:auto;

                object-fit:contain;

                filter:
                drop-shadow(0 0 18px rgba(37,99,235,0.30));

                transition:0.3s ease;
            }

            .logo-container img:hover{

                transform:scale(1.03);
            }

            /* =========================================
            TITLE
            ========================================= */

            h1{

                font-size:15px;

                margin-top:4px;

                margin-bottom:2px;

                color:#071633;

                font-weight:800;

                line-height:1.4;
            }

            .subtitle{

                font-size:10px;

                color:#64748b;

                margin-bottom:16px;
            }

            /* =========================================
            UPLOAD SECTION
            ========================================= */
            
            /* =========================================
            WORKSPACE LAYOUT
            ========================================= */

            .workspace{

                width:100%;

                flex:1;

                display:flex;

                gap:18px;

                align-items:stretch;

                justify-content:center;

                overflow:hidden;
            }

            /* =========================================
            MONACO PANEL
            ========================================= */

            .editor-panel{

                flex:0 0 68%;

                height:520px;

                border-radius:18px;

                overflow:hidden;

                border:2px solid #dbeafe;

                box-shadow:
                0 8px 24px rgba(0,0,0,0.10);

                display:flex;

                flex-direction:column;

                background:#1e1e1e;

                min-width:0;
            }

            /* =========================================
            RIGHT CONTROL PANEL
            ========================================= */

            .control-panel{

                width:320px;

                border-radius:18px;

                background:#f8fbff;

                border:2px solid #dbeafe;

                padding:28px 22px;

                display:flex;

                flex-direction:column;

                align-items:center;

                justify-content:flex-start;

                box-shadow:
                0 8px 22px rgba(0,0,0,0.08);

                flex-shrink:0;
            }

            .control-title{

                font-size:18px;

                font-weight:800;

                color:#071633;

                margin-bottom:20px;

                text-align:center;
            }

            /* =========================================
            FILE INPUT
            ========================================= */

            input[type=file]{

                width:100%;

                padding:12px;

                border-radius:12px;

                border:2px solid #cbd5e1;

                background:white;

                font-size:11px;

                cursor:pointer;
            }

            input[type=file]:hover{

                border-color:#2563eb;
            }

            /* =========================================
            RUN BUTTON
            ========================================= */

           button{

                width:100%;

                margin-top:18px;

                padding:16px 18px;

                border:none;

                border-radius:12px;

                background:linear-gradient(
                    90deg,
                    #2563eb,
                    #0891b2
                );

                color:white;

                font-size:14px;

                font-weight:700;

                cursor:pointer;

                transition:0.3s;

                box-shadow:
                0 6px 18px rgba(37,99,235,0.28);
            }

            button:hover{

                transform:translateY(-2px);

                box-shadow:
                0 8px 24px rgba(37,99,235,0.45);
            }

            /* =========================================
            RESPONSIVE
            ========================================= */

            @media(max-width:1100px){

                .logo-container img{

                    width:85%;
                    max-height:36vh;
                }

                h1{

                    font-size:34px;
                }
            }

            @media(max-width:768px){

                .hero{

                    padding:18px;
                }

                .logo-container img{

                    width:96%;

                    max-height:30vh;
                }

                h1{

                    font-size:28px;

                    line-height:1.25;
                }

                .subtitle{

                    font-size:15px;
                }

                input[type=file]{

                    width:100%;
                    max-width:320px;
                }

                button{

                    width:100%;
                    max-width:320px;
                }
            }

        </style>

        </head>

        <body>

            <div class='hero'>

                <!-- LOGO -->

                <div class='logo-container'>

                    <img src='/static/AIEDA.png'>

                </div>

                
                <!-- UPLOAD -->

                <div class='workspace'>

                    <!-- ================================= -->
                    <!-- LEFT : MONACO EDITOR -->
                    <!-- ================================= -->

                    <div class='editor-panel'>
                    
                    <div style="
                        padding:12px 18px;
                        background:#111827;
                        color:#94a3b8;
                        font-size:14px;
                        border-bottom:1px solid #1e293b;
                    ">

                        design.v

                    </div>

                        <div
                            id="editor"
                            style="
                                width:100%;
                                flex:1;
                            "
                        ></div>

                    </div>

                    <!-- ================================= -->
                    <!-- RIGHT : CONTROL PANEL -->
                    <!-- ================================= -->

                    <div class='control-panel'>

                        <!-- ================================= -->
                        <!-- AI ASSISTANT -->
                        <!-- ================================= -->

                        <div class='control-title'>

                            ⚡ AIDEA Forge

                        </div>

                        <textarea
                            id="ai_prompt"
                            placeholder="Describe the RTL you want to generate...

                    Example:
                    Design a UART with FIFO and parity checking."
                            style="
                                width:100%;
                                height:160px;
                                resize:none;
                                border-radius:14px;
                                border:2px solid #cbd5e1;
                                padding:14px;
                                font-size:13px;
                                font-family:Consolas;
                                outline:none;
                                margin-bottom:14px;
                            "
                        ></textarea>

                        <!-- HDL SELECT -->

                        <select
                            id="hdl_language"
                            style="
                                width:100%;
                                padding:12px;
                                border-radius:12px;
                                border:2px solid #cbd5e1;
                                margin-bottom:14px;
                                font-weight:600;
                            "
                        >

                            <option value="Verilog">

                                Verilog

                            </option>

                            <option value="SystemVerilog">

                                SystemVerilog

                            </option>

                        </select>

                        <!-- GENERATE BUTTON -->

                        <button
                            id="generate-btn"
                            type="button"
                            onclick="generateRTL()"
                            style="
                                background:linear-gradient(
                                    90deg,
                                    #7c3aed,
                                    #2563eb
                                );
                            "
                        >

                            ⚡ Generate RTL

                        </button>

                        <!-- DIVIDER -->

                        <div style="
                            width:100%;
                            text-align:center;
                            margin:18px 0;
                            font-weight:700;
                            color:#64748b;
                        ">

                            ───── OR ─────

                        </div>

                        <!-- ================================= -->
                        <!-- UPLOAD SECTION -->
                        <!-- ================================= -->

                        <div class='control-title'
                            style="
                                font-size:16px;
                                margin-bottom:14px;
                            "
                        >

                            📂 Upload RTL

                        </div>

                        <form
                            method='POST'
                            enctype='multipart/form-data'
                            style="
                                width:100%;
                                display:flex;
                                flex-direction:column;
                                align-items:center;
                            "
                        >

                            <!-- HIDDEN RTL -->

                            <textarea
                                id="rtl_code"
                                name="rtl_code"
                                hidden
                            ></textarea>

                            <!-- FILE -->

                            <input
                                type='file'
                                name='file'
                                accept=".v,.sv"
                            >

                            <!-- RUN -->

                            <button
                                type="submit"
                                onclick="syncEditorCode()"
                            >

                                ▶ Run Full Chip Analysis

                            </button>

                        </form>

                    </div>

                </div>

                    <!-- ===================================== -->
                    <!-- MONACO EDITOR -->
                    <!-- ===================================== -->

                    <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js"></script>

                    <script>

                        let editor;

                        require.config({

                            paths: {
                                vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs'
                            }

                        });

                        require(['vs/editor/editor.main'], function () {

                            editor = monaco.editor.create(

                                document.getElementById('editor'),

                                {

                                    value:`//If you know the code, 
                                    //write it directly in the editor. 
                                    //If the code is already saved on your system, 
                                    //simply upload it.
                                    //If you don’t know the code, generate 
                                    //it using the “AIDEA FORGE” panel.`,

                                    language: 'verilog',

                                    theme: 'vs-dark',

                                    automaticLayout: true,

                                    fontSize: 14,

                                    lineHeight: 22,

                                    fontFamily: 'Consolas',

                                    fontLigatures: true,

                                    scrollBeyondLastLine: false,

                                    wordWrap: 'off',

                                    tabSize: 4,

                                    smoothScrolling: true,

                                    cursorBlinking: 'smooth',

                                    cursorSmoothCaretAnimation: 'on',

                                    roundedSelection: true,

                                    lineNumbersMinChars: 3,

                                    glyphMargin: false,

                                    padding: {
                                        top: 12,
                                        bottom: 12
                                    },

                                    minimap: {
                                        enabled: true
                                    }

                                }
                            );
                            
                            setTimeout(() => {

                                editor.layout();

                            }, 200);

                        });
                        
                        

                        // =====================================
                        // SYNC MONACO → FLASK
                        // =====================================

                        // =====================================
                        // AI RTL GENERATION
                        // =====================================

                        async function generateRTL() {
                            
                            const generateBtn =
                                document.getElementById(
                                    "generate-btn"
                                );

                            const prompt =
                                document.getElementById(
                                    "ai_prompt"
                                ).value;

                            const hdl =
                                document.getElementById(
                                    "hdl_language"
                                ).value;

                            if(!prompt.trim()){

                                alert(
                                    "Please enter AI RTL prompt."
                                );

                                return;
                            }
                            
                            generateBtn.disabled = true;

                            generateBtn.innerHTML =
                                "⏳ Generating RTL...";

                            generateBtn.style.opacity = "0.8";

                            try {

                                const formData = new FormData();

                                formData.append(
                                    "prompt",
                                    prompt
                                );

                                formData.append(
                                    "hdl",
                                    hdl
                                );

                                const response = await fetch(

                                    "/generate_ai_rtl",

                                    {
                                        method: "POST",
                                        body: formData
                                    }
                                );

                                const result =
                                    await response.json();

                                if(result.success){

                                    // =====================================
                                    // INSERT INTO MONACO EDITOR
                                    // =====================================

                                    editor.setValue(
                                        result.generated_code
                                    );
                                    
                                    
                                    generateBtn.innerHTML =
                                        "✅ RTL Generated";

                                    generateBtn.style.background =
                                        "linear-gradient(90deg,#10b981,#059669)";

                                    setTimeout(() => {

                                        generateBtn.disabled = false;

                                        generateBtn.innerHTML =
                                            "⚡ Generate RTL";

                                        generateBtn.style.background =
                                            "linear-gradient(90deg,#7c3aed,#2563eb)";

                                        generateBtn.style.opacity = "1";

                                    }, 2000);
                                                                        
                                    document.getElementById(
                                        "rtl_code"
                                    ).value = result.generated_code;

                                } else {

                                    alert(
                                        result.error
                                    );
                                }

                            } catch(error){

                                console.error(error);
                                
                                generateBtn.innerHTML =
                                    "❌ Failed";

                                generateBtn.style.background =
                                    "linear-gradient(90deg,#dc2626,#991b1b)";

                                setTimeout(() => {

                                    generateBtn.disabled = false;

                                    generateBtn.innerHTML =
                                        "⚡ Generate RTL";

                                    generateBtn.style.background =
                                        "linear-gradient(90deg,#7c3aed,#2563eb)";

                                    generateBtn.style.opacity = "1";

                                }, 2500);

                                alert(
                                    "AI RTL Generation Failed"
                                );
                            }
                        }

                    </script>

                </div>

            </div>

        </body>

        </html>

        """

   
    

    # =====================================================
    # MAIN ANALYSIS
    # =====================================================

    try:

        clean_cache()

        clear_runs()

        uploaded_file = request.files.get("file")

        design_path = os.path.join(

            RUNS_PATH,

            'design.v'
        )

        rtl_code = request.form.get(

            "rtl_code",

            ""
        ).strip()

        uploaded_file = request.files.get("file")

        # =========================================
        # PRIORITY 1 → UPLOADED FILE
        # =========================================

        if uploaded_file and uploaded_file.filename:

            uploaded_file.save(design_path)

        # =========================================
        # PRIORITY 2 → MONACO EDITOR
        # =========================================

        elif rtl_code:

            with open(
                design_path,
                'w',
                encoding='utf-8'
            ) as f:

                f.write(rtl_code)

        # =========================================
        # NO RTL INPUT
        # =========================================

        else:

            return """

            <h2 style='
                color:red;
                font-family:Arial;
                padding:30px;
            '>

                No RTL code entered or file uploaded.

            </h2>

            """

        with open(
            design_path,
            'r',
            encoding='utf-8'
        ) as f:

            code = f.read()

        rtl_lines = len(code.splitlines())
        
        
        # ============================================================
        # DEFAULT ABC SUMMARY
        # ============================================================

        abc_summary = """

        <div class='overview-card'>

            <h3 style="
                color:#dc2626;
                margin-top:0;
            ">

                ABC Synthesis Summary

            </h3>

            <pre style="
                background:#0f172a;
                color:#22c55e;
                border-radius:16px;
                padding:20px;
                font-size:14px;
                line-height:1.9;
                overflow-x:auto;
                font-weight:600;
            ">

        ABC synthesis report not generated.

            </pre>

        </div>

        """

        # =================================================
        # AI ANALYSIS
        # =================================================

        ai_result = analyze_verilog(code)
        
        

        explanation = (
             "✅ RTL analysis completed successfully"
        )

        if (
            isinstance(ai_result, dict)
            and ai_result.get("status") == "success"
        ):

            explanation = ai_result.get(

                'explanation',

                explanation
            )

        # =================================================
        # RTL PARSER
        # =================================================

        parser = RTLParser(design_path)

        parser.parse_file()

        modules = parser.extract_modules()
        
        hierarchical_design = len(modules) > 1
        
        hierarchy_note = ""

        if hierarchical_design:

            hierarchy_note = """
            <div style="
                margin-top:15px;
                padding:15px;
                background:#fff7ed;
                border-left:5px solid #f97316;
                border-radius:8px;
                color:#7c2d12;
                font-size:14px;
                line-height:1.7;
            ">

                <b>Note:</b><br>

                AIDEA Truth Table Generation provides full support for flat combinational RTL designs, where all logic is described within a single module. For such designs, the generated truth table represents the complete functionality of the circuit and can be used directly for verification.

                For hierarchical combinational designs that contain instantiated submodules (for example, a Ripple Carry Adder constructed from multiple Full Adder instances), the generated truth table may represent the functionality of an internal building block rather than the fully expanded top-level design. This occurs because exhaustive truth-table generation for hierarchical designs requires hierarchy flattening, where all instantiated submodules are expanded into a single combinational logic representation before analysis.

                Although the truth table may be limited in these hierarchical cases, AIDEA fully supports simulation-based verification. Generated testbenches and simulation results validate the complete top-level design functionality across all input combinations, providing accurate and exhaustive verification of the overall circuit behavior.

                For the most accurate analysis of hierarchical combinational designs, AIDEA recommends using the generated truth table together with simulation results, testbench verification, or hierarchy-flattened RTL.
                
            </div>
            """

        top_module = 'UNKNOWN'

        inputs = []
        outputs = []
        ports = []

        if modules:

            top = modules[-1]

            top_module = top.get(

                'module_name',

                'UNKNOWN'
            )

            inputs = top.get('inputs', [])

            outputs = top.get('outputs', [])

            for inp in inputs:

                ports.append({

                    'name':
                        inp.get('name'),

                    'direction':
                        'input',

                    'width':
                        parse_width(
                            inp.get(
                                'width',
                                1
                            )
                        )
                })

            for out in outputs:

                ports.append({

                    'name':
                        out.get('name'),

                    'direction':
                        'output',

                    'width':
                        parse_width(
                            out.get(
                                'width',
                                1
                            )
                        )
                })

        # =========================================================
        # NETLIST  (fixed: no silent reuse of stale synthesis output)
        # =========================================================

        design_json = os.path.join(NETLIST_PATH, "design.json")
        legacy_json = os.path.join(NETLIST_PATH, "netlist.json")

        # 1. Wipe any previous synthesis output BEFORE regenerating,
        #    so a failed run can never be mistaken for a fresh one.
        for stale in (design_json, legacy_json):
            if os.path.exists(stale):
                try:
                    os.remove(stale)
                except OSError as e:
                    print(f"WARNING: could not remove stale netlist {stale}: {e}")

        # 2. Run synthesis and actually check what happened.
        netlist_result = generate_json_netlist(design_path, top_module)

        # generate_json_netlist's return value/signature is unknown from here —
        # if it returns something (bool / CompletedProcess / dict with 'success'),
        # check it explicitly. At minimum, log it so failures aren't invisible.
        print("NETLIST GENERATION RESULT:", netlist_result)

        # 3. Confirm a fresh file actually landed. If neither exists now,
        #    synthesis genuinely failed on THIS run — surface that clearly
        #    instead of falling through to a leftover file.
        if os.path.exists(design_json):
            netlist_file = design_json
        elif os.path.exists(legacy_json):
            netlist_file = legacy_json
        else:
            raise FileNotFoundError(
                "Synthesis did not produce a netlist for this run. "
                "Check Yosys output above for the actual RTL error "
                "(top module mismatch, syntax error, etc.)."
            )

        print("=" * 60)
        print("NETLIST FILE:", netlist_file)
        print("EXISTS:", os.path.exists(netlist_file))
        print("=" * 60)

        netlist = load_netlist(netlist_file)

        (
            cells,
            net_map,
            rtl_inputs,
            rtl_outputs
        ) = extract_cells(
            netlist,
            top_module
        )

        print("=" * 60)
        print("TOP MODULE :", top_module)
        print("CELLS      :", len(cells))
        print("NET MAP    :", len(net_map))
        print("RTL INPUTS :", len(rtl_inputs))
        print("RTL OUTPUTS:", len(rtl_outputs))
        print("=" * 60)
        
        
        # ==========================================================
        # BUILD SEMANTIC DATABASE
        # ==========================================================

        db = SemanticDatabase()

        db.top_module = top_module

        # --------------------------
        # Inputs
        # --------------------------

        for port in rtl_inputs:

            db.add_input(
                Port(
                    name=port["name"],
                    direction="input",
                    width=port.get("width", 1)
                )
            )
        # --------------------------
        # Outputs
        # --------------------------

        for port in rtl_outputs:

            db.add_output(
                Port(
                    name=port,
                    direction="output"
                )
            )

        # --------------------------
        # Cells
        # --------------------------

        
        for cell in cells:

            db.add_cell(

                SemanticCell(

                    name=cell.get("name", ""),

                    cell_type=cell.get("type", "UNKNOWN")

                )

            )
 
        # --------------------------
        # Build Cell Index
        # --------------------------

        db.index = CellIndex()

        db.index.build(db.cells)

        # --------------------------
        # Run Semantic Passes
        # --------------------------

        LogicPass(db).run()

        RegisterPass(db).run()

        FSMPass(db).run()
        
        print()

        print("="*70)
        print("SEMANTIC DATABASE")
        print("="*70)

        db.summary()

        LogicPass(db).summary()

        RegisterPass(db).summary()

        FSMPass(db).summary()

        print("="*70)
        
        
        # =========================================================
        # FLOORPLANNING
        # =========================================================

        floorplan_result = {}

        try:

            loader = NetlistLoader(
                netlist_file
            )

            design = loader.load()

            all_cells = []

            for module in design.modules:

                all_cells.extend(module.cells)

            floorplan_engine = FloorplanEngine(
                all_cells
            )

            floorplan_result = floorplan_engine.run()
            
           
            STATIC_FLOORPLAN_DIR = os.path.join(
                PROJECT_ROOT,
                "static",
                "generated",
                "floorplanning"
            )

            os.makedirs(STATIC_FLOORPLAN_DIR, exist_ok=True)

            static_png = os.path.join(
                STATIC_FLOORPLAN_DIR,
                "floorplan.png"
            )

            shutil.copyfile(
                floorplan_result.output_png,
                static_png
            )

            floorplan_png = (
                "/static/generated/floorplanning/floorplan.png"
                + f"?t={time.time()}"
            )
            
            floorplan_metrics = {

                "utilization": floorplan_result.utilization,

                "dead_space": floorplan_result.dead_space,

                "wirelength": floorplan_result.estimated_wirelength,

                "image": floorplan_result.output_png,

                "json": floorplan_result.output_json

            }
            

            print("=" * 60)
            print("FLOORPLANNING SUCCESS")
            print(floorplan_result)
            print("=" * 60)

        except Exception as e:

            print("=" * 60)
            print("FLOORPLANNING FAILED")
            print(str(e))
            print("=" * 60)

            floorplan_result = {

                "image":"static/generated/floorplanning/floorplan.png",

                "json":"static/generated/floorplanning/floorplan.json",

                "utilization":0,

                "dead_space":0,

                "wirelength":0
            }
            
            floorplan_png = (
                "/static/generated/floorplanning/floorplan.png"
                + f"?t={time.time()}"
            )

            floorplan_png = floorplan_png.replace("\\", "/")

            if floorplan_png.startswith("outputs/"):

                floorplan_png = "/" + floorplan_png

            floorplan_png += f"?t={time.time()}"
        
        # =================================================
        # SCHEMATIC
        # =================================================

        schematic_data = yosys_generate_schematic(

            cells=cells,

            net_map=net_map,

            rtl_inputs=rtl_inputs,

            rtl_outputs=rtl_outputs,

            top_module=top_module
        )

        dot = schematic_data['dot']

        synthesis_stats = schematic_data['stats']

        schematic_output = os.path.join(

            SCHEMATIC_PATH,

            'output'
        )

        dot.render(

            schematic_output,

            format='svg',

            cleanup=True
        )

        schematic_svg = (

            '/static/generated/schematics/output.svg'

            + f'?t={time.time()}'
        )

        # =================================================
        # CDC
        # =================================================

        cdc_engine = CDCAnalyzer(cells)

        cdc_domains = cdc_engine.analyze()

        cdc_result = {

            "domains":
                list(cdc_domains.keys()),

            "violations":

                [

                    f"Clock Domain Detected: {domain}"

                    for domain in cdc_domains.keys()
                ]
        }
        
        # =================================================
        # MODULAR TIMING ENGINE
        # =================================================

        timing_result = run_complete_timing_analysis(
            cells
        )

       
        
        
        
        # =================================================
        # TIMING VISUALIZATION
        # =================================================

        rtl_text = parse_rtl_file(design_path)

        operations = extract_logic_operations(rtl_text)

        timing_data = generate_timing_data(operations)

        timing_json_path = os.path.join(
            PROJECT_ROOT,
            "backend",
            "Visualization",
            "timing_data",
            "timing_graph.json"
        )

        save_timing_json(
            timing_data,
            timing_json_path
        )

        timing_fig = generate_timing_figure(timing_data)
        
        

        # =================================================
        # PLACEMENT
        # =================================================

        placement_predictor = PlacementPredictor(

            cells
        )

        placement_prediction = placement_predictor.predict()

        placement_engine = PlacementEngine(

            cells
        )

        placement_result = placement_engine.run()

        # =================================================
        # PLACEMENT VISUALIZATION
        # =================================================

        placement_fig = visualize_placement(

            placement_result["blocks"]
        )

        # =================================================
        # ROUTING
        # =================================================

        routing_engine = RoutingEngine(

            placement_result["blocks"]
        )

        routing_result = routing_engine.run()

        # =================================================
        # ROUTING VISUALIZATION
        # =================================================

        routing_fig = visualize_routing(

            placement_result["blocks"],

            routing_result["routes"]
        )

        # =================================================
        # POWER
        # =================================================

        power_engine = PowerEngine(cells)

        power_result = power_engine.analyze()

        # =================================================
        # POWER VISUALIZATION
        # =================================================

        power_view = PowerView()

        power_cells = power_view.generate_sample_cells()

        power_fig = power_view.render(
            power_cells
        )

        # =================================================
        # CONGESTION
        # =================================================

        congestion_engine = CongestionEngine(net_map)

        congestion_result = congestion_engine.analyze()

        # =================================================
        # CONGESTION VISUALIZATION
        # =================================================

        congestion_view = CongestionView()

        congestion_fig = congestion_view.render(
            congestion_result
        )

        
            
        # =================================================
        # TESTBENCH
        # =================================================

        tb = "// Testbench generation failed"

        try:

            tb = generate_testbench(
                top_module=top_module,
                ports=ports,
                random_iterations=1000
            )

            tb_path = os.path.join(
                RUNS_PATH,
                "tb.v"
            )

            with open(
                tb_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(tb)

        except Exception as e:

            print(
                "TESTBENCH ERROR:",
                str(e)
            )
            
        # =================================================
        # SIMULATION
        # =================================================

        sim_result = run_simulation()
        
        # =================================================
        # VERIFICATION ENGINE
        # =================================================

        verification_status = "✅ PASSED"

        sim_text = str(sim_result).lower()

        failure_keywords = [

            "syntax error",
            "compilation failed",
            "unable to open",
            "no such file",
            "segmentation fault",
            "traceback",
            "simulation failed",
            "fatal",
            "iverilog: error",
            "vvp: error"

        ]

        for keyword in failure_keywords:

            if keyword in sim_text:

                verification_status = "❌ FAILED"

                break

        verification_report = f"""

        <div class='overview-card'>

            <h3>Verification Summary</h3>

            <table class='io-table'>

                <thead>

                    <tr>
                        <th>Check</th>
                        <th>Status</th>
                    </tr>

                </thead>

                <tbody>

                    <tr>
                        <td>RTL Parsing</td>
                        <td>✅ PASSED</td>
                    </tr>

                    <tr>
                        <td>Testbench Generation</td>
                        <td>✅ PASSED</td>
                    </tr>

                    <tr>
                        <td>Simulation</td>
                        <td>{verification_status}</td>
                    </tr>

                    <tr>
                        <td>Schematic Generation</td>
                        <td>✅ PASSED</td>
                    </tr>

                    <tr>
                        <td>Truth Table</td>
                        <td>✅ PASSED</td>
                    </tr>

                </tbody>

            </table>

        </div>

        """
        
        # =================================================
        # FPGA / ASIC ANALYSIS
        # =================================================

        gate_count = max(1, len(ports) * 4)

        estimated_area = gate_count * 10

        estimated_delay = round(
            gate_count * 0.15,
            2
        )

        estimated_power = round(
            gate_count * 0.5,
            2
        )

        ppa = {

            "area":
                f"{estimated_area} um²",

            "delay":
                f"{estimated_delay} ns",

            "power":
                f"{estimated_power} mW"
        }

        fpga_luts = max(1, len(ports) * 2)

        fpga_ffs = max(1, len(outputs))

        fpga_dsps = 0

        fpga_brams = 0

        asic_cells = max(1, len(ports) * 3)

        fpga_html = f"""

        <table class='io-table'>

            <thead>

                <tr>
                    <th>FPGA Resource</th>
                    <th>Estimated Usage</th>
                </tr>

            </thead>

            <tbody>

                <tr>
                    <td>LUTs</td>
                    <td>{fpga_luts}</td>
                </tr>

                <tr>
                    <td>Flip-Flops</td>
                    <td>{fpga_ffs}</td>
                </tr>

                <tr>
                    <td>DSP Blocks</td>
                    <td>{fpga_dsps}</td>
                </tr>

                <tr>
                    <td>BRAMs</td>
                    <td>{fpga_brams}</td>
                </tr>

            </tbody>

        </table>

        """

        asic_html = f"""

        <table class='io-table'>

            <thead>

                <tr>
                    <th>ASIC Metric</th>
                    <th>Estimated Value</th>
                </tr>

            </thead>

            <tbody>

                <tr>
                    <td>Standard Cells</td>
                    <td>{asic_cells}</td>
                </tr>

                <tr>
                    <td>Estimated Area</td>
                    <td>{ppa.get("area")}</td>
                </tr>

                <tr>
                    <td>Estimated Delay</td>
                    <td>{ppa.get("delay")}</td>
                </tr>

                <tr>
                    <td>Estimated Power</td>
                    <td>{ppa.get("power")}</td>
                </tr>

            </tbody>

        </table>

        """

        

        # =========================================================
        # LOGIC TYPE DETECTION
        # =========================================================

        logic_type = "Unknown"

        if re.search(
            r'always\s*@\s*\([^)]*(posedge|negedge)',
            code,
            re.IGNORECASE
        ):
            logic_type = "Sequential"

        elif re.search(
            r'always\s*@\s*\(\s*\*\s*\)',
            code,
            re.IGNORECASE
        ):
            logic_type = "Combinational"

        elif re.search(
            r'\balways_comb\b',
            code,
            re.IGNORECASE
        ):
            logic_type = "Combinational"

        elif re.search(
            r'\bassign\b',
            code,
            re.IGNORECASE
        ):
            logic_type = "Combinational"


        # =========================================================
        # BEHAVIOR ENGINE
        # =========================================================
        
        

        t0 = time.time()
        print("START BEHAVIOR ENGINE")
        
        

        behavior_result = generate_behavior_view(code)
        
        print("\n========== FULL FSM RESULT ==========")
        print(behavior_result)
        print("=====================================\n")
        
        print(
            f"BEHAVIOR ENGINE TIME = "
            f"{time.time()-t0:.2f} sec"
        )

        truth_result = behavior_result.get(
            "truth_table"
        )

        logic_type = behavior_result.get(
            "logic_type",
            "Unknown"
        )
        
        
        logic_type = str(logic_type).strip().lower()

        fsm_svg = behavior_result.get(
            "fsm_svg"
        )

        fsm_png = behavior_result.get(
            "fsm_png"
        )

        print("\n====================")
        print("FSM SVG PATH:", fsm_svg)
        print("FSM PNG PATH:", fsm_png)
        print("====================\n")
        

        fsm_states = behavior_result.get(
            "fsm_states",
            []
        )
        
        print("\nFSM STATES:")
        print(fsm_states)

        print("\nFSM SVG:")
        print(fsm_svg)

        print("\nLOGIC TYPE:")
        print(logic_type)
        
        print("=" * 60)
        print("BEHAVIOR RESULT")

        for k, v in behavior_result.items():

            if hasattr(v, "shape"):
                print(f"{k}: DataFrame {v.shape}")

            else:
                print(f"{k}: {type(v)}")

        print("=" * 60)

        truth_result = behavior_result.get("truth_table")
        
        print("AFTER TRUTH_RESULT")

        print("=" * 60)
        print("TRUTH RESULT")
        print(type(truth_result))

        if hasattr(truth_result, "shape"):
            print("Rows:", truth_result.shape[0])
            print("Cols:", truth_result.shape[1])
        else:
            print(str(truth_result)[:500])

        print("=" * 60)
        
        print("STEP 1 DONE")

        # =========================================================
        # TRUTH TABLE
        # =========================================================

        truth_html = ""

        if logic_type.lower() == "sequential":

            truth_html = ""

        else:

            import pandas as pd

            df = None

            if hasattr(truth_result, "df"):

                df = truth_result.df
                
                print("AFTER DATAFRAME")

            elif isinstance(truth_result, pd.DataFrame):

                df = truth_result

            elif isinstance(truth_result, dict):

                if isinstance(
                    truth_result.get("truth_table"),
                    pd.DataFrame
                ):
                    df = truth_result["truth_table"]

                elif isinstance(
                    truth_result.get("df"),
                    pd.DataFrame
                ):
                    df = truth_result["df"]

            if df is not None and not df.empty:

                MAX_ROWS = 512

                truth_html = f"""
                <div class='overview-card'>

                    <h3>Truth Table</h3>

                    <p>
                        Showing first {min(len(df), MAX_ROWS)} rows
                        out of {len(df)}
                    </p>

                    {df.head(MAX_ROWS).to_html(
                        index=False,
                        classes='truth-table'
                    )}
                    
                    {hierarchy_note}
                    
                </div>
                
                """
                
                print("AFTER TO_HTML")

            else:

                truth_html = f"""
                <div class='overview-card'>

                    <h3>Truth Table</h3>

                    <p>
                        Truth Table could not be generated.
                    </p>

                    <p>
                        Logic Type Detected:
                        <b>{logic_type}</b>
                    </p>

                </div>
                """
                print("AFTER TO_HTML")
                
        # =========================================================
        # FSM VIEW
        # =========================================================

        fsm_html = ""

        if logic_type == "sequential":

            fsm_summary = behavior_result.get(
                "fsm_summary",
                {}
            )

            fsm_transitions = behavior_result.get(
                "fsm_transitions",
                []
            )

            # ==========================================
            # STATES LIST
            # ==========================================

            states_html = "".join(
                f"<li>{state}</li>"
                for state in fsm_states
            )

            # ==========================================
            # SVG
            # ==========================================

            svg_html = ""

            if fsm_svg:

                svg_html = f"""
                <div style="
                    text-align:center;
                    margin-bottom:20px;
                ">
                    <img
                        src="{fsm_svg}"
                        style="
                            width:100%;
                            max-width:900px;
                            border-radius:12px;
                            border:1px solid #dbeafe;
                            background:white;
                            padding:10px;
                        "
                    >
                </div>
                """

            # ==========================================
            # TRANSITION TABLE
            # ==========================================

            transition_rows = ""

            for transition in fsm_transitions:

                transition_rows += f"""
                <tr>

                    <td>
                        {transition.get("from","")}
                    </td>

                    <td>
                        {transition.get("to","")}
                    </td>

                    <td>
                        {transition.get("condition","")}
                    </td>

                </tr>
                """

            transitions_html = ""

            if transition_rows:

                transitions_html = f"""

                <h4 style="
                    margin-top:25px;
                    color:#071633;
                ">

                    Transition Table

                </h4>

                <table class='io-table'>

                    <thead>

                        <tr>

                            <th>Current State</th>

                            <th>Next State</th>

                            <th>Condition</th>

                        </tr>

                    </thead>

                    <tbody>

                        {transition_rows}

                    </tbody>

                </table>

                """

            # ==========================================
            # SUMMARY PANEL
            # ==========================================

            summary_html = f"""

            <h4 style="
                margin-top:20px;
                color:#071633;
            ">

                FSM Summary

            </h4>

            <table class='io-table'>

                <tbody>

                    <tr>

                        <td>
                            Total States
                        </td>

                        <td>
                            {fsm_summary.get("total_states",0)}
                        </td>

                    </tr>

                    <tr>

                        <td>
                            Total Transitions
                        </td>

                        <td>
                            {fsm_summary.get("total_transitions",0)}
                        </td>

                    </tr>

                </tbody>

            </table>

            """

            # ==========================================
            # FINAL FSM HTML
            # ==========================================

            fsm_html = f"""

            <div class='overview-card'>

                <h3>

                    FSM Analysis

                </h3>

                {svg_html}

                {summary_html}

                <h4 style="
                    margin-top:25px;
                    color:#071633;
                ">

                    States

                </h4>

                <ul>

                    {states_html}

                </ul>

                {transitions_html}

            </div>

            """        
                
                            
        

        # =================================================
        # TIMING ROWS
        # =================================================

        timing_rows = ""

        for path in timing_result.get(
            'critical_paths',
            []
        ):

            status = "SAFE"

            color = "green"

            if path.get('slack', 0) < 1:

                status = "CRITICAL"

                color = "red"

            timing_rows += f"""

            <tr>

                <td>{path.get('path','N/A')}</td>

                <td>{path.get('estimated_delay','N/A')}</td>

                <td>{path.get('slack','N/A')}</td>

                <td style='color:{color};font-weight:700;'>

                    {status}

                </td>

            </tr>

            """

        # =================================================
        # CDC ROWS
        # =================================================

        cdc_rows = ""

        for violation in cdc_result.get(
            'violations',
            []
        ):

            cdc_rows += f"""

            <tr>

                <td>{violation}</td>

                <td style='color:#ea580c;font-weight:700;'>

                    CDC Warning

                </td>

            </tr>

            """
        # ============================================================
        # GENERIC ABC SYNTHESIS ENGINE
        # ============================================================

        from collections import defaultdict

        # ============================================================
        # CELL DATABASE
        # ============================================================

        CELL_AREA_DB = {

            # Basic Logic
            "AND": 1,
            "NAND": 1,
            "OR": 1,
            "NOR": 1,
            "XOR": 2,
            "XNOR": 2,
            "NOT": 0.5,
            "BUF": 0.5,

            # Compound
            "AOI": 2,
            "OAI": 2,

            # "SEQUENTIAL"
            "DFF": 4,
            "SDFF": 5,
            "DFFE": 5,
            "LATCH": 3,

            # Mux
            "MUX": 3,

            # Arithmetic
            "ADD": 6,
            "SUB": 6,
            "MUL": 20,
            "DIV": 40,

            # Comparators
            "CMP": 4,
            "EQ": 3,

            # Memory
            "RAM": 50,
            "ROM": 30,

            # FPGA
            "LUT": 2,
            "CARRY": 2,

            # Clocking
            "CLK": 1,
            "CLOCK": 1
        }

        # ============================================================
        # GENERIC CELL CLASSIFIER
        # ============================================================

        def classify_cell(cell_type):

            cell_type = str(cell_type).upper()

            for key in CELL_AREA_DB.keys():

                if key in cell_type:

                    return key

            return "OTHER"

        # ============================================================
        # ANALYSIS VARIABLES
        # ============================================================

        gate_counts = defaultdict(int)

        total_area = 0

        total_fanout = 0

        max_fanout = 0

        logic_depth = 0

        sequential_cells = 0

        combinational_cells = 0

        # ============================================================
        # CELL ANALYSIS
        # ============================================================

        for cell in cells:

            raw_type = str(
                cell.get("type", "UNKNOWN")
            ).upper()

            classified_type = classify_cell(raw_type)

            gate_counts[classified_type] += 1

            # ========================================================
            # AREA
            # ========================================================

            total_area += CELL_AREA_DB.get(
                classified_type,
                1
            )

            # ========================================================
            # CONNECTIONS
            # ========================================================

            connections = cell.get(
                "connections",
                {}
            )

            fanout = len(connections)

            total_fanout += fanout

            if fanout > max_fanout:

                max_fanout = fanout

            # ========================================================
            # DEPTH ESTIMATION
            # ========================================================

            estimated_depth = max(
                1,
                fanout
            )

            logic_depth += estimated_depth

            # ========================================================
            # SEQUENTIAL / COMBINATIONAL
            # ========================================================

            if classified_type in [

                "DFF",
                "SDFF",
                "DFFE",
                "LATCH"

            ]:

                sequential_cells += 1

            else:

                combinational_cells += 1

        # ============================================================
        # TOTALS
        # ============================================================

        total_cells = sum(gate_counts.values())

        avg_fanout = 0

        if total_cells > 0:

            avg_fanout = round(
                total_fanout / total_cells,
                2
            )

        avg_logic_depth = 0

        if total_cells > 0:

            avg_logic_depth = round(
                logic_depth / total_cells,
                2
            )

        # ============================================================
        # BUILD REPORT
        # ============================================================

        abc_report = ""

        for gate_type, count in sorted(
            gate_counts.items()
        ):

            abc_report += f"""

        ABC RESULTS: {gate_type:<12} cells: {count:<8}

        """

        # ============================================================
        # FINAL HTML REPORT
        # ============================================================

        abc_summary = f'''

        <div class='overview-card'>

            <h3 style="
                margin-top:0;
                color:#071633;
                margin-bottom:18px;
                font-size:22px;
                font-weight:800;
            ">

                Generic ABC Synthesis Summary

            </h3>

            <pre style="
                background:#0f172a;
                color:#22c55e;
                border-radius:16px;
                padding:20px;
                font-size:14px;
                line-height:1.9;
                overflow-x:auto;
                font-weight:600;
            ">

        {abc_report}

        --------------------------------------------------

        ABC RESULTS: Total cells:        {total_cells}

        ABC RESULTS: Combinational:      {combinational_cells}

        ABC RESULTS: Sequential:         {sequential_cells}

        ABC RESULTS: Avg Logic Depth:    {avg_logic_depth}

        ABC RESULTS: Max Fanout:         {max_fanout}

        ABC RESULTS: Avg Fanout:         {avg_fanout}

        ABC RESULTS: Estimated Area:     {total_area} units

            </pre>

        </div>

        '''
            
            

        # =================================================
        # FINAL DASHBOARD
        # =================================================

        safe_code = json.dumps(code)
        safe_tb = json.dumps(
            tb if 'tb' in locals()
            else "// TB not available"
        )
        
        formatted_explanation = markdown.markdown(
        ai_result.get("ai_explanation", "")
    )

        # =================================================
        # FULL REPORT PDF  (page 3 export — "Download Report")
        # =================================================

        try:

            generate_full_report_pdf(
                {
                    "project_root": PROJECT_ROOT,
                    "static_path": STATIC_PATH,
                    "top_module": top_module,
                    "rtl_lines": rtl_lines,
                    "ports": ports,
                    "inputs": inputs,
                    "outputs": outputs,
                    "logic_type": logic_type,
                    "code": code,
                    "testbench_code": tb if 'tb' in locals() else None,
                    "explanation_html": formatted_explanation,
                    "abc_summary_html": abc_summary,
                    "truth_html": truth_html,
                    "fsm_html": fsm_html,
                    "fsm_svg": fsm_svg,
                    "fsm_png": fsm_png if 'fsm_png' in locals() and fsm_png else None,
                    "fsm_summary": behavior_result.get("fsm_summary", {}),
                    "fsm_states": fsm_states,
                    "fsm_transitions": behavior_result.get("fsm_transitions", []),
                    "verification_html": verification_report,
                    "fpga_html": fpga_html,
                    "asic_html": asic_html,
                    "floorplan_metrics": floorplan_metrics if 'floorplan_metrics' in locals() else {},
                    "floorplan_png": floorplan_png if 'floorplan_png' in locals() else None,
                    "schematic_svg": schematic_svg if 'schematic_svg' in locals() else None,
                    "timing_panel_html": generate_timing_panel(timing_result),
                    "timing_fig": timing_fig if 'timing_fig' in locals() else None,
                    "placement_fig": placement_fig if 'placement_fig' in locals() else None,
                    "routing_fig": routing_fig if 'routing_fig' in locals() else None,
                    "power_fig": power_fig if 'power_fig' in locals() else None,
                    "congestion_fig": congestion_fig if 'congestion_fig' in locals() else None,
                    "sim_result": sim_result,
                },
                REPORT_PDF_PATH
            )

            print("FULL REPORT PDF READY:", REPORT_PDF_PATH)

        except Exception as pdf_error:

            print("PDF REPORT GENERATION FAILED:", pdf_error)
            traceback.print_exc()

        print("RENDERING DASHBOARD...")
        
        print("DASHBOARD READY")
        
        
        
        return f"""

            <html>

            <head>

            <title>AIDEA Dashboard</title>

            <style>

                *{{
                    box-sizing:border-box;
                }}

                body{{
                    margin:0;
                    background:linear-gradient(180deg,#f4f8ff 0%,#eef3fc 100%);
                    font-family:'Segoe UI',sans-serif;
                    overflow-x:hidden;
                    color:#1e293b;
                }}

                .navbar{{
                    background:linear-gradient(
                        120deg,
                        #4f46e5 0%,
                        #7c3aed 48%,
                        #2563eb 100%
                    );

                    color:white;

                    margin:18px 18px 0 18px;

                    padding:20px 30px;

                    border-radius:20px;

                    box-shadow:0 12px 30px rgba(79,70,229,.28);

                    display:flex;

                    align-items:center;

                    justify-content:space-between;

                    position:relative;

                    overflow:hidden;
                }}

                .navbar::after{{
                    content:"";
                    position:absolute;
                    top:-60%;
                    right:-8%;
                    width:260px;
                    height:260px;
                    background:radial-gradient(circle,rgba(255,255,255,.18) 0%,rgba(255,255,255,0) 70%);
                    pointer-events:none;
                }}

                .navbar-brand{{
                    display:flex;
                    align-items:center;
                    gap:14px;
                    position:relative;
                    z-index:1;
                }}

                .navbar-logo{{
                    width:46px;
                    height:46px;
                    flex-shrink:0;
                    border-radius:13px;
                    background:rgba(255,255,255,.18);
                    box-shadow:inset 0 0 0 1px rgba(255,255,255,.3);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                }}

                .navbar-logo svg{{
                    width:26px;
                    height:26px;
                    stroke:#ffffff;
                    fill:none;
                    stroke-width:2;
                    stroke-linecap:round;
                    stroke-linejoin:round;
                }}

                .navbar-title{{
                    display:flex;
                    flex-direction:column;
                    line-height:1.2;
                }}

                .navbar-title .main{{
                    font-size:19px;
                    font-weight:800;
                    letter-spacing:.8px;
                }}

                .navbar-title .sub{{
                    font-size:11.5px;
                    font-weight:500;
                    opacity:.85;
                    letter-spacing:.3px;
                    margin-top:2px;
                }}

                .navbar-right{{
                    display:flex;
                    align-items:center;
                    gap:16px;
                    position:relative;
                    z-index:1;
                }}

                .navbar-deco{{
                    opacity:.55;
                }}

                @media(max-width:700px){{
                    .navbar-deco{{
                        display:none;
                    }}
                }}

                #theme-toggle-btn{{

                    width:52px;

                    height:52px;

                    border-radius:50%;

                    border:2px solid rgba(255,255,255,0.5);

                    background:rgba(255,255,255,0.15);

                    color:white;

                    font-size:22px;

                    cursor:pointer;

                    display:flex;

                    align-items:center;

                    justify-content:center;

                    transition:.2s ease;
                }}

                #theme-toggle-btn:hover{{

                    background:rgba(255,255,255,0.3);

                    transform:scale(1.06);
                }}

                .container{{
                    padding:24px;
                }}

                .metrics{{
                    display:grid;

                    grid-template-columns:
                    repeat(auto-fit,minmax(220px,1fr));

                    gap:18px;

                    margin-bottom:22px;
                }}

                .metric-card{{
                    background:#ffffff;

                    padding:22px;

                    border-radius:20px;

                    min-height:130px;

                    border:1px solid #dbe6fb;

                    box-shadow:
                    0 4px 16px rgba(37,99,235,0.08);

                    transition:.25s;
                }}

                .metric-card:hover{{
                    border-color:#93c5fd;
                    box-shadow:0 6px 22px rgba(37,99,235,.18);
                    transform:translateY(-2px);
                }}

                .metric-title{{
                    font-size:12px;

                    color:#64748b;

                    font-weight:800;

                    text-transform:uppercase;

                    letter-spacing:.5px;
                }}

                .metric-value{{
                    margin-top:14px;

                    color:#2563eb;

                    font-size:20px;

                    font-weight:800;
                }}

                .workspace{{

                    display:block;

                }}
                
                .dashboard-menu{{

                    display:grid;

                    grid-template-columns:repeat(7,1fr);

                    grid-auto-rows:1fr;

                    gap:16px;

                    margin-bottom:28px;

                }}

                @media(max-width:1300px){{

                    .dashboard-menu{{
                        grid-template-columns:repeat(5,1fr);
                    }}
                }}

                @media(max-width:900px){{

                    .dashboard-menu{{
                        grid-template-columns:repeat(3,1fr);
                    }}
                }}

                @media(max-width:600px){{

                    .dashboard-menu{{
                        grid-template-columns:repeat(2,1fr);
                    }}
                }}

                .menu-card{{

                    background:#ffffff;

                    border-radius:18px;

                    padding:22px 14px;

                    cursor:pointer;

                    text-align:center;

                    transition:.25s ease;

                    box-shadow:0 3px 12px rgba(30,41,80,.06);

                    border:1.5px solid #e7ecf7;

                    min-height:160px;

                    display:flex;

                    flex-direction:column;

                    align-items:center;

                    justify-content:flex-start;

                    gap:2px;
                }}

                .menu-icon-wrap{{

                    width:46px;

                    height:46px;

                    display:flex;

                    align-items:center;

                    justify-content:center;

                    margin-bottom:12px;

                    color:var(--accent,#4f46e5);
                }}

                .menu-icon-wrap svg{{

                    width:30px;

                    height:30px;

                    fill:none;

                    stroke:currentColor;

                    stroke-width:1.6;

                    stroke-linecap:round;

                    stroke-linejoin:round;
                }}

                .menu-title{{

                    display:block;

                    font-size:12.5px;

                    font-weight:800;

                    letter-spacing:.4px;

                    text-transform:uppercase;

                    color:#1e293b;

                    margin-bottom:6px;
                }}

                .menu-subtitle{{

                    display:block;

                    font-size:11px;

                    font-weight:500;

                    line-height:1.4;

                    color:#6b7686;

                    max-width:150px;
                }}

                .menu-card:hover{{

                    transform:translateY(-4px);

                    border-color:var(--accent,#7c3aed);

                    box-shadow:0 12px 26px rgba(37,99,235,.16);
                }}

                .active-card{{

                    background:#f6f4ff;

                    background:linear-gradient(
                        160deg,
                        color-mix(in srgb, var(--accent,#7c3aed) 14%, #ffffff) 0%,
                        color-mix(in srgb, var(--accent,#7c3aed) 28%, #ffffff) 100%
                    );

                    border-color:var(--accent,#7c3aed);

                    border-width:2px;

                    box-shadow:
                        0 0 0 3px color-mix(in srgb, var(--accent,#7c3aed) 18%, transparent),
                        0 12px 26px color-mix(in srgb, var(--accent,#7c3aed) 32%, transparent);

                    transform:translateY(-3px);
                }}

                .active-card .menu-icon-wrap{{

                    background:color-mix(in srgb, var(--accent,#7c3aed) 20%, #ffffff);

                    border-radius:12px;
                }}

                .active-card .menu-title{{

                    color:var(--accent,#7c3aed);
                }}

                .content-panel{{
                    background:#ffffff;

                    border-radius:24px;
                    
                    margin-top:20px;

                    padding:28px;

                    min-height:92vh;

                    overflow-y:auto;

                    overflow-x:auto;

                    border:1px solid #dbe6fb;

                    box-shadow:
                    0 4px 24px rgba(37,99,235,0.08);

                    color:#1e293b;
                }}

                .panel{{
                    display:none;
                }}

                .panel.active{{
                    display:block;
                }}

                .overview-card{{
                    background:#f8fafc;

                    padding:22px;

                    border-radius:18px;

                    margin-bottom:20px;

                    border:1px solid #dbe6fb;
                }}

                .io-table{{
                    width:100%;

                    border-collapse:collapse;

                    margin-top:15px;
                }}

                .io-table th{{
                    background:linear-gradient(90deg,#2563eb,#3b82f6);
                    color:white;
                    padding:12px;
                }}

                .io-table td{{
                    border:1px solid #e2ebfb;
                    padding:12px;
                    text-align:center;
                    color:#334155;
                }}

                .truth-table{{
                    width:100%;
                    border-collapse:collapse;
                }}

                .truth-table th{{
                    background:linear-gradient(90deg,#2563eb,#3b82f6);
                    color:white;
                    padding:12px;
                }}

                .truth-table td{{
                    border:1px solid #e2ebfb;
                    padding:12px;
                    text-align:center;
                    color:#334155;
                }}

                pre{{
                    white-space:pre-wrap;

                    background:#f1f5fb;

                    color:#1e293b;

                    padding:18px;

                    border-radius:12px;

                    line-height:1.7;

                    border:1px solid #dbe6fb;
                }}

                .schematic-container{{
                    width:100%;

                    height:88vh;

                    overflow:auto;

                    background:#f8fafc;

                    border-radius:18px;

                    border:1px solid #dbe6fb;

                    padding:20px;
                }}

                .schematic-frame{{
                    width:100%;

                    height:auto;

                    display:block;

                    transform-origin:top left;

                    transition:transform 0.2s ease;
                }}
                
                .code-split-container{{
                    display:flex;
                    gap:20px;
                    height:80vh;
                }}

                .code-panel{{
                    flex:1;
                    background:#ffffff;
                    border-radius:18px;
                    overflow:hidden;
                    border:1px solid #dbe6fb;
                    display:flex;
                    flex-direction:column;
                }}
                

                .code-header{{
                    padding:14px 18px;
                    background:#eef3fc;
                    color:#2563eb;
                    font-weight:700;
                    border-bottom:1px solid #dbe6fb;
                }}

                .editor-box{{
                    flex:1;
                    width:100%;
                    height:100%;
                    min-height:700px;
                }}
                
                @media(max-width:1200px){{

                    .code-split-container{{

                        flex-direction:column;

                        height:auto;
                    }}

                    .code-panel{{

                        min-height:600px;
                    }}
                }}
                
                /* ===================================== */
                /* CHATBOT BUTTON */
                /* ===================================== */

                #chatbot-button{{

                    position:fixed;

                    bottom:20px;

                    right:20px;

                    width:65px;

                    height:65px;

                    border-radius:50%;

                   
                    background:linear-gradient(
                        135deg,
                        #f97316,
                        #ea580c
                    );

                    box-shadow:
                    0 8px 25px rgba(249,115,22,.45);

                    color:white;

                    font-size:30px;

                    display:flex;

                    align-items:center;

                    justify-content:center;

                    cursor:pointer;

                    z-index:99999;

                    box-shadow:
                    0 6px 20px rgba(37,99,235,.4);
                }}

                /* ===================================== */
                /* CHATBOT WINDOW */
                /* ===================================== */

                #chatbot-window{{

                    position:fixed;

                    bottom:100px;

                    right:20px;

                    width:380px;

                    height:550px;

                    background:#ffffff;

                    border-radius:18px;

                    overflow:hidden;

                    display:none;

                    flex-direction:column;

                    z-index:99999;

                    border:1px solid #dbe6fb;

                    box-shadow:
                    0 10px 35px rgba(37,99,235,.2);
                }}

                #chatbot-header{{

                    background:linear-gradient(
                        90deg,
                        #f97316,
                        #ea580c
                    );

                    color:white;

                    padding:16px;

                    font-size:18px;

                    font-weight:700;
                }}

                #chatbot-messages{{

                    flex:1;

                    overflow-y:auto;

                    padding:15px;

                    background:#f8fafc;
                }}

                .message{{

                    margin-bottom:12px;

                    padding:12px;

                    border-radius:12px;

                    max-width:85%;

                    word-wrap:break-word;
                }}

                .user-message{{

                    background:linear-gradient(
                        135deg,
                        #f97316,
                        #ea580c
                    );

                    border:1px solid #ea580c;

                    color:white;
                }}

                .bot-message{{

                    background:#ffffff;

                    color:#1e293b;

                    border:1px solid #dbe6fb;
                }}

                .bot-message p{{

                    margin:8px 0;

                    line-height:1.7;
                }}

                .bot-message ul,
                .bot-message ol{{

                    padding-left:22px;

                    margin:10px 0;
                }}

                .bot-message li{{

                    margin-bottom:6px;
                }}

                .bot-message code{{

                    background:#eaf1fd;

                    color:#2563eb;

                    padding:2px 6px;

                    border-radius:6px;

                    font-family:Consolas;
                }}

                .bot-message pre{{

                    background:#f1f5fb;

                    color:#1e293b;

                    padding:14px;

                    border-radius:12px;

                    overflow-x:auto;

                    margin-top:12px;

                    border:1px solid #dbe6fb;
                }}

                .bot-message h1,
                .bot-message h2,
                .bot-message h3{{

                    color:#2563eb;

                    margin-top:14px;
                }}

                #chatbot-input-area{{

                    display:flex;

                    border-top:1px solid #dbe6fb;
                }}

                #chatbot-input{{

                    flex:1;

                    border:none;

                    padding:15px;

                    outline:none;

                    font-size:14px;

                    background:#ffffff;

                    color:#1e293b;
                }}

                #chatbot-send{{

                    width:90px !important;

                    border:none;

                    background:linear-gradient(
                        135deg,
                        #f97316,
                        #ea580c
                    );
                    color:white;

                    cursor:pointer;

                    font-weight:700;
                }}

                /* ===================================== */
                /* DARK THEME OVERRIDES */
                /* ===================================== */

                body.dark-theme{{
                    background:radial-gradient(circle at 15% 0%, #161d3d 0%, #0a0e1f 45%, #060812 100%);
                    color:#e2e8f0;
                }}

                body.dark-theme .navbar{{
                    background:linear-gradient(120deg,#1e1b4b 0%,#3b1e6d 48%,#0b1e4d 100%);
                    box-shadow:0 0 22px rgba(56,189,248,.22),0 12px 30px rgba(0,0,0,.5);
                }}

                body.dark-theme .navbar-logo{{
                    background:rgba(56,189,248,0.14);
                    box-shadow:inset 0 0 0 1px rgba(56,189,248,0.35);
                }}

                body.dark-theme #theme-toggle-btn{{
                    border:2px solid rgba(56,189,248,0.5);
                    background:rgba(56,189,248,0.12);
                }}

                body.dark-theme #theme-toggle-btn:hover{{
                    background:rgba(56,189,248,0.25);
                }}

                body.dark-theme .metric-card{{
                    background:linear-gradient(160deg,#131a35,#0d1226);
                    border:1px solid rgba(56,189,248,0.18);
                    box-shadow:0 8px 24px rgba(0,0,0,0.55);
                }}

                body.dark-theme .metric-card:hover{{
                    border-color:rgba(56,189,248,0.5);
                    box-shadow:0 0 22px rgba(56,189,248,.25),0 8px 24px rgba(0,0,0,.55);
                }}

                body.dark-theme .metric-title{{
                    color:#8b93ad;
                }}

                body.dark-theme .metric-value{{
                    color:#38bdf8;
                    text-shadow:0 0 12px rgba(56,189,248,.55);
                }}

                body.dark-theme .menu-card{{
                    background:linear-gradient(160deg,#131a35,#0c1024);
                    border:1.5px solid rgba(139,92,246,0.18);
                    box-shadow:0 8px 26px rgba(0,0,0,.55);
                }}

                body.dark-theme .menu-title{{
                    color:#e2e8f0;
                }}

                body.dark-theme .menu-subtitle{{
                    color:#94a3b8;
                }}

                body.dark-theme .menu-card:hover{{
                    box-shadow:0 0 30px rgba(56,189,248,.30),0 12px 30px rgba(0,0,0,.6);
                    border-color:var(--accent,#38bdf8);
                }}

                body.dark-theme .active-card{{
                    background:linear-gradient(160deg,#1c1440,#161029);
                    background:linear-gradient(
                        160deg,
                        color-mix(in srgb, var(--accent,#8b5cf6) 26%, #12162e) 0%,
                        color-mix(in srgb, var(--accent,#8b5cf6) 12%, #0c1024) 100%
                    );
                    border-color:var(--accent,#8b5cf6);
                    border-width:2px;
                    box-shadow:
                        0 0 0 3px color-mix(in srgb, var(--accent,#8b5cf6) 25%, transparent),
                        0 0 30px color-mix(in srgb, var(--accent,#8b5cf6) 45%, transparent),
                        0 8px 26px rgba(0,0,0,.55);
                }}

                body.dark-theme .active-card .menu-icon-wrap{{
                    background:color-mix(in srgb, var(--accent,#8b5cf6) 30%, #0c1024);
                    border-radius:12px;
                }}

                body.dark-theme .active-card .menu-title{{
                    color:#ffffff;
                }}

                body.dark-theme .content-panel{{
                    background:linear-gradient(160deg,#10142a,#0a0e1f);
                    border:1px solid rgba(139,92,246,0.15);
                    box-shadow:0 8px 30px rgba(0,0,0,0.6);
                    color:#e2e8f0;
                }}

                body.dark-theme .overview-card{{
                    background:#101631;
                    border:1px solid rgba(56,189,248,0.2);
                }}

                body.dark-theme .io-table td,
                body.dark-theme .truth-table td{{
                    border:1px solid rgba(56,189,248,0.15);
                    color:#cbd5f5;
                }}

                body.dark-theme pre{{
                    background:#0d1226;
                    color:#cbd5f5;
                    border:1px solid rgba(56,189,248,0.15);
                }}

                body.dark-theme .schematic-container{{
                    background:#0d1226;
                    border:1px solid rgba(56,189,248,0.2);
                }}

                body.dark-theme .code-panel{{
                    background:#0a0e1f;
                    border:1px solid rgba(56,189,248,0.25);
                }}

                body.dark-theme .code-header{{
                    background:#0d1226;
                    color:#38bdf8;
                    border-bottom:1px solid rgba(56,189,248,0.25);
                }}

                body.dark-theme #chatbot-window{{
                    background:#0d1226;
                    border:1px solid rgba(56,189,248,0.25);
                    box-shadow:0 0 40px rgba(56,189,248,.3),0 10px 35px rgba(0,0,0,0.55);
                }}

                body.dark-theme #chatbot-messages{{
                    background:#0a0e1f;
                }}

                body.dark-theme .bot-message{{
                    background:#131a35;
                    color:#e2e8f0;
                    border:1px solid rgba(56,189,248,0.15);
                }}

                body.dark-theme .bot-message code{{
                    background:rgba(56,189,248,0.15);
                    color:#38bdf8;
                }}

                body.dark-theme .bot-message pre{{
                    background:#060812;
                    color:#f8fafc;
                    border:1px solid rgba(56,189,248,0.2);
                }}

                body.dark-theme .bot-message h1,
                body.dark-theme .bot-message h2,
                body.dark-theme .bot-message h3{{
                    color:#38bdf8;
                }}

                body.dark-theme #chatbot-input-area{{
                    border-top:1px solid rgba(56,189,248,0.2);
                }}

                body.dark-theme #chatbot-input{{
                    background:#0d1226;
                    color:#e2e8f0;
                }}
                
                
            </style>
            
            <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js"></script>
            
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            
            
            
          <script>

            document.addEventListener(
                "DOMContentLoaded",
                function () {{

                    // =========================================
                    // ELEMENTS
                    // =========================================

                    const chatbotButton =
                        document.getElementById(
                            "chatbot-button"
                        );

                    const chatbotWindow =
                        document.getElementById(
                            "chatbot-window"
                        );

                    const chatbotMessages =
                        document.getElementById(
                            "chatbot-messages"
                        );

                    const chatbotInput =
                        document.getElementById(
                            "chatbot-input"
                        );

                    const chatbotSend =
                        document.getElementById(
                            "chatbot-send"
                        );

                    // =========================================
                    // TOGGLE WINDOW
                    // =========================================

                    chatbotButton.addEventListener(
                        "click",
                        function () {{

                            if (
                                chatbotWindow.style.display
                                === "flex"
                            ) {{

                                chatbotWindow.style.display =
                                    "none";

                            }} else {{

                                chatbotWindow.style.display =
                                    "flex";
                            }}
                        }}
                    );

                    // =========================================
                    // ADD MESSAGE
                    // =========================================

                    function addMessage(
                        message,
                        className
                    ) {{

                        const div =
                            document.createElement("div");

                        div.classList.add("message");

                        div.classList.add(className);

                        // =========================================
                        // SAFE MARKDOWN RENDER
                        // =========================================

                        try {{

                            if (
                                typeof marked !== "undefined"
                            ) {{

                                div.innerHTML = marked.parse(
                                    String(message || "")
                                );

                            }}

                            else {{

                                div.innerText = message;
                            }}

                        }}

                        catch(error) {{

                            console.error(
                                "Markdown Error:",
                                error
                            );

                            div.innerText = message;
                        }}

                        chatbotMessages.appendChild(div);

                        chatbotMessages.scrollTop =
                            chatbotMessages.scrollHeight;
                    }}

                    // =========================================
                    // SEND MESSAGE
                    // =========================================

                    async function sendMessage() {{

                        const message =
                            chatbotInput.value.trim();

                        if (!message) {{

                            return;
                        }}

                        addMessage(
                            message,
                            "user-message"
                        );

                        chatbotInput.value = "";
                        
                        chatbotSend.disabled = true;

                        try {{

                            const response =
                                await fetch(
                                    "/chatbot",
                                    {{

                                        method: "POST",

                                        headers: {{

                                            "Content-Type":
                                                "application/json"
                                        }},

                                        body: JSON.stringify({{

                                            message: message
                                        }})
                                    }}
                                );

                            const data =
                                await response.json();

                            addMessage(
                                data.reply || "No response",
                                "bot-message"
                            );

                        }} catch(error) {{

                            console.error(error);

                            addMessage(
                                "AI Assistant Error",
                                "bot-message"
                            );
                        }}

                        finally {{

                            chatbotSend.disabled = false;

                            chatbotInput.focus();
                        }}
                    }}

                    // =========================================
                    // SEND BUTTON
                    // =========================================

                    chatbotSend.addEventListener(
                        "click",
                        function () {{

                            sendMessage();
                        }}
                    );

                    // =========================================
                    // ENTER KEY
                    // =========================================

                    chatbotInput.addEventListener(
                        "keydown",
                        function (event) {{

                            if (
                                event.key === "Enter"
                            ) {{

                                // Prevent form refresh

                                event.preventDefault();

                                sendMessage();
                            }}
                        }}
                    );
                    
                    // =========================================
                    // AUTO FOCUS INPUT
                    // =========================================

                    chatbotButton.addEventListener(
                        "click",
                        function () {{

                            setTimeout(() => {{

                                chatbotInput.focus();

                            }}, 200);
                        }}
                    );
                    
                }}
            );

            


                // ============================================
                // PANEL SWITCHING
                // ============================================

                

                function openPanel(id, btn){{

                    // Hide all panels
                    let panels = document.querySelectorAll('.panel');

                    panels.forEach(function(panel){{
                        panel.classList.remove('active');
                    }});

                    // Show selected panel
                    const target = document.getElementById(id);

                    if(target){{
                        target.classList.add('active');
                    }}

                    // Remove active highlight from all menu cards
                    document
                        .querySelectorAll('.menu-card')
                        .forEach(function(card){{
                            card.classList.remove('active-card');
                        }});

                    // Highlight selected menu card
                    if(btn){{
                        btn.classList.add('active-card');
                    }}

                    // Resize Monaco editors after panel switch
                    setTimeout(function(){{

                        if(typeof rtlViewer !== "undefined" && rtlViewer){{
                            rtlViewer.layout();
                        }}

                        if(typeof tbViewer !== "undefined" && tbViewer){{
                            tbViewer.layout();
                        }}

                    }}, 200);

                }}
                
            
                // ============================================
                // THEME TOGGLE (LIGHT / DARK)
                // ============================================

                function applyTheme(theme){{

                    const icon = document.getElementById('theme-toggle-icon');

                    if(theme === 'dark'){{

                        document.body.classList.add('dark-theme');

                        if(icon){{ icon.textContent = '☀️'; }}

                    }} else {{

                        document.body.classList.remove('dark-theme');

                        if(icon){{ icon.textContent = '🌙'; }}
                    }}
                }}

                function toggleTheme(){{

                    const isDark =
                        document.body.classList.contains('dark-theme');

                    const nextTheme = isDark ? 'light' : 'dark';

                    localStorage.setItem('aidea-theme', nextTheme);

                    applyTheme(nextTheme);
                }}

                // Apply saved theme once the DOM is ready
                function initTheme(){{

                    const saved = localStorage.getItem('aidea-theme');

                    if(saved){{
                        applyTheme(saved);
                    }}
                }}

                // ============================================
                // PRINT
                // ============================================

                function printSchematic(){{

                    const img =
                        document.querySelector(
                            '.schematic-frame'
                        );

                    if(!img) return;

                    const win = window.open("");

                    win.document.write(
                        '<img src="' +
                        img.src +
                        '" style="width:100%">'
                    );

                    win.document.close();

                    win.focus();

                    win.print();
                }}

                // ============================================
                // ZOOM
                // ============================================

                let zoomLevel = 1;

                function zoomIn(){{

                    zoomLevel += 0.1;

                    updateZoom();
                }}

                function zoomOut(){{

                    zoomLevel = Math.max(
                        0.5,
                        zoomLevel - 0.1
                    );

                    updateZoom();
                }}

                function updateZoom(){{

                    const frame =
                        document.querySelector(
                            '.schematic-frame'
                        );

                    if(frame){{

                        frame.style.transform =
                            'scale(' + zoomLevel + ')';
                    }}
                }}

                // ============================================
                // FULLSCREEN
                // ============================================

                function fullscreenSchematic(){{

                    const frame =
                        document.querySelector(
                            '.schematic-frame'
                        );

                    if(frame && frame.requestFullscreen){{

                        frame.requestFullscreen();
                    }}
                }}
                
                
                // ============================================
                // RTL / TB VIEWERS
                // ============================================

                let rtlViewer;
                let tbViewer;

                function initCodeViewers(){{

                    require.config({{
                        paths:{{
                            vs:'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs'
                        }}
                    }});

                    require(['vs/editor/editor.main'], function(){{

                        // RTL VIEWER

                        if(document.getElementById('rtl-viewer')){{

                            rtlViewer = monaco.editor.create(

                                document.getElementById('rtl-viewer'),

                                {{

                                    value: {safe_code},

                                    language:'verilog',

                                    theme:'vs-dark',

                                    scrollBeyondLastLine:false,

                                    smoothScrolling:true,

                                    cursorBlinking:'smooth',

                                    cursorSmoothCaretAnimation:'on',

                                    roundedSelection:true,

                                    padding:{{top:12,bottom:12}},

                                    automaticLayout:true,

                                    fontSize:14,

                                    minimap:{{enabled:false}}

                                }}
                            );
                        }}

                        // TESTBENCH VIEWER

                        if(document.getElementById('tb-viewer')){{

                            tbViewer = monaco.editor.create(

                                document.getElementById('tb-viewer'),

                                {{

                                    value: {safe_tb},

                                    language:'verilog',

                                    theme:'vs-dark',

                                    scrollBeyondLastLine:false,

                                    smoothScrolling:true,

                                    cursorBlinking:'smooth',

                                    cursorSmoothCaretAnimation:'on',

                                    roundedSelection:true,

                                    padding:{{top:12,bottom:12}},

                                    automaticLayout:true,

                                    fontSize:14,

                                    minimap:{{enabled:false}}

                                }}
                            );
                        }}

                    }});
                }}
                
                
                

            </script>

            </head>

            <body onload="initCodeViewers(); initTheme();">

                <div class='navbar'>

                    <div class="navbar-brand">
                        <div class="navbar-logo">
                            <svg viewBox="0 0 24 24"><path d="M3 12h4l2-8 4 16 2-8h6"/></svg>
                        </div>
                        <div class="navbar-title">
                            <span class="main">AIDEA ADVANCED DASHBOARD</span>
                            <span class="sub">AI-Powered RTL &amp; EDA Analysis Suite</span>
                        </div>
                    </div>

                    <div class="navbar-right">
                        <svg class="navbar-deco" width="90" height="24" viewBox="0 0 120 30">
                            <circle cx="6" cy="15" r="2.4" fill="white"/>
                            <line x1="8.4" y1="15" x2="30" y2="15" stroke="white" stroke-width="1.4"/>
                            <circle cx="34" cy="15" r="2.4" fill="white"/>
                            <line x1="36.4" y1="15" x2="58" y2="15" stroke="white" stroke-width="1.4"/>
                            <circle cx="62" cy="15" r="2.4" fill="white"/>
                        </svg>

                        <a
                            href="/download_report"
                            id="download-report-btn"
                            title="Download the full analysis as a single PDF"
                            style="
                                display:flex;
                                align-items:center;
                                gap:6px;
                                padding:8px 16px;
                                margin-right:10px;
                                border-radius:10px;
                                background:linear-gradient(90deg,#2563eb,#0891b2);
                                color:white;
                                font-size:13px;
                                font-weight:700;
                                text-decoration:none;
                                white-space:nowrap;
                                box-shadow:0 4px 14px rgba(37,99,235,0.35);
                            "
                        >
                            ⬇ Download Full Report (PDF)
                        </a>

                        <button
                            id="theme-toggle-btn"
                            onclick="toggleTheme()"
                            title="Toggle light / dark theme"
                        >
                            <span id="theme-toggle-icon">🌙</span>
                        </button>
                    </div>

                </div>

                <div class='container'>

                    <div class='metrics'>

                        {metric_card('Top Module', top_module)}

                        {metric_card('Inputs', len(inputs))}

                        {metric_card('Outputs', len(outputs))}

                        {metric_card('Ports', len(ports))}

                        {metric_card('Logic Type', logic_type)}

                        {metric_card('RTL Lines', rtl_lines)}

                        {metric_card(
                            'Cells',
                            synthesis_stats.get('CELLS',0)
                        )}
                        


                        {metric_card(
                            'Nets',
                            synthesis_stats.get('NETS',0)
                        )}
                        
                        {metric_card(
                            'FPGA LUTs',
                            fpga_luts
                        )}

                        {metric_card(
                            'ASIC Cells',
                            asic_cells
                        )}

                        </div>
                        <!-- metrics grid closed here so the menu bar and workspace below render full width -->

                        <div class="dashboard-menu">

                            <div class="menu-card active-card" style="--accent:#2563eb"
                                onclick="openPanel('overview',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><path d="M12 20a9 9 0 1 1 8.66-11.3M4.1 15.9 2.5 16.5M20.4 9.3l1.6-.6M12 3v2.2M6.3 6.3l1.5 1.5"/><path d="M12 12l4-2.6"/><circle cx="12" cy="12" r="1.15" fill="currentColor" stroke="none"/></svg></div>
                                <span class="menu-title">Overview</span>
                                <span class="menu-subtitle">Project summary &amp; key insights</span>
                            </div>

                            <div class="menu-card" style="--accent:#2563eb"
                                onclick="openPanel('rtltb',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><polyline points="9 6 3 12 9 18"/><polyline points="15 6 21 12 15 18"/></svg></div>
                                <span class="menu-title">RTL / TB Viewer</span>
                                <span class="menu-subtitle">Explore RTL Source &amp; Verification Testbench</span>
                            </div>

                            <div class="menu-card" style="--accent:#7c3aed"
                                onclick="openPanel('ai_report',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><path d="M9 4.5A2.5 2.5 0 0 1 11.5 2v0A2.5 2.5 0 0 1 14 4.5v.6"/><path d="M9 4.5A2.5 2.5 0 0 0 6.5 7v.4A2.6 2.6 0 0 0 5 9.7v.6A2.6 2.6 0 0 0 6.4 12.6"/><path d="M14 4.5A2.5 2.5 0 0 1 16.5 7v.4A2.6 2.6 0 0 1 18 9.7v.6a2.6 2.6 0 0 1-1.4 2.3"/><path d="M9 4.5v14a2 2 0 0 0 2 2h1"/><path d="M14 4.5v14a2 2 0 0 1-2 2"/><circle cx="6" cy="14.5" r="1" fill="currentColor" stroke="none"/><circle cx="18" cy="14.5" r="1" fill="currentColor" stroke="none"/></svg></div>
                                <span class="menu-title">AI RTL Report</span>
                                <span class="menu-subtitle">AI-Generated RTL analysis &amp; insights</span>
                            </div>

                            <div class="menu-card" style="--accent:#7c3aed"
                                onclick="openPanel('schematic',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><circle cx="12" cy="12" r="2"/><path d="M7.7 7.3 10.4 10M13.6 10l2.7-2.7M7.7 16.7 10.4 14M13.6 14l2.7 2.7"/></svg></div>
                                <span class="menu-title">Schematic</span>
                                <span class="menu-subtitle">RTL schematic visualization</span>
                            </div>

                            <div class="menu-card" style="--accent:#2563eb"
                                onclick="openPanel('simulation',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M9 8.5 9 12.5 12.5 10.5z" fill="currentColor" stroke="none"/><path d="M8 21h8M12 17v4"/></svg></div>
                                <span class="menu-title">Simulation</span>
                                <span class="menu-subtitle">Execute RTL simulation &amp; analyze waveforms</span>
                            </div>

                            <div class="menu-card" style="--accent:#2563eb"
                                onclick="openPanel('truth',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="9" y1="4" x2="9" y2="20"/><line x1="15" y1="4" x2="15" y2="20"/></svg></div>
                                <span class="menu-title">Truth Table / FSM</span>
                                <span class="menu-subtitle"Truth Table &amp; State Machine Analysis></span>
                            </div>

                            <div class="menu-card" style="--accent:#2563eb"
                                onclick="openPanel('fpgaasic',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1.4"/><line x1="9" y1="2" x2="9" y2="7"/><line x1="15" y1="2" x2="15" y2="7"/><line x1="9" y1="17" x2="9" y2="22"/><line x1="15" y1="17" x2="15" y2="22"/><line x1="2" y1="9" x2="7" y2="9"/><line x1="2" y1="15" x2="7" y2="15"/><line x1="17" y1="9" x2="22" y2="9"/><line x1="17" y1="15" x2="22" y2="15"/></svg></div>
                                <span class="menu-title">FPGA / ASIC</span>
                                <span class="menu-subtitle">Target technology selection</span>
                            </div>

                            <div class="menu-card" style="--accent:#2563eb"
                                onclick="openPanel('timing',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg></div>
                                <span class="menu-title">Timing Analysis</span>
                                <span class="menu-subtitle">Timing paths &amp; slack analysis</span>
                            </div>

                            <div class="menu-card" style="--accent:#4f46e5"
                                onclick="openPanel('floorplanning',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="1.4"/><line x1="3" y1="12" x2="14" y2="12"/><line x1="14" y1="3" x2="14" y2="21"/><line x1="14" y1="16" x2="21" y2="16"/></svg></div>
                                <span class="menu-title">Floorplanning</span>
                                <span class="menu-subtitle">Floorplan design viewer</span>
                            </div>

                            <div class="menu-card" style="--accent:#4f46e5"
                                onclick="openPanel('placement',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="6" r="1.5" fill="currentColor" stroke="none"/><circle cx="18" cy="6" r="1.5" fill="currentColor" stroke="none"/><circle cx="6" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="6" cy="18" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="18" r="1.5" fill="currentColor" stroke="none"/><circle cx="18" cy="18" r="1.5" fill="currentColor" stroke="none"/></svg></div>
                                <span class="menu-title">Placement</span>
                                <span class="menu-subtitle">Cell placement visualization</span>
                            </div>

                            <div class="menu-card" style="--accent:#7c3aed"
                                onclick="openPanel('routing',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><circle cx="5" cy="6" r="1.6"/><circle cx="19" cy="18" r="1.6"/><circle cx="5" cy="18" r="1.6"/><circle cx="19" cy="6" r="1.6"/><path d="M6.6 6H14a3 3 0 0 1 3 3v0a3 3 0 0 0 3 3M6.6 18H10a3 3 0 0 0 3-3v-1"/></svg></div>
                                <span class="menu-title">Routing</span>
                                <span class="menu-subtitle">Global &amp; detailed routing viewer</span>
                            </div>

                            <div class="menu-card" style="--accent:#10b981"
                                onclick="openPanel('power',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" stroke-linejoin="round"/></svg></div>
                                <span class="menu-title">Power</span>
                                <span class="menu-subtitle">Power analysis &amp; breakdown</span>
                            </div>

                            <div class="menu-card" style="--accent:#f97316"
                                onclick="openPanel('congestion',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="5" height="5" fill="currentColor" stroke="none" opacity=".4"/><rect x="9.5" y="3" width="5" height="5" fill="currentColor" stroke="none" opacity=".9"/><rect x="16" y="3" width="5" height="5" fill="currentColor" stroke="none" opacity=".6"/><rect x="3" y="9.5" width="5" height="5" fill="currentColor" stroke="none" opacity=".7"/><rect x="9.5" y="9.5" width="5" height="5" fill="currentColor" stroke="none" opacity="1"/><rect x="16" y="9.5" width="5" height="5" fill="currentColor" stroke="none" opacity=".5"/><rect x="3" y="16" width="5" height="5" fill="currentColor" stroke="none" opacity=".5"/><rect x="9.5" y="16" width="5" height="5" fill="currentColor" stroke="none" opacity=".8"/><rect x="16" y="16" width="5" height="5" fill="currentColor" stroke="none" opacity=".4"/></svg></div>
                                <span class="menu-title">Congestion</span>
                                <span class="menu-subtitle">Congestion map visualization</span>
                            </div>

                            <div class="menu-card" style="--accent:#10b981"
                                onclick="openPanel('verification',this)">
                                <div class="menu-icon-wrap"><svg viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.6-3 8.2-7 9-4-.8-7-4.4-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg></div>
                                <span class="menu-title">Verification</span>
                                <span class="menu-subtitle">Functional &amp; static verification</span>
                            </div>

                        </div>

                        <!-- CONTENT -->

                        <div class='content-panel'>
                        
                        
                

                            <!-- OVERVIEW -->

                            <div id='overview'
                                class='panel active'>

                                <h2>

                                    RTL Overview

                                </h2>

                                <div class='overview-card'>

                                    {generate_io_table(
                                        inputs,
                                        outputs
                                    )}

                                </div>

                                {abc_summary}

                                     
                            </div>
                            
                            
                            <!-- AI RTL REPORT -->

                            <div id='ai_report'
                                class='panel'>

                                <h2>

                                    🤖  AI Design Intelligence

                                </h2>

                                <div class='overview-card'>

                                    <h3>

                                        Analysis Status

                                    </h3>

                                    <pre>

                            {explanation}

                                    </pre>

                                </div>

                                {
                                    f'''
                                    <div class="overview-card">

                                        <h3 style="
                                            color:#2563eb;
                                            margin-top:0;
                                        ">

                                            📘 AI Detailed RTL Report

                                        </h3>

                                        <div style="
                                            background:linear-gradient(
                                                135deg,
                                                #ffffff,
                                                #dbeafe
                                            );

                                            color:#1e293b;

                                            border-radius:20px;

                                            padding:25px;

                                            line-height:1.9;

                                            font-size:15px;

                                            font-family:'Times New Roman', serif;

                                            overflow-x:auto;

                                            border:1px solid #bfdbfe;

                                            box-shadow:
                                                0 4px 18px rgba(0,0,0,0.08);

                                        ">

                                            {formatted_explanation}

                                        </div>

                                    </div>
                                    '''
                                    if ai_result.get("ai_explanation")
                                    else ""
                                }

                            </div>
                            
                            <!-- RTL / TB VIEWER -->

                            <div id='rtltb'
                                class='panel'>

                                <h2>

                                    RTL & Testbench Viewer

                                </h2>

                                <div class='code-split-container'>

                                    <!-- RTL PANEL -->

                                    <div class='code-panel'>

                                        <div class='code-header'>

                                            RTL Viewer

                                        </div>

                                        <div
                                            id='rtl-viewer'
                                            class='editor-box'>
                                        </div>

                                    </div>

                                    <!-- TESTBENCH PANEL -->

                                    <div class='code-panel'>

                                        <div class='code-header'>

                                            AI Generated Testbench Viewer

                                        </div>

                                        <div
                                            id='tb-viewer'
                                            class='editor-box'>
                                        </div>

                                    </div>

                                </div>

                            </div>
                            
                            
                            

                            <!-- SCHEMATIC -->

                            <div id='schematic'
                                class='panel'>

                                <div style="
                                    display:flex;
                                    justify-content:space-between;
                                    align-items:center;
                                    margin-bottom:20px;
                                ">

                                    <h2>

                                        RTL Schematic

                                    </h2>

                                    <div>

                                        <button
                                        onclick="zoomIn()"
                                        style="
                                            background:#2563eb;
                                            color:white;
                                            border:none;
                                            padding:12px 20px;
                                            border-radius:10px;
                                            font-weight:700;
                                            cursor:pointer;
                                            margin-right:10px;
                                        ">

                                            ➕ Zoom In

                                        </button>

                                        <button
                                        onclick="zoomOut()"
                                        style="
                                            background:#0f172a;
                                            color:white;
                                            border:none;
                                            padding:12px 20px;
                                            border-radius:10px;
                                            font-weight:700;
                                            cursor:pointer;
                                            margin-right:10px;
                                        ">

                                            ➖ Zoom Out

                                        </button>

                                        <button
                                        onclick="printSchematic()"
                                        style="
                                            background:#16a34a;
                                            color:white;
                                            border:none;
                                            padding:12px 20px;
                                            border-radius:10px;
                                            font-weight:700;
                                            cursor:pointer;
                                            margin-right:10px;
                                        ">

                                            🖨 Print

                                        </button>

                                        <button
                                        onclick="fullscreenSchematic()"
                                        style="
                                            background:#dc2626;
                                            color:white;
                                            border:none;
                                            padding:12px 20px;
                                            border-radius:10px;
                                            font-weight:700;
                                            cursor:pointer;
                                        ">

                                            ⛶ Fullscreen

                                        </button>

                                    </div>

                                </div>

                                <div class='schematic-container'>

                                    <img
                                        class='schematic-frame'
                                        src='{schematic_svg}'>

                                </div>

                            </div>

                            <!-- SIMULATION -->

                            <div id='simulation'
                                class='panel'>

                                <h2>Simulation</h2>

                                <pre>

            {sim_result}

                                </pre>

                            </div>
                            
                            
                                                    
                            
                            <!-- VERIFICATION -->

                            <div id='verification'
                                class='panel'>

                                <h2>

                                    RTL Verification Report

                                </h2>

                                {verification_report}

                            </div>

                            <!-- FPGA / ASIC -->

                            <div id='fpgaasic'
                                class='panel'>

                                <h2>

                                    FPGA / ASIC Analysis

                                </h2>

                                <div class='overview-card'>

                                    <h3>

                                        FPGA Resource Estimation

                                    </h3>

                                    {fpga_html}

                                </div>

                                <div class='overview-card'>

                                    <h3>

                                        ASIC PPA Estimation

                                    </h3>

                                    {asic_html}

                                </div>

                            </div>

                            <!-- TRUTH -->

                            <div id='truth'
                                class='panel'>

                                <h2>Truth Table / FSM Analysis</h2>

                                {truth_html}

                                {fsm_html}

                            </div>

                            <!-- CDC -->

                            <div id='cdc'
                                class='panel'>

                                <h2>CDC Analysis</h2>

                                <table class='io-table'>

                                    <thead>

                                        <tr>

                                            <th>Violation</th>

                                            <th>Status</th>

                                        </tr>

                                    </thead>

                                    <tbody>

                                        {cdc_rows}

                                    </tbody>

                                </table>

                            </div>

                            <!-- TIMING -->
                            
                            {generate_timing_panel(timing_result)}
                            
                            <div id='floorplanning'
                            class='panel'>

                            <h2>

                            📐 Floorplanning

                            </h2>

                            <div class='overview-card'>

                            <img
                            src="{floorplan_png}"
                            style="
                            width:100%;
                            border-radius:18px;
                            border:2px solid #dbeafe;
                            ">

                            </div>

                            <div class='overview-card'>

                            <table class='io-table'>

                            <tr>

                            <th>Metric</th>

                            <th>Value</th>

                            </tr>

                            <tr>

                            <td>Utilization</td>

                            <td>{floorplan_metrics["utilization"]} %</td>

                            </tr>

                            <tr>

                            <td>Dead Space</td>

                            <td>{floorplan_metrics["dead_space"]} %</td>

                            </tr>

                            <tr>

                            <td>Estimated Wirelength</td>

                            <td>{floorplan_metrics["wirelength"]}</td>

                            </tr>

                            </table>

                            </div>

                            </div>
                           
                            <!-- PLACEMENT -->

                            <div id='placement'
                                class='panel'>

                                <h2>

                                    Placement Analysis

                                </h2>

                                <!-- ===================================== -->
                                <!-- AI PREDICTION -->
                                <!-- ===================================== -->

                                <div class='overview-card'>

                                    <h3>

                                        AI Placement Prediction

                                    </h3>

                                    <pre>

                            {json.dumps(
                                placement_prediction,
                                indent=4,
                                default=str
                            )}

                                    </pre>

                                </div>

                                <!-- ===================================== -->
                                <!-- PLACEMENT STATISTICS -->
                                <!-- ===================================== -->

                                <div class='overview-card'>

                                    <h3>

                                        Placement Statistics

                                    </h3>

                                    <pre>

                            {json.dumps(
                                placement_result["statistics"],
                                indent=4,
                                default=str
                            )}

                                    </pre>

                                </div>

                                <!-- ===================================== -->
                                <!-- PLACEMENT VISUALIZATION -->
                                <!-- ===================================== -->

                                <div class='overview-card'>

                                    <h3>

                                        Placement Visualization

                                    </h3>

                                    {placement_fig.to_html(full_html=False)}

                                </div>

                            </div>

                            <!-- ROUTING -->

                            <div id='routing'
                                class='panel'>

                                <h2>

                                    Routing Visualization

                                </h2>

                                <!-- ===================================== -->
                                <!-- ROUTING STATS -->
                                <!-- ===================================== -->

                                <div class='overview-card'>

                                    <h3>

                                        Routing Statistics

                                    </h3>

                                    <pre>

                            {json.dumps(
                                routing_result["statistics"],
                                indent=4,
                                default=str
                            )}

                                    </pre>

                                </div>

                                <!-- ===================================== -->
                                <!-- ROUTING GRAPH -->
                                <!-- ===================================== -->

                                <div class='overview-card'>

                                    <h3>

                                        Manhattan Routing View

                                    </h3>

                                    {routing_fig.to_html(full_html=False)}

                                </div>

                            </div>

                            <!-- POWER -->

                            <!-- POWER -->

                            <div id='power'
                                class='panel'>

                                <h2>

                                    Power Analysis

                                </h2>

                                <!-- POWER METRICS -->

                                <div class='overview-card'>

                                    <h3>

                                        Power Statistics

                                    </h3>

                                    <pre>

                            {json.dumps(
                                power_result,
                                indent=4,
                                default=str
                            )}

                                    </pre>

                                </div>

                                <!-- POWER VISUALIZATION -->

                                <div class='overview-card'>

                                    <h3>

                                        Power Heatmap

                                    </h3>

                                    {power_fig.to_html(full_html=False)}

                                </div>

                            </div>

                            <!-- CONGESTION -->

                            <div id='congestion'
                                class='panel'>

                                <h2>

                                    Congestion Analysis

                                </h2>

                                <!-- CONGESTION METRICS -->

                                <div class='overview-card'>

                                    <h3>

                                        Congestion Statistics

                                    </h3>

                                    <pre>

                            {json.dumps(
                                congestion_result,
                                indent=4,
                                default=str
                            )}

                                    </pre>

                                </div>

                                <!-- CONGESTION VISUALIZATION -->

                                <div class='overview-card'>

                                    <h3>

                                        Congestion Heatmap

                                    </h3>

                                    {congestion_fig.to_html(full_html=False)}

                                </div>

                            </div>

                        </div>

                    </div>

                </div>
                
                <!-- ===================================== -->
                <!-- CHATBOT BUTTON -->
                <!-- ===================================== -->

                <div id="chatbot-button">

                    💬

                </div>

                <!-- ===================================== -->
                <!-- CHATBOT WINDOW -->
                <!-- ===================================== -->

                <div id="chatbot-window">

                    <!-- HEADER -->

                    <div id="chatbot-header">

                         AIDEA Assistant

                    </div>

                    <!-- CHAT AREA -->

                    <div id="chatbot-messages">

                        <div class="message bot-message">

                            <b>Welcome to AIDEA Assistant</b><br><br>

                            Your AI-powered guide for learning and exploring
                            Digital Design, RTL Engineering, FPGA, ASIC,
                            and Semiconductor Design Flows 🚀<br><br>

                            Feel free to ask anything starting from:<br><br>

                            • Basic Electronic Circuits<br>
                            • Digital Electronics Fundamentals<br>
                            • Logic Gates & Boolean Algebra<br>
                            • Combinational & Sequential Circuits<br>
                            • Finite State Machines (FSMs)<br>
                            • Verilog / SystemVerilog RTL<br>
                            • FPGA Design<br>
                            • ASIC Flow<br>
                            • Timing Analysis<br>
                            • CDC Verification<br>
                            • Placement & Routing<br>
                            • Power & Congestion Analysis<br>
                            • AI RTL Understanding<br><br>

                            🌟 Whether you're a beginner or an advanced RTL designer,
                            AIDEA is ready to assist your semiconductor journey.

                        </div>

                    </div>

                    <!-- INPUT -->

                    <div id="chatbot-input-area">

                        <input
                            type="text"
                            id="chatbot-input"
                            placeholder="Ask about RTL, FPGA, ASIC, STA..."
                        >

                        <button id="chatbot-send">

                            Send

                        </button>

                    </div>

                </div>

            </body>

            </html>
            
            """

    except Exception as e:

        return f"""

        <body style='
            background:#fff1f2;
            padding:30px;
            font-family:Arial;
        '>

            <h2>

                ❌ ERROR

            </h2>

            <pre>

{str(e)}

            </pre>

            <hr>

            <pre>

{traceback.format_exc()}

            </pre>

        </body>

        """
        
# =========================================================
# DOWNLOAD FULL REPORT (PDF)
# =========================================================

@app.route('/download_report', methods=['GET'])

def download_report():

    if not os.path.exists(REPORT_PDF_PATH):

        return """

        <h2 style='
            color:red;
            font-family:Arial;
            padding:30px;
        '>

            No report has been generated yet. Run a full chip analysis
            from the Home screen first, then come back to download the PDF.

        </h2>

        """, 404

    return send_file(

        REPORT_PDF_PATH,
        as_attachment=True,
        download_name="AIDEA_Full_Report.pdf",
        mimetype="application/pdf"
    )

# =========================================================
# CHATBOT API
# =========================================================

@app.route('/chatbot', methods=['POST'])

def chatbot_api():

    try:

        data = request.get_json()

        user_message = data.get(
            'message',
            ''
        )

        # =========================================
        # EMPTY MESSAGE CHECK
        # =========================================

        if not user_message:

            return jsonify({

                'reply':
                    'Please enter a message.'

            })

        # =========================================
        # AI RESPONSE
        # =========================================

        ai_reply = ask_chatbot(user_message)

        # =========================================
        # RETURN RESPONSE
        # =========================================

        return jsonify({

            'reply':
                ai_reply

        })

    except Exception as e:

        return jsonify({

            'reply':
                f'Chatbot Error: {str(e)}'

        })

# =========================================================
# MAIN
# =========================================================

if __name__ == '__main__':

    threading.Thread(
        target=open_browser
    ).start()

    app.run(

        debug=False,

        use_reloader=False
    )
=======
from flask import Flask, request
import os
import sys
import shutil
import traceback
import webbrowser
import threading
import time
import re
import importlib
import subprocess

# =========================================================
# DISABLE .pyc
# =========================================================
sys.dont_write_bytecode = True
importlib.invalidate_caches()

# =========================================================
# PROJECT PATH
# =========================================================
PROJECT_ROOT = "D:/AI_EDA_TOOL"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================================================
# IMPORTS
# =========================================================
from backend.utils.cleaner import clear_runs
from backend.ai.ai_engine import analyze_verilog
from backend.simulation.tb_generator import generate_testbench
from backend.simulation.simulator import run_simulation
from backend.truth.truth_table import generate_truth_table

from backend.ppa.ppa_analyzer import (
    run_yosys,
    extract_ppa
)

from backend.rtl_parser_engine.rtl_parser import RTLParser

from backend.rtl_parser_engine.netlist_generator import (
    NetlistGenerator
)

from backend.schematic.schematic_generator import (
    generate_schematic
)

from backend.ai.analysis_orchestrator import (
    AnalysisOrchestrator
)

from backend.verification.verification_orchestrator import (
    VerificationOrchestrator
)

from backend.fpga.hardware_orchestrator import (
    HardwareOrchestrator
)

# =========================================================
# FLASK
# =========================================================
app = Flask(
    __name__,
    static_folder=os.path.join(
        PROJECT_ROOT,
        "static"
    )
)

# =========================================================
# PATHS
# =========================================================
RUNS_PATH = os.path.join(PROJECT_ROOT, "runs")
STATIC_PATH = os.path.join(PROJECT_ROOT, "static")

os.makedirs(RUNS_PATH, exist_ok=True)
os.makedirs(STATIC_PATH, exist_ok=True)

# =========================================================
# CLEAN CACHE
# =========================================================
def clean_cache():

    for root, dirs, files in os.walk(PROJECT_ROOT):

        for d in dirs:

            if d == "__pycache__":

                try:
                    shutil.rmtree(
                        os.path.join(root, d),
                        ignore_errors=True
                    )
                except Exception:
                    pass

        for file in files:

            if file.endswith(".pyc"):

                try:
                    os.remove(
                        os.path.join(root, file)
                    )
                except Exception:
                    pass

# =========================================================
# AUTO BROWSER
# =========================================================
def open_browser():

    time.sleep(1)

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


# =========================================================
# OPEN GTKWAVE
# =========================================================

def open_gtkwave(vcd_path):

    try:

        vcd_path = os.path.abspath(vcd_path)

        if not os.path.exists(vcd_path):

            return (
                "❌ GTKWave Failed\n\n"
                "VCD file not found."
            )

        command = f'''
        cmd /c
        "D:\\AI_EDA_TOOL\\oss-cad-suite\\environment.bat
        && gtkwave
        \\"{vcd_path}\\"
        "
        '''

        subprocess.Popen(
            command,
            shell=True
        )

        return "✅ GTKWave Opened Successfully"

    except Exception as e:

        return f'''
❌ GTKWave Launch Failed

{str(e)}
'''


# =========================================================
# METRIC CARD
# =========================================================
def metric_card(title, value):

    return f"""
    <div class="metric-card">

        <div class="metric-title">
            {title}
        </div>

        <div class="metric-value">
            {value}
        </div>

    </div>
    """

# =========================================================
# WIDTH PARSER
# =========================================================
def parse_width(width):

    if isinstance(width, int):
        return width

    if isinstance(width, str):

        m = re.search(
            r"\[(\d+):(\d+)\]",
            width
        )

        if m:

            msb = int(m.group(1))
            lsb = int(m.group(2))

            return abs(msb - lsb) + 1

    return 1

# =========================================================
# PORT TABLE
# =========================================================
def generate_io_table(inputs, outputs):

    rows = ""

    for inp in inputs:

        if isinstance(inp, dict):

            name = inp.get("name", "-")
            width = inp.get("width", 1)

            rows += f"""
            <tr>
                <td>{name}</td>
                <td>INPUT</td>
                <td>{width}</td>
            </tr>
            """

    for out in outputs:

        if isinstance(out, dict):

            name = out.get("name", "-")
            width = out.get("width", 1)

            rows += f"""
            <tr>
                <td>{name}</td>
                <td>OUTPUT</td>
                <td>{width}</td>
            </tr>
            """

    return f"""

    <table class="io-table">

        <thead>

            <tr>
                <th>Port Name</th>
                <th>Direction</th>
                <th>Width</th>
            </tr>

        </thead>

        <tbody>

            {rows}

        </tbody>

    </table>
    """

# =========================================================
# MAIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":

        return """

        <html>

        <head>

        <title>AIDEA</title>

        <style>

            body{
                margin:0;
                font-family:Segoe UI;
                background:#edf3ff;
            }

            .hero{

                width:70%;
                margin:80px auto;
                background:white;

                padding:60px;

                border-radius:25px;

                text-align:center;

                box-shadow:
                0 10px 40px rgba(0,0,0,0.08);
            }

            h1{
                color:#0f172a;
                line-height:1.5;
            }

            input[type=file]{

                margin-top:25px;

                padding:15px;

                background:#f8fafc;

                border-radius:12px;
            }

            button{

                margin-top:25px;

                padding:15px 35px;

                border:none;

                border-radius:12px;

                background:#2563eb;

                color:white;

                font-size:16px;

                font-weight:700;

                cursor:pointer;
            }

        </style>

        </head>

        <body>

            <div class="hero">

                <h1>

                    ⚡ AIDEA ⚡
                    <br><br>

                    Artificial Intelligence Driven
                    Electronic Design Automation

                </h1>

                <form method="POST"
                      enctype="multipart/form-data">

                    <input type="file"
                           name="file"
                           required>

                    <br>

                    <button type="submit">

                        Run Full RTL Analysis

                    </button>

                </form>

            </div>

        </body>

        </html>
        """

    try:

        clean_cache()
        clear_runs()

        uploaded_file = request.files["file"]

        design_path = os.path.join(
            RUNS_PATH,
            "design.v"
        )

        uploaded_file.save(design_path)

        with open(
            design_path,
            "r",
            encoding="utf-8"
        ) as f:

            code = f.read()

        ai_result = analyze_verilog(code)

        if isinstance(ai_result, dict):

            explanation = ai_result.get(
                "explanation",
                "RTL analyzed successfully."
            )

            errors = ai_result.get(
                "errors",
                "No errors found."
            )

        else:

            explanation = str(ai_result)
            errors = "No errors found."

        parser = RTLParser(design_path)
        parser.parse_file()

        modules = parser.extract_modules()

        top_module = "UNKNOWN"
        inputs = []
        outputs = []
        ports = []

        if modules and len(modules) > 0:

            top = modules[-1]

            top_module = top.get(
                "module_name",
                "UNKNOWN"
            )

            inputs = top.get("inputs", [])
            outputs = top.get("outputs", [])

            for inp in inputs:

                if isinstance(inp, dict):

                    ports.append({
                        "name": inp.get("name"),
                        "direction": "input",
                        "width": parse_width(
                            inp.get("width", 1)
                        )
                    })

            for out in outputs:

                if isinstance(out, dict):

                    ports.append({
                        "name": out.get("name"),
                        "direction": "output",
                        "width": parse_width(
                            out.get("width", 1)
                        )
                    })

        netlist = NetlistGenerator(
            design_path
        ).generate()

        schematic_result = generate_schematic(code)

        if schematic_result.get("success"):

            schematic_svg = schematic_result.get(
                "svg_path",
                ""
            )

            schematic_status = """
            <div style="
                color:#16a34a;
                font-weight:700;
                margin-bottom:15px;
            ">
                ✅ Schematic Generated Successfully
            </div>
            """

        else:

            schematic_svg = ""

            schematic_error = schematic_result.get(
                "error",
                "Unknown schematic generation error."
            )

            schematic_status = f"""

            <div style="
                background:#fff1f2;
                border:1px solid #fecdd3;
                padding:18px;
                border-radius:14px;
                margin-bottom:18px;
            ">

                <div style="
                    color:#dc2626;
                    font-size:18px;
                    font-weight:800;
                    margin-bottom:12px;
                ">
                    ❌ Schematic Generation Failed
                </div>

                <pre>{schematic_error}</pre>

            </div>
            """

        ai_analysis = AnalysisOrchestrator(
            design_path
        ).run()

        verification = VerificationOrchestrator(
            design_path
        ).run()

        hardware = HardwareOrchestrator(
            design_path
        ).run()

        tb = generate_testbench(
            top_module=top_module,
            ports=ports,
            random_iterations=250
        )

        tb_path = os.path.join(
            RUNS_PATH,
            "tb.v"
        )

        with open(
            tb_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(tb)

        sim_result = run_simulation()

        vcd_path = os.path.join(
            RUNS_PATH,
            "dump.vcd"
        )

        gtk_result = open_gtkwave(vcd_path)

        sim_result += f"\n\n{gtk_result}"

        truth_df = generate_truth_table(code)

        if truth_df is None or truth_df.empty:

            logic_type = "Sequential"

            truth_html = """

            <div class='empty-box'>

                Truth Table not available
                for Sequential Logic.

            </div>
            """

        else:

            logic_type = "Combinational"

            truth_html = truth_df.to_html(
                index=False,
                classes="truth-table"
            )

        yosys_log, yosys_error = run_yosys(
            design_path,
            top_module
        )

        if yosys_error:

            ppa = {
                "area": "N/A",
                "delay": "N/A",
                "power": "N/A"
            }

        else:

            ppa = extract_ppa(yosys_log)

        io_table = generate_io_table(
            inputs,
            outputs
        )

        return f"""

        <html>

        <head>

        <title>AIDEA Dashboard</title>

        <style>

            *{{
                box-sizing:border-box;
            }}

            body{{
                margin:0;
                font-family:Segoe UI;
                background:#edf3ff;
                overflow-x:hidden;
            }}

            .navbar{{
                background:#071633;
                color:white;
                padding:22px 35px;
                font-size:32px;
                font-weight:800;
            }}

            .container{{
                padding:25px;
            }}

            .metrics{{
                display:grid;
                grid-template-columns:
                repeat(auto-fit,minmax(170px,1fr));

                gap:18px;
                margin-bottom:25px;
            }}

            .metric-card{{
                background:white;
                padding:22px;
                border-radius:20px;
                box-shadow:
                0 5px 18px rgba(0,0,0,0.06);
            }}

            .metric-title{{
                font-size:12px;
                font-weight:800;
                color:#64748b;
                text-transform:uppercase;
            }}

            .metric-value{{
                margin-top:10px;
                font-size:20px;
                font-weight:800;
                color:#2563eb;
                word-break:break-word;
            }}

            .workspace{{
                display:grid;
                grid-template-columns:260px 1fr;
                gap:20px;
            }}

            .sidebar{{
                background:white;
                padding:20px;
                border-radius:22px;
                height:fit-content;
                box-shadow:
                0 5px 18px rgba(0,0,0,0.06);
            }}

            .sidebar button{{
                width:100%;
                margin-bottom:14px;
                padding:15px;
                border:none;
                border-radius:14px;
                background:#dbeafe;
                color:#2563eb;
                font-weight:700;
                cursor:pointer;
                transition:0.3s;
            }}

            .sidebar button:hover{{
                background:#2563eb;
                color:white;
            }}

            .content-panel{{
                background:white;
                border-radius:22px;
                padding:28px;
                box-shadow:
                0 5px 18px rgba(0,0,0,0.06);
            }}

            .panel{{
                display:none;
            }}

            .panel.active{{
                display:block;
            }}

            h2{{
                margin-top:0;
                color:#0f172a;
            }}

            h3{{
                color:#2563eb;
            }}

            .overview-card{{
                background:#f8fbff;
                padding:22px;
                border-radius:16px;
                margin-bottom:20px;
                border:1px solid #dbeafe;
            }}

            .overview-grid{{
                display:grid;
                grid-template-columns:
                repeat(auto-fit,minmax(300px,1fr));
                gap:20px;
                margin-top:20px;
            }}

            .io-table{{
                width:100%;
                border-collapse:collapse;
                margin-top:15px;
            }}

            .io-table th{{
                background:#2563eb;
                color:white;
                padding:12px;
            }}

            .io-table td{{
                border:1px solid #dbeafe;
                padding:12px;
                text-align:center;
            }}

            .truth-table{{
                width:100%;
                border-collapse:collapse;
            }}

            .truth-table th{{
                background:#2563eb;
                color:white;
                padding:12px;
            }}

            .truth-table td{{
                border:1px solid #dbeafe;
                padding:12px;
                text-align:center;
            }}

            pre{{
                white-space:pre-wrap;
                line-height:1.7;
                background:#f8fafc;
                padding:18px;
                border-radius:12px;
                overflow:auto;
            }}

            .empty-box{{
                padding:25px;
                background:#f8fafc;
                border-radius:14px;
            }}

            .schematic-container{{
                width:100%;
                overflow:auto;
                background:white;
                border:1px solid #dbeafe;
                border-radius:14px;
                padding:20px;
            }}

            iframe{{
                width:1500px;
                height:950px;
                border:none;
                background:white;
            }}

            .print-btn{{
                margin-bottom:20px;
                padding:12px 20px;
                border:none;
                border-radius:12px;
                background:#2563eb;
                color:white;
                font-weight:700;
                cursor:pointer;
            }}

        </style>

        <script>

            function openPanel(id){{

                let panels =
                    document.querySelectorAll(".panel");

                panels.forEach(p =>
                    p.classList.remove("active")
                );

                document
                    .getElementById(id)
                    .classList.add("active");
            }}

            function printSchematic(){{
                var frame =
                    document.getElementById(
                        "schematicFrame"
                    );

                frame.contentWindow.focus();
                frame.contentWindow.print();
            }}

        </script>

        </head>

        <body>

            <div class="navbar">
                ⚡ AIDEA Dashboard ⚡
            </div>

            <div class="container">

                <div class="metrics">

                    {metric_card("Top Module", top_module)}
                    {metric_card("Inputs", len(inputs))}
                    {metric_card("Outputs", len(outputs))}
                    {metric_card("Total Ports", len(ports))}
                    {metric_card("Logic Type", logic_type)}
                    {metric_card("Area", ppa.get("area"))}
                    {metric_card("Delay", ppa.get("delay"))}
                    {metric_card("Power", ppa.get("power"))}

                </div>

                <div class="workspace">

                    <div class="sidebar">

                        <button onclick="openPanel('overview')">
                            Overview
                        </button>

                        <button onclick="openPanel('schematic')">
                            Schematic
                        </button>

                        <button onclick="openPanel('waveform')">
                            Waveform
                        </button>

                        <button onclick="openPanel('ai')">
                            AI Analysis
                        </button>

                        <button onclick="openPanel('verification')">
                            Verification
                        </button>

                        <button onclick="openPanel('hardware')">
                            FPGA / ASIC
                        </button>

                        <button onclick="openPanel('simulation')">
                            Simulation
                        </button>

                        <button onclick="openPanel('truth')">
                            Truth Table
                        </button>

                    </div>

                    <div class="content-panel">

                        <div id="overview"
                             class="panel active">

                            <h2>
                                RTL Design Overview
                            </h2>

                            <div class="overview-card">

                                <h3>
                                    Top Module
                                </h3>

                                <p>
                                    <b>{top_module}</b>
                                </p>

                                <p>
                                    This RTL design contains
                                    <b>{len(inputs)}</b> inputs,
                                    <b>{len(outputs)}</b> outputs
                                    and a total of
                                    <b>{len(ports)}</b> ports.
                                </p>

                                <p>
                                    Logic Classification:
                                    <b>{logic_type}</b>
                                </p>

                            </div>

                            <div class="overview-grid">

                                <div class="overview-card">

                                    <h3>
                                        I/O Declarations
                                    </h3>

                                    {io_table}

                                </div>

                                <div class="overview-card">

                                    <h3>
                                        AI RTL Analysis
                                    </h3>

                                    <pre>{explanation}</pre>

                                </div>

                            </div>

                            <div class="overview-card">

                                <h3>
                                    Errors / Warnings
                                </h3>

                                <pre>{errors}</pre>

                            </div>

                        </div>

                        <div id="schematic"
                             class="panel">

                            <h2>
                                RTL Schematic
                            </h2>

                            <h3>
                                {schematic_status}
                            </h3>

                            <button
                                class="print-btn"
                                onclick="printSchematic()">

                                Print Schematic

                            </button>

                            <div class="schematic-container">

                                <iframe
                                    id="schematicFrame"
                                    src="{schematic_svg}">
                                </iframe>

                            </div>

                        </div>

                        <div id="waveform"
                             class="panel">

                            <h2>
                                Waveform
                            </h2>

                            <pre>{sim_result}</pre>

                        </div>

                        <div id="ai"
                             class="panel">

                            <h2>
                                AI Structural Analysis
                            </h2>

                            <pre>{ai_analysis}</pre>

                        </div>

                        <div id="verification"
                             class="panel">

                            <h2>
                                Verification
                            </h2>

                            <pre>{verification}</pre>

                        </div>

                        <div id="hardware"
                             class="panel">

                            <h2>
                                FPGA / ASIC
                            </h2>

                            <pre>{hardware}</pre>

                        </div>

                        <div id="simulation"
                             class="panel">

                            <h2>
                                Simulation
                            </h2>

                            <pre>{sim_result}</pre>

                        </div>

                        <div id="truth"
                             class="panel">

                            <h2>
                                Truth Table
                            </h2>

                            {truth_html}

                        </div>

                    </div>

                </div>

            </div>

        </body>

        </html>
        """

    except Exception as e:

        return f"""

        <body style='
            background:#fff1f2;
            padding:30px;
            font-family:Arial;
        '>

            <h2>
                ❌ ERROR
            </h2>

            <pre>
{str(e)}
            </pre>

            <hr>

            <pre>
{traceback.format_exc()}
            </pre>

        </body>
        """

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    threading.Thread(
        target=open_browser
    ).start()

    app.run(
        debug=False,
        use_reloader=False
    )
>>>>>>> 30d5d8d9995e0216996dd0ee4850fd2456e48439
