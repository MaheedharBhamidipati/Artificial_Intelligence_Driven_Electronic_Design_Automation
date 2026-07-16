class DesignExplainer:
    def explain(self, analysis_data):
        explanation = []

        if analysis_data["resource"]["total_gates"] < 5:
            explanation.append("Small combinational logic block detected.")

        if analysis_data["critical_path"]["logic_depth"] > 5:
            explanation.append("Deep combinational path may impact timing.")

        return explanation
