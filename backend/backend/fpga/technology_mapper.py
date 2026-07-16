from backend.fpga.fpga_resource_mapper import FPGAResourceMapper
from backend.fpga.asic_cell_mapper import ASICCellMapper


class TechnologyMapper:
    def map(self, netlist):
        return {
            "fpga": FPGAResourceMapper().map_resources(netlist),
            "asic": ASICCellMapper().map_cells(netlist)
        }
