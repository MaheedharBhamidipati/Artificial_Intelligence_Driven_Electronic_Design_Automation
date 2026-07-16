class LogicOptimizer:
    def __init__(self, netlist):
        self.netlist = netlist

    def optimize(self):
        suggestions = []

        for gate in self.netlist["gates"]:
            if gate["gate_type"] == "BUFFER":
                suggestions.append(
                    f"Remove redundant buffer driving {gate['output']}"
                )

        return suggestions
