def rewrite(graph):
    fired = []
    for n in list(graph.nodes):
        op, cs = n["op"], n["children"]
        if op in {"+", "*"} and len(cs) == 2:
            a, b = map(graph.find, cs)
            if graph.union(n["id"], graph.add(op, [b, a], depth=n["depth"])):
                fired.append((True, "commutativity"))
            # Bounded associativity is naturally limited by the engine's node bound.
            for outer, inner in ((a, b), (b, a)):
                nested = next(
                    (
                        x
                        for x in graph.nodes
                        if graph.find(x["id"]) == inner
                        and x["op"] == op
                        and len(x["children"]) == 2
                    ),
                    None,
                )
                if nested:
                    x, y = nested["children"]
                    candidate = graph.add(
                        op, [graph.add(op, [outer, x], depth=n["depth"]), y], depth=n["depth"]
                    )
                    if graph.union(n["id"], candidate):
                        fired.append((True, "associativity"))
            if op == "*":
                for side in (0, 1):
                    product = next(
                        (
                            x
                            for x in graph.nodes
                            if graph.find(x["id"]) == graph.find(cs[side])
                            and x["op"] == "+"
                            and len(x["children"]) == 2
                        ),
                        None,
                    )
                    if product:
                        left = graph.add(
                            "*", [product["children"][0], cs[1 - side]], depth=n["depth"]
                        )
                        right = graph.add(
                            "*", [product["children"][1], cs[1 - side]], depth=n["depth"]
                        )
                        expanded = graph.add("+", [left, right], depth=n["depth"])
                        if graph.union(n["id"], expanded):
                            fired.append((True, "distributivity"))
        if op in {"+", "-", "*", "/", "<<"} and len(cs) == 2:
            a, b = map(graph.find, cs)
            av, bv = graph.constant.get(a), graph.constant.get(b)
            if av is not None and bv is not None:
                try:
                    if op == "+":
                        val = _int32(av + bv)
                    elif op == "-":
                        val = _int32(av - bv)
                    elif op == "*":
                        val = _int32(av * bv)
                    elif op == "/":
                        val = _int32(abs(av) // abs(bv) * (-1 if (av < 0) != (bv < 0) else 1))
                    elif op == "<<":
                        val = _int32(av << (bv & 31))
                    else:
                        continue
                    fired.append(
                        (graph.union(n["id"], graph.add("const", value=val)), "constant-fold")
                    )
                except (ZeroDivisionError, TypeError):
                    pass
            if (op == "+" and bv == 0) or (op == "*" and bv == 1):
                fired.append((graph.union(n["id"], a), "identity"))
            if op == "*" and bv == 0:
                fired.append((graph.union(n["id"], b), "zero"))
            if op == "-" and a == b:
                fired.append(
                    (graph.union(n["id"], graph.add("const", value=0)), "self-subtraction")
                )
            if op == "*" and bv and bv > 0 and bv & (bv - 1) == 0:
                fired.append(
                    (
                        graph.union(
                            n["id"],
                            graph.add("<<", [a, graph.add("const", value=bv.bit_length() - 1)]),
                        ),
                        "strength-reduction",
                    )
                )
    return list(dict.fromkeys(label for changed, label in fired if changed))


def _int32(value):
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)
