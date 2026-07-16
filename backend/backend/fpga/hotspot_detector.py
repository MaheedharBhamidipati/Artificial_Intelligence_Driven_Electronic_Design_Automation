class HotspotDetector:
    def detect(self, netlist):
        hotspots = []

        for gate in netlist["gates"]:
            if gate["gate_type"] in ["MUL", "DIV"]:
                hotspots.append({
                    "gate_id": gate["gate_id"],
                    "reason": "High-complexity arithmetic block"
                })

        return hotspots
