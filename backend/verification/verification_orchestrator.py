from backend.verification.fsm_extractor import FSMExtractor
from backend.verification.latch_detector import LatchDetector
from backend.verification.comb_loop_detector import CombLoopDetector
from backend.verification.sequential_timing_analyzer import SequentialTimingAnalyzer
from backend.verification.cdc_checker import CDCChecker
from backend.verification.constraint_parser import ConstraintParser


class VerificationOrchestrator:
    def __init__(self, filepath):
        self.filepath = filepath

    def run(self):
        return {
            "fsm_analysis": FSMExtractor(self.filepath).extract(),
            "latch_warnings": LatchDetector(self.filepath).detect(),
            "comb_loop": CombLoopDetector(self.filepath).detect(),
            "sequential_timing": SequentialTimingAnalyzer(self.filepath).analyze(),
            "cdc": CDCChecker(self.filepath).check(),
            "constraints": ConstraintParser().parse(None)
        }