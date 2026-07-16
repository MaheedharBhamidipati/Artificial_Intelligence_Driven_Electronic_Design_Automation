class FPGAResourceMapper:
    def map_resources(self, netlist):
        lut = 0
        ff = 0
        dsp = 0
        bram = 0

        for gate in netlist["gates"]:
            gt = gate["gate_type"]

            if gt in ["AND", "OR", "XOR", "NOT", "BUFFER", "COMPARATOR"]:
                lut += 1
            elif gt in ["ADD", "SUB", "MUL", "DIV"]:
                dsp += 1

        return {
            "LUTs": lut,
            "FFs": ff,
            "DSPs": dsp,
            "BRAMs": bram
        }
