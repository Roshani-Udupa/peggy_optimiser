from dataclasses import dataclass, field


@dataclass
class Expr:
    kind: str
    value: str = ""
    args: list["Expr"] = field(default_factory=list)
    line: int = 1


@dataclass
class Stmt:
    kind: str
    name: str = ""
    expr: Expr | None = None
    body: list["Stmt"] = field(default_factory=list)
    otherwise: list["Stmt"] = field(default_factory=list)
    init: "Stmt | None" = None
    update: "Stmt | None" = None
    target: Expr | None = None
    line: int = 1


@dataclass
class Program:
    statements: list[Stmt]
    functions: dict[str, tuple[list[str], list[Stmt]]] = field(default_factory=dict)
    parameters: list[str] = field(default_factory=list)
    entry_name: str = ""
