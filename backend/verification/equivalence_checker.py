class EquivalenceChecker:
    def compare(self, rtl_netlist, generated_netlist):
        rtl_count = len(rtl_netlist["gates"])
        gen_count = len(generated_netlist["gates"])

        return {
            "equivalent": rtl_count == gen_count,
            "rtl_gate_count": rtl_count,
            "generated_gate_count": gen_count
        }
