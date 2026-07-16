import re


class LatchDetector:
    def __init__(self, filepath):
        self.filepath = filepath

    def detect(self):
        with open(self.filepath, "r") as f:
            code = f.read()

        warnings = []

        always_blocks = re.findall(
            r'always\s*@\((.*?)\)(.*?)end',
            code,
            re.DOTALL
        )

        for sens, body in always_blocks:
            if "*" in sens and "else" not in body:
                warnings.append(
                    "Possible latch inference: combinational always block without full assignment/else."
                )

        return warnings
