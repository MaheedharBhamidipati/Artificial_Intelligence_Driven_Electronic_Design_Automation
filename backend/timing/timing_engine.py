# ================================================================
# TIMING ENGINE
# ================================================================

import re

from backend.timing.slack_estimator import (
    SlackEstimator
)

from backend.timing.path_visualizer import (
    TimingPathVisualizer
)


class TimingEngine:

    def __init__(

        self,

        paths=None
    ):

        # ========================================================
        # DEFAULT PATHS
        # ========================================================

        if paths is None:

            paths = []

        # ========================================================
        # STORE PATHS
        # ========================================================

        self.paths = paths

        # ========================================================
        # HELPERS
        # ========================================================

        self.visualizer = TimingPathVisualizer()

        self.slack_estimator = SlackEstimator()

    # ============================================================
    # PARSE TEMPUS REPORT
    # ============================================================

    def parse_tempus_report(

        self,

        report_text
    ):

        endpoint_match = re.search(

            r'Endpoint:\s+(.*)',

            report_text
        )

        slack_match = re.search(

            r'Slack Time\s+(-?\d+\.\d+)',

            report_text
        )

        arrival_match = re.search(

            r'Arrival Time\s+(-?\d+\.\d+)',

            report_text
        )

        path_group_match = re.search(

            r'Path Group:\s+\{(.*)\}',

            report_text
        )

        endpoint = (

            endpoint_match.group(1)

            if endpoint_match else "UNKNOWN"
        )

        slack = (

            float(slack_match.group(1))

            if slack_match else 0.0
        )

        arrival = (

            float(arrival_match.group(1))

            if arrival_match else 0.0
        )

        path_group = (

            path_group_match.group(1)

            if path_group_match else "default"
        )

        if "recovery" in report_text.lower():

            violation_type = "recovery"

        elif "hold" in report_text.lower():

            violation_type = "hold"

        else:

            violation_type = "setup"

        status = (

            "VIOLATION"

            if slack < 0

            else "SAFE"
        )

        parsed = {

            "source": "START",

            "destination": endpoint,

            "delay": arrival,

            "arrival_time": arrival,

            "slack": slack,

            "status": status,

            "path_group": path_group,

            "violation_type": violation_type
        }

        self.paths.append(parsed)

        self.visualizer.add_path(

            source="START",

            destination=endpoint,

            delay=arrival,

            slack=slack,

            status=status,

            path_type=violation_type
        )

        return parsed

    # ============================================================
    # GET WORST PATH
    # ============================================================

    def get_worst_path(self):

        if not self.paths:

            return None

        return min(

            self.paths,

            key=lambda x: x["slack"]
        )

    # ============================================================
    # ANALYZE TIMING
    # ============================================================

    def analyze_timing(self):

        return self.slack_estimator.analyze_paths(

            self.paths
        )

    # ============================================================
    # GENERATE SUMMARY
    # ============================================================

    def generate_summary(self):

        summary = {

            "total_paths": len(self.paths),

            "violations": 0,

            "safe_paths": 0,

            "critical_path": self.get_worst_path()
        }

        for path in self.paths:

            if path["slack"] < 0:

                summary["violations"] += 1

            else:

                summary["safe_paths"] += 1

        return summary

    # ============================================================
    # GET GRAPH DATA
    # ============================================================

    def get_graph_data(self):

        return self.visualizer.generate_graph_data()