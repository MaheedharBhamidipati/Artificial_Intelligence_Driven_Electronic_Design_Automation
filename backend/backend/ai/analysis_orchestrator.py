from backend.rtl_parser_engine.netlist_generator import NetlistGenerator

from backend.ai.critical_path_analyzer import CriticalPathAnalyzer
from backend.ai.resource_estimator import ResourceEstimator
from backend.ai.logic_optimizer import LogicOptimizer
from backend.ai.design_explainer import DesignExplainer
from backend.ai.structural_classifier import StructuralClassifier
from backend.ai.design_checker import DesignChecker


class AnalysisOrchestrator:
    def __init__(self, filepath):
        self.filepath = filepath

    def run(self):
        netlist = NetlistGenerator(self.filepath).generate()

        critical = CriticalPathAnalyzer(self.filepath).analyze()
        resource = ResourceEstimator(self.filepath).estimate()
        optimize = LogicOptimizer(netlist).optimize()
        classify = StructuralClassifier().classify(netlist)
        checks = DesignChecker().check(netlist)

        analysis_data = {
            "critical_path": critical,
            "resource": resource,
            "optimization_suggestions": optimize,
            "classification": classify,
            "warnings": checks
        }

        explanation = DesignExplainer().explain(analysis_data)

        analysis_data["explanation"] = explanation

        return analysis_data