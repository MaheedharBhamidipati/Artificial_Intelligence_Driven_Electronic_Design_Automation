# ================================================================
# VIOLATION CLASSIFIER
# ================================================================


class ViolationClassifier:

    def __init__(self):

        self.violations = []

    # ============================================================
    # CLASSIFY SLACK
    # ============================================================

    def classify_slack(

        self,

        slack
    ):

        if slack < 0:

            return "VIOLATION"

        elif slack < 0.5:

            return "CRITICAL"

        else:

            return "SAFE"

    # ============================================================
    # DETECT VIOLATION TYPE
    # ============================================================

    def detect_violation_type(

        self,

        report_text
    ):

        report_text = report_text.lower()

        if "recovery" in report_text:

            return "recovery"

        elif "hold" in report_text:

            return "hold"

        elif "removal" in report_text:

            return "removal"

        elif "clock gating" in report_text:

            return "clock_gating"

        elif "cdc" in report_text:

            return "cdc"

        else:

            return "setup"

    # ============================================================
    # ANALYZE REPORT
    # ============================================================

    def analyze_report(

        self,

        report_data
    ):

        slack = report_data.get(

            "slack",

            0.0
        )

        status = self.classify_slack(

            slack
        )

        report_data["status"] = status

        self.violations.append(

            report_data
        )

        return report_data

    # ============================================================
    # GET VIOLATIONS
    # ============================================================

    def get_violations(self):

        return [

            v for v in self.violations

            if v["status"] == "VIOLATION"
        ]

    # ============================================================
    # SUMMARY
    # ============================================================

    def generate_summary(self):

        summary = {

            "total": len(self.violations),

            "violations": 0,

            "critical": 0,

            "safe": 0
        }

        for item in self.violations:

            status = item["status"]

            if status == "VIOLATION":

                summary["violations"] += 1

            elif status == "CRITICAL":

                summary["critical"] += 1

            else:

                summary["safe"] += 1

        return summary