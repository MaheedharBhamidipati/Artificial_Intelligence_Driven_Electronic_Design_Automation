
import re


def generate_testbench(
    top_module,
    ports,
    parameters=None,
    clock_period=10,
    exhaustive_limit=12,
    random_iterations=100
):

    """
    UNIVERSAL GENERIC TESTBENCH GENERATOR

    Supports:
    -------------------------
    ✅ Combinational Logic
    ✅ Sequential Logic
    ✅ Clock Detection
    ✅ Reset Detection
    ✅ Vector Signals
    ✅ Signed Signals
    ✅ Exhaustive Testing
    ✅ Randomized Testing
    ✅ Parameterized Modules
    ✅ Smart Monitor
    ✅ RCA / ALU / FSM / Counters / FIFO / UART etc.

    PORT FORMAT:
    -------------------------
    {
        "name": "A",
        "direction": "input",
        "width": 4,
        "signed": False
    }
    """

    tb = ""

    # =========================================================
    # HEADER
    # =========================================================

    tb += "`timescale 1ns/1ps\n\n"

    tb += "module tb;\n\n"

    # =========================================================
    # PARAMETER SUPPORT
    # =========================================================

    if parameters:

        for pname, pvalue in parameters.items():

            tb += f"parameter {pname} = {pvalue};\n"

        tb += "\n"

    # =========================================================
    # SIGNAL CLASSIFICATION
    # =========================================================

    inputs = []
    outputs = []

    clock_signals = []
    reset_signals = []

    for port in ports:

        name = port["name"]
        direction = port["direction"]
        width = port.get("width", 1)
        signed = port.get("signed", False)

        lname = name.lower()

        if direction == "input":
            inputs.append(port)

            if lname in [
                "clk",
                "clock",
                "clk_i",
                "i_clk"
            ]:
                clock_signals.append(name)

            if (
                "rst" in lname or
                "reset" in lname
            ):
                reset_signals.append(name)

        else:
            outputs.append(port)

    is_sequential = len(clock_signals) > 0

    # =========================================================
    # SIGNAL DECLARATION
    # =========================================================

    tb += "// =====================================================\n"
    tb += "// INPUTS\n"
    tb += "// =====================================================\n\n"

    for port in inputs:

        name = port["name"]
        width = port.get("width", 1)
        signed = port.get("signed", False)

        sign_str = "signed " if signed else ""

        if width > 1:
            tb += f"reg {sign_str}[{width-1}:0] {name};\n"
        else:
            tb += f"reg {sign_str}{name};\n"

    tb += "\n"

    tb += "// =====================================================\n"
    tb += "// OUTPUTS\n"
    tb += "// =====================================================\n\n"

    for port in outputs:

        name = port["name"]
        width = port.get("width", 1)
        signed = port.get("signed", False)

        sign_str = "signed " if signed else ""

        if width > 1:
            tb += f"wire {sign_str}[{width-1}:0] {name};\n"
        else:
            tb += f"wire {sign_str}{name};\n"

    tb += "\n"

    # =========================================================
    # ITERATION VARIABLE
    # =========================================================

    tb += "integer i;\n\n"

    # =========================================================
    # DUT INSTANTIATION
    # =========================================================

    tb += "// =====================================================\n"
    tb += "// DUT INSTANTIATION\n"
    tb += "// =====================================================\n\n"

    if parameters:

        tb += f"{top_module} #(\n"

        plist = []

        for pname in parameters.keys():

            plist.append(
                f"    .{pname}({pname})"
            )

        tb += ",\n".join(plist)

        tb += "\n) uut (\n"

    else:

        tb += f"{top_module} uut (\n"

    connections = []

    for port in ports:

        name = port["name"]

        connections.append(
            f"    .{name}({name})"
        )

    tb += ",\n".join(connections)

    tb += "\n);\n\n"

    # =========================================================
    # DUMPFILE
    # =========================================================

    tb += "// =====================================================\n"
    tb += "// DUMPFILE\n"
    tb += "// =====================================================\n\n"

    tb += """
initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, tb);
end

"""

    # =========================================================
    # CLOCK GENERATION
    # =========================================================

    if is_sequential:

        tb += "// =====================================================\n"
        tb += "// CLOCK GENERATION\n"
        tb += "// =====================================================\n\n"

        half_period = int(clock_period / 2)

        for clk in clock_signals:

            tb += f"always #{half_period} {clk} = ~{clk};\n"

        tb += "\n"

    # =========================================================
    # INITIALIZATION
    # =========================================================

    tb += "// =====================================================\n"
    tb += "// STIMULUS\n"
    tb += "// =====================================================\n\n"

    tb += "initial begin\n\n"

    tb += '    $display("\\n========================================");\n'
    tb += '    $display("STARTING TESTBENCH");\n'
    tb += '    $display("========================================");\n\n'

    # =========================================================
    # INITIALIZE INPUTS
    # =========================================================

    tb += "    // Initialize Inputs\n"

    for port in inputs:

        name = port["name"]

        tb += f"    {name} = 0;\n"

    tb += "\n"

    # =========================================================
    # RESET SEQUENCE
    # =========================================================

    if len(reset_signals) > 0:

        tb += "    // Reset Sequence\n"

        for rst in reset_signals:

            if rst.lower().endswith("_n"):

                tb += f"    {rst} = 0;\n"

            else:

                tb += f"    {rst} = 1;\n"

        tb += "\n"

        if is_sequential:

            tb += f"    #{clock_period * 2};\n\n"

        else:

            tb += "    #20;\n\n"

        for rst in reset_signals:

            if rst.lower().endswith("_n"):

                tb += f"    {rst} = 1;\n"

            else:

                tb += f"    {rst} = 0;\n"

        tb += "\n"

    # =========================================================
    # CALCULATE TOTAL INPUT WIDTH
    # =========================================================

    total_input_width = 0

    stimulus_ports = []

    for port in inputs:

        name = port["name"]

        if (
            name not in clock_signals and
            name not in reset_signals
        ):

            width = port.get("width", 1)

            total_input_width += width

            stimulus_ports.append(port)

    # =========================================================
    # EXHAUSTIVE TESTING
    # =========================================================

    if (
        not is_sequential and
        total_input_width <= exhaustive_limit
    ):

        total_combinations = 2 ** total_input_width

        tb += "    // Exhaustive Testing\n\n"

        tb += f"    for(i = 0; i < {total_combinations}; i = i + 1) begin\n\n"

        concat_signals = []

        for port in stimulus_ports:

            concat_signals.append(
                port["name"]
            )

        concat_str = ",".join(concat_signals)

        tb += f"        {{{concat_str}}} = i;\n\n"

        tb += "        #10;\n\n"

        tb += '        $display("\\nTEST VECTOR %0d", i);\n'

        for port in inputs:

            name = port["name"]
            width = port.get("width", 1)

            if width > 1:
                tb += f'        $display("{name} = %h", {name});\n'
            else:
                tb += f'        $display("{name} = %b", {name});\n'

        for port in outputs:

            name = port["name"]
            width = port.get("width", 1)

            if width > 1:
                tb += f'        $display("{name} = %h", {name});\n'
            else:
                tb += f'        $display("{name} = %b", {name});\n'

        tb += "\n"

        tb += "    end\n\n"

    # =========================================================
    # RANDOM TESTING
    # =========================================================

    else:

        tb += "    // Randomized Testing\n\n"

        tb += f"    for(i = 0; i < {random_iterations}; i = i + 1) begin\n\n"

        for port in stimulus_ports:

            name = port["name"]
            width = port.get("width", 1)

            if width > 1:

                max_val = (2 ** width) - 1

                tb += (
                    f"        {name} = "
                    f"$random & {width}'h{max_val:X};\n"
                )

            else:

                tb += (
                    f"        {name} = "
                    f"$random;\n"
                )

        tb += "\n"

        if is_sequential:

            tb += "        @(posedge "

            tb += clock_signals[0]

            tb += ");\n\n"

        else:

            tb += "        #10;\n\n"

        tb += '        $display("\\nRANDOM TEST %0d", i);\n'

        for port in inputs:

            name = port["name"]
            width = port.get("width", 1)

            if width > 1:
                tb += f'        $display("{name} = %h", {name});\n'
            else:
                tb += f'        $display("{name} = %b", {name});\n'

        for port in outputs:

            name = port["name"]
            width = port.get("width", 1)

            if width > 1:
                tb += f'        $display("{name} = %h", {name});\n'
            else:
                tb += f'        $display("{name} = %b", {name});\n'

        tb += "\n"

        tb += "    end\n\n"

    # =========================================================
    # FINISH
    # =========================================================

    tb += '    $display("\\n========================================");\n'
    tb += '    $display("TESTBENCH COMPLETED");\n'
    tb += '    $display("========================================");\n\n'

    tb += "    $finish;\n"

    tb += "end\n\n"

    # =========================================================
    # MONITOR
    # =========================================================

    tb += "// =====================================================\n"
    tb += "// LIVE MONITOR\n"
    tb += "// =====================================================\n\n"

    tb += "initial begin\n"

    monitor_fmt = []
    monitor_vars = []

    for port in ports:

        name = port["name"]
        width = port.get("width", 1)

        if width > 1:
            monitor_fmt.append(f"{name}=%h")
        else:
            monitor_fmt.append(f"{name}=%b")

        monitor_vars.append(name)

    fmt_string = " ".join(monitor_fmt)

    vars_string = ", ".join(monitor_vars)

    tb += (
        f'    $monitor('
        f'"T=%0t {fmt_string}", '
        f'$time, {vars_string}'
        f');\n'
    )

    tb += "end\n\n"

    tb += "endmodule\n"

    return tb