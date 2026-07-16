# ============================================================
# STABLE CONGESTION ENGINE
# ============================================================

class CongestionEngine:

    def __init__(self, nets):

        # ----------------------------------------------------
        # SAFE INITIALIZATION
        # ----------------------------------------------------

        if nets is None:

            self.nets = {}

        elif isinstance(nets, dict):

            self.nets = nets

        elif isinstance(nets, list):

            # convert list to indexed dict
            self.nets = {

                f"net_{i}": net

                for i, net in enumerate(nets)
            }

        else:

            self.nets = {}

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(self):

        try:

            total_nets = len(self.nets)

            density = min(

                100,

                total_nets * 2
            )

            hotspots = []

            congestion_map = []

            # ------------------------------------------------
            # SAFE ITERATION
            # ------------------------------------------------

            for i, (net_name, connections) in enumerate(

                list(self.nets.items())[:50]

            ):

                # --------------------------------------------
                # CONNECTION COUNT
                # --------------------------------------------

                if isinstance(connections, list):

                    fanout = len(connections)

                elif isinstance(connections, dict):

                    fanout = len(connections.keys())

                else:

                    fanout = 1

                congestion_score = min(

                    100,

                    fanout * 8
                )

                hotspot = {

                    "net": str(net_name),

                    "fanout": fanout,

                    "congestion_score": congestion_score,

                    "x": 80 + (i % 8) * 140,

                    "y": 80 + (i // 8) * 120
                }

                hotspots.append(hotspot)

                congestion_map.append({

                    "net": str(net_name),

                    "score": congestion_score
                })

            # ------------------------------------------------
            # HOTSPOT LEVEL
            # ------------------------------------------------

            hotspot_level = "LOW"

            if density > 70:

                hotspot_level = "HIGH"

            elif density > 40:

                hotspot_level = "MEDIUM"

            return {

                "total_nets": total_nets,

                "density": f"{density}%",

                "hotspot_level": hotspot_level,

                "hotspots": hotspots,

                "congestion_map": congestion_map
            }

        except Exception as e:

            return {

                "total_nets": 0,

                "density": "0%",

                "hotspot_level": "UNKNOWN",

                "hotspots": [],

                "congestion_map": [],

                "error": str(e)
            }