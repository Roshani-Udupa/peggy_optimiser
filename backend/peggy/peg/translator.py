from peggy.parser.ast import Expr, Program


class PEG:
    def __init__(self):
        self.nodes: list[dict] = []
        self.memo: dict[tuple, int] = {}
        self.functions = {}
        self.inlining = set()
        self.returns = []
        self.root_id = None

    def add(self, op, *children, value=None, depth=0):
        key = (op, tuple(children), value, depth)
        if key not in self.memo:
            idx = len(self.nodes)
            self.memo[key] = idx
            self.nodes.append(
                {"id": idx, "op": op, "children": list(children), "value": value, "depth": depth}
            )
        return self.memo[key]

    def expr(self, expr: Expr, env, depth=0):
        if expr.kind == "const":
            return self.add("const", value=int(expr.value), depth=depth)
        if expr.kind == "var":
            if expr.value not in env:
                env[expr.value] = self.add("param", value=expr.value, depth=depth)
            return env[expr.value]
        if expr.kind == "array":
            array = self.expr(expr.args[0], env, depth)
            index = self.expr(expr.args[1], env, depth)
            return self.add("arrayload", env["$heap"], array, index, depth=depth)
        if expr.kind == "field":
            receiver = self.expr(expr.args[0], env, depth)
            return self.add("fieldload", env["$heap"], receiver, value=expr.value, depth=depth)
        children = [self.expr(a, env, depth) for a in expr.args]
        if expr.kind == "call":
            function = self.functions.get(expr.value)
            if (
                function
                and expr.value not in self.inlining
                and self._simple_pure_method(function[1])
            ):
                call = self.add("call", *children, value=expr.value, depth=depth)
                parameters, body = function
                inline_env = {name: value for name, value in zip(parameters, children)}
                inline_env["$heap"] = env["$heap"]
                self.inlining.add(expr.value)
                self.statements(body[:-1], inline_env, depth)
                body_value = self.expr(body[-1].expr, inline_env, depth)
                self.inlining.remove(expr.value)
                self.add("inlinecandidate", call, body_value, value=expr.value, depth=depth)
                return call
            invocation = self.add("invoke", env["$heap"], *children, value=expr.value, depth=depth)
            env["$heap"] = self.add("heapproj", invocation, depth=depth)
            return self.add("valueproj", invocation, depth=depth)
        return self.add(
            expr.value if expr.kind != "call" else "call",
            *children,
            value=expr.value if expr.kind == "call" else None,
            depth=depth,
        )

    def statements(self, stmts, env, depth=0):
        for stmt in stmts:
            if stmt.kind == "declare":
                env[stmt.name] = self.add("undef", value=stmt.name, depth=depth)
            elif stmt.kind == "assign":
                value = self.expr(stmt.expr, env, depth)
                target = stmt.target or Expr("var", stmt.name, line=stmt.line)
                if target.kind == "var":
                    env[stmt.name] = value
                elif target.kind == "array":
                    array = self.expr(target.args[0], env, depth)
                    index = self.expr(target.args[1], env, depth)
                    env["$heap"] = self.add(
                        "arraystore", env["$heap"], array, index, value, depth=depth
                    )
                elif target.kind == "field":
                    receiver = self.expr(target.args[0], env, depth)
                    env["$heap"] = self.add(
                        "fieldstore",
                        env["$heap"],
                        receiver,
                        value,
                        value=target.value,
                        depth=depth,
                    )
            elif stmt.kind == "expr":
                self.expr(stmt.expr, env, depth)
            elif stmt.kind == "if":
                cond = self.expr(stmt.expr, env, depth)
                left, right = env.copy(), env.copy()
                self.statements(stmt.body, left, depth)
                self.statements(stmt.otherwise, right, depth)
                for name in left.keys() | right.keys():
                    a = left.get(name, env.get(name))
                    b = right.get(name, env.get(name))
                    if a is not None and b is not None:
                        env[name] = self.add("phi", cond, a, b, depth=depth)
            elif stmt.kind in {"while", "for"}:
                if stmt.kind == "for" and stmt.init is not None:
                    self.statements([stmt.init], env, depth)
                before = env.copy()
                changed_names = self._assigned_names(stmt.body)
                if stmt.kind == "for" and stmt.update is not None:
                    changed_names |= self._assigned_names([stmt.update])
                carried_names = changed_names & before.keys()
                theta = {
                    name: self.add(f"theta{depth}", value=name, depth=depth)
                    for name in carried_names
                }
                loopenv = dict(env) | theta
                cond = self.expr(stmt.expr, loopenv, depth + 1)
                self.statements(stmt.body, loopenv, depth + 1)
                if stmt.kind == "for" and stmt.update is not None:
                    self.statements([stmt.update], loopenv, depth + 1)
                pass_node = self.add(f"pass{depth}", cond, depth=depth)
                for name in carried_names:
                    base = before[name]
                    nxt = loopenv.get(name, base)
                    self.nodes[theta[name]]["children"] = [base, nxt]
                    env[name] = self.add(
                        f"eval{depth}",
                        theta[name],
                        pass_node,
                        depth=depth,
                    )
            elif stmt.kind == "return" and stmt.expr:
                self.returns.append(
                    self.add("return", self.expr(stmt.expr, env, depth), depth=depth)
                )

    def build(self, program: Program):
        self.functions = program.functions
        env = {name: self.add("param", value=name) for name in program.parameters}
        env["$heap"] = self.add("sigma", value="entry")
        self.statements(program.statements, env)
        self.root_id = self.add("program", *self.returns, env["$heap"])
        return self.nodes

    def _assigned_names(self, statements):
        names = set()
        for stmt in statements:
            if stmt.kind == "declare":
                continue
            if stmt.kind == "assign":
                names.add(stmt.name)
            names.update(self._assigned_names(stmt.body))
            names.update(self._assigned_names(stmt.otherwise))
            if stmt.target and stmt.target.kind != "var":
                names.add("$heap")
            if stmt.expr and self._contains_call(stmt.expr):
                names.add("$heap")
        return names

    def _contains_call(self, expr):
        return expr.kind == "call" or any(self._contains_call(arg) for arg in expr.args)

    def _simple_pure_method(self, body):
        if not body or body[-1].kind != "return" or body[-1].expr is None:
            return False
        for stmt in body:
            if stmt.kind not in {"assign", "return"}:
                return False
            if stmt.target and stmt.target.kind != "var":
                return False
            if stmt.expr and self._contains_effect(stmt.expr):
                return False
        return True

    def _contains_effect(self, expr):
        return expr.kind in {"call", "array", "field"} or any(
            self._contains_effect(arg) for arg in expr.args
        )


def to_peg(program: Program):
    peg = PEG()
    return peg, peg.build(program)
