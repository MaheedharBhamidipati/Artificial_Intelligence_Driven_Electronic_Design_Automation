# ============================================================
# SHARED PLOT UTILITIES
# ============================================================

import matplotlib.pyplot as plt

# ------------------------------------------------------------
# DARK THEME
# ------------------------------------------------------------

def apply_dark_theme(ax):

    ax.set_facecolor("#101820")

    ax.grid(

        True,

        color="white",

        alpha=0.15
    )

# ------------------------------------------------------------
# TITLE STYLE
# ------------------------------------------------------------

def set_title(ax, title):

    ax.set_title(

        title,

        fontsize=16,

        color="white",

        pad=20
    )

# ------------------------------------------------------------
# AXIS STYLE
# ------------------------------------------------------------

def style_axes(ax):

    ax.tick_params(

        colors="white"
    )

    for spine in ax.spines.values():

        spine.set_color("white")

# ------------------------------------------------------------
# CONGESTION COLOR
# ------------------------------------------------------------

def congestion_color(score):

    if score < 30:

        return "green"

    elif score < 60:

        return "yellow"

    elif score < 80:

        return "orange"

    return "red"

# ------------------------------------------------------------
# POWER COLOR
# ------------------------------------------------------------

def power_color(power):

    if power < 25:

        return "blue"

    elif power < 50:

        return "green"

    elif power < 75:

        return "yellow"

    return "red"