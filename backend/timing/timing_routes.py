# ================================================================
# TIMING ROUTES
# ================================================================

from flask import Blueprint
from flask import jsonify


timing_bp = Blueprint(

    "timing_bp",

    __name__
)


# ================================================================
# HEALTH CHECK
# ================================================================

@timing_bp.route("/timing/health")

def timing_health():

    return jsonify({

        "status":
            "Timing Engine Active"
    })