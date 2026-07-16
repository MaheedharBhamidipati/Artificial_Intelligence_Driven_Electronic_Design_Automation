from backend.rtl_parser_engine.netlist_generator import NetlistGenerator


class ResourceEstimator:
    def __init__(self, filepath):
        self.filepath = filepath

    def estimate(self):
        netlist = NetlistGenerator(self.filepath).generate()
        gates = netlist["gates"]

        counts = {}
        for gate in gates:
            gt = gate["gate_type"]
            counts[gt] = counts.get(gt, 0) + 1

        total = sum(counts.values())

        return {
            "total_gates": total,
            "gate_breakdown": counts,
            "estimated_luts": total,
            "estimated_area_score": total * 1.0
        }