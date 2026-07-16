# ============================================================
# FILE: backend/placement/placement_cost.py
# ============================================================

import math


def calculate_wirelength(edges, placement):

    total_wirelength = 0

    for edge in edges:

        source = edge["source"]
        target = edge["target"]

        x1, y1 = placement[source]
        x2, y2 = placement[target]

        distance = abs(x2 - x1) + abs(y2 - y1)

        total_wirelength += distance

    return total_wirelength


def calculate_congestion(placement):

    congestion_score = len(placement) / 100

    return round(congestion_score, 2)