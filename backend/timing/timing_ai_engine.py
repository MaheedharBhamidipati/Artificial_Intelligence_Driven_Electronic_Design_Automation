# ================================================================
# TIMING AI ENGINE
# ================================================================


class TimingAIEngine:

    def __init__(self):

        pass

    # ============================================================
    # GENERATE FIX SUGGESTIONS
    # ============================================================

    def generate_fix_suggestions(

        self,

        timing_data
    ):

        violation_type = timing_data.get(

            "violation_type",

            "setup"
        )

        slack = timing_data.get(

            "slack",

            0.0
        )

        suggestions = []

        # ========================================================
        # SETUP
        # ========================================================

        if violation_type == "setup":

            suggestions.extend([

                "Reduce combinational logic depth",

                "Add pipeline stages",

                "Optimize critical path",

                "Increase clock period"
            ])

        # ========================================================
        # HOLD
        # ========================================================

        elif violation_type == "hold":

            suggestions.extend([

                "Add delay buffers",

                "Reduce clock skew",

                "Adjust routing delays"
            ])

        # ========================================================
        # RECOVERY
        # ========================================================

        elif violation_type == "recovery":

            suggestions.extend([

                "Add reset synchronizer",

                "Convert async reset to sync reset",

                "Add false path if intentional"
            ])

        # ========================================================
        # REMOVAL
        # ========================================================

        elif violation_type == "removal":

            suggestions.extend([

                "Synchronize reset deassertion",

                "Review asynchronous control logic"
            ])

        # ========================================================
        # CRITICAL SLACK
        # ========================================================

        if slack < -1.0:

            suggestions.append(

                "Severe timing violation detected"
            )

        return suggestions

    # ============================================================
    # GENERATE EXPLANATION
    # ============================================================

    def generate_explanation(

        self,

        timing_data
    ):

        violation = timing_data.get(

            "violation_type",

            "setup"
        )

        slack = timing_data.get(

            "slack",

            0.0
        )

        endpoint = timing_data.get(

            "endpoint",

            "UNKNOWN"
        )

        explanation = (

            f'{violation.upper()} violation detected '
            f'at endpoint {endpoint}. '
            f'Slack = {slack} ns.'
        )

        return explanation

    # ============================================================
    # COMPLETE AI ANALYSIS
    # ============================================================

    def analyze(

        self,

        timing_data
    ):

        return {

            "explanation": self.generate_explanation(

                timing_data
            ),

            "suggestions": self.generate_fix_suggestions(

                timing_data
            )
        }