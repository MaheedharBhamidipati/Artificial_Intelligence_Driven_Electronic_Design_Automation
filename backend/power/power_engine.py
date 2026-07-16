# ============================================================
# POWER ENGINE
# ============================================================

import random

# ============================================================
# POWER ENGINE CLASS
# ============================================================

class PowerEngine:

    def __init__(self, cells):

        self.cells = cells

        # --------------------------------------------
        # TECHNOLOGY PARAMETERS
        # --------------------------------------------

        self.voltage = 1.0          # Volts
        self.frequency = 100e6      # 100 MHz

    # ========================================================
    # DYNAMIC POWER CALCULATION
    # ========================================================

    def calculate_dynamic_power(self, activity, capacitance):

        dynamic_power = (
            activity *
            capacitance *
            (self.voltage ** 2) *
            self.frequency
        )

        return dynamic_power

    # ========================================================
    # LEAKAGE POWER CALCULATION
    # ========================================================

    def calculate_leakage_power(self, leakage_current):

        leakage_power = leakage_current * self.voltage

        return leakage_power

    # ========================================================
    # MAIN ANALYSIS
    # ========================================================

    def analyze(self):

        total_dynamic = 0
        total_leakage = 0

        cell_power_map = []

        # ----------------------------------------------------
        # CELL-BY-CELL ANALYSIS
        # ----------------------------------------------------

        for index, cell in enumerate(self.cells):

            # --------------------------------------------
            # RANDOMIZED ACTIVITY FACTOR
            # --------------------------------------------

            activity = random.uniform(0.1, 0.9)

            # --------------------------------------------
            # RANDOMIZED CAPACITANCE
            # --------------------------------------------

            capacitance = random.uniform(1e-12, 5e-12)

            # --------------------------------------------
            # RANDOMIZED LEAKAGE CURRENT
            # --------------------------------------------

            leakage_current = random.uniform(1e-6, 5e-6)

            # --------------------------------------------
            # POWER CALCULATIONS
            # --------------------------------------------

            dynamic = self.calculate_dynamic_power(
                activity,
                capacitance
            )

            leakage = self.calculate_leakage_power(
                leakage_current
            )

            total = dynamic + leakage

            total_dynamic += dynamic
            total_leakage += leakage

            # --------------------------------------------
            # STORE CELL POWER DATA
            # --------------------------------------------

            cell_power_map.append({

                "cell_id": f"CELL_{index}",

                "dynamic_power": dynamic,

                "leakage_power": leakage,

                "total_power": total
            })

        # ----------------------------------------------------
        # FINAL TOTALS
        # ----------------------------------------------------

        total_power = total_dynamic + total_leakage

        return {

            "dynamic_power":
                f"{total_dynamic * 1000:.2f} mW",

            "leakage_power":
                f"{total_leakage * 1000:.2f} mW",

            "total_power":
                f"{total_power * 1000:.2f} mW",

            "cell_power_map":
                cell_power_map
        }