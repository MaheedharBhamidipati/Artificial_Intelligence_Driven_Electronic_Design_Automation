class StructuralClassifier:
    def classify(self, netlist):
        gate_types = {g["gate_type"] for g in netlist["gates"]}

        if "ADD" in gate_types:
            return "Arithmetic Datapath"

        if "COMPARATOR" in gate_types:
            return "Control Logic"

        if len(netlist["gates"]) <= 5:
            return "Simple Combinational Logic"

        return "General Digital Logic"
