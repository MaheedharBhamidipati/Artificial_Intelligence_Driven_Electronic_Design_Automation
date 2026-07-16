
import subprocess
import os
import re

# =========================================================
# PATHS
# =========================================================
PROJECT_ROOT = "D:/AI_EDA_TOOL"

RUNS_PATH = os.path.join(
    PROJECT_ROOT,
    "runs"
)

YOSYS_EXE = r"D:/AI_Intergating_VERILOG_Project/oss-cad-suite/bin/yosys.exe"


# =========================================================
# RUN YOSYS
# =========================================================
def run_yosys(
    design_path,
    top_module
):

    yosys_script = os.path.join(
        RUNS_PATH,
        "yosys_script.ys"
    )

    yosys_log = os.path.join(
        RUNS_PATH,
        "yosys_log.txt"
    )

    netlist_out = os.path.join(
        RUNS_PATH,
        "synth_netlist.v"
    )

    # =====================================================
    # CREATE SCRIPT
    # =====================================================
    script = f"""

read_verilog {design_path}

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

stat

write_verilog {netlist_out}

"""

    with open(
        yosys_script,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(script)

    # =====================================================
    # RUN COMMAND
    # =====================================================
    cmd = [
        YOSYS_EXE,
        yosys_script
    ]

    try:

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        full_log = (
            result.stdout
            + "\n"
            + result.stderr
        )

        with open(
            yosys_log,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(full_log)

        # ERROR
        if result.returncode != 0:

            return None, full_log

        return full_log, None

    except Exception as e:

        return None, str(e)


# =========================================================
# EXTRACT PPA
# =========================================================
def extract_ppa(yosys_output):

    ppa = {

        "area": "N/A",

        "delay": "N/A",

        "power": "N/A",

        "cells": 0,

        "wires": 0
    }

    if not yosys_output:

        return ppa

    # =====================================================
    # CELL COUNT
    # =====================================================
    cell_match = re.search(
        r"Number of cells:\s+(\d+)",
        yosys_output
    )

    if cell_match:

        cells = int(
            cell_match.group(1)
        )

        ppa["cells"] = cells

        # =================================================
        # SIMPLE ESTIMATION MODELS
        # =================================================
        ppa["area"] = round(
            cells * 10.5,
            2
        )

        ppa["delay"] = round(
            max(1.0, cells * 0.12),
            2
        )

        ppa["power"] = round(
            cells * 0.05,
            3
        )

    # =====================================================
    # WIRE COUNT
    # =====================================================
    wire_match = re.search(
        r"Number of wires:\s+(\d+)",
        yosys_output
    )

    if wire_match:

        ppa["wires"] = int(
            wire_match.group(1)
        )

    return ppa