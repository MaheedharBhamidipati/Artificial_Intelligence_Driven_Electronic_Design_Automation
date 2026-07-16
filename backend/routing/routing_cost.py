# ============================================================
# ROUTING COST ESTIMATION
# ============================================================

def calculate_wirelength(routes):

    total_length = 0

    for route in routes:

        points = route["path"]

        for i in range(len(points) - 1):

            x1, y1 = points[i]

            x2, y2 = points[i + 1]

            distance = abs(x2 - x1) + abs(y2 - y1)

            total_length += distance

    return total_length