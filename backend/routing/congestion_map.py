# ============================================================
# CONGESTION ESTIMATION
# ============================================================

def estimate_congestion(routes):

    congestion_score = len(routes) * 0.5

    return round(congestion_score, 2)