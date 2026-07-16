from .ai_behavior_engine import (
    analyze_rtl_behavior
)

from .truth_table import (
    generate_truth_table,
    is_sequential
)

from .fsm_extractor import (
    extract_fsm
)


def generate_behavior_view(code):

    ai_result = analyze_rtl_behavior(code)

    print("\n========== AI RESULT ==========")
    print(ai_result)
    print("===============================\n")

    ai_logic_type = str(
        ai_result.get("logic_type", "unknown")
    ).strip().lower()

    # =====================================================
    # DETERMINISTIC LOGIC-TYPE GATE
    # =====================================================
    # The AI classifier (Groq) can fail for reasons that have
    # nothing to do with the RTL itself — timeouts, rate limits,
    # malformed JSON, a deprecated model name, etc. When that
    # happens ai_behavior_engine.py falls back to "unknown", and
    # truth-table generation used to be skipped entirely even
    # for perfectly valid flat combinational RTL.
    #
    # generate_truth_table() already has its own robust,
    # deterministic check (is_sequential(), a simple posedge/
    # negedge regex) and simulates the RTL directly — it does
    # not need the AI's opinion to run correctly. So we use the
    # deterministic check as the real gate, and only fall back
    # to the AI's classification when it actually agrees or when
    # it says "sequential" (which we trust, since a false
    # "sequential" just skips a table rather than producing a
    # wrong one).
    # =====================================================

    deterministic_is_sequential = is_sequential(code)

    if deterministic_is_sequential:
        effective_logic_type = "sequential"
    elif ai_logic_type in ("combinational", "mixed"):
        effective_logic_type = ai_logic_type
    else:
        # AI was unsure / the API call failed — but the regex
        # check says this isn't sequential, so still attempt it.
        print(
            "Logic type gate: AI returned "
            f"'{ai_logic_type}' (possibly an API/parse failure), "
            "but deterministic check found no posedge/negedge — "
            "proceeding as combinational."
        )
        effective_logic_type = "combinational"

    result = {

        "logic_type":
            effective_logic_type,

        "truth_table":
            None,

        "fsm_svg":
            None,

        "fsm_states":
            [],

        "fsm_transitions":
            [],

        "fsm_summary":
            {},

        "summary":
            ai_result.get(
                "summary",
                ""
            )
    }

    # =====================================================
    # COMBINATIONAL LOGIC
    # =====================================================

    if effective_logic_type in (

        "combinational",
        "mixed"

    ):

        try:

            truth_result = generate_truth_table(
                code
            )

            result["truth_table"] = (
                truth_result
            )

        except Exception as e:

            print(
                "Truth Table Error:",
                str(e)
            )

    # =====================================================
    # FSM EXTRACTION
    # =====================================================

    if ai_result.get(
        "is_fsm",
        False
    ):

        try:

            fsm_result = extract_fsm(
                code
            )

            result["fsm_svg"] = (
                fsm_result.get(
                    "fsm_svg"
                )
            )

            result["fsm_states"] = (
                fsm_result.get(
                    "states",
                    []
                )
            )

            result["fsm_transitions"] = (
                fsm_result.get(
                    "transitions",
                    []
                )
            )

            result["fsm_summary"] = (
                fsm_result.get(
                    "summary",
                    {}
                )
            )

        except Exception as e:

            print(
                "FSM Extraction Error:",
                str(e)
            )

    print("\n========== BEHAVIOR RESULT ==========")
    print(result)
    print("=====================================\n")

    return result