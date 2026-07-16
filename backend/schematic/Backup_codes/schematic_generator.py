# =========================================================
# AIDEA RTL SCHEMATIC GENERATOR
# GENERIC + STABLE VERSION
# Supports:
# ✔ Combinational Circuits
# ✔ Sequential Circuits
# ✔ FSMs
# ✔ Multi-module RTL
# ✔ Hierarchical Designs
# ✔ Generic Verilog Projects
# =========================================================
# =========================================================
# AIDEA RTL SCHEMATIC GENERATOR
# PROFESSIONAL GENERIC VERSION
# =========================================================

import os
import re
import subprocess
import textwrap


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..")
)

UPLOAD_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "uploads"
)

SCHEMATIC_DIR = os.path.join(
    PROJECT_ROOT,
    "static",
    "schematics"
)

OSS_CAD_DIR = os.path.join(
    PROJECT_ROOT,
    "oss-cad-suite"
)

YOSYS_EXE = os.path.join(
    OSS_CAD_DIR,
    "bin",
    "yosys.exe"
)

DOT_EXE = "dot"

# =========================================================
# CREATE DIRECTORIES
# =========================================================

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SCHEMATIC_DIR, exist_ok=True)

# =========================================================
# VERIFY TOOLS
# =========================================================

def verify_tools():

    if not os.path.exists(YOSYS_EXE):

        return (
            False,
            f"Yosys not found:\n{YOSYS_EXE}"
        )

    try:

        subprocess.run(
            [DOT_EXE, "-V"],
            capture_output=True,
            text=True
        )

    except Exception:

        return (
            False,
            "Graphviz not installed."
        )

    return (True, "")

# =========================================================
# SANITIZE MODULE NAME
# =========================================================

def sanitize_name(name):

    return re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        name
    )

# =========================================================
# EXTRACT TOP MODULE
# =========================================================

def extract_top_module(verilog_code):

    modules = re.findall(

        r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_]*)",

        verilog_code
    )

    if not modules:

        return "top"

    instantiated = re.findall(

        r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s+"
        r"[a-zA-Z_][a-zA-Z0-9_]*\s*\(",

        verilog_code
    )

    keywords = {

        "if",
        "for",
        "while",
        "case",
        "assign",
        "always",
        "module"
    }

    instantiated = {

        x for x in instantiated

        if x not in keywords
    }

    possible_tops = [

        m for m in modules

        if m not in instantiated
    ]

    if possible_tops:

        return possible_tops[-1]

    return modules[-1]

# =========================================================
# CLEAN FILES
# =========================================================

def clean_previous_files(top_module):

    extensions = [

        ".v",
        ".ys",
        ".dot",
        ".svg",
        ".png"
    ]

    for ext in extensions:

        paths = [

            os.path.join(
                UPLOAD_DIR,
                f"{top_module}{ext}"
            ),

            os.path.join(
                SCHEMATIC_DIR,
                f"{top_module}{ext}"
            )
        ]

        for path in paths:

            if os.path.exists(path):

                try:

                    os.remove(path)

                except:
                    pass

