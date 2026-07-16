# ================================================================
# GENERIC BUS ROUTER
# ================================================================

import re
from collections import defaultdict


class GenericBusRouter:

    def __init__(self, dot):

        self.dot = dot

        self.created_buses = {}

        self.bus_drivers = defaultdict(list)

        self.bus_consumers = defaultdict(list)

    # ============================================================
    # NORMALIZE BUS
    # ============================================================

    def normalize_bus(self, signal_name):

        return re.sub(

            r'\[\d+(:\d+)?\]',

            '',

            str(signal_name)
        ).upper()

    # ============================================================
    # CREATE BUS NODE
    # ============================================================

    def create_bus_node(

        self,

        signal_name,

        label=None
    ):

        base = self.normalize_bus(signal_name)

        if base in self.created_buses:

            return self.created_buses[base]

        bus_node = f"BUS_{base}"
        if label is None:

            label = base

        self.dot.node(

            bus_node,

            label,

            shape="box",

            style="filled,rounded",

            fillcolor="#B7D8FF",

            color="#0055AA",

            penwidth="3.0",

            width="3.5",

            height="0.5"
        )

        self.created_buses[base] = bus_node

        return bus_node

    # ============================================================
    # REGISTER DRIVER
    # ============================================================

    def register_driver(

        self,

        signal_name,

        node
    ):

        base = self.normalize_bus(signal_name)

        self.bus_drivers[base].append(node)

    # ============================================================
    # REGISTER CONSUMER
    # ============================================================

    def register_consumer(

        self,

        signal_name,

        node
    ):

        base = self.normalize_bus(signal_name)

        self.bus_consumers[base].append(node)

    # ============================================================
    # BUILD TOPOLOGY
    # ============================================================

    def build_topology(self):

        drawn = set()

        for base in self.created_buses:

            bus_node = self.created_buses[base]

            drivers = sorted(

                set(

                    self.bus_drivers.get(base, [])
                )
            )

            consumers = sorted(

                set(

                    self.bus_consumers.get(base, [])
                )
            )

            # ====================================================
            # DRIVER -> BUS
            # ====================================================

            for drv in drivers:

                edge_key = f"{drv}->{bus_node}"

                if edge_key in drawn:

                    continue

                drawn.add(edge_key)

                self.dot.edge(

                    drv,

                    bus_node,

                    color="#0055AA",

                    penwidth="4",

                    arrowhead="none"
                )

            # ====================================================
            # BUS -> CONSUMER
            # ====================================================

            for con in consumers:

                edge_key = f"{bus_node}->{con}"

                if edge_key in drawn:

                    continue

                drawn.add(edge_key)

                self.dot.edge(

                    bus_node,

                    con,

                    color="#0055AA",

                    penwidth="4",

                    arrowsize="0.8"
                )