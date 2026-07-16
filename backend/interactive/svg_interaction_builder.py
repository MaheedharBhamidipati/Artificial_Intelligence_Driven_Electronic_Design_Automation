# ================================================================
# SVG INTERACTION BUILDER
# ================================================================

import json


class SVGInteractionBuilder:

    def __init__(self):

        self.metadata = {}

    # ============================================================
    # REGISTER NODE
    # ============================================================

    def register_node(

        self,

        node_name,

        metadata
    ):

        self.metadata[node_name] = metadata

    # ============================================================
    # EXPORT JSON
    # ============================================================

    def export_json(

        self,

        output_file
    ):

        with open(output_file, "w") as f:

            json.dump(

                self.metadata,

                f,

                indent=4
            )