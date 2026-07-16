import re
from .gate_library import GATE_OPERATORS


class ExpressionParser:

    def __init__(self):
        pass

    def detect_operator(self, expression):

        for op in sorted(GATE_OPERATORS.keys(), key=len, reverse=True):

            if op in expression:
                return op

        return None

    def parse_expression(self, expression):

        expression = expression.strip().replace(";", "")

        operator = self.detect_operator(expression)

        if not operator:
            return {
                "gate_type": "BUFFER",
                "inputs": [expression]
            }

        parts = expression.split(operator)

        inputs = [p.strip() for p in parts]

        return {
            "gate_type": GATE_OPERATORS[operator],
            "operator": operator,
            "inputs": inputs
        }


if __name__ == "__main__":

    parser = ExpressionParser()

    expressions = [
        "a & b",
        "x | y",
        "p ^ q",
        "~a",
        "a + b"
    ]

    for expr in expressions:
        print("\nExpression:", expr)
        print(parser.parse_expression(expr))
