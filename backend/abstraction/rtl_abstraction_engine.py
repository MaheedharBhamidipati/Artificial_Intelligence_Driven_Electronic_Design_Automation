# ================================================================
# RTL ABSTRACTION ENGINE
# ================================================================
# Purpose:
#   Master abstraction controller
#
# Supports:
#   - Arithmetic abstraction
#   - Pipeline abstraction
#   - FSM abstraction
#   - Register bank abstraction
#
# ================================================================

from backend.abstraction.arithmetic_detector import detect_arithmetic_structures

from backend.abstraction.pipeline_detector import detect_pipeline_structures

from backend.abstraction.fsm_detector import detect_fsm_structures

from backend.abstraction.register_bank_detector import detect_register_banks


class RTLAbstractionEngine:

    def __init__(self, cells):

        self.cells = cells

        self.abstracted_cells = []

        self.abstractions = {

            "arithmetic": [],
            "pipelines": [],
            "fsm": [],
            "register_banks": []
        }

    # ============================================================
    # RUN ALL DETECTORS
    # ============================================================

    def analyze(self):

        self.abstractions["arithmetic"] = \
            detect_arithmetic_structures(self.cells)

        self.abstractions["pipelines"] = \
            detect_pipeline_structures(self.cells)

        self.abstractions["fsm"] = \
            detect_fsm_structures(self.cells)

        self.abstractions["register_banks"] = \
            detect_register_banks(self.cells)

        return self.abstractions

    # ============================================================
    # MARK ABSTRACTED CELLS
    # ============================================================

    def mark_abstracted_cells(self):

        abstracted = set()

        for category in self.abstractions.values():

            for block in category:

                for cell in block.get("cells", []):

                    cname = cell.get("name")

                    abstracted.add(cname)

        for cell in self.cells:

            if cell.get("name") in abstracted:

                cell["abstracted"] = True

        return self.cells