# ============================================================
# ROUTING DENSITY
# ============================================================

import numpy as np

class RoutingDensity:

    def __init__(self):

        self.grid_size = 20

    def generate_density_map(self):

        density_map = np.random.randint(
            0,
            100,
            (self.grid_size, self.grid_size)
        )

        return density_map