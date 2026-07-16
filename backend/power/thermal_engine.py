# ============================================================
# THERMAL ENGINE
# ============================================================

import random

class ThermalEngine:

    def __init__(self):

        self.ambient_temperature = 27

    # --------------------------------------------------------
    # GENERATE THERMAL MAP
    # --------------------------------------------------------

    def analyze_temperature(self, hotspots):

        thermal_map = []

        for hotspot in hotspots:

            congestion = hotspot.get(

                "congestion_score",

                0
            )

            estimated_temp = (

                self.ambient_temperature +

                (congestion * 0.6) +

                random.uniform(0, 5)
            )

            thermal_map.append({

                "region": hotspot["net"],

                "temperature": round(

                    estimated_temp,

                    2
                )
            })

        return thermal_map

    # --------------------------------------------------------
    # PEAK TEMPERATURE
    # --------------------------------------------------------

    def get_peak_temperature(self, thermal_map):

        if not thermal_map:

            return 0

        return max(

            region["temperature"]

            for region in thermal_map
        )