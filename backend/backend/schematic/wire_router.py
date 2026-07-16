class WireRouter:

    def __init__(self):
        pass

    def generate_wires(self, gates):

        wires = []

        for gate in gates:

            gx = gate["x"]
            gy = gate["y"]

            # -------------------------------
            # INPUT WIRES
            # -------------------------------
            for idx, inp in enumerate(gate["inputs"]):

                wires.append({
                    "signal": inp,
                    "x1": gx - 100,
                    "y1": gy + 10 + (idx * 15),
                    "x2": gx,
                    "y2": gy + 10 + (idx * 15)
                })

            # -------------------------------
            # OUTPUT WIRE
            # -------------------------------
            wires.append({
                "signal": gate["output"],
                "x1": gx + 80,
                "y1": gy + 20,
                "x2": gx + 180,
                "y2": gy + 20
            })

        return wires
