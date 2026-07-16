# ============================================================
# ROUTING ENGINE
# ============================================================

from backend.routing.net_extractor import (
    extract_nets
)

from backend.routing.utils import (
    get_block_map
)

from backend.routing.manhattan_router import (
    generate_manhattan_route
)

from backend.routing.routing_cost import (
    calculate_wirelength
)

from backend.routing.congestion_map import (
    estimate_congestion
)


class RoutingEngine:

    def __init__(self, blocks):

        self.blocks = blocks

    # ========================================================
    # MAIN ROUTING
    # ========================================================

    def run(self):

        routes = []

        block_map = get_block_map(

            self.blocks
        )

        nets = extract_nets(

            self.blocks
        )

        # ====================================================
        # ROUTE EACH NET
        # ====================================================

        for net in nets:

            source = net["source"]

            target = net["target"]

            source_block = block_map[source]

            target_block = block_map[target]

            route_path = generate_manhattan_route(

                source_block,
                target_block
            )

            routes.append({

                "source": source,

                "target": target,

                "path": route_path
            })

        # ====================================================
        # METRICS
        # ====================================================

        wirelength = calculate_wirelength(

            routes
        )

        congestion = estimate_congestion(

            routes
        )

        return {

            "routes": routes,

            "statistics": {

                "total_routes":
                    len(routes),

                "wirelength":
                    wirelength,

                "congestion":
                    congestion
            }
        }