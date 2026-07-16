# ============================================================
# CONGESTION RENDERER
# ============================================================

import matplotlib.pyplot as plt

class CongestionRenderer:

    def render_overflows(self, overflow_regions):

        fig, ax = plt.subplots(figsize=(12, 8))

        for region in overflow_regions:

            rect = plt.Rectangle(

                (region["x"], region["y"]),

                100,

                80,

                color="red",

                alpha=0.9
            )

            ax.add_patch(rect)

            ax.text(

                region["x"] + 10,

                region["y"] + 40,

                region["net"],

                color="white",

                fontsize=8
            )

        ax.set_title(

            "AIDEA Overflow Regions",

            fontsize=16
        )

        ax.set_facecolor("#101820")

        plt.grid(True)

        plt.show()