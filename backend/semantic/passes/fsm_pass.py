"""
============================================================

AIDEA FSM Detection Pass

Detects

• FSM Presence
• State Registers
• Next State Logic
• Output Logic
• Mealy / Moore
• State Encoding

Author : AIDEA
Phase : 2.1

============================================================
"""

from backend.semantic.semantic_database import (
    SemanticDatabase,
    SemanticBlock
)


class FSMPass:

    """
    Semantic FSM Detection Pass
    """

    # =========================================================

    def __init__(self, database: SemanticDatabase):

        self.db = database

        self.index = getattr(database, "index", None)

    # =========================================================

    def run(self):

        print("\nRunning FSM Pass...")

        if not self.detect_fsm():

            print("No FSM Detected.")

            return

        self.detect_state_registers()

        self.detect_next_state_logic()

        self.detect_output_logic()

        self.detect_encoding()

        self.detect_machine_type()

        self.create_semantic_blocks()

        self.update_metrics()

        print("FSM Pass Complete.")

    # =========================================================

    def detect_fsm(self):

        """
        Decide whether the design is likely an FSM.
        """

        register_count = 0

        if self.index:

            register_count = len(self.index.registers)

        else:

            for cell in self.db.cells:

                if "DFF" in cell.cell_type.upper():

                    register_count += 1

        if register_count == 0:

            self.db.fsm.detected = False

            return False

        # --------------------------------------------------
        # Heuristic 1
        # --------------------------------------------------

        if "FSM" in self.db.logic_type.upper():

            self.db.fsm.detected = True

            return True

        # --------------------------------------------------
        # Heuristic 2
        # --------------------------------------------------

        if register_count >= 2:

            self.db.fsm.detected = True

            return True

        # --------------------------------------------------
        # Heuristic 3
        # --------------------------------------------------

        state_keywords = [

            "state",

            "current_state",

            "next_state"

        ]

        for cell in self.db.cells:

            name = cell.name.lower()

            if any(

                keyword in name

                for keyword in state_keywords

            ):

                self.db.fsm.detected = True

                return True

        self.db.fsm.detected = False

        return False

    # =========================================================

    def detect_state_registers(self):

        """
        Detect state registers.
        """

        state_regs = []

        if self.index:

            candidates = self.index.registers

        else:

            candidates = self.db.cells

        for cell in candidates:

            name = cell.name.lower()

            if (

                "state" in name

                or

                "current" in name

                or

                "cs" == name

            ):

                state_regs.append(cell)

        # fallback

        if len(state_regs) == 0:

            if self.index:

                state_regs = self.index.registers[:]

        self.db.attributes["state_registers"] = state_regs
        
        
            # =========================================================

    def detect_next_state_logic(self):

        """
        Detect next-state logic.

        This will be improved later using
        graph connectivity.
        """

        next_logic = []

        keywords = [

            "next",

            "ns",

            "next_state"

        ]

        for cell in self.db.cells:

            n = cell.name.lower()

            if any(

                k in n

                for k in keywords

            ):

                next_logic.append(cell)

        self.db.attributes["next_state_logic"] = next_logic

    # =========================================================

    def detect_output_logic(self):

        """
        Detect output logic.

        Currently heuristic-based.
        """

        outputs = []

        for cell in self.db.cells:

            n = cell.name.lower()

            if (

                "out" in n

                or

                "output" in n

                or

                "z" == n

            ):

                outputs.append(cell)

        self.db.attributes["output_logic"] = outputs

    # =========================================================

    def detect_encoding(self):

        """
        Determine encoding style.

        Binary

        One-Hot

        Gray

        Unknown
        """

        regs = self.db.attributes.get(

            "state_registers",

            []

        )

        bits = len(regs)

        if bits == 0:

            self.db.fsm.encoding = "Unknown"

            return

        if bits <= 6:

            self.db.fsm.encoding = "Binary"

        else:

            self.db.fsm.encoding = "One-Hot"
            
            
                # =========================================================

    def detect_machine_type(self):

        """
        Placeholder.

        Phase 2.2 will distinguish
        Mealy and Moore using graph analysis.
        """

        self.db.fsm.machine_type = "Unknown"

    # =========================================================

    def create_semantic_blocks(self):

        """
        Create physical semantic blocks.
        """

        if not self.db.fsm.detected:

            return

        regs = self.db.attributes.get(

            "state_registers",

            []

        )

        block = SemanticBlock(

            name="State Register Bank",

            block_type="FSM Registers",

            description="FSM State Registers",

            cells=regs

        )

        self.db.add_block(block)

    # =========================================================

    def update_metrics(self):

        regs = self.db.attributes.get(

            "state_registers",

            []

        )

        self.db.fsm.number_of_states = (

            2 ** len(regs)

            if len(regs)

            else 0

        )
        
            # =========================================================

    def summary(self):

        print()

        print("=" * 60)

        print("FSM PASS")

        print("=" * 60)

        print()

        print("Detected       :", self.db.fsm.detected)

        print("Machine        :", self.db.fsm.machine_type)

        print("Encoding       :", self.db.fsm.encoding)

        print("State Registers:", len(

            self.db.attributes.get(

                "state_registers",

                []

            )

        ))

        print("Estimated States:",

              self.db.fsm.number_of_states)

        print()

        print("=" * 60)
        
            
            