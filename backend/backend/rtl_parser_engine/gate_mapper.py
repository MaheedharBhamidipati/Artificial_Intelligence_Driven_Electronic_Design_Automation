import re
from .expression_parser import ExpressionParser

class GateMapper:

    def __init__(self, filepath):

        self.filepath = filepath

        self.parser = ExpressionParser()

        self.gates = []

    def read_file(self):

        with open(self.filepath, "r") as f:
            return f.readlines()

    def extract_assignments(self):

        lines = self.read_file()

        assign_lines = []

        for line in lines:

            line = line.strip()

            if line.startswith("assign"):
                assign_lines.append(line)

        return assign_lines

    def map_gates(self):

        assignments = self.extract_assignments()

        gate_id = 0

        for assign in assignments:

            match = re.match(r"assign\s+(.*?)\s*=\s*(.*)", assign)

            if not match:
                continue

            output_signal = match.group(1).strip()

            expression = match.group(2).strip()

            parsed = self.parser.parse_expression(expression)

            gate_data = {
                "gate_id": f"GATE_{gate_id}",
                "output": output_signal,
                "gate_type": parsed["gate_type"],
                "inputs": parsed["inputs"]
            }

            self.gates.append(gate_data)

            gate_id += 1

        return self.gates


if __name__ == "__main__":

    mapper = GateMapper("example.v")

    gates = mapper.map_gates()

    from pprint import pprint
    pprint(gates)
