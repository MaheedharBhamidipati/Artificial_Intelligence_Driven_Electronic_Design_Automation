import re
from .expression_parser import ExpressionParser


class GateMapper:

    def __init__(self, filepath):

        self.filepath = filepath
        self.parser = ExpressionParser()
        self.gates = []

    # =====================================================
    # FILE READER
    # =====================================================

    def read_file(self):

        with open(self.filepath, "r") as f:
            return f.read()

    # =====================================================
    # ASSIGN EXTRACTION
    # =====================================================

    def extract_assignments(self, code):

        return re.findall(
            r'assign\s+(.*?)\s*=\s*(.*?)\s*;',
            code,
            re.DOTALL
        )

    # =====================================================
    # ALWAYS BLOCK EXTRACTION
    # =====================================================

    def extract_always_blocks(self, code):

        pattern = re.compile(
            r'always\s*@\s*\([^)]*\)\s*begin(.*?)end',
            re.DOTALL | re.IGNORECASE
        )

        return pattern.findall(code)

    # =====================================================
    # CASE EXTRACTION
    # =====================================================

    def extract_case_statements(self, block):

        case_pattern = re.compile(
            r'case\s*\((.*?)\)(.*?)endcase',
            re.DOTALL | re.IGNORECASE
        )

        return case_pattern.findall(block)

    # =====================================================
    # ADD GATE
    # =====================================================

    def add_gate(
        self,
        gate_type,
        output_signal,
        inputs
    ):

        gate_id = len(self.gates)

        self.gates.append(
            {
                "gate_id": f"GATE_{gate_id}",
                "gate_type": gate_type,
                "output": output_signal,
                "inputs": inputs
            }
        )

    # =====================================================
    # PROCESS ASSIGNMENTS
    # =====================================================

    def process_assignments(self, code):

        assignments = self.extract_assignments(code)

        for lhs, rhs in assignments:

            parsed = self.parser.parse_expression(rhs)

            self.add_gate(
                parsed["gate_type"],
                lhs.strip(),
                parsed["inputs"]
            )

    # =====================================================
    # PROCESS CASE BLOCKS
    # =====================================================

    def process_case_blocks(self, code):

        always_blocks = self.extract_always_blocks(code)

        for block in always_blocks:

            cases = self.extract_case_statements(block)

            for selector, _ in cases:

                self.add_gate(
                    "CASE_DECODER",
                    "CASE_OUTPUT",
                    [selector.strip()]
                )

    # =====================================================
    # PROCESS IF BLOCKS
    # =====================================================

    def process_if_blocks(self, code):

        if_matches = re.findall(
            r'if\s*\((.*?)\)',
            code,
            re.IGNORECASE
        )

        for condition in if_matches:

            self.add_gate(
                "MUX",
                "IF_OUTPUT",
                [condition.strip()]
            )

    # =====================================================
    # DETECT LOGIC TYPE
    # =====================================================

    def detect_logic_type(self, code):

        if re.search(
            r'posedge|negedge',
            code,
            re.IGNORECASE
        ):
            return "Sequential"

        if re.search(
            r'always\s*@\s*\(\s*\*\s*\)',
            code,
            re.IGNORECASE
        ):
            return "Combinational"

        if re.search(
            r'\bassign\b',
            code,
            re.IGNORECASE
        ):
            return "Combinational"

        return "Unknown"

    # =====================================================
    # MAIN GATE MAPPING
    # =====================================================

    def map_gates(self):

        self.gates = []

        code = self.read_file()

        self.process_assignments(code)

        self.process_case_blocks(code)

        self.process_if_blocks(code)

        return {
            "logic_type": self.detect_logic_type(code),
            "gate_count": len(self.gates),
            "gates": self.gates
        }


if __name__ == "__main__":

    mapper = GateMapper("example.v")

    result = mapper.map_gates()

    from pprint import pprint

    pprint(result)