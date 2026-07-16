"""
============================================================

Yosys Netlist Loader

Converts Yosys JSON into
AIDEA Design Object

============================================================
"""

import json

from backend.floorplanning.design import (

    Design,

    Module,

    Cell,

    Port,

    Net

)


class NetlistLoader:

    def __init__(self, json_file):

        self.json_file = json_file

    # ======================================================

    def load(self):

        with open(

            self.json_file,

            "r",

            encoding="utf-8"

        ) as f:

            yosys = json.load(f)

        design = Design()

        modules = yosys.get(

            "modules",

            {}

        )

        for module_name, module_data in modules.items():

            module = Module(

                name=module_name

            )

            # ------------------------------------------
            # Ports
            # ------------------------------------------

            for pname, pdata in module_data.get(

                "ports",

                {}

            ).items():

                module.ports.append(

                    Port(

                        name=pname,

                        direction=pdata.get(

                            "direction",

                            "input"

                        ),

                        bits=pdata.get(

                            "bits",

                            []

                        )

                    )

                )

            # ------------------------------------------
            # Cells
            # ------------------------------------------

            for cname, cdata in module_data.get(

                "cells",

                {}

            ).items():

                module.cells.append(

                    Cell(

                        name=cname,

                        cell_type=cdata.get(

                            "type",

                            ""

                        ),

                        connections=cdata.get(

                            "connections",

                            {}

                        )

                    )

                )

            # ------------------------------------------
            # Nets
            # ------------------------------------------

            for nname, ndata in module_data.get(

                "netnames",

                {}

            ).items():

                module.nets.append(

                    Net(

                        name=nname,

                        bits=ndata.get(

                            "bits",

                            []

                        )

                    )

                )

            design.modules.append(

                module

            )

        if design.modules:

            design.top = design.modules[0].name

        return design