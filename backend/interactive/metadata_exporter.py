# ================================================================
# RTL METADATA EXPORTER
# ================================================================

import json


class RTLMetadataExporter:

    def __init__(self):

        self.metadata = {}

    # ============================================================
    # ADD ENTRY
    # ============================================================

    def add(

        self,

        name,

        info
    ):

        self.metadata[name] = info

    # ============================================================
    # EXPORT
    # ============================================================

    def export(

        self,

        filename
    ):

        with open(filename, "w") as f:

            json.dump(

                self.metadata,

                f,

                indent=4
            )