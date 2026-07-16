import json

# =====================================================
# LOAD JSON NETLIST
# =====================================================

def load_netlist(json_file):

    with open(json_file, "r") as f:

        data = json.load(f)

    return data

# =====================================================
# FORMAT BUS NAME
# =====================================================

def format_bus_name(name, width):

    name = str(name)

    # =================================================
    # SCALAR SIGNAL
    # =================================================

    if width <= 1:

        return name

    # =================================================
    # INTERNAL YOSYS SIGNAL
    # =================================================

    if name.startswith("$"):

        return name

    # =================================================
    # ALREADY VECTOR
    # =================================================

    if "[" in name:

        return name

    # =================================================
    # VECTOR FORMAT
    # =================================================

    return f"{name}[{width-1}:0]"

# =====================================================
# EXTRACT CELLS + NET MAP + PORTS
# =====================================================

def extract_cells(netlist, top_module):

    # =================================================
    # GET MODULE
    # =================================================

    module = netlist["modules"][top_module]

    # =================================================
    # EXTRACT CELLS
    # =================================================

    cells = []

    for cell_name, cell_data in module[
        "cells"
    ].items():

        cells.append({

            "name": cell_name,

            "type": cell_data.get(
                "type",
                "UNKNOWN"
            ),

            "connections": cell_data.get(
                "connections",
                {}
            )
        })

    # =================================================
    # CREATE NET MAP
    # =================================================

    net_map = {}

    for net_name, net_data in module.get(
        "netnames",
        {}
    ).items():

        bits = net_data.get(
            "bits",
            []
        )

        # =================================================
        # VECTOR NETS
        # =================================================

        if len(bits) > 1:

            vector_name = format_bus_name(

                net_name,

                len(bits)
            )

            for idx, bit in enumerate(bits):

                net_map[
                    str(bit)
                ] = vector_name

        # =================================================
        # SCALAR NETS
        # =================================================

        else:

            for bit in bits:

                net_map[
                    str(bit)
                ] = net_name

    # =================================================
    # EXTRACT INPUTS / OUTPUTS
    # =================================================

    inputs = []
    outputs = []

    ports = module.get(
        "ports",
        {}
    )

    for port_name, port_data in ports.items():

        direction = port_data.get(
            "direction",
            ""
        )

        bits = port_data.get(
            "bits",
            []
        )

        width = len(bits)

        # =================================================
        # DISPLAY NAME
        # =================================================

        display_name = format_bus_name(

            port_name,

            width
        )

        # =================================================
        # PORT INFO
        # =================================================

        port_info = {

            # VECTOR DISPLAY NAME
            "name": display_name,

            # ORIGINAL RAW NAME
            "raw_name": port_name,

            # VECTOR WIDTH
            "width": width,

            # DISPLAY LABEL
            "label": display_name
        }

        # =============================================
        # INPUTS
        # =============================================

        if direction == "input":

            inputs.append(
                port_info
            )

        # =============================================
        # OUTPUTS
        # =============================================

        elif direction == "output":

            outputs.append(
                port_info
            )

    # =================================================
    # RETURN EVERYTHING
    # =================================================

    return (

        cells,

        net_map,

        inputs,

        outputs
    )