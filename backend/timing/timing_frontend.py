# ================================================================
# TIMING FRONTEND
# ================================================================

import json


# ================================================================
# GENERATE TIMING PANEL
# ================================================================

def generate_timing_panel(timing_result):

    timing_rows = ""

    for path in timing_result.get(
        "critical_paths",
        []
    ):

        slack = path.get("slack", 0)

        status = path.get(
            "status",
            "SAFE"
        )

        color = "#16a34a"

        if status == "CRITICAL":

            color = "#f59e0b"

        elif status == "VIOLATION":

            color = "#dc2626"

        timing_rows += f"""

        <tr>

            <td>
                {path.get("endpoint")}
            </td>

            <td>
                {path.get("delay")}
            </td>

            <td>
                {slack}
            </td>

            <td style="
                color:{color};
                font-weight:700;
            ">

                {status}

            </td>

        </tr>
        """

    dashboard = timing_result.get(
        "dashboard",
        {}
    )

    # ============================================================
    # AI SUMMARY
    # ============================================================

    dashboard = timing_result.get(
        "dashboard",
        {}
    )

    worst_slack = dashboard.get(
        "worst_slack",
        0
    )

    violations = dashboard.get(
        "violations",
        0
    )

    total_paths = dashboard.get(
        "total_paths",
        0
    )

    if violations > 0:

        ai_summary = f"""

        Timing analysis detected
        <b>{violations}</b> violating paths
        out of <b>{total_paths}</b> total paths.

        The design shows timing pressure near
        critical combinational regions with
        worst slack reaching
        <b>{worst_slack} ns</b>.

        Recommended optimizations include
        logic balancing, pipelining,
        reducing combinational depth,
        and improving timing closure.

        """

    else:

        ai_summary = f"""

        Timing analysis completed successfully
        with no timing violations detected.

        The current design meets estimated
        timing requirements with a
        worst slack of
        <b>{worst_slack} ns</b>.

        Minor optimizations may still improve
        performance and routing efficiency.

        """

    ai_html = f"""

    <div class='overview-card'>

        <h3>

            AI Timing Insight

        </h3>

        <p style="
            line-height:1.8;
            font-size:15px;
        ">

            {ai_summary}

        </p>

    </div>

    """

    return f"""

    <div id='timing'
        class='panel'>

        <h2>

            Timing Analysis

        </h2>

        <!-- DASHBOARD -->

        <div class='metrics'>

            <div class='metric-card'>

                <div class='metric-title'>

                    Total Paths

                </div>

                <div class='metric-value'>

                    {dashboard.get("total_paths",0)}

                </div>

            </div>

            <div class='metric-card'>

                <div class='metric-title'>

                    Violations

                </div>

                <div class='metric-value'>

                    {dashboard.get("violations",0)}

                </div>

            </div>

            <div class='metric-card'>

                <div class='metric-title'>

                    Worst Slack

                </div>

                <div class='metric-value'>

                    {dashboard.get("worst_slack",0)} ns

                </div>

            </div>

        </div>

        <!-- TABLE -->

        <table class='io-table'>

            <thead>

                <tr>

                    <th>Path</th>

                    <th>Delay</th>

                    <th>Slack</th>

                    <th>Status</th>

                </tr>

            </thead>

            <tbody>

                {timing_rows}

            </tbody>

        </table>

        <!-- GRAPH -->

        <div class='overview-card'>

            <h3>

                Timing Graph Data

            </h3>
            
            <div class='overview-card'>

                <h3>

                    Timing Visualization

                </h3>

                <img
                    src="data:image/png;base64,
                    {timing_result.get('timing_plot','')}"
                    style="
                        width:100%;
                        border-radius:12px;
                    "
                >

            </div>



        </div>

        <!-- AI -->

        {ai_html}

    </div>
    """