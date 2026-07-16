# ============================================================
# POWER ESTIMATOR
# ============================================================

import random

class PowerEstimator:

    def __init__(self):

        self.voltage = 1.0
        self.frequency = 100e6

    # --------------------------------------------------------
    # DYNAMIC POWER
    # --------------------------------------------------------

    def calculate_dynamic_power(self, activity, capacitance):

        return activity * capacitance * (self.voltage ** 2) * self.frequency

    # --------------------------------------------------------
    # LEAKAGE POWER
    # --------------------------------------------------------

    def calculate_leakage_power(self, leakage_current):

        return leakage_current * self.voltage

    # --------------------------------------------------------
    # TOTAL POWER
    # --------------------------------------------------------

    def calculate_total_power(self, cells):

        total_dynamic = 0
        total_leakage = 0

        for cell in cells:

            activity = random.uniform(0.1, 0.9)
            capacitance = random.uniform(1e-12, 5e-12)
            leakage = random.uniform(1e-6, 5e-6)

            dynamic = self.calculate_dynamic_power(
                activity,
                capacitance
            )

            leakage_power = self.calculate_leakage_power(
                leakage
            )

            total_dynamic += dynamic
            total_leakage += leakage_power

        return {
            "dynamic_power": total_dynamic,
            "leakage_power": total_leakage,
            "total_power": total_dynamic + total_leakage
        }