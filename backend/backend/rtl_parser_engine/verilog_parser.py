import re
import json

# ============================================================
# VERILOG KEYWORDS / PRIMITIVES
# ============================================================
VERILOG_KEYWORDS = {
    "module", "endmodule", "input", "output", "inout",
    "wire", "reg", "integer", "real", "parameter", "localparam",
    "assign", "always", "initial", "begin", "end",
    "if", "else", "for", "while", "case", "casex", "casez",
    "default", "posedge", "negedge", "or", "and", "not",
    "generate", "genvar", "function", "endfunction",
    "task", "endtask", "specify", "endspecify",
    "nand", "nor", "xor", "xnor", "buf", "notif1"
}

# ============================================================
# CLEAN VERILOG CODE
# ============================================================
def clean_code(code: str) -> str:
    code = re.sub(r'//.*?(?=\n|$)', '', code, flags=re.MULTILINE)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'\n\s*\n', '\n', code)
    return code.strip()


# ============================================================
# EXTRACT ALL MODULE DEFINITIONS
# ============================================================
def extract_modules(code: str) -> list:
    cleaned = clean_code(code)
    return re.findall(r'\bmodule\s+([A-Za-z_]\w*)', cleaned)


# ============================================================
# EXTRACT INSTANTIATED MODULES
# ============================================================
def extract_instantiations(code: str) -> list:
    cleaned = clean_code(code)

    raw_matches = re.findall(
        r'\b([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\(',
        cleaned
    )

    instantiated = []

    for module_name, _ in raw_matches:
        if module_name.lower() not in VERILOG_KEYWORDS:
            instantiated.append(module_name)

    return list(dict.fromkeys(instantiated))


# ============================================================
# FIND TOP MODULE
# ============================================================
def find_top_module(code: str) -> str:
    modules = extract_modules(code)

    if not modules:
        return None

    instantiated = set(extract_instantiations(code))
    top_candidates = [m for m in modules if m not in instantiated]

    if len(top_candidates) == 1:
        return top_candidates[0]
    elif len(top_candidates) > 1:
        return top_candidates[-1]

    return modules[-1]


# ============================================================
# EXTRACT COMPLETE MODULE BLOCK
# ============================================================
def extract_module_block(code: str, module_name: str) -> str:
    if not module_name:
        return ""

    pattern = rf'\bmodule\s+{re.escape(module_name)}\b.*?endmodule'

    match = re.search(
        pattern,
        code,
        re.DOTALL | re.IGNORECASE
    )

    return match.group(0) if match else ""


# ============================================================
# EXTRACT PORTS
# ============================================================
def extract_ports(code: str, module_name: str) -> list:
    if not module_name:
        return []

    cleaned = clean_code(code)
    module_block = extract_module_block(cleaned, module_name)

    if not module_block:
        return []

    ports = []
    seen = set()

    ansi_pattern = (
        r'\b(input|output|inout)\s+'
        r'(?:wire|reg|logic)?\s*'
        r'(?:signed)?\s*'
        r'(?:\[.*?\])?\s*'
        r'([A-Za-z_]\w*)'
    )

    ansi_matches = re.findall(
        ansi_pattern,
        module_block,
        re.DOTALL | re.IGNORECASE
    )

    for direction, port_name in ansi_matches:
        key = (direction.lower(), port_name)

        if key not in seen:
            seen.add(key)
            ports.append((direction.lower(), port_name))

    non_ansi_pattern = (
        r'\b(input|output|inout)\s+'
        r'(?:wire|reg|logic)?\s*'
        r'(?:signed)?\s*'
        r'(?:\[.*?\])?\s*'
        r'([^;,{]+?)(?=[;,]|$)'
    )

    non_ansi_matches = re.findall(
        non_ansi_pattern,
        module_block,
        re.DOTALL | re.MULTILINE | re.IGNORECASE
    )

    for direction, port_list in non_ansi_matches:

        individual_ports = [
            p.strip()
            for p in re.split(r'\s*,\s*', port_list)
            if p.strip()
        ]

        for port_str in individual_ports:
            name_match = re.search(
                r'([A-Za-z_]\w*)(?:\s*\[.*?\])?$',
                port_str
            )

            if name_match:
                port_name = name_match.group(1)

                key = (direction.lower(), port_name)

                if key not in seen:
                    seen.add(key)
                    ports.append((direction.lower(), port_name))

    return ports


