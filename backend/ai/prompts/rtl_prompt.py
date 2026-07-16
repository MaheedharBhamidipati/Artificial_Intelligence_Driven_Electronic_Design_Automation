def build_rtl_fix_prompt(code):

    return f"""
You are an expert Verilog RTL engineer.

Fix syntax issues in this RTL.

Return response in this JSON format:

{{
  "fixed_code": "...",
  "explanation": [
    "...",
    "..."
  ],
  "errors": [
    "...",
    "..."
  ]
}}

Return ONLY valid JSON.

RTL:

{code[:2000]}
"""