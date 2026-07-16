from backend.floorplanning import FloorplanEngine

cells=[

    {"name":"g1","type":"$_AND_"},

    {"name":"g2","type":"$_OR_"},

    {"name":"g3","type":"$_XOR_"},

    {"name":"g4","type":"$_DFF_P_"},

    {"name":"g5","type":"$_MUX_"},

    {"name":"g6","type":"RAM"}

]

engine=FloorplanEngine(cells)

result=engine.run()

print()

print("Floorplanning Successful")

print(result.output_png)

print(result.output_json)

print(result.utilization)