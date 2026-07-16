from backend.semantic import *
from backend.semantic.index import CellIndex

db = SemanticDatabase()

db.add_cell(SemanticCell("U1","DFF"))
db.add_cell(SemanticCell("U2","ADD"))
db.add_cell(SemanticCell("U3","MUX"))
db.add_cell(SemanticCell("U4","RAM"))
db.add_cell(SemanticCell("U5","AND"))

idx = CellIndex()

idx.build(db.cells)

idx.summary()