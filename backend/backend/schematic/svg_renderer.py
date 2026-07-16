import svgwrite

from backend.schematic.color_config import (
    BLOCK_COLOR,
    WIRE_COLOR,
    TEXT_COLOR,
    BACKGROUND_COLOR
)


class SVGRenderer:

    def __init__(self, filename="D:/AI_EDA_TOOL/static/schematic.svg"):

        self.filename = filename

        self.dwg = svgwrite.Drawing(
            filename,
            size=("1600px", "1200px")
        )

        self.dwg.add(
            self.dwg.rect(
                insert=(0, 0),
                size=("100%", "100%"),
                fill=BACKGROUND_COLOR
            )
        )

    def draw_gate(self, gate):

        x = gate["x"]
        y = gate["y"]

        rect = self.dwg.rect(
            insert=(x, y),
            size=(80, 40),
            fill=BLOCK_COLOR,
            stroke="black",
            stroke_width=2,
            rx=10,
            ry=10
        )

        self.dwg.add(rect)

        self.dwg.add(
            self.dwg.text(
                gate["gate_type"],
                insert=(x + 12, y + 25),
                fill=TEXT_COLOR,
                font_size="14px"
            )
        )

    def draw_wires(self, wires):

        for wire in wires:

            self.dwg.add(
                self.dwg.line(
                    start=(wire["x1"], wire["y1"]),
                    end=(wire["x2"], wire["y2"]),
                    stroke=WIRE_COLOR,
                    stroke_width=3
                )
            )

            self.dwg.add(
                self.dwg.text(
                    wire["signal"],
                    insert=(wire["x1"] - 25, wire["y1"] - 5),
                    fill=TEXT_COLOR,
                    font_size="12px"
                )
            )

    def save(self):

        self.dwg.save()

        print(f"SVG schematic generated -> {self.filename}")