# =========================================================
# SVG OPTIMIZATION
# =========================================================
def optimize_svg(svg_file):

    if not os.path.exists(svg_file):
        return

    with open(
        svg_file,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        svg = f.read()

    # =====================================================
    # REMOVE FIXED WIDTH/HEIGHT
    # =====================================================

    svg = re.sub(
        r'width="[^"]+"',
        '',
        svg
    )

    svg = re.sub(
        r'height="[^"]+"',
        '',
        svg
    )

    # =====================================================
    # FIX INVALID EMPTY SVG ATTRIBUTES
    # =====================================================

    # stroke=""
    svg = re.sub(
        r'stroke=""',
        'stroke="#475569"',
        svg
    )

    # stroke=
    svg = re.sub(
        r'stroke=([ >])',
        r'stroke="#475569"\\1',
        svg
    )

    # fill=""
    svg = re.sub(
        r'fill=""',
        'fill="none"',
        svg
    )

    # fill=
    svg = re.sub(
        r'fill=([ >])',
        r'fill="none"\\1',
        svg
    )

    # stroke-width=""
    svg = re.sub(
        r'stroke-width=""',
        'stroke-width="2"',
        svg
    )

    # font-size=""
    svg = re.sub(
        r'font-size=""',
        'font-size="16"',
        svg
    )

    # font-family=""
    svg = re.sub(
        r'font-family=""',
        'font-family="Arial"',
        svg
    )
    
    # =====================================================
    # REMOVE BROKEN XML CHARACTERS
    # =====================================================

    svg = svg.replace("￾", "")

    # =====================================================
    # PROFESSIONAL STYLE
    # =====================================================

    style = """

<style>

svg{

    background:white;
}

text{

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    font-size:18px;
    font-weight:bold;

    fill:#111827;
}

polygon,
path,
rect,
circle,
ellipse,
line{

    stroke-width:2;
}

.node rect{

    fill:#f8fafc;

    stroke:#334155;
}

.edge path{

    stroke:#475569;
}

</style>

"""

    if "</svg>" in svg:

        svg = svg.replace(
            "</svg>",
            f"{style}</svg>"
        )

    with open(
        svg_file,
        "w",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        f.write(svg)

# =========================================================
# CREATE YOSYS SCRIPT
# =========================================================

def create_yosys_script(
    verilog_file,
    top_module
):

    output_prefix = os.path.join(
        SCHEMATIC_DIR,
        top_module
    ).replace("\\", "/")

    script = f"""

# =====================================================
# READ VERILOG
# =====================================================

read_verilog "{verilog_file}"

# =====================================================
# HIERARCHY
# =====================================================

hierarchy -auto-top
hierarchy -check -top {top_module}

# =====================================================
# GENERIC RTL PROCESSING
# =====================================================

proc
opt

memory
opt

fsm
opt

clean

# =====================================================
# GENERATE DOT SCHEMATIC
# =====================================================

show \\
-stretch \\
-width \\
-format dot \\
-prefix {output_prefix} \\
-colors 8 \\
-notitle

"""

    return textwrap.dedent(script)

# =========================================================
# RUN YOSYS
# =========================================================

def run_yosys(yosys_script_file):

    command = [

        YOSYS_EXE,

        "-s",

        yosys_script_file
    ]

    result = subprocess.run(

        command,

        capture_output=True,

        text=True
    )

    print("\n========== YOSYS STDOUT ==========\n")
    print(result.stdout)

    print("\n========== YOSYS STDERR ==========\n")
    print(result.stderr)

    return result

# =========================================================
# RUN GRAPHVIZ
# =========================================================

def run_graphviz(
    dot_file,
    svg_file,
    png_file
):

    graphviz_args = [

        DOT_EXE,

        "-Gsplines=polyline",
        "-Grankdir=LR",

        "-Gnodesep=0.7",
        "-Granksep=1.5",

        "-Gconcentrate=true",
        "-Goverlap=false",

        "-Gpack=true",
        "-Gpackmode=cluster",

        "-Tsvg",
        dot_file,

        "-o",
        svg_file
    ]


    svg_result = subprocess.run(

        graphviz_args,

        capture_output=True,
        text=True
    )

    subprocess.run(

        [

            DOT_EXE,

            "-Gsplines=polyline",
            "-Grankdir=LR",

            "-Tpng",
            dot_file,

            "-o",
            png_file
        ],

        capture_output=True,
        text=True
    )

    return svg_result

# =========================================================
# MAIN SCHEMATIC GENERATOR
# =========================================================

def generate_schematic(verilog_code):

    try:

        # =================================================
        # VERIFY TOOLS
        # =================================================

        tools_ok, tool_error = verify_tools()

        if not tools_ok:

            return {

                "success": False,

                "error": tool_error
            }

        # =================================================
        # TOP MODULE
        # =================================================

        top_module = extract_top_module(
            verilog_code
        )

        top_module = sanitize_name(
            top_module
        )

        # =================================================
        # CLEAN
        # =================================================

        clean_previous_files(top_module)

        # =================================================
        # FILES
        # =================================================

        verilog_file = os.path.join(
            UPLOAD_DIR,
            f"{top_module}.v"
        )

        yosys_script_file = os.path.join(
            UPLOAD_DIR,
            f"{top_module}.ys"
        )

        dot_file = os.path.join(
            SCHEMATIC_DIR,
            f"{top_module}.dot"
        )

        svg_file = os.path.join(
            SCHEMATIC_DIR,
            f"{top_module}.svg"
        )

        png_file = os.path.join(
            SCHEMATIC_DIR,
            f"{top_module}.png"
        )

        # =================================================
        # SAVE RTL
        # =================================================

        with open(
            verilog_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(verilog_code)

        # =================================================
        # CREATE YOSYS SCRIPT
        # =================================================

        yosys_script = create_yosys_script(

            verilog_file,
            top_module
        )

        with open(
            yosys_script_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(yosys_script)

        # =================================================
        # RUN YOSYS
        # =================================================

        yosys_result = run_yosys(
            yosys_script_file
        )

        if yosys_result.returncode != 0:

            return {

                "success": False,

                "error":
                    yosys_result.stderr
                    + "\n\n"
                    + yosys_result.stdout
            }

        # =================================================
        # VERIFY DOT
        # =================================================

        if not os.path.exists(dot_file):

            return {

                "success": False,

                "error":
                    "DOT file not generated."
            }

        # =================================================
        # GRAPHVIZ
        # =================================================

        graphviz_result = run_graphviz(

            dot_file,
            svg_file,
            png_file
        )

        if graphviz_result.returncode != 0:

            return {

                "success": False,

                "error":
                    graphviz_result.stderr
            }

        # =================================================
        # VERIFY SVG
        # =================================================

        if not os.path.exists(svg_file):

            return {

                "success": False,

                "error":
                    "SVG generation failed."
            }

        # =================================================
        # OPTIMIZE SVG
        # =================================================

        optimize_svg(svg_file)

        # =================================================
        # SUCCESS
        # =================================================

        return {

            "success": True,

            "top_module": top_module,

            "svg_path":
                f"/static/schematics/{top_module}.svg",

            "png_path":
                f"/static/schematics/{top_module}.png",

            "dot_path":
                f"/static/schematics/{top_module}.dot",

            "message":
                "Schematic generated successfully."
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }