import math
from backend.schematic.symbol_library import gate_dimensions


class LayoutEngine:

    def __init__(self):
        self.x_spacing = 250
        self.y_spacing = 140
        self.max_per_column = 5

    def generate_layout(self, gates):

        positioned = []

        for idx, gate in enumerate(gates):

            col = idx // self.max_per_column
            row = idx % self.max_per_column

            x = 200 + col * self.x_spacing
            y = 100 + row * self.y_spacing

            w, h = gate_dimensions(gate["gate_type"])

            gate["x"] = x
            gate["y"] = y
            gate["width"] = w
            gate["height"] = h

            positioned.append(gate)

        return positioned
