# ================================================================
# DRILLDOWN ENGINE
# ================================================================

class DrilldownEngine:

    def __init__(self):

        self.drill_map = {}

    # ============================================================
    # REGISTER EXPANSION
    # ============================================================

    def register(

        self,

        abstract_block,

        internal_cells
    ):

        self.drill_map[abstract_block] = internal_cells

    # ============================================================
    # GET INTERNALS
    # ============================================================

    def get_internal_cells(

        self,

        abstract_block
    ):

        return self.drill_map.get(

            abstract_block,

            []
        )