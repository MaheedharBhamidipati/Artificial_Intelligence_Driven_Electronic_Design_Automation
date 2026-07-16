# ================================================================
# TIMING DASHBOARD GENERATOR
# ================================================================


class TimingDashboardGenerator:

    def __init__(

        self,

        timing_reports
    ):

        self.reports = timing_reports

    # ============================================================
    # GENERATE DASHBOARD
    # ============================================================

    def generate_dashboard(self):

        dashboard = {

            "total_paths": len(self.reports),

            "setup": 0,

            "hold": 0,

            "recovery": 0,

            "removal": 0,

            "violations": 0,

            "worst_slack": 0.0
        }

        worst_slack = 9999

        for report in self.reports:

            violation_type = report.get(

                "violation_type",

                "setup"
            )

            slack = report.get(

                "slack",

                0.0
            )

            dashboard[violation_type] += 1

            if slack < 0:

                dashboard["violations"] += 1

            if slack < worst_slack:

                worst_slack = slack

        dashboard["worst_slack"] = worst_slack

        return dashboard