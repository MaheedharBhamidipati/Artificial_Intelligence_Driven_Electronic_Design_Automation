from backend.semantic import *

from backend.semantic.passes import *

db = SemanticDatabase()

db.add_cell(

    SemanticCell(

        "state_reg",

        "DFF"

    )

)

db.add_cell(

    SemanticCell(

        "pipe0",

        "DFF"

    )

)

db.add_cell(

    SemanticCell(

        "shift0",

        "DFF"

    )

)

RegisterPass(

    db

).run()

RegisterPass(

    db

).summary()