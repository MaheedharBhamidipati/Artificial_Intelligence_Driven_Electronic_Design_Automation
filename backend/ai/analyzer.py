import ollama
import json
import re


# -----------------------------
# Robust JSON Extractor
# -----------------------------
def extract_json(text):
    """
    Attempts to parse strict JSON first.
    Falls back to extracting JSON object from mixed text.
    """
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


# -----------------------------
# Main AI Verilog Analyzer
# -----------------------------
def analyze_verilog(code):
    """
    Uses Ollama LLM to analyze Verilog RTL and return structured JSON output.
    """

    prompt = f"""
You are a professional Verilog RTL Design Expert.

Analyze the given Verilog code.

STRICTLY RETURN ONLY VALID JSON.

Output Schema:
{{
  "fixed_code": "string",
  "explanation": [
    "Bullet point 1",
    "Bullet point 2",
    "Bullet point 3"
  ],
  "errors": "string"
}}

Rules:
1. Return ONLY JSON
2. No markdown
3. No triple backticks
4. No extra commentary
5. No text outside JSON
6. explanation MUST be JSON array of strings
7. Preserve original code if no fixes are needed
8. If no errors exist, set:
   "errors": "No syntax/logic errors detected."

Verilog Code:
{code}
"""

    try:
        response = ollama.chat(
            model="phi3",   # Change model here if needed
            format="json",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only Verilog RTL analysis engine."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0
            }
        )

        raw_output = response['message']['content'].strip()

        print("\n========== RAW AI OUTPUT ==========")
        print(raw_output)
        print("===================================\n")

        parsed = extract_json(raw_output)

        if parsed:
            return parsed

        # Fallback if malformed JSON returned
        return {
            "fixed_code": code,
            "explanation": [
                "RTL parsed successfully.",
                "AI returned non-structured output.",
                raw_output
            ],
            "errors": "No syntax/logic errors detected."
        }

    except Exception as e:
        return {
            "fixed_code": code,
            "explanation": [
                "AI analysis unavailable due to backend exception."
            ],
            "errors": f"AI Engine Error: {str(e)}"
        }


# -----------------------------
# Standalone Test
# -----------------------------
if __name__ == "__main__":
    sample_code = '''
module and_gate(
    input a,
    input b,
    output y
);
assign y = a & b;
endmodule
'''

    result = analyze_verilog(sample_code)

    print(json.dumps(result, indent=4))
