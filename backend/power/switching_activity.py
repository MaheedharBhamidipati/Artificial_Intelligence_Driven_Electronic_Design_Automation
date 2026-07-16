# ============================================================
# SWITCHING ACTIVITY ENGINE
# ============================================================

import random

class SwitchingActivity:

    def __init__(self):

        self.default_toggle_rate = 0.5

    # --------------------------------------------------------
    # GENERATE ACTIVITY
    # --------------------------------------------------------

    def generate_activity(self, cells):

        activity_data = []

        for cell in cells:

            toggle_rate = round(

                random.uniform(0.1, 1.0),

                2
            )

            activity_factor = round(

                toggle_rate * self.default_toggle_rate,

                2
            )

            activity_data.append({

                "cell": str(cell),

                "toggle_rate": toggle_rate,

                "activity_factor": activity_factor
            })

        return activity_data