from backend.rtl_parser_engine.netlist_generator import NetlistGenerator

from backend.fpga.fpga_resource_mapper import FPGAResourceMapper
from backend.fpga.asic_cell_mapper import ASICCellMapper
from backend.fpga.ppa_estimator import PPAEstimator
from backend.fpga.hotspot_detector import HotspotDetector
from backend.fpga.architecture_advisor import ArchitectureAdvisor


class HardwareOrchestrator:
    def __init__(self, filepath):
        self.filepath = filepath

    def run(self):
        netlist = NetlistGenerator(self.filepath).generate()

        fpga = FPGAResourceMapper().map_resources(netlist)
        asic = ASICCellMapper().map_cells(netlist)
        ppa = PPAEstimator().estimate(netlist)
        hotspots = HotspotDetector().detect(netlist)
        advice = ArchitectureAdvisor().recommend(ppa, fpga)

        return {
            "fpga_resources": fpga,
            "asic_cells": asic,
            "ppa_estimation": ppa,
            "hotspots": hotspots,
            "architecture_advice": advice
        }