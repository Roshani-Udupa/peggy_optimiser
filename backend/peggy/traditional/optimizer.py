import re

from peggy.parser.parser import parse


def optimise(code, order):
    current = code
    steps = []
    for name in order:
        before = current
        if name == "constant fold":
            current = re.sub(r"\b(\d+)\s*\+\s*0\b", r"\1", current)
        elif name == "strength reduction":
            current = re.sub(
                r"\b([A-Za-z_]\w*)\s*\*\s*([248])\b",
                lambda m: f"({m[1]} << {int(m[2]).bit_length() - 1})",
                current,
            )
        elif name == "algebraic":
            current = re.sub(r"\b([A-Za-z_]\w*)\s*\*\s*1\b", r"\1", current)
        elif name == "peephole":
            current = current.replace("(a * 2) / 2", "a")
        steps.append(
            {"pass": name, "code": current, "changed": current != before, "cost": _cost(current)}
        )
    return current, steps


def _cost(code):
    """Estimate executed work from the parsed Java tree, including memory and calls."""
    program = parse(code)
    operators = {
        "*": 5,
        "/": 10,
        "%": 10,
        "+": 2,
        "-": 2,
        "<<": 1,
        ">>": 1,
        "<": 1,
        ">": 1,
        "<=": 1,
        ">=": 1,
        "==": 1,
        "!=": 1,
        "&&": 1,
        "||": 1,
    }

    def expression_cost(expr, depth):
        total = sum(expression_cost(arg, depth) for arg in expr.args)
        weight = 20 ** min(depth, 4)
        if expr.kind == "op":
            return total + operators.get(expr.value, 1) * weight
        if expr.kind in {"array", "field"}:
            return total + 8 * weight
        if expr.kind == "call":
            return total + 12 * weight
        return total

    def statements_cost(statements, depth=0):
        total = 0
        for stmt in statements:
            if stmt.expr:
                total += expression_cost(stmt.expr, depth)
            if stmt.target and stmt.target.kind in {"array", "field"}:
                total += expression_cost(stmt.target, depth) + 10 * (20 ** min(depth, 4))
            if stmt.kind == "if":
                total += statements_cost(stmt.body, depth) + statements_cost(stmt.otherwise, depth)
            elif stmt.kind in {"while", "for"}:
                if stmt.init:
                    total += statements_cost([stmt.init], depth)
                total += statements_cost(stmt.body, depth + 1)
                if stmt.update:
                    total += statements_cost([stmt.update], depth + 1)
        return total

    return sum(statements_cost(body) for _, body in program.functions.values()) + statements_cost(
        program.statements
    )
