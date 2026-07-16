import re


class FSMExtractor:
    def __init__(self, filepath):
        self.filepath = filepath

    def extract(self):
        with open(self.filepath, "r") as f:
            code = f.read()

        always_blocks = re.findall(
            r'always\s*@\([^)]+\)(.*?)end',
            code,
            re.DOTALL
        )

        fsm_candidates = []

        for idx, block in enumerate(always_blocks):
            if "case" in block and "<=" in block:
                fsm_candidates.append({
                    "fsm_id": f"FSM_{idx}",
                    "type": "Detected FSM"
                })

        return fsm_candidates
