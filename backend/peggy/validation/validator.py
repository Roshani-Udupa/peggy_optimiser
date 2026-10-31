import random

from peggy.parser.ast import Expr, Program
from peggy.parser.parser import parse


class _Returned(Exception):
    def __init__(self, value):
        self.value = value


class _Interpreter:
    def __init__(self, program: Program, source: str):
        self.program = program
        self.source = source
        self.steps = 0
        self.max_steps = 20_000
        self.array_parameters = self._array_parameters()

    def _array_parameters(self):
        names = set()

        def visit_expr(expr):
            if expr.kind == "array" and expr.args[0].kind == "var":
                names.add(expr.args[0].value)
            for arg in expr.args:
                visit_expr(arg)

        def visit_statements(statements):
            for stmt in statements:
                if stmt.expr:
                    visit_expr(stmt.expr)
                if stmt.target:
                    visit_expr(stmt.target)
                visit_statements(stmt.body)
                visit_statements(stmt.otherwise)
                if stmt.init:
                    visit_statements([stmt.init])
                if stmt.update:
                    visit_statements([stmt.update])

        visit_statements(self.program.statements)
        for _, body in self.program.functions.values():
            visit_statements(body)
        return names

    @staticmethod
    def _int32(value):
        return (int(value) + (1 << 31)) % (1 << 32) - (1 << 31)

    def _tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise RuntimeError("interpreter step limit reached")

    def expression(self, expr: Expr, env):
        self._tick()
        if expr.kind == "const":
            return int(expr.value)
        if expr.kind == "var":
            return env.get(expr.value, 0)
        if expr.kind == "array":
            array = self.expression(expr.args[0], env)
            index = int(self.expression(expr.args[1], env))
            return array[index]
        if expr.kind == "field":
            receiver = self.expression(expr.args[0], env)
            return receiver.get(expr.value, 0)
        if expr.kind == "call":
            arguments = [self.expression(arg, env) for arg in expr.args]
            if expr.value in self.program.functions:
                params, body = self.program.functions[expr.value]
                return self.invoke(params, body, arguments)
            return 0
        if expr.kind != "op":
            return 0
        operator = expr.value
        if operator == "&&":
            left = bool(self.expression(expr.args[0], env))
            return int(left and bool(self.expression(expr.args[1], env)))
        if operator == "||":
            left = bool(self.expression(expr.args[0], env))
            return int(left or bool(self.expression(expr.args[1], env)))
        values = [self.expression(arg, env) for arg in expr.args]
        if operator == "neg":
            return self._int32(-int(values[0]))
        if operator == "!":
            return int(not values[0])
        left, right = values
        if operator == "+":
            return self._int32(left + right)
        if operator == "-":
            return self._int32(left - right)
        if operator == "*":
            return self._int32(left * right)
        if operator == "/":
            if right == 0:
                raise ZeroDivisionError
            if left == -(1 << 31) and right == -1:
                return -(1 << 31)
            return self._int32(abs(left) // abs(right) * (-1 if (left < 0) != (right < 0) else 1))
        if operator == "%":
            quotient = self.expression(Expr("op", "/", expr.args), env)
            return left - quotient * right
        if operator == "<<":
            return self._int32(left << (right & 31))
        if operator == ">>":
            return self._int32(left) >> (right & 31)
        if operator == "<":
            return int(left < right)
        if operator == ">":
            return int(left > right)
        if operator == "<=":
            return int(left <= right)
        if operator == ">=":
            return int(left >= right)
        if operator == "==":
            return int(left == right)
        if operator == "!=":
            return int(left != right)
        raise RuntimeError(f"unsupported operator {operator}")

    def assign(self, target: Expr, value, env):
        if target.kind == "var":
            env[target.value] = value
        elif target.kind == "array":
            array = self.expression(target.args[0], env)
            index = int(self.expression(target.args[1], env))
            array[index] = value
        elif target.kind == "field":
            receiver = self.expression(target.args[0], env)
            receiver[target.value] = value

    def statements(self, statements, env):
        for stmt in statements:
            self._tick()
            if stmt.kind == "declare":
                env.setdefault(stmt.name, 0)
            elif stmt.kind == "assign":
                target = stmt.target or Expr("var", stmt.name)
                self.assign(target, self.expression(stmt.expr, env), env)
            elif stmt.kind == "expr":
                self.expression(stmt.expr, env)
            elif stmt.kind == "return":
                raise _Returned(self.expression(stmt.expr, env) if stmt.expr else None)
            elif stmt.kind == "if":
                branch = stmt.body if self.expression(stmt.expr, env) else stmt.otherwise
                self.statements(branch, env)
            elif stmt.kind == "while":
                while self.expression(stmt.expr, env):
                    self.statements(stmt.body, env)
            elif stmt.kind == "for":
                if stmt.init:
                    self.statements([stmt.init], env)
                while self.expression(stmt.expr, env):
                    self.statements(stmt.body, env)
                    if stmt.update:
                        self.statements([stmt.update], env)
            elif stmt.kind == "block":
                self.statements(stmt.body, env)

    def invoke(self, params, body, arguments):
        self._tick()
        env = dict(zip(params, arguments))
        try:
            self.statements(body, env)
        except _Returned as returned:
            return returned.value
        return None

    def run(self, rng):
        params = self.program.parameters
        arguments = []
        for name in params:
            if name in self.array_parameters:
                arguments.append([rng.randint(-4, 8) for _ in range(16)])
            else:
                arguments.append(rng.randint(-4, 8))
        try:
            result = self.invoke(params, self.program.statements, arguments)
        except (IndexError, KeyError, ZeroDivisionError, RuntimeError, TypeError):
            return None
        observable_arguments = tuple(
            tuple(value) if isinstance(value, list) else value for value in arguments
        )
        return result, observable_arguments


def validate(original, optimised, roots_merged=False, samples=8):
    try:
        original_program = parse(original)
        optimised_program = parse(optimised)
        original_interpreter = _Interpreter(original_program, original)
        optimised_interpreter = _Interpreter(optimised_program, optimised)
    except (ValueError, TypeError) as exc:
        return {"equivalent": False, "message": f"Not proven: {exc}", "samples": 0}

    checked = 0
    rng = random.Random(7)
    for _ in range(samples):
        case_seed = rng.randrange(1 << 30)
        left = original_interpreter.run(random.Random(case_seed))
        right = optimised_interpreter.run(random.Random(case_seed))
        if left is None or right is None:
            continue
        checked += 1
        if left != right:
            return {
                "equivalent": False,
                "message": "Not proven: interpreter counterexample",
                "samples": checked,
            }

    return {
        "equivalent": bool(roots_merged),
        "message": "Equivalent: roots merged" if roots_merged else "Not proven",
        "samples": checked,
    }
