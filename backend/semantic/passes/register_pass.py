"""
============================================================

AIDEA Register Pass

Detects

• Registers
• Register Banks
• Pipeline Registers
• Shift Registers
• State Registers

============================================================
"""

from collections import defaultdict

from backend.semantic.semantic_database import (
    SemanticBlock,
    SemanticDatabase
)


class RegisterPass:

    def __init__(
        self,
        database: SemanticDatabase
    ):

        self.db = database

    # =====================================================

    def run(self):

        self.detect_registers()

        self.detect_state_register()

        self.detect_pipeline_registers()

        self.detect_shift_registers()

    # =====================================================

    def detect_registers(self):

        register_cells = []

        for cell in self.db.cells:

            ctype = cell.cell_type.upper()

            if "DFF" in ctype \
            or "SDFF" in ctype \
            or "FDRE" in ctype \
            or "FDSE" in ctype:

                register_cells.append(cell)

        if len(register_cells) == 0:

            return

        block = SemanticBlock(

            name="Register Bank",

            block_type="Register",

            description="Sequential Storage",

            cells=register_cells

        )

        block.area = len(register_cells)

        self.db.add_block(block)

        self.db.attributes["register_cells"] = register_cells

    # =====================================================

    def detect_state_register(self):

        if not self.db.fsm.detected:

            return

        regs = self.db.attributes.get(
            "register_cells",
            []
        )

        if len(regs):

            self.db.fsm.state_register = regs[0].name

    # =====================================================

    def detect_pipeline_registers(self):

        pipelines = []

        regs = self.db.attributes.get(
            "register_cells",
            []
        )

        for reg in regs:

            name = reg.name.lower()

            if "pipe" in name:

                pipelines.append(reg)

        if pipelines:

            block = SemanticBlock(

                name="Pipeline Registers",

                block_type="Pipeline",

                cells=pipelines

            )

            self.db.add_block(block)

    # =====================================================

    def detect_shift_registers(self):

        shifts = []

        regs = self.db.attributes.get(
            "register_cells",
            []
        )

        for reg in regs:

            name = reg.name.lower()

            if "shift" in name:

                shifts.append(reg)

        if shifts:

            block = SemanticBlock(

                name="Shift Register",

                block_type="Shift Register",

                cells=shifts

            )

            self.db.add_block(block)

    # =====================================================

    def summary(self):

        print()

        print("="*60)

        print("REGISTER PASS")

        print("="*60)

        print()

        for block in self.db.blocks:

            if block.block_type in (

                "Register",

                "Pipeline",

                "Shift Register"

            ):

                print(

                    block.name,

                    ":",

                    len(block.cells),

                    "cells"

                )

        print()

        print("="*60)