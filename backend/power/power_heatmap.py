# ============================================================
# POWER HEATMAP
# ============================================================

import numpy as np
import matplotlib.pyplot as plt

class PowerHeatmap:

    def generate_heatmap(self):

        grid = np.random.rand(20, 20)

        plt.figure(figsize=(10, 8))

        plt.imshow(
            grid,
            cmap='hot',
            interpolation='nearest'
        )

        plt.colorbar(label="Power Density")

        plt.title("AIDEA Power Heatmap")

        plt.xlabel("X Grid")

        plt.ylabel("Y Grid")

        plt.show()