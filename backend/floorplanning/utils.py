import random


# ======================================================
# COLOR MAP
# ======================================================

COLORS = {

    "Arithmetic": "#4CAF50",

    "Logic": "#2196F3",

    "Sequential": "#F44336",

    "Memory": "#9C27B0",

    "MUX": "#FF9800",

    "IO": "#607D8B",

    "FSM": "#795548",

    "Output": "#009688",

    "Unknown": "#9E9E9E"

}


# ======================================================
# RANDOM LIGHT COLOR
# ======================================================

def random_color():

    return random.choice(list(COLORS.values()))


# ======================================================
# GET COLOR
# ======================================================

def get_color(macro_type):

    return COLORS.get(

        macro_type,

        COLORS["Unknown"]
    )


# ======================================================
# OVERLAP
# ======================================================

def overlap(a, b):

    return not (

        a.x + a.width < b.x

        or

        b.x + b.width < a.x

        or

        a.y + a.height < b.y

        or

        b.y + b.height < a.y

    )


# ======================================================
# OVERLAP AREA
# ======================================================
# Same rectangle contract as overlap() (duck-typed x/y/width/
# height), but returns the actual overlapping area instead of
# a boolean. Needed anywhere overlap is a matter of degree, not
# just yes/no -- e.g. area-weighted demand/supply calculations,
# where a bin barely clipped by a blockage should be debited
# far less than a bin it fully covers.

def overlap_area(a, b):

    x0 = max(a.x, b.x)

    y0 = max(a.y, b.y)

    x1 = min(a.x + a.width, b.x + b.width)

    y1 = min(a.y + a.height, b.y + b.height)

    if x1 <= x0 or y1 <= y0:

        return 0.0

    return (x1 - x0) * (y1 - y0)