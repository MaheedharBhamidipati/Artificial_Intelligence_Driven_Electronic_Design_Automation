# ================================================================
# CLOCK DOMAIN ANALYZER
# ================================================================

from collections import defaultdict


class ClockDomainAnalyzer:

    def __init__(

        self,

        cells
    ):

        self.cells = cells

        self.clock_domains = defaultdict(list)

    # ============================================================
    # ANALYZE CLOCK DOMAINS
    # ============================================================

    def analyze(self):

        for cell in self.cells:

            connections = cell.get(

                "connections",

                {}
            )

            for port, signals in connections.items():

                if "clk" not in port.lower():

                    continue

                if not isinstance(

                    signals,

                    list
                ):

                    signals = [signals]

                for clk_signal in signals:

                    clk_signal = str(clk_signal)

                    self.clock_domains[
                        clk_signal
                    ].append(

                        cell.get(
                            "name",
                            "UNKNOWN"
                        )
                    )

        return dict(self.clock_domains)

    # ============================================================
    # DOMAIN COUNT
    # ============================================================

    def get_domain_count(self):

        return len(

            self.clock_domains
        )

    # ============================================================
    # MULTI DOMAIN CHECK
    # ============================================================

    def detect_multiple_domains(self):

        return (

            len(self.clock_domains) > 1
        )

    # ============================================================
    # CDC PATH DETECTION
    # ============================================================

    def detect_cdc_paths(self):

        domains = list(

            self.clock_domains.keys()
        )

        cdc_paths = []

        if len(domains) <= 1:

            return cdc_paths

        for i in range(len(domains)):

            for j in range(i + 1, len(domains)):

                cdc_paths.append({

                    "from": domains[i],

                    "to": domains[j],

                    "type": "CDC"
                })

        return cdc_paths

    # ============================================================
    # GENERATE CDC SUMMARY
    # ============================================================

    def generate_summary(self):

        return {

            "total_domains": self.get_domain_count(),

            "multiple_domains": self.detect_multiple_domains(),

            "cdc_paths": self.detect_cdc_paths()
        }