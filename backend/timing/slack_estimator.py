# ================================================================
# SLACK ESTIMATOR
# ================================================================

DEFAULT_CLOCK_PERIOD = 10.0

DEFAULT_CLOCK_UNCERTAINTY = 0.2


class SlackEstimator:

    def __init__(

        self,

        clock_period=DEFAULT_CLOCK_PERIOD,

        clock_uncertainty=DEFAULT_CLOCK_UNCERTAINTY
    ):

        self.clock_period = clock_period

        self.clock_uncertainty = clock_uncertainty

    # ============================================================
    # SETUP SLACK
    # ============================================================

    def calculate_setup_slack(

        self,

        arrival_time,

        required_time=None
    ):

        if required_time is None:

            required_time = (

                self.clock_period
                - self.clock_uncertainty
            )

        slack = required_time - arrival_time

        return round(slack, 3)

    # ============================================================
    # HOLD SLACK
    # ============================================================

    def calculate_hold_slack(

        self,

        arrival_time,

        hold_requirement=0.1
    ):

        slack = arrival_time - hold_requirement

        return round(slack, 3)

    # ============================================================
    # CLASSIFY STATUS
    # ============================================================

    def classify_status(

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
    # ANALYZE PATHS
    # ============================================================

    def analyze_paths(

        self,

        timing_paths,

        analysis_type="setup"
    ):

        report = []

        for path in timing_paths:

            arrival = path.get(

                "arrival_time",

                path.get("delay", 0)
            )

            if analysis_type == "hold":

                slack = self.calculate_hold_slack(

                    arrival
                )

            else:

                slack = self.calculate_setup_slack(

                    arrival
                )

            status = self.classify_status(

                slack
            )

            report.append({

                "source": path.get("source"),

                "destination": path.get("destination"),

                "arrival_time": arrival,

                "slack": slack,

                "status": status,

                "violation_type": analysis_type
            })

        return report