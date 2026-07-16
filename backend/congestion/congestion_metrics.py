# ============================================================
# CONGESTION METRICS
# ============================================================

class CongestionMetrics:

    def generate_report(self, congestion_data):

        print("\n========== CONGESTION REPORT ==========\n")

        print(

            f"Total Nets       : "

            f"{congestion_data['total_nets']}"
        )

        print(

            f"Density          : "

            f"{congestion_data['density']}"
        )

        print(

            f"Hotspot Level    : "

            f"{congestion_data['hotspot_level']}"
        )

        print(

            f"Hotspot Count    : "

            f"{len(congestion_data['hotspots'])}"
        )

        print("\n=======================================\n")