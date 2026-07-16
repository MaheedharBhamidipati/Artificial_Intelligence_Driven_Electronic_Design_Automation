# ============================================================
# POWER METRICS
# ============================================================

class PowerMetrics:

    def generate_report(self, power_data):

        print("\n========== POWER REPORT ==========\n")

        print(f"Dynamic Power : {power_data['dynamic_power']:.6f} W")
        print(f"Leakage Power : {power_data['leakage_power']:.6f} W")
        print(f"Total Power   : {power_data['total_power']:.6f} W")

        print("\n==================================\n")