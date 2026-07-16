# ================================================================
# AI RTL ANALYZER
# ================================================================

from backend.ai.hotspot_detector import detect_hotspots
from backend.ai.congestion_predictor import predict_congestion
from backend.ai.critical_path_estimator import estimate_critical_paths
from backend.ai.topology_optimizer import optimize_topology


class AIRTLAnalyzer:

    def __init__(

        self,

        cells,

        net_map,

        abstractions
    ):

        self.cells = cells

        self.net_map = net_map

        self.abstractions = abstractions

        self.analysis = {}

    # ============================================================
    # RUN AI ANALYSIS
    # ============================================================

    def analyze(self):

        self.analysis["hotspots"] = detect_hotspots(

            self.cells
        )

        self.analysis["congestion"] = predict_congestion(

            self.cells
        )

        self.analysis["critical_paths"] = estimate_critical_paths(

            self.cells,

            self.net_map
        )

        self.analysis["topology"] = optimize_topology(

            self.cells
        )

        return self.analysis