from backend.semantic import *
from backend.semantic.index import CellIndex
from backend.semantic.passes import FSMPass

db = SemanticDatabase()

db.logic_type = "FSM"

db.add_cell(SemanticCell("state_reg0", "DFF"))
db.add_cell(SemanticCell("state_reg1", "DFF"))
db.add_cell(SemanticCell("next_state_logic", "AND"))
db.add_cell(SemanticCell("output_logic", "OR"))

db.index = CellIndex()
db.index.build(db.cells)

fsm = FSMPass(db)
fsm.run()
fsm.summary()