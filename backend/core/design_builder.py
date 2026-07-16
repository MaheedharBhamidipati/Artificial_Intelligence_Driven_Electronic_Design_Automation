"""
============================================================

AIDEA Design Builder

Converts Yosys JSON into the AIDEA Design Database.

============================================================
"""

from backend.core.database import (
    Design,
    Module,
    Cell,
    Net,
    Port,
)


def build_design(netlist: dict) -> Design:

    design = Design()

    modules = netlist.get("modules", {})

    if not modules:
        return design

    for module_name, module_data in modules.items():

        module = Module(name=module_name)

        # -------------------------
        # Ports
        # -------------------------
        for pname, pdata in module_data.get("ports", {}).items():

            module.ports.append(
                Port(
                    name=pname,
                    direction=pdata.get("direction", ""),
                    bits=pdata.get("bits", []),
                )
            )

        # -------------------------
        # Cells
        # -------------------------
        for cname, cdata in module_data.get("cells", {}).items():

            module.cells.append(
                Cell(
                    name=cname,
                    cell_type=cdata.get("type", ""),
                    connections=cdata.get("connections", {}),
                    attributes=cdata.get("attributes", {}),
                )
            )

        # -------------------------
        # Nets
        # -------------------------
        for nname, ndata in module_data.get("netnames", {}).items():

            module.nets.append(
                Net(
                    name=nname,
                    bits=ndata.get("bits", []),
                )
            )

        design.modules.append(module)

    design.top = design.modules[0].name

    design.metadata["module_count"] = len(design.modules)
    design.metadata["cell_count"] = sum(len(m.cells) for m in design.modules)
    design.metadata["net_count"] = sum(len(m.nets) for m in design.modules)
    design.metadata["port_count"] = sum(len(m.ports) for m in design.modules)

    return design