def build_netlist(elaborated):
    """
    Build netlist connectivity database.
    """
    netlist = {
        "instances": [],
        "nets": {}
    }

    for inst in elaborated["instances"]:
        netlist["instances"].append({
            "name": inst["path"],
            "type": inst["type"]
        })

        for port, signal in inst["connections"].items():
            if signal not in netlist["nets"]:
                netlist["nets"][signal] = {
                    "drivers": [],
                    "loads": []
                }

            # Heuristic: output-like port names treated as drivers
            if port.lower().startswith(("out", "q", "y", "z")):
                netlist["nets"][signal]["drivers"].append(
                    f"{inst['path']}.{port}"
                )
            else:
                netlist["nets"][signal]["loads"].append(
                    f"{inst['path']}.{port}"
                )

    return netlist
