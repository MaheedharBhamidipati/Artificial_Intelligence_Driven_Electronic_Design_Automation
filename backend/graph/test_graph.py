from backend.core.design_builder import build_design

from backend.yosys_engine.netlist_parser import load_netlist

from backend.graph.connectivity_engine import (
    ConnectivityEngine
)

import os


paths = [

    "static/generated/netlists/design.json",

    "static/generated/netlists/netlist.json"

]


json_file = None

for p in paths:

    if os.path.exists(p):

        json_file = p

        break

if json_file is None:

    raise FileNotFoundError

netlist = load_netlist(

    json_file

)

design = build_design(

    netlist

)

engine = ConnectivityEngine(

    design

)

result = engine.run()

print()

print(result["metrics"])