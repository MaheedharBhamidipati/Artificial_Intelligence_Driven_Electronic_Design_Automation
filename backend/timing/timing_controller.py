# ================================================================
# TIMING CONTROLLER
# ================================================================

from backend.timing.timing_engine import TimingEngine

from backend.timing.timing_ai_engine import (
    TimingAIEngine
)

from backend.timing.timing_dashboard_generator import (
    TimingDashboardGenerator
)

from backend.timing.timing_graph_builder import (
    TimingGraphBuilder
)

from backend.timing.violation_classifier import (
    ViolationClassifier
)

from backend.timing.clock_domain_analyzer import (
    ClockDomainAnalyzer
)

from backend.timing.timing_plotter import (
    TimingPlotter
)

# ============================================================
# TIMING PATH TRAVERSER
# ============================================================

from backend.timing.timing_path_traverser import (
    TimingPathTraverser
)

from backend.timing.timing_plotter import (
    TimingPlotter
)


# ================================================================
# COMPLETE TIMING ANALYSIS
# ================================================================

def run_complete_timing_analysis(cells):

    # ============================================================
    # CRITICAL PATH ESTIMATION
    # ============================================================

    # ============================================================
    # REAL PATH TRAVERSAL
    # ============================================================

    path_traverser = TimingPathTraverser(

        cells,

        {}
    )

    critical_paths = path_traverser.find_paths()

    # ============================================================
    # FALLBACK SAFETY
    # ============================================================

    if len(critical_paths) == 0:

        critical_paths = [{

            "startpoint": "START",

            "endpoint": "NO_PATH_FOUND",

            "delay": 0.0,

            "arrival_time": 0.0,

            "required_time": 5.0,

            "slack": 5.0,

            "status": "SAFE",

            "violation_type": "setup"
        }]

        

    # ============================================================
    # TIMING ENGINE
    # ============================================================

    timing_engine = TimingEngine()

    timing_engine.paths = critical_paths

    worst_path = timing_engine.get_worst_path()

    # ============================================================
    # VIOLATION CLASSIFIER
    # ============================================================

    classifier = ViolationClassifier()

    analyzed_paths = []

    for path in critical_paths:

        analyzed = classifier.analyze_report(path)

        analyzed_paths.append(analyzed)

    # ============================================================
    # AI ENGINE
    # ============================================================

    ai_engine = TimingAIEngine()

    ai_reports = []

    for path in analyzed_paths:

        ai_reports.append(

            ai_engine.analyze(path)
        )

    # ============================================================
    # DASHBOARD
    # ============================================================

    dashboard_generator = TimingDashboardGenerator(

        analyzed_paths
    )

    dashboard = (

        dashboard_generator.generate_dashboard()
    )

    # ============================================================
    # GRAPH
    # ============================================================

    graph_builder = TimingGraphBuilder(

        analyzed_paths
    )

    graph_data = graph_builder.build_graph()
    
    # ============================================================
    # TIMING PLOT
    # ============================================================

    plotter = TimingPlotter(
        analyzed_paths
    )

    timing_plot = plotter.generate_slack_plot()

    # ============================================================
    # CDC
    # ============================================================

    cdc_engine = ClockDomainAnalyzer(cells)

    cdc_domains = cdc_engine.analyze()

    cdc_summary = cdc_engine.generate_summary()

    # ============================================================
    # FINAL RESULT
    # ============================================================

    return {

        "critical_paths":
            analyzed_paths,

        "worst_path":
            worst_path,

        "dashboard":
            dashboard,

        "graph":
            graph_data,

        "ai_reports":
            ai_reports,

        "cdc_domains":
            cdc_domains,
            
         "timing_plot":
           timing_plot,   

        "cdc_summary":
            cdc_summary
            
    }