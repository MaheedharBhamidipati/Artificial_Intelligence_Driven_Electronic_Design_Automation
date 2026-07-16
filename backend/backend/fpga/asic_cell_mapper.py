class ASICCellMapper:
    def map_cells(self, netlist):
        std_cells = []

        for gate in netlist["gates"]:
            std_cells.append({
                "gate_id": gate["gate_id"],
                "std_cell": f"{gate['gate_type']}_X1"
            })

        return std_cells
