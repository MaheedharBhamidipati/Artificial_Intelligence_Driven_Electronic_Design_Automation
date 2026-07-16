# ============================================================
# POWER UTILITIES
# ============================================================

def normalize_power(value, max_value):

    if max_value == 0:

        return 0

    return round(

        (value / max_value) * 100,

        2
    )

# ------------------------------------------------------------
# COLOR SELECTOR
# ------------------------------------------------------------

def power_color(power):

    if power < 25:

        return "blue"

    elif power < 50:

        return "green"

    elif power < 75:

        return "yellow"

    else:

        return "red"