# ================================================================
# TIMING PATH TRAVERSER
# ================================================================

import random
from collections import defaultdict


class TimingPathTraverser:

    def __init__(

        self,

        cells,

        net_map
    ):

        self.cells = cells

        self.net_map = net_map

        self.graph = defaultdict(list)

        self.cell_lookup = {}

        self.paths = []

    # ============================================================
    # BUILD CONNECTIVITY GRAPH
    # ============================================================

    def build_graph(self):

        signal_drivers = {}

        signal_receivers = defaultdict(list)

        # ========================================================
        # PASS 1 : BUILD DRIVER / RECEIVER DATABASE
        # ========================================================

        for cell in self.cells:

            cell_name = cell.get(
                "name",
                "UNKNOWN"
            )

            # ========================================================
            # CLEAN ABC NAMES
            # ========================================================

            if "$abc$" in cell_name:

                cell_name = f"CELL_{len(self.cell_lookup)}"

            self.cell_lookup[cell_name] = cell

            connections = cell.get(

                "connections",

                {}
            )

            for port, signals in connections.items():

                if not isinstance(signals, list):

                    signals = [signals]

                for sig in signals:

                    sig = str(sig)

                    signal_name = self.net_map.get(

                        sig,

                        sig
                    )

                    # ====================================================
                    # OUTPUT PORTS
                    # ====================================================

                    if port.upper() in [

                        "Y",
                        "Q",
                        "OUT",
                        "QN",
                        "SUM",
                        "COUT",
                        "Z"
                    ]:

                        signal_drivers[
                            signal_name
                        ] = cell_name

                    # ====================================================
                    # INPUT PORTS
                    # ====================================================

                    else:

                        signal_receivers[
                            signal_name
                        ].append(cell_name)

        # ========================================================
        # PASS 2 : BUILD CELL GRAPH
        # ========================================================

        for signal, driver in signal_drivers.items():

            receivers = signal_receivers.get(

                signal,

                []
            )

            for recv in receivers:

                self.graph[driver].append(recv)

    # ============================================================
    # ESTIMATE CELL DELAY
    # ============================================================

    def estimate_cell_delay(

        self,

        cell
    ):

        connections = cell.get(

            "connections",

            {}
        )

        base_delay = (

            len(connections)
            * 0.25
        )

        random_factor = random.uniform(

            0.8,

            1.8
        )

        delay = round(

            base_delay * random_factor,

            2
        )

        return max(delay, 0.1)

    # ============================================================
    # DFS TRAVERSAL
    # ============================================================

    def dfs(

        self,

        current,

        visited,

        path,

        total_delay
    ):

        visited.add(current)

        path.append(current)

        current_cell = self.cell_lookup.get(

            current,

            {}
        )

        total_delay += self.estimate_cell_delay(

            current_cell
        )

        neighbors = self.graph.get(

            current,

            []
        )

        # ========================================================
        # ENDPOINT
        # ========================================================

        if len(neighbors) == 0:

            clock_period = 5.0

            slack = round(

                clock_period - total_delay,

                2
            )

            self.paths.append({

                "startpoint": path[0],

                "endpoint": path[-1],

                "path": list(path),

                "delay": round(total_delay, 2),

                "arrival_time": round(total_delay, 2),

                "required_time": clock_period,

                "slack": slack,

                "status": (

                    "SAFE"
                    if slack >= 0
                    else "VIOLATION"
                ),

                "violation_type": "setup"
            })

        # ========================================================
        # CONTINUE DFS
        # ========================================================

        else:

            for neighbor in neighbors:

                if neighbor not in visited:

                    self.dfs(

                        neighbor,

                        visited.copy(),

                        list(path),

                        total_delay
                    )

    # ============================================================
    # FIND ALL PATHS
    # ============================================================

    def find_paths(self):

        self.build_graph()

        all_destinations = set()

        for src in self.graph:

            for dst in self.graph[src]:

                all_destinations.add(dst)

        start_nodes = [

            node for node in self.graph

            if node not in all_destinations
        ]

        # ========================================================
        # DFS FROM ALL START NODES
        # ========================================================

        for start in start_nodes:

            self.dfs(

                start,

                set(),

                [],

                0.0
            )

        return self.paths