# ============================================================
# CONGESTION UTILITIES
# ============================================================

def normalize_congestion(score):

    return min(

        100,

        max(

            0,

            score
        )
    )

# ------------------------------------------------------------
# COLOR MAPPING
# ------------------------------------------------------------

def congestion_color(score):

    if score < 30:

        return "green"

    elif score < 60:

        return "yellow"

    elif score < 80:

        return "orange"

    else:

        return "red"