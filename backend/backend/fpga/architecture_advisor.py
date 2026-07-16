class ArchitectureAdvisor:
    def recommend(self, ppa, fpga_resources):
        if fpga_resources["DSPs"] > 5:
            return "DSP-heavy design: FPGA with abundant DSP slices recommended."

        if ppa["estimated_area_um2"] > 1000:
            return "Large design may benefit from ASIC implementation."

        return "Suitable for FPGA prototyping and moderate ASIC scaling."
