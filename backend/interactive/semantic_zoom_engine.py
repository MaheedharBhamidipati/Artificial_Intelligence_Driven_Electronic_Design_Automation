# ================================================================
# SEMANTIC ZOOM ENGINE
# ================================================================

class SemanticZoomEngine:

    def __init__(self):

        self.zoom_levels = {

            0: "SYSTEM",

            1: "MODULE",

            2: "DATAPATH",

            3: "RTL",

            4: "GATE"
        }

    # ============================================================
    # GET VIEW
    # ============================================================

    def get_view(self, zoom_level):

        return self.zoom_levels.get(

            zoom_level,

            "RTL"
        )