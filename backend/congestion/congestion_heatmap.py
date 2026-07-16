# ============================================================
# CONGESTION HEATMAP
# ============================================================

import matplotlib.pyplot as plt

class CongestionHeatmap:

    def generate(self, hotspots):

        fig, ax = plt.subplots(figsize=(12, 8))

        for hotspot in hotspots:

            x = hotspot["x"]
            y = hotspot["y"]

            score = hotspot["congestion_score"]

            # ------------------------------------------------
            # COLOR SELECTION
            # ------------------------------------------------

            if score < 30:

                color = "green"

            elif score < 60:

                color = "yellow"

            elif score < 80:

                color = "orange"

            else:

                color = "red"

            # ------------------------------------------------
            # DRAW HOTSPOT
            # ------------------------------------------------

            rect = plt.Rectangle(

                (x, y),
                100,
                80,

                color=color,
                alpha=0.8
            )

            ax.add_patch(rect)

            ax.text(

                x + 10,
                y + 40,

                hotspot["net"],

                fontsize=7,
                color="white"
            )

        # ----------------------------------------------------
        # GRAPH SETTINGS
        # ----------------------------------------------------

        ax.set_xlim(0, 1400)
        ax.set_ylim(0, 1000)

        ax.set_title(

            "AIEDA Congestion Heatmap",

            fontsize=16
        )

        ax.set_facecolor("#101820")

        plt.grid(True)

        plt.show()