# ================================================================
# TIMING PATH VISUALIZER
# ================================================================

import json


class TimingPathVisualizer:

    def __init__(self):

        self.paths = []

    # ============================================================
    # ADD PATH
    # ============================================================

    def add_path(

        self,

        source,

        destination,

        delay,

        slack=0.0,

        status="SAFE",

        path_type="setup",

        cells=None,

        clock_domain="clk"
    ):

        if cells is None:

            cells = []

        self.paths.append({

            "source": source,

            "destination": destination,

            "delay": delay,

            "slack": slack,

            "status": status,

            "path_type": path_type,

            "cells": cells,

            "clock_domain": clock_domain
        })

    # ============================================================
    # GET ALL PATHS
    # ============================================================

    def get_paths(self):

        return self.paths

    # ============================================================
    # GET CRITICAL PATH
    # ============================================================

    def get_critical_path(self):

        if not self.paths:

            return None

        return min(

            self.paths,

            key=lambda x: x["slack"]
        )

    # ============================================================
    # GET VIOLATING PATHS
    # ============================================================

    def get_violating_paths(self):

        return [

            path for path in self.paths

            if path["slack"] < 0
        ]

    # ============================================================
    # EXPORT SUMMARY
    # ============================================================

    def export_summary(self):

        summary = []

        for path in self.paths:

            summary.append(

                f'{path["source"]} -> '
                f'{path["destination"]} | '
                f'Delay={path["delay"]}ns | '
                f'Slack={path["slack"]}ns | '
                f'Status={path["status"]}'
            )

        return summary

    # ============================================================
    # EXPORT JSON
    # ============================================================

    def export_json(self):

        return json.dumps(

            self.paths,

            indent=4
        )

    # ============================================================
    # GENERATE CYTOSCAPE GRAPH
    # ============================================================

    def generate_graph_data(self):

        nodes = []

        edges = []

        added_nodes = set()

        for path in self.paths:

            src = path["source"]

            dst = path["destination"]

            if src not in added_nodes:

                nodes.append({

                    "data": {

                        "id": src,

                        "label": src
                    }
                })

                added_nodes.add(src)

            if dst not in added_nodes:

                nodes.append({

                    "data": {

                        "id": dst,

                        "label": dst
                    }
                })

                added_nodes.add(dst)

            edges.append({

                "data": {

                    "source": src,

                    "target": dst,

                    "delay": path["delay"],

                    "slack": path["slack"],

                    "status": path["status"]
                }
            })

        return {

            "nodes": nodes,

            "edges": edges
        }