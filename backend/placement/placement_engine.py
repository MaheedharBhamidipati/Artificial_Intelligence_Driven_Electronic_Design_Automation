# ============================================================
# PLACEMENT ENGINE
# ============================================================

from backend.placement.utils import (
    extract_cell_type
)

from backend.placement.cell_library import (
    CELL_TYPES
)


class PlacementEngine:

    def __init__(self, cells):

        self.cells = cells

        self.canvas_width = 1600
        self.canvas_height = 900

        self.start_x = 80
        self.start_y = 80

        self.x_spacing = 220
        self.y_spacing = 180

    # ============================================================
    # MAIN ENGINE
    # ============================================================

    def run(self):

        blocks = []

        # ========================================================
        # GRID CONFIGURATION
        # ========================================================

        GRID_COLUMNS = 12

        START_X = 80
        START_Y = 80

        X_SPACING = 120
        Y_SPACING = 120

        current_col = 0
        current_row = 0

        total_area = 0

        # ========================================================
        # CELL PLACEMENT
        # ========================================================

        for index, cell in enumerate(self.cells):

            cell_name = cell.get(
                "name",
                "UNKNOWN"
            )

            cell_type = extract_cell_type(
                cell_name
            )

            properties = CELL_TYPES.get(

                cell_type,

                {
                    "width": 1,
                    "height": 1,
                    "color": "gray"
                }
            )

            # ====================================================
            # SMALLER CELL SIZES
            # ====================================================

            block_width = properties["width"] * 60
            block_height = properties["height"] * 40

            color = properties["color"]

            # ====================================================
            # GRID POSITIONING
            # ====================================================

            x = START_X + (
                current_col * X_SPACING
            )

            y = START_Y + (
                current_row * Y_SPACING
            )

            blocks.append({

                "name": cell_name,

                "type": cell_type,

                "x": x,
                "y": y,

                "w": block_width,
                "h": block_height,

                "color": color,

                "center_x":
                    x + block_width / 2,

                "center_y":
                    y + block_height / 2
            })

            total_area += (
                block_width *
                block_height
            )

            # ====================================================
            # MOVE GRID
            # ====================================================

            current_col += 1

            if current_col >= GRID_COLUMNS:

                current_col = 0

                current_row += 1

        # ========================================================
        # CHIP AREA
        # ========================================================

        canvas_width = 1800

        canvas_height = max(

            1000,

            (current_row + 2) * Y_SPACING
        )

        chip_area = (
            canvas_width *
            canvas_height
        )

        utilization = round(

            (total_area / chip_area) * 100,

            2
        )

        # ========================================================
        # RETURN
        # ========================================================

        return {

            "blocks": blocks,

            "canvas": {

                "width": canvas_width,

                "height": canvas_height
            },

            "statistics": {

                "total_cells":
                    len(blocks),

                "utilization":
                    f"{utilization}%",

                "total_area":
                    total_area
            }
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample_cells = [

        {"name": "INPUT"},
        {"name": "ADD_1"},
        {"name": "FF_2"},
        {"name": "MUX_3"},
        {"name": "MUL_4"},
        {"name": "MUL_5"},
        {"name": "FF_6"},
        {"name": "FF_7"},
        {"name": "FF_8"},
        {"name": "OUTPUT"}
    ]

    engine = PlacementEngine(sample_cells)

    results = engine.run()

    print("\n")
    print("======================================")
    print(" AIEDA Placement Engine")
    print("======================================\n")

    for block in results["blocks"]:

        print(block)

    print("\n")
    print(results["statistics"])