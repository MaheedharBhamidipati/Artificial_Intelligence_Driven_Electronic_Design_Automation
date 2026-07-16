# ================================================================
# HOTSPOT DETECTOR
# ================================================================

from collections import defaultdict


# ================================================================
# DETECT HIGH FANOUT HOTSPOTS
# ================================================================

def detect_hotspots(cells):

    signal_usage = defaultdict(int)

    hotspots = []

    # ============================================================
    # COUNT SIGNAL USAGE
    # ============================================================

    for cell in cells:

        connections = cell.get(

            "connections",

            {}
        )

        for conn_name, conn_value in connections.items():

            if not isinstance(conn_value, list):

                conn_value = [conn_value]

            for signal in conn_value:

                signal_usage[str(signal)] += 1

    # ============================================================
    # DETECT HOTSPOTS
    # ============================================================

    for signal, usage in signal_usage.items():

        if usage >= 8:

            hotspots.append({

                "signal": signal,

                "fanout": usage,

                "severity": "HIGH"
            })

        elif usage >= 5:

            hotspots.append({

                "signal": signal,

                "fanout": usage,

                "severity": "MEDIUM"
            })

    return hotspots