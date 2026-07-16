# ============================================================
# OVERFLOW ANALYSIS
# ============================================================

class OverflowAnalysis:

    def __init__(self):

        self.threshold = 80

    # --------------------------------------------------------
    # DETECT OVERFLOW
    # --------------------------------------------------------

    def detect(self, hotspots):

        overflow_regions = []

        for hotspot in hotspots:

            if hotspot["congestion_score"] > self.threshold:

                overflow_regions.append({

                    "net": hotspot["net"],

                    "score": hotspot["congestion_score"],

                    "x": hotspot["x"],

                    "y": hotspot["y"]
                })

        return overflow_regions

    # --------------------------------------------------------
    # OVERFLOW COUNT
    # --------------------------------------------------------

    def count_overflows(self, overflow_regions):

        return len(overflow_regions)