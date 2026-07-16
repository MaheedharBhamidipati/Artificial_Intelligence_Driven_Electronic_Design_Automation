import re


class CDCChecker:
    def __init__(self, filepath):
        self.filepath = filepath

    def check(self):
        with open(self.filepath, "r") as f:
            code = f.read()

        clocks = re.findall(
            r'posedge\s+(\w+)',
            code
        )

        unique_clocks = list(set(clocks))

        if len(unique_clocks) > 1:
            return {
                "multiple_clock_domains": True,
                "clocks": unique_clocks,
                "warning": "Potential CDC detected."
            }

        return {
            "multiple_clock_domains": False,
            "clocks": unique_clocks
        }
