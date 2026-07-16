# =========================================================
# AI-EDA RTL SCHEMATIC GENERATOR
# FINAL STABLE VERSION
# =========================================================

import os
import re
import shutil
import subprocess
import textwrap


# =========================================================
# BASE DIRECTORIES
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..")
)

TOOLS_DIR = PROJECT_ROOT

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

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SCHEMATIC_DIR, exist_ok=True)


# =========================================================
# TOOL DIRECTORIES
# =========================================================

OSS_CAD_DIR = os.path.join(
    TOOLS_DIR,
    "oss-cad-suite"
)

GRAPHVIZ_DIR = os.path.join(
    TOOLS_DIR,
    "Graphviz"
)

IVERILOG_DIR = os.path.join(
    TOOLS_DIR,
    "iverilog"
)

YOSYS_EXE = os.path.join(
    OSS_CAD_DIR,
    "bin",
    "yosys.exe"
)

DOT_EXE = os.path.join(
    GRAPHVIZ_DIR,
    "bin",
    "dot.exe"
)

IVERILOG_EXE = os.path.join(
    IVERILOG_DIR,
    "bin",
    "iverilog.exe"
)


# =========================================================
# VERIFY TOOLS
# =========================================================

def verify_tools():

    required_tools = {

        "Yosys": YOSYS_EXE,
        "Graphviz": DOT_EXE,
        "Iverilog": IVERILOG_EXE
    }

    for tool_name, tool_path in required_tools.items():

        if not os.path.exists(tool_path):

            return (
                False,
                f"{tool_name} not found:\n{tool_path}"
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

    matches = re.findall(
        r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        verilog_code
    )

    if matches:
        return matches[0]

    return "top_module"


# =========================================================
# CLEAN OLD FILES
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

        file_paths = [

            os.path.join(
                UPLOAD_DIR,
                f"{top_module}{ext}"
            ),

            os.path.join(
                SCHEMATIC_DIR,
                f"{top_module}{ext}"
            )
        ]

        for path in file_paths:

            if os.path.exists(path):

                try:
                    os.remove(path)

                except Exception:
                    pass


# =========================================================
# SVG OPTIMIZATION
# =========================================================

def optimize_svg(svg_file):

    if not os.path.exists(svg_file):
        return

    with open(svg_file, "r", encoding="utf-8") as f:

        svg = f.read()

    # =====================================================
    # REMOVE FIXED DIMENSIONS
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
    # RESPONSIVE SVG
    # =====================================================

    svg = svg.replace(
        "<svg",
        "<svg preserveAspectRatio='xMidYMid meet'"
    )

    # =====================================================
    # STYLE
    # =====================================================

    style = """

    <style>

    svg {

        width: 100%;
        height: auto;
        background: white;
    }

    text {

        font-family:
            Arial,
            Helvetica,
            sans-serif;

        font-size: 15px;
        font-weight: bold;

        fill: #111827;
    }

    polygon,
    path,
    rect,
    circle,
    ellipse,
    line {

        stroke-width: 2.2;
    }

    </style>

    """

    svg = svg.replace(
        ">",
        f">{style}",
        1
    )

    with open(svg_file, "w", encoding="utf-8") as f:

        f.write(svg)


# =========================================================
# CREATE YOSYS SCRIPT
# =========================================================

def create_yosys_script(
    verilog_file,
    top_module,
    output_prefix
):

    script = f"""

    # ==============================================
    # READ RTL
    # ==============================================

    read_verilog "{verilog_file}"

    hierarchy -check -top {top_module}

    # ==============================================
    # RTL PROCESSING
    # ==============================================

    proc
    opt

    # ==============================================
    # FSM EXTRACTION
    # ==============================================

    fsm
    opt

    # ==============================================
    # MEMORY HANDLING
    # ==============================================

    memory
    opt

    # ==============================================
    # TECH MAPPING
    # ==============================================

    techmap
    opt

    clean

    # ==============================================
    # GENERATE RTL SCHEMATIC
    # ==============================================

    show \\
        -format dot \\
        -prefix "{output_prefix}"

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

def run_graphviz(dot_file, svg_file, png_file):

    svg_result = subprocess.run(

        [
            DOT_EXE,
            "-Tsvg",
            dot_file,
            "-o",
            svg_file
        ],

        capture_output=True,

        text=True
    )

    subprocess.run(

        [
            DOT_EXE,
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
# FIND GENERATED DOT FILE
# =========================================================

def find_dot_file(top_module):

    possible_locations = [

        os.path.join(
            UPLOAD_DIR,
            f"{top_module}.dot"
        ),

        os.path.join(
            SCHEMATIC_DIR,
            f"{top_module}.dot"
        ),

        os.path.join(
            OSS_CAD_DIR,
            f"{top_module}.dot"
        ),

        os.path.join(
            os.getcwd(),
            f"{top_module}.dot"
        ),

        os.path.join(
            BASE_DIR,
            f"{top_module}.dot"
        )
    ]

    for path in possible_locations:

        if os.path.exists(path):

            return path

    return None


# =========================================================
# GENERATE SCHEMATIC
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
        # CLEAN OLD FILES
        # =================================================

        clean_previous_files(top_module)

        # =================================================
        # FILE PATHS
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
        # SAVE VERILOG
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
            top_module,
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
        # FIND DOT FILE
        # =================================================

        generated_dot = find_dot_file(
            top_module
        )

        if generated_dot is None:

            return {

                "success": False,

                "error":
                    "DOT file not generated."
            }

        # =================================================
        # COPY DOT FILE
        # =================================================

        shutil.copy(
            generated_dot,
            dot_file
        )

        # =================================================
        # RUN GRAPHVIZ
        # =================================================

        svg_result = run_graphviz(

            dot_file,
            svg_file,
            png_file
        )

        if svg_result.returncode != 0:

            return {

                "success": False,

                "error":
                    svg_result.stderr
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


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    rtl = '''

    module and_gate(
        input a,
        input b,
        output y
    );

    assign y = a & b;

    endmodule

    '''

    result = generate_schematic(rtl)

    print(result)