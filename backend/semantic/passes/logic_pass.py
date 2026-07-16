"""
==========================================================

AIDEA Semantic Logic Pass

Determines

• Combinational
• Sequential
• FSM
• Mixed

==========================================================
"""

from collections import Counter

from backend.semantic.semantic_database import SemanticDatabase


class LogicPass:

    def __init__(

        self,

        database: SemanticDatabase

    ):

        self.db = database

    # ==================================================

    def run(self):

        self.detect_logic_type()

        self.detect_clock()

        self.detect_reset()

        self.update_metrics()

    # ==================================================

    def detect_logic_type(self):

        sequential = 0

        combinational = 0

        cell_counter = Counter()

        for cell in self.db.cells:

            ctype = cell.cell_type.upper()

            cell_counter[ctype] += 1

            if "DFF" in ctype:

                sequential += 1

            else:

                combinational += 1

        self.db.metrics.register_count = sequential

        self.db.metrics.sequential_cells = sequential

        self.db.metrics.combinational_cells = combinational

        if sequential == 0:

            self.db.logic_type = "Combinational"

        elif sequential > 0 and combinational == 0:

            self.db.logic_type = "Sequential"

        else:

            self.db.logic_type = "Mixed"

        self.db.attributes["cell_summary"] = dict(cell_counter)

    # ==================================================

    def detect_clock(self):

        clocks = []

        for port in self.db.inputs:

            name = port.name.lower()

            if name in (

                "clk",

                "clock",

                "sys_clk",

                "i_clk"

            ):

                clocks.append(port.name)

        self.db.attributes["clock_ports"] = clocks

    # ==================================================

    def detect_reset(self):

        resets = []

        for port in self.db.inputs:

            name = port.name.lower()

            if (

                "rst" in name

                or

                "reset" in name

            ):

                resets.append(port.name)

        self.db.attributes["reset_ports"] = resets

    # ==================================================

    def update_metrics(self):

        self.db.metrics.input_count = len(

            self.db.inputs

        )

        self.db.metrics.output_count = len(

            self.db.outputs

        )

        self.db.metrics.gate_count = len(

            self.db.cells

        )

        self.db.metrics.net_count = len(

            self.db.nets

        )

    # ==================================================

    def summary(self):

        print()

        print("="*60)

        print("LOGIC PASS")

        print("="*60)

        print()

        print(

            "Logic Type :",

            self.db.logic_type

        )

        print(

            "Registers :",

            self.db.metrics.register_count

        )

        print(

            "Combinational :",

            self.db.metrics.combinational_cells

        )

        print()

        print(

            "Clock Ports :",

            self.db.attributes.get(

                "clock_ports",

                []

            )

        )

        print(

            "Reset Ports :",

            self.db.attributes.get(

                "reset_ports",

                []

            )

        )

        print()

        print("="*60)