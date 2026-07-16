# ============================================================
# TIMING PLOTTER
# ============================================================

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import io
import base64


class TimingPlotter:

    def __init__(self, timing_paths):

        self.paths = timing_paths

    # ========================================================
    # EXTRACT CLEAN LABEL
    # ========================================================

    def _get_endpoint_label(self, endpoint, idx):

        endpoint = str(endpoint)

        # --------------------------------------------
        # YOSYS AUTO GENERATED ENDPOINTS
        # --------------------------------------------
        if ":" in endpoint:

            label = endpoint.split(":")[-1]

            if label.strip():

                return label

        # --------------------------------------------
        # FALLBACK
        # --------------------------------------------
        return endpoint

    # ========================================================
    # GENERATE SLACK BAR GRAPH
    # ========================================================

    def generate_slack_plot(self):

        if not self.paths:

            return ""

        # ====================================================
        # SORT BY WORST SLACK FIRST
        # ====================================================

        sorted_paths = sorted(

            self.paths,

            key=lambda x: x.get("slack", 0)
        )

        # ====================================================
        # SHOW ONLY WORST 50 PATHS
        # ====================================================

        MAX_PATHS = 50

        plot_paths = sorted_paths[:MAX_PATHS]

        labels = []
        slacks = []
        colors = []

        # ====================================================
        # BUILD GRAPH DATA
        # ====================================================

        for idx, path in enumerate(plot_paths):

            endpoint = path.get(

                "endpoint",

                f"Path_{idx + 1}"
            )

            slack = float(

                path.get(

                    "slack",

                    0
                )
            )

            label = self._get_endpoint_label(

                endpoint,

                idx
            )

            # ----------------------------------------
            # ENSURE UNIQUE LABELS
            # ----------------------------------------

            label = f"{label}_{idx+1}"

            labels.append(label)

            slacks.append(slack)

            # ----------------------------------------
            # COLOR CODING
            # ----------------------------------------

            if slack < 0:

                colors.append("red")

            elif slack < 2.0:

                colors.append("orange")

            else:

                colors.append("green")

        # ====================================================
        # FIGURE SIZE AUTO SCALE
        # ====================================================

        fig_width = max(

            12,

            len(labels) * 0.8
        )

        fig, ax = plt.subplots(

            figsize=(fig_width, 6)
        )

        bars = ax.bar(

            labels,

            slacks,

            color=colors
        )

        # ====================================================
        # ZERO SLACK REFERENCE LINE
        # ====================================================

        ax.axhline(

            y=0,

            linestyle="--",

            linewidth=1
        )
        
        
        # ====================================================
        # GRAPH TITLE
        # ====================================================

        total_paths = len(sorted_paths)

        if total_paths <= MAX_PATHS:

            title = f"Timing Slack Analysis ({total_paths} paths)"

        else:

            title = (
                f"Timing Slack Analysis "
                f"(Showing Worst {MAX_PATHS} of {total_paths} Paths)"
            )
        
        
        # ====================================================
        # TIMING LEGEND
        # ====================================================

        violations = sum(1 for s in slacks if s < 0)
        critical   = sum(1 for s in slacks if 0 <= s < 2)
        safe       = sum(1 for s in slacks if s >= 2)

        fig.text(

            0.5,

            0.89,

            f"Path Classification: Red = Violations | Orange = Critical | Green = Safe\n"
            f"Summary: {violations} Violating Paths | {critical} Critical Paths | {safe} Safe Paths",

            ha="center",

            fontsize=10,

            fontweight="bold",

            color="black"
        )

        # ====================================================
        # BAR VALUE LABELS
        # ====================================================

        for bar, slack in zip(

            bars,

            slacks
        ):

            ax.text(

                bar.get_x()
                + bar.get_width() / 2,

                bar.get_height(),

                f"{slack:.2f}",

                ha="center",

                va="bottom",

                fontsize=8
            )

        # ====================================================
        # GRAPH LABELS
        # ====================================================

        # ====================================================
        # GRAPH LABELS
        # ====================================================

        total_paths = len(sorted_paths)

        if total_paths <= MAX_PATHS:

            title = f"Timing Slack Analysis ({total_paths} paths)"

        else:

            title = (
                f"Timing Slack Analysis "
                f"({MAX_PATHS} out of {total_paths} paths)"
            )

        ax.set_title(

            title,

            fontsize=14,

            fontweight="bold"
        )

        ax.set_ylabel(

            "Timing Margin (ns)",
            
            fontweight="bold"
        )

        ax.set_xlabel(

            "critical paths",
            
            fontweight="bold"
        )

        plt.xticks(

            rotation=60,

            ha="right",
            
            fontsize=10,

            fontweight="bold", 
            
        )

        plt.tight_layout()

        # ====================================================
        # CONVERT TO BASE64
        # ====================================================

        buf = io.BytesIO()

        plt.savefig(

            buf,

            format="png",

            bbox_inches="tight"
        )

        buf.seek(0)

        image_base64 = base64.b64encode(

            buf.read()

        ).decode("utf-8")

        plt.close()

        return image_base64