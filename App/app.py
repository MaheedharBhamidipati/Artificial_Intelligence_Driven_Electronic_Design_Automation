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
