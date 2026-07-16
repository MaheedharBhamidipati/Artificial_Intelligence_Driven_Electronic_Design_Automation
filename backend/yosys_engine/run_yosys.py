import os
import subprocess

# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = r"D:/AI_EDA_TOOL"

# =========================================================
# OUTPUT DIRECTORIES
# =========================================================

GENERATED_NETLIST_DIR = os.path.join(
    PROJECT_ROOT,
    "static",
    "generated",
    "netlists"
)

TEMP_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "yosys_engine",
    "temp"
)

# =========================================================
# CREATE REQUIRED FOLDERS
# =========================================================

os.makedirs(
    GENERATED_NETLIST_DIR,
    exist_ok=True
)

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)

# =========================================================
# OPTIONAL:
# FULL YOSYS PATH
# =========================================================
# If "yosys" command fails,
# uncomment and use your yosys.exe path
# Example:
#
# YOSYS_BINARY = r"D:/oss-cad-suite/bin/yosys.exe"
#
# Otherwise keep:
# =========================================================

YOSYS_BINARY = "yosys"

# =========================================================
# GENERATE JSON NETLIST
# =========================================================

def generate_json_netlist(
    verilog_file,
    top_module
):

    # =====================================================
    # VALIDATE INPUT VERILOG FILE
    # =====================================================

    if not os.path.exists(verilog_file):

        raise FileNotFoundError(
            f"Verilog file not found:\n{verilog_file}"
        )

    # =====================================================
    # OUTPUT FILES
    # =====================================================
    json_output = os.path.join(
        GENERATED_NETLIST_DIR,
        "design.json"
    )

    gate_netlist = os.path.join(
        GENERATED_NETLIST_DIR,
        "gate_level_netlist.v"
    )

    statistics_file = os.path.join(
        GENERATED_NETLIST_DIR,
        "statistics.json"
    )


    yosys_script_path = os.path.join(
        TEMP_DIR,
        "temp.ys"
    )

    # =====================================================
    # REMOVE OLD NETLIST
    # =====================================================

    if os.path.exists(json_output):

        os.remove(json_output)

    # =====================================================
    # YOSYS SCRIPT
    # =====================================================

    file_ext = os.path.splitext(verilog_file)[1].lower()

    if file_ext == ".sv":
        read_cmd = f'read_verilog -sv "{verilog_file}"'
    else:
        read_cmd = f'read_verilog "{verilog_file}"'

    # =====================================================
    # OUTPUT FILES
    # =====================================================

    json_output = os.path.join(
        GENERATED_NETLIST_DIR,
        "design.json"
    )

    gate_netlist = os.path.join(
        GENERATED_NETLIST_DIR,
        "gate_level_netlist.v"
    )

    statistics_file = os.path.join(
        GENERATED_NETLIST_DIR,
        "statistics.txt"
    )

    yosys_script = f"""
    {read_cmd}

    hierarchy -check -top {top_module}

    proc
    opt

    fsm
    opt

    memory
    opt

    techmap
    opt

    abc -fast

    clean

    # -----------------------------
    # Reports
    # -----------------------------

    stat

    tee -o "{statistics_file}" stat

    # -----------------------------
    # Outputs
    # -----------------------------
    
    write_json "{json_output}"

    write_json "{os.path.join(GENERATED_NETLIST_DIR,'netlist.json')}"

    write_verilog -noattr "{gate_netlist}"
    """
    

    # =====================================================
    # WRITE TEMP SCRIPT
    # =====================================================

    with open(
        yosys_script_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(yosys_script)

    # =====================================================
    # DEBUG INFO
    # =====================================================

    print("\n====================================")
    print("VERILOG FILE:")
    print(verilog_file)

    print("\nTOP MODULE:")
    print(top_module)

    print("\nJSON OUTPUT:")
    print(json_output)

    print("\nYOSYS SCRIPT:")
    print(yosys_script_path)

    print("====================================\n")

    # =====================================================
    # RUN YOSYS
    # =====================================================

    try:

        result = subprocess.run(

            [
                YOSYS_BINARY,
                yosys_script_path
            ],

            capture_output=True,

            text=True
        )

    except Exception as e:

        raise Exception(
            f"Failed to run Yosys:\n\n{str(e)}"
        )

    # =====================================================
    # PRINT LOGS
    # =====================================================

    print("\n========== YOSYS STDOUT ==========\n")

    print(result.stdout)

    print("\n========== YOSYS STDERR ==========\n")

    print(result.stderr)

    # =====================================================
    # CHECK IF JSON GENERATED
    # =====================================================

    if not os.path.exists(json_output):

        raise Exception(

            f"""
Yosys failed to generate design.json

Possible reasons:

1. Invalid Verilog syntax
2. Wrong top module name
3. Yosys not installed
4. Yosys path not set
5. ABC synthesis failure

STDERR:
{result.stderr}
"""
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    return {

        "success": True,

        "design_json": json_output,

        "gate_netlist": gate_netlist,

        "statistics": statistics_file,

        "yosys_script": yosys_script_path,

        "stdout": result.stdout,

        "stderr": result.stderr
    }