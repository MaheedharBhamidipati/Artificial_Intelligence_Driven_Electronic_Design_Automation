"""
============================================================

AIDEA Cell Index

Indexes synthesized cells for very fast lookup.

Instead of scanning thousands of cells repeatedly,
every semantic pass uses this cache.

Author : AIDEA
Phase : 2.1

============================================================
"""

from collections import defaultdict

from backend.semantic.semantic_database import SemanticCell


class CellIndex:

    def __init__(self):

        # --------------------------------------------
        # Master Cell List
        # --------------------------------------------

        self.cells = []

        # --------------------------------------------
        # Direct Lookup
        # --------------------------------------------

        self.by_name = {}

        self.by_type = defaultdict(list)

        # --------------------------------------------
        # Categories
        # --------------------------------------------

        self.registers = []

        self.combinational = []

        self.sequential = []

        self.arithmetic = []

        self.memories = []

        self.muxes = []

        self.comparators = []

        self.counters = []

        self.decoders = []

        self.encoders = []

        self.shift_registers = []

        self.pipeline_registers = []

        self.clock_cells = []

        self.reset_cells = []

        self.io_cells = []

        self.control_cells = []

        self.unknown = []
        
            # ======================================================

    def clear(self):

        self.cells.clear()

        self.by_name.clear()

        self.by_type.clear()

        self.registers.clear()

        self.combinational.clear()

        self.sequential.clear()

        self.arithmetic.clear()

        self.memories.clear()

        self.muxes.clear()

        self.comparators.clear()

        self.counters.clear()

        self.decoders.clear()

        self.encoders.clear()

        self.shift_registers.clear()

        self.pipeline_registers.clear()

        self.clock_cells.clear()

        self.reset_cells.clear()

        self.io_cells.clear()

        self.control_cells.clear()

        self.unknown.clear()
        
            # ======================================================

    def build(

        self,

        cells

    ):

        self.clear()

        self.cells = list(cells)

        for cell in self.cells:

            self.index_cell(cell)
            
                # ======================================================

    def index_cell(

        self,

        cell: SemanticCell

    ):

        self.by_name[cell.name] = cell

        ctype = cell.cell_type.upper()

        self.by_type[ctype].append(cell)

        # --------------------------------------
        # Sequential
        # --------------------------------------

        if "DFF" in ctype:

            self.registers.append(cell)

            self.sequential.append(cell)

        else:

            self.combinational.append(cell)

        # --------------------------------------
        # Arithmetic
        # --------------------------------------

        if any(

            x in ctype

            for x in

            [

                "ADD",

                "SUB",

                "MUL",

                "DIV",

                "MAC"

            ]

        ):

            self.arithmetic.append(cell)

        # --------------------------------------
        # MUX
        # --------------------------------------

        elif "MUX" in ctype:

            self.muxes.append(cell)

        # --------------------------------------
        # Comparator
        # --------------------------------------

        elif any(

            x in ctype

            for x in

            [

                "EQ",

                "LT",

                "GT",

                "CMP"

            ]

        ):

            self.comparators.append(cell)

        # --------------------------------------
        # Memory
        # --------------------------------------

        elif any(

            x in ctype

            for x in

            [

                "RAM",

                "ROM",

                "MEM"

            ]

        ):

            self.memories.append(cell)

        # --------------------------------------
        # Unknown
        # --------------------------------------

        else:

            self.unknown.append(cell)
            
                # ======================================================

    def get(

        self,

        name

    ):

        return self.by_name.get(name)

    # ======================================================

    def get_type(

        self,

        cell_type

    ):

        return self.by_type.get(

            cell_type.upper(),

            []

        )
        
            # ======================================================

    @property

    def number_of_cells(self):

        return len(self.cells)

    @property

    def number_of_registers(self):

        return len(self.registers)

    @property

    def number_of_arithmetic(self):

        return len(self.arithmetic)

    @property

    def number_of_muxes(self):

        return len(self.muxes)

    @property

    def number_of_memories(self):

        return len(self.memories)
    
        # ======================================================

    def summary(self):

        print()

        print("="*60)

        print("CELL INDEX")

        print("="*60)

        print()

        print("Cells        :",len(self.cells))

        print("Registers    :",len(self.registers))

        print("Arithmetic   :",len(self.arithmetic))

        print("MUX          :",len(self.muxes))

        print("Comparators  :",len(self.comparators))

        print("Memory       :",len(self.memories))

        print("Unknown      :",len(self.unknown))

        print()

        print("="*60)