# ============================================================
# EXTRACT ASSIGN STATEMENTS
# ============================================================
def extract_assigns(code: str) -> list:
    cleaned = clean_code(code)

    return re.findall(
        r'\bassign\s+([A-Za-z_]\w*)\s*=\s*(.*?);',
        cleaned,
        re.DOTALL
    )


# ============================================================
# EXTRACT MODULE INSTANCES
# ============================================================
def extract_module_instances(code: str, parent_module: str) -> list:
    module_block = extract_module_block(code, parent_module)

    if not module_block:
        return []

    instance_pattern = r'''
        \b([A-Za-z_]\w*)
        \s+
        ([A-Za-z_]\w*)
        \s*
        \(
        (.*?)
        \)
        \s*;
    '''

    matches = re.findall(
        instance_pattern,
        module_block,
        re.DOTALL | re.VERBOSE
    )

    instances = []

    for module_type, instance_name, port_block in matches:

        if module_type.lower() in VERILOG_KEYWORDS:
            continue

        if module_type == parent_module:
            continue

        port_connections = {}

        named_ports = re.findall(
            r'\.(\w+)\s*\(\s*([^)]+)\s*\)',
            port_block
        )

        for port_name, signal_name in named_ports:
            port_connections[port_name] = signal_name.strip()

        instances.append({
            "module_type": module_type,
            "instance_name": instance_name,
            "connections": port_connections
        })

    return instances


# ============================================================
# HIERARCHY ELABORATION
# ============================================================
def elaborate_hierarchy(code: str, top_module: str) -> dict:
    elaborated = {
        "top_module": top_module,
        "instances": []
    }

    visited_paths = set()

    def recurse(module_name, prefix=""):

        key = (module_name, prefix)

        if key in visited_paths:
            return

        visited_paths.add(key)

        instances = extract_module_instances(code, module_name)

        for inst in instances:

            full_path = (
                f"{prefix}/{inst['instance_name']}"
                if prefix else inst["instance_name"]
            )

            elaborated["instances"].append({
                "path": full_path,
                "type": inst["module_type"],
                "connections": inst["connections"]
            })

            recurse(inst["module_type"], full_path)

    recurse(top_module)

    return elaborated


# ============================================================
# BUILD NETLIST
# ============================================================
def build_netlist(elaborated: dict, code: str = "") -> dict:
    """
    Build robust netlist using actual module port directions.
    """
    netlist = {
        "instances": [],
        "nets": {}
    }

    module_port_cache = {}

    for inst in elaborated["instances"]:

        module_type = inst["type"]

        if module_type not in module_port_cache:
            module_port_cache[module_type] = dict(
                extract_ports(code, module_type)
            )

        port_dirs = module_port_cache[module_type]

        netlist["instances"].append({
            "name": inst["path"],
            "type": module_type
        })

        for port, signal in inst["connections"].items():

            signal = signal.strip()

            if signal not in netlist["nets"]:
                netlist["nets"][signal] = {
                    "drivers": [],
                    "loads": []
                }

            direction = port_dirs.get(port, "input")

            if direction == "output":
                netlist["nets"][signal]["drivers"].append(
                    f"{inst['path']}.{port}"
                )
            else:
                netlist["nets"][signal]["loads"].append(
                    f"{inst['path']}.{port}"
                )

    return netlist
# ============================================================
# MASTER ANALYZER
# ============================================================
def analyze_verilog(code: str) -> dict:
    code = clean_code(code)

    top_module = find_top_module(code)

    elaborated = elaborate_hierarchy(code, top_module)

    netlist = build_netlist(elaborated)

    return {
        "modules": extract_modules(code),
        "top_module": top_module,
        "ports": extract_ports(code, top_module),
        "assigns": extract_assigns(code),
        "elaborated": elaborated,
        "netlist": netlist
    }


# ============================================================
# TEST DRIVER
# ============================================================
if __name__ == "__main__":

    sample_code = """
    module full_adder(
        input a,
        input b,
        input cin,
        output sum,
        output cout
    );
        assign sum = a ^ b ^ cin;
        assign cout = (a&b)|(b&cin)|(a&cin);
    endmodule

    module top(
        input a,
        input b,
        input cin,
        output sum,
        output cout
    );

        full_adder FA1(
            .a(a),
            .b(b),
            .cin(cin),
            .sum(sum),
            .cout(cout)
        );

    endmodule
    """

    result = analyze_verilog(sample_code)

    print(json.dumps(result, indent=4))
