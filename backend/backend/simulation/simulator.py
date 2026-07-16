import subprocess
import os
import shutil

# =========================================================
# PROJECT PATHS
# =========================================================
PROJECT_ROOT = "D:/AI_EDA_TOOL"

RUNS_PATH = os.path.join(
    PROJECT_ROOT,
    "runs"
)

# =========================================================
# TOOL EXECUTABLES
# =========================================================
IVERILOG_EXE = "iverilog"
VVP_EXE = "vvp"
GTKWAVE_EXE = "gtkwave"

# =========================================================
# RUN SIMULATION
# =========================================================
def run_simulation():

    # =====================================================
    # FILE PATHS
    # =====================================================
    design_file = os.path.join(
        RUNS_PATH,
        "design.v"
    )

    tb_file = os.path.join(
        RUNS_PATH,
        "tb.v"
    )

    output_vvp = os.path.join(
        RUNS_PATH,
        "sim.out"
    )

    # FINAL FIX
    # dump.vcd generated directly in RUNS_PATH
    vcd_file = os.path.join(
        RUNS_PATH,
        "dump.vcd"
    )

    # =====================================================
    # CLEAN OLD FILES
    # =====================================================
    for f in [output_vvp, vcd_file]:

        if os.path.exists(f):

            try:
                os.remove(f)
            except:
                pass

    # =====================================================
    # VERIFY INPUT FILES
    # =====================================================
    if not os.path.exists(design_file):

        return f"""
❌ design.v NOT FOUND

Expected:
{design_file}
"""

    if not os.path.exists(tb_file):

        return f"""
❌ tb.v NOT FOUND

Expected:
{tb_file}
"""

    # =====================================================
    # COMPILE USING IVERILOG
    # =====================================================
    compile_cmd = [

        IVERILOG_EXE,

        "-g2012",

        "-o",
        output_vvp,

        design_file,
        tb_file
    ]

    compile_proc = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True,
        cwd=RUNS_PATH
    )

    # =====================================================
    # COMPILATION FAILED
    # =====================================================
    if compile_proc.returncode != 0:

        return f"""
❌ IVERILOG COMPILATION FAILED

COMMAND:
{' '.join(compile_cmd)}

STDOUT:
{compile_proc.stdout}

STDERR:
{compile_proc.stderr}
"""

    # =====================================================
    # RUN VVP SIMULATION
    # =====================================================
    run_cmd = [
        VVP_EXE,
        output_vvp
    ]

    run_proc = subprocess.run(
        run_cmd,
        capture_output=True,
        text=True,
        cwd=RUNS_PATH
    )

    # =====================================================
    # SIMULATION FAILED
    # =====================================================
    if run_proc.returncode != 0:

        return f"""
❌ VVP SIMULATION FAILED

COMMAND:
{' '.join(run_cmd)}

STDOUT:
{run_proc.stdout}

STDERR:
{run_proc.stderr}
"""

    # =====================================================
    # FALLBACK VCD SEARCH
    # =====================================================
    if not os.path.exists(vcd_file):

        # Search current directory
        local_vcd = os.path.join(
            os.getcwd(),
            "dump.vcd"
        )

        if os.path.exists(local_vcd):

            try:

                shutil.move(
                    local_vcd,
                    vcd_file
                )

            except:
                pass

    # =====================================================
    # FINAL VCD CHECK
    # =====================================================
    if not os.path.exists(vcd_file):

        return f"""
❌ dump.vcd NOT GENERATED

Simulation Output:
{run_proc.stdout}

Simulation Errors:
{run_proc.stderr}

Possible causes:
- Missing $dumpfile
- Missing $dumpvars
- Simulation terminated early
"""

    # =====================================================
    # OPEN GTKWAVE
    # =====================================================
    gtkwave_msg = ""

    try:

        subprocess.Popen(
            [
                GTKWAVE_EXE,
                vcd_file
            ],
            cwd=RUNS_PATH
        )

        gtkwave_msg = "✅ GTKWave Opened Successfully"

    except Exception as e:

        gtkwave_msg = f"""
⚠ GTKWave Launch Failed

{str(e)}
"""

    # =====================================================
    # SUCCESS
    # =====================================================
    return f"""
✅ SIMULATION SUCCESSFUL

Generated Files:
{output_vvp}
{vcd_file}

{gtkwave_msg}

Simulation Output:
{run_proc.stdout}

Simulation Errors:
{run_proc.stderr}
"""