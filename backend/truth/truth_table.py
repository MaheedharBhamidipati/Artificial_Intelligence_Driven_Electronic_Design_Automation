import os
import re
import math
import tempfile
import subprocess
import itertools
import pandas as pd
from backend.rtl_parser_engine.rtl_parser import RTLParser

# ============================================================
# PORT EXTRACTION
# ============================================================



def extract_ports_from_ast(verilog_code):

    with tempfile.NamedTemporaryFile(
        suffix=".v",
        delete=False,
        mode="w",
        encoding="utf-8"
    ) as f:

        f.write(verilog_code)

        temp_file = f.name

    try:

        parser = RTLParser(temp_file)

        parser.parse_file()

        modules = parser.extract_modules()

        if not modules:
            return [], []

        module = modules[0]

        inputs = module["inputs"]
        outputs = module["outputs"]

        print("\n========== PORTS ==========")
        print("INPUTS =", inputs)
        print("OUTPUTS =", outputs)
        print("===========================\n")

        return (
            inputs,
            outputs
        )

    finally:

        if os.path.exists(temp_file):
            os.remove(temp_file)
            
            
    

# ============================================================
# MODULE NAME
# ============================================================

def get_module_name(code):

    m = re.search(
        r'\bmodule\s+(\w+)',
        code,
        re.IGNORECASE
    )

    if not m:
        raise ValueError(
            "Could not find module name in Verilog code."
        )

    return m.group(1)


# ============================================================
# SEQUENTIAL DETECTION
# ============================================================

def is_sequential(code):

    return bool(
        re.search(
            r'\b(posedge|negedge)\b',
            code,
            re.IGNORECASE
        )
    )


# ============================================================
# TESTBENCH GENERATOR
# ============================================================

def generate_testbench(
    module_name,
    inputs,
    outputs
):

    reg_decl = []
    wire_decl = []

    for p in inputs:

        if p["width"] == 1:
            reg_decl.append(
                f"reg {p['name']};"
            )
        else:
            reg_decl.append(
                f"reg [{p['width']-1}:0] {p['name']};"
            )

    for p in outputs:

        if p["width"] == 1:
            wire_decl.append(
                f"wire {p['name']};"
            )
        else:
            wire_decl.append(
                f"wire [{p['width']-1}:0] {p['name']};"
            )

    connections = []

    for p in inputs + outputs:
        connections.append(
            f".{p['name']}({p['name']})"
        )

    print("\n========== TB DEBUG ==========")
    print("INPUTS =", inputs)
    print("OUTPUTS =", outputs)

    total_bits = sum(
        int(p.get("width", 1))
        for p in inputs
    )

    print("TOTAL_BITS =", total_bits)

    max_vectors = min(
        2 ** total_bits,
        65536
    )

    print("MAX_VECTORS =", max_vectors)
    print("==============================\n")


    total_bits = sum(
        p["width"]
        for p in inputs
    )

    display_list = []

    for p in inputs:
        display_list.append(p["name"])

    for p in outputs:
        display_list.append(p["name"])

    display_fmt = " ".join(
        ["%b"] * len(display_list)
    )

    max_vectors = min(
        2 ** total_bits,
        65536
    )

    tb = f"""
module tb;

{' '.join(reg_decl)}
{' '.join(wire_decl)}

{module_name} dut(
{','.join(connections)}
);

integer i;

initial begin

    for(i=0;i<{max_vectors};i=i+1)
    begin

        {{ {','.join([p['name'] for p in inputs])} }} = i;

        #1;

        $display("{display_fmt}",
            {",".join(display_list)}
        );

    end

    $finish;

end

endmodule
"""

    return tb




# ============================================================
# SIMULATION
# ============================================================

def run_simulation(
    rtl_code,
    tb_code
):

    with tempfile.TemporaryDirectory() as tmp:

        rtl_file = os.path.join(
            tmp,
            "dut.v"
        )

        tb_file = os.path.join(
            tmp,
            "tb.v"
        )

        exe_file = os.path.join(
            tmp,
            "sim.out"
        )

        with open(rtl_file, "w") as f:
            f.write(rtl_code)

        with open(tb_file, "w") as f:
            f.write(tb_code)

        compile_cmd = [
            "iverilog.exe",
            "-o",
            exe_file,
            rtl_file,
            tb_file
        ]
        
        print(compile_cmd)

        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )
        
        print("COMPILE RC =", compile_result.returncode)
        print(compile_result.stderr)

        if compile_result.returncode != 0:

            raise RuntimeError(
                compile_result.stderr
            )

        print("SIM FILE =", exe_file)
        print("SIM EXISTS =", os.path.exists(exe_file))
        
        sim_result = subprocess.run(
            [
                r"D:\AI_EDA_TOOL\oss-cad-suite\bin\vvp.exe",
                exe_file
            ],
            capture_output=True,
            text=True
        )

        print("\n========== SIM OUTPUT ==========")
        print(sim_result.stdout)
        print("================================\n")

        print("\n========== SIM STDERR ==========")
        print(sim_result.stderr)
        print("================================\n")

        return sim_result.stdout
            


# ============================================================
# PARSE OUTPUT
# ============================================================

def parse_simulation_output(
    sim_text,
    inputs,
    outputs
):

    columns = []

    for p in inputs:
        columns.append(p["name"])

    for p in outputs:
        columns.append(p["name"])

    rows = []

    for line in sim_text.splitlines():

        line = line.strip()

        if not line:
            continue

        values = line.split()

        if len(values) != len(columns):
            continue

        rows.append(values)

    return pd.DataFrame(
        rows,
        columns=columns
    )


# ============================================================
# MAIN API
# ============================================================

def generate_truth_table(
    verilog_code
):

    if is_sequential(verilog_code):

        return {
            "logic_type": "sequential",
            "truth_table": None,
            "message":
                "Truth table not supported for sequential logic"
        }

    module_name = get_module_name(
        verilog_code
    )

    inputs, outputs = extract_ports_from_ast(
        verilog_code
    )

    tb = generate_testbench(
        module_name,
        inputs,
        outputs
    )

    sim_output = run_simulation(
        verilog_code,
        tb
    )
    
    print("SIM OUTPUT LENGTH:", len(sim_output))
    print("SIM OUTPUT:")
    print(sim_output)

    df = parse_simulation_output(
        sim_output,
        inputs,
        outputs
    )

    return {
        "logic_type": "combinational",
        "truth_table": df,
        "rows": len(df)
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    code = '''
    def extract_ports(code):

    module_match = re.search(
        r'module\s+\w+\s*\((.*?)\)\s*;',
        code,
        re.DOTALL
    )

    if not module_match:
        return [], []

    port_text = module_match.group(1)

    inputs = []
    outputs = []

    for line in port_text.split(","):

        line = line.strip()

        if line.startswith("input"):

            name = line.split()[-1]

            inputs.append({
                "name": name,
                "width": 1
            })

        elif line.startswith("output"):

            name = line.split()[-1]

            outputs.append({
                "name": name,
                "width": 1
            })

    return inputs, outputs
    '''

    result = generate_truth_table(code)

    print(result["truth_table"])