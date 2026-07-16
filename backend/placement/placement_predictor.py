# ================================================================
# AI PLACEMENT PREDICTOR
# ================================================================

class PlacementPredictor:

    def __init__(self, cells):

        self.cells = cells

    # ============================================================
    # GROUP BY TYPE
    # ============================================================

    def predict(self):

        placement = {}

        for cell in self.cells:

            ctype = str(

                cell.get(
                    "type",
                    "logic"
                )
            )

            if ctype not in placement:

                placement[ctype] = []

            placement[ctype].append(

                cell.get("name")
            )

        return placement