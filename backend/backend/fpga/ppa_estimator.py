class PPAEstimator:
    def estimate(self, netlist):
        gate_count = len(netlist["gates"])

        return {
            "estimated_area_um2": gate_count * 10,
            "estimated_power_mw": round(gate_count * 0.5, 2),
            "estimated_delay_ns": round(gate_count * 0.15, 2)
        }
