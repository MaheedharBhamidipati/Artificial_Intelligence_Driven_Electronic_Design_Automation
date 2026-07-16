# ================================================================
# TIMING REPORT PARSER
# ================================================================

import re


class TimingReportParser:

    def __init__(self):

        self.paths = []

    # ============================================================
    # PARSE TEMPUS REPORT
    # ============================================================

    def parse_tempus_report(

        self,

        report_text
    ):

        parsed = {}

        endpoint_match = re.search(

            r'Endpoint:\s+(.*)',

            report_text
        )

        startpoint_match = re.search(

            r'Startpoint:\s+(.*)',

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

        required_match = re.search(

            r'Required Time\s+(-?\d+\.\d+)',

            report_text
        )

        path_group_match = re.search(

            r'Path Group:\s+\{(.*)\}',

            report_text
        )

        parsed["startpoint"] = (

            startpoint_match.group(1)

            if startpoint_match else "UNKNOWN"
        )

        parsed["endpoint"] = (

            endpoint_match.group(1)

            if endpoint_match else "UNKNOWN"
        )

        parsed["slack"] = (

            float(slack_match.group(1))

            if slack_match else 0.0
        )

        parsed["arrival_time"] = (

            float(arrival_match.group(1))

            if arrival_match else 0.0
        )

        parsed["required_time"] = (

            float(required_match.group(1))

            if required_match else 0.0
        )

        parsed["path_group"] = (

            path_group_match.group(1)

            if path_group_match else "default"
        )

        report_lower = report_text.lower()

        if "recovery" in report_lower:

            parsed["violation_type"] = "recovery"

        elif "hold" in report_lower:

            parsed["violation_type"] = "hold"

        elif "removal" in report_lower:

            parsed["violation_type"] = "removal"

        else:

            parsed["violation_type"] = "setup"

        parsed["status"] = (

            "VIOLATION"

            if parsed["slack"] < 0

            else "SAFE"
        )

        self.paths.append(parsed)

        return parsed

    # ============================================================
    # GET ALL PATHS
    # ============================================================

    def get_paths(self):

        return self.paths

    # ============================================================
    # CLEAR PATHS
    # ============================================================

    def clear(self):

        self.paths = []