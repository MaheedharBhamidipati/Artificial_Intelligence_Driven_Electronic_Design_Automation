# ================================================================
# DATAPATH ENGINE
# ================================================================

from backend.datapath.layer_builder import build_datapath_layers


class DatapathEngine:

    def __init__(

        self,

        cells,

        abstractions
    ):

        self.cells = cells

        self.abstractions = abstractions

        self.layers = {}

    # ============================================================
    # BUILD DATAPATH
    # ============================================================

    def build(self):

        self.layers = build_datapath_layers(

            self.cells,

            self.abstractions
        )

        return self.layers