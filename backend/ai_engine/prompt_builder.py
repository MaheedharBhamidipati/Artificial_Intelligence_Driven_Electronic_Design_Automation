def build_rtl_prompt(user_prompt, hdl_language):

    final_prompt = f"""
Generate synthesizable {hdl_language} HDL code.

Requirements:
{user_prompt}

Rules:
- Generate complete RTL
- Use proper module declarations
- Include comments
- FPGA synthesizable
- No markdown
- No explanations
"""

    return final_prompt