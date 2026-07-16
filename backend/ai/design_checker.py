class DesignChecker:
    def check(self, netlist):
        warnings = []

        for gate in netlist["gates"]:
            if len(gate["inputs"]) > 4:
                warnings.append(
                    f"{gate['gate_id']} has high fan-in ({len(gate['inputs'])})"
                )

        return warnings
