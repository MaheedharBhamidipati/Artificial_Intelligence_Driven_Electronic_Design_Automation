def build_timing_prompt(report):

    return f"""
Analyze this timing report.

Explain:
- setup violations
- hold violations
- critical paths

Timing Report:

{report}
"""