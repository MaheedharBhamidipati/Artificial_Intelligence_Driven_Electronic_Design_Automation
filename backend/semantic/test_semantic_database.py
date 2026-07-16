from backend.semantic import *

db = SemanticDatabase()

db.design_name = "AIDEA Demo"

db.top_module = "fsm"

db.logic_type = "FSM"

db.add_input(

    Port(

        "clk",

        "input"

    )

)

db.add_input(

    Port(

        "rst",

        "input"

    )

)

db.add_output(

    Port(

        "z",

        "output"

    )

)

db.update_metrics()

db.summary()

print()

print(db)

print()

print(db.to_dict())