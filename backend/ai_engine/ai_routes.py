from flask import Blueprint
from flask import request
from flask import jsonify

import re

from backend.ai_engine.groq_codegen import generate_rtl_code
from backend.ai_engine.prompt_builder import build_rtl_prompt
from backend.ai_engine.rtl_saver import save_generated_rtl


ai_bp = Blueprint(
    "ai_bp",
    __name__
)

@ai_bp.route(
    "/generate_ai_rtl",
    methods=["POST"]
)
def generate_ai_rtl():

    try:

        user_prompt = request.form.get("prompt")
        hdl_language = request.form.get("hdl")

        final_prompt = build_rtl_prompt(
            user_prompt,
            hdl_language
        )

        generated_code = generate_rtl_code(
            final_prompt,
            hdl_language
        )

        # -----------------------------------
        # REMOVE MARKDOWN CODE BLOCKS
        # -----------------------------------

        generated_code = re.sub(
            r"```[\w]*",
            "",
            generated_code
        )

        generated_code = generated_code.replace(
            "```",
            ""
        ).strip()

        # -----------------------------------

        extension = ".sv"

        if hdl_language.lower() == "verilog":
            extension = ".v"

        filepath = save_generated_rtl(
            generated_code,
            extension
        )

        return jsonify({

            "success": True,

            "generated_code":
                generated_code,

            "generated_file":
                filepath
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })