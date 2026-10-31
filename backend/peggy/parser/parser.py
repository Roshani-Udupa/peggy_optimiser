import re

from peggy.parser.ast import Expr, Program, Stmt

TOKEN = re.compile(
    r"\s+|//[^\n]*|/\*[\s\S]*?\*/|(?:\d+)|(?:[A-Za-z_$][\w$]*)|(?:==|!=|<=|>=|&&|\|\||<<|>>|\+=|-=|\*=|/=|\+\+|--)|[^\s]"
)
MODIFIERS = {"public", "private", "protected", "static", "final", "abstract", "synchronized"}
TYPES = {"int", "long", "short", "byte", "boolean", "char", "float", "double", "void", "String"}


class ParseError(ValueError):
    pass


class Parser:
    def __init__(self, source: str):
        self.tokens = [
            (m.group(), source.count("\n", 0, m.start()) + 1)
            for m in TOKEN.finditer(source)
            if not m.group().isspace() and not m.group().startswith(("//", "/*"))
        ]
        self.i = 0

    def peek(self, value=None):
        if self.i >= len(self.tokens):
            return ""
        token = self.tokens[self.i][0]
        return token == value if value is not None else token

    def pop(self, expected=None):
        if self.i >= len(self.tokens):
            raise ParseError("line 1: unexpected end of input")
        token, line = self.tokens[self.i]
        if expected and token != expected:
            raise ParseError(f"line {line}: expected {expected!r}, found {token!r}")
        self.i += 1
        return token

    @property
    def line(self):
        return self.tokens[self.i][1] if self.i < len(self.tokens) else 1

    def parse(self):
        statements = []
        functions = {}
        parameters = []
        entry_name = ""
        while self.peek():
            if self.peek("package") or self.peek("import"):
                self._skip_to_semicolon()
                continue
            if self.peek() in MODIFIERS:
                self._modifiers()
            if self.peek("class"):
                self.pop("class")
                self.pop()  # class name
                while self.peek() and not self.peek("{"):
                    self.pop()  # extends/implements clause
                self.pop("{")
                while self.peek() and not self.peek("}"):
                    self._modifiers()
                    if not self.peek():
                        break
                    self.pop()  # return type
                    if self.peek("["):
                        self.pop("[")
                        self.pop("]")
                    method_name = self.pop()
                    if self.peek("("):
                        params = self._parameters()
                        body = self.block()
                        functions[method_name] = (params, body)
                    else:
                        self._skip_to_semicolon()
                self.pop("}")
                if functions:
                    preferred = next(
                        (name for name in ("run", "compute", "main") if name in functions),
                        next(iter(functions)),
                    )
                    parameters, statements = functions.pop(preferred)
                    entry_name = preferred
                continue
            if self.peek() in TYPES:
                start = self.i
                self.pop()
                name = self.pop()
                if self.peek("("):
                    params = self._parameters()
                    body = self.block()
                    functions[name] = (params, body)
                    if not statements:
                        statements, parameters, entry_name = body, params, name
                    continue
                self.i = start
            statements.append(self.statement())
        return Program(statements, functions, parameters, entry_name)

    def _skip_to_semicolon(self):
        while self.peek() and not self.peek(";"):
            self.pop()
        if self.peek(";"):
            self.pop()

    def _modifiers(self):
        while self.peek() in MODIFIERS:
            self.pop()

    def _parameters(self):
        self.pop("(")
        result = []
        while self.peek() and not self.peek(")"):
            self.pop()  # parameter type
            while self.peek("["):
                self.pop("[")
                self.pop("]")
            result.append(self.pop())
            if not self.peek(","):
                break
            self.pop(",")
        self.pop(")")
        return result

    def _for_assignment(self):
        if self.peek(";") or self.peek(")"):
            return None
        line = self.line
        if self.peek() in TYPES and self.peek() != "void":
            self.pop()
        name = self.pop()
        if self.peek("++") or self.peek("--"):
            op = self.pop()
            value = Expr("const", "1", line=line)
            expr = Expr(
                "op", "+" if op == "++" else "-", [Expr("var", name, line=line), value], line
            )
            return Stmt("assign", name=name, expr=expr, line=line)
        op = self.pop()
        expr = self.expression()
        if op == "+=":
            expr = Expr("op", "+", [Expr("var", name, line=line), expr], line)
        elif op == "-=":
            expr = Expr("op", "-", [Expr("var", name, line=line), expr], line)
        elif op != "=":
            raise ParseError(f"line {line}: unsupported for-loop update operator {op!r}")
        return Stmt("assign", name=name, expr=expr, line=line)

    def block(self):
        self.pop("{")
        result = []
        while self.peek() and not self.peek("}"):
            result.append(self.statement())
        self.pop("}")
        return result

    def statement(self):
        line = self.line
        if self.peek("{"):
            return Stmt("block", body=self.block(), line=line)
        if self.peek("if"):
            self.pop()
            self.pop("(")
            cond = self.expression()
            self.pop(")")
            body = self.block() if self.peek("{") else [self.statement()]
            other = []
            if self.peek("else"):
                self.pop()
                other = self.block() if self.peek("{") else [self.statement()]
            return Stmt("if", expr=cond, body=body, otherwise=other, line=line)
        if self.peek("while"):
            self.pop()
            self.pop("(")
            cond = self.expression()
            self.pop(")")
            body = self.block() if self.peek("{") else [self.statement()]
            return Stmt("while", expr=cond, body=body, line=line)
        if self.peek("for"):
            self.pop()
            self.pop("(")
            init = self._for_assignment()
            self.pop(";")
            cond = self.expression()
            self.pop(";")
            update = self._for_assignment()
            self.pop(")")
            body = self.block() if self.peek("{") else [self.statement()]
            return Stmt("for", expr=cond, init=init, update=update, body=body, line=line)
        if self.peek("return"):
            self.pop()
            expr = None if self.peek(";") else self.expression()
            self.pop(";")
            return Stmt("return", expr=expr, line=line)
        declared_type = self.peek() in TYPES and self.peek() != "void"
        if declared_type:
            self.pop()
            while self.peek("["):
                self.pop("[")
                self.pop("]")
        name = self.pop()
        if not re.fullmatch(r"[A-Za-z_$][\w$]*", name):
            raise ParseError(f"line {line}: unsupported statement starting with {name!r}")
        target = Expr("var", name, line=line)
        while self.peek("["):
            self.pop("[")
            index = self.expression()
            self.pop("]")
            target = Expr("array", "", [target, index], line)
        while self.peek("."):
            self.pop(".")
            member = self.pop()
            if self.peek("("):
                target = Expr("call", member, [target, *self._arguments()], line)
            else:
                target = Expr("field", member, [target], line)
        if declared_type and target.kind == "var" and self.peek(";"):
            self.pop(";")
            return Stmt("declare", name=name, line=line)
        if target.kind == "var" and (self.peek("++") or self.peek("--")):
            op = self.pop()
            self.pop(";")
            expr = Expr(
                "op",
                "+" if op == "++" else "-",
                [Expr("var", name, line=line), Expr("const", "1", line=line)],
                line,
            )
            return Stmt("assign", name=name, expr=expr, line=line)
        if self.peek("=") or self.peek("+=") or self.peek("-="):
            op = self.pop()
            expr = self.expression()
            self.pop(";")
            if op == "+=":
                expr = Expr("op", "+", [target, expr], line)
            elif op == "-=":
                expr = Expr("op", "-", [target, expr], line)
            return Stmt("assign", name=name, expr=expr, target=target, line=line)
        if target.kind == "var" and self.peek("("):
            self.i -= 1
            expr = self.expression()
            self.pop(";")
            return Stmt("expr", expr=expr, line=line)
        if target.kind == "call":
            self.pop(";")
            return Stmt("expr", expr=target, line=line)
        raise ParseError(f"line {line}: unsupported construct after {name!r}")

    def expression(self, min_prec=0):
        line = self.line
        if self.peek("!") or self.peek("-"):
            op = self.pop()
            left = Expr("op", "!" if op == "!" else "neg", [self.expression(7)], line)
        elif self.peek("("):
            self.pop()
            left = self.expression()
            self.pop(")")
        else:
            token = self.pop()
            if token.isdigit():
                left = Expr("const", token, line=line)
            elif token in {"true", "false"}:
                left = Expr("const", "1" if token == "true" else "0", line=line)
            elif self.peek("("):
                self.pop()
                args = []
                if not self.peek(")"):
                    args.append(self.expression())
                    while self.peek(","):
                        self.pop()
                        args.append(self.expression())
                self.pop(")")
                left = Expr("call", token, args, line)
            else:
                left = Expr("var", token, line=line)
            while self.peek("[") or self.peek("."):
                if self.peek("["):
                    self.pop("[")
                    index = self.expression()
                    self.pop("]")
                    left = Expr("array", "", [left, index], line)
                else:
                    self.pop(".")
                    member = self.pop()
                    if self.peek("("):
                        left = Expr("call", member, [left, *self._arguments()], line)
                    else:
                        left = Expr("field", member, [left], line)
        prec = {
            "||": 1,
            "&&": 2,
            "==": 3,
            "!=": 3,
            "<": 3,
            ">": 3,
            "<=": 3,
            ">=": 3,
            "+": 4,
            "-": 4,
            "*": 5,
            "/": 5,
            "%": 5,
            "<<": 5,
            ">>": 5,
        }
        while self.peek() in prec and prec[self.peek()] >= min_prec:
            op = self.pop()
            right = self.expression(prec[op] + 1)
            left = Expr("op", op, [left, right], line)
        return left

    def _arguments(self):
        self.pop("(")
        args = []
        if not self.peek(")"):
            args.append(self.expression())
            while self.peek(","):
                self.pop()
                args.append(self.expression())
        self.pop(")")
        return args


def parse(source: str) -> Program:
    return Parser(source).parse()
