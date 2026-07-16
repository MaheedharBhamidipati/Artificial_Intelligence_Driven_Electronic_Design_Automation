from .rtl_parser import RTLParser


class SignalTracker:

    def __init__(self, filepath):
        self.filepath = filepath
        self.modules = []

    def analyze(self):

        parser = RTLParser(self.filepath)

        parser.parse_file()

        self.modules = parser.extract_modules()

        signal_database = {}

        for module in self.modules:

            signal_database[module["module_name"]] = {
                "inputs": module["inputs"],
                "outputs": module["outputs"],
                "wires": module["wires"],
                "regs": module["regs"]
            }

        return signal_database


if __name__ == "__main__":

    tracker = SignalTracker("example.v")

    signals = tracker.analyze()

    from pprint import pprint
    pprint(signals)
