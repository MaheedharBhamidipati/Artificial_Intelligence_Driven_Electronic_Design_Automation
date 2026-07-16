# ================================================================
# TOPOLOGY OPTIMIZER
# ================================================================

def optimize_topology(cells):

    suggestions = []

    total_cells = len(cells)

    # ============================================================
    # LARGE DESIGN
    # ============================================================

    if total_cells > 300:

        suggestions.append(

            "Enable hierarchy abstraction"
        )

    # ============================================================
    # SEQUENTIAL HEAVY
    # ============================================================

    sequential = 0

    for cell in cells:

        ctype = str(
            cell.get("type", "")
        ).lower()

        if any(

            x in ctype

            for x in [

                "dff",
                "ff",
                "register"
            ]
        ):

            sequential += 1

    if sequential > 50:

        suggestions.append(

            "Enable register bank compression"
        )

    # ============================================================
    # ARITHMETIC HEAVY
    # ============================================================

    arithmetic = 0

    for cell in cells:

        ctype = str(
            cell.get("type", "")
        ).lower()

        if any(

            x in ctype

            for x in [

                "add",
                "sub",
                "alu",
                "mul"
            ]
        ):

            arithmetic += 1

    if arithmetic > 20:

        suggestions.append(

            "Enable arithmetic abstraction"
        )

    return suggestions