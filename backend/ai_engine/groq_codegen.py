import os

from groq import Groq

from dotenv import load_dotenv

load_dotenv()

client = Groq(

    api_key=os.getenv(
        "AIDEA_RTL_API"
    )
)

def generate_rtl_code(
    prompt,
    hdl_language
):

    system_prompt = f"""
You are an expert RTL Design Engineer.

Generate ONLY synthesizable {hdl_language} HDL code.

STRICT RULES:
- No markdown
- No explanations
- No ``` blocks
- Only code
- Synthesizable RTL only
- Include comments
"""

    completion = client.chat.completions.create(

        model="openai/gpt-oss-120b", # meta-llama/llama-4-scout-17b-16e-instruct

        messages=[

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_tokens=4096,

        top_p=0.95
    )

    generated_code = (

        completion
        .choices[0]
        .message.content
    )

    return generated_code