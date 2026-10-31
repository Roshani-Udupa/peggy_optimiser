def _member(graph, class_id, op):
    root = graph.find(class_id)
    return next(
        (node for node in graph.nodes if graph.find(node["id"]) == root and node["op"] == op), None
    )


def _contains_loop_value(graph, class_id, depth, seen=None):
    seen = seen or set()
    root = graph.find(class_id)
    if root in seen:
        return False
    seen.add(root)
    for node in graph.nodes:
        if graph.find(node["id"]) != root:
            continue
        if node["op"] == f"theta{depth}":
            return True
        if any(_contains_loop_value(graph, child, depth, seen) for child in node["children"]):
            return True
    return False


def rewrite(graph):
    fired = []
    for node in list(graph.nodes):
        op, children = node["op"], node["children"]
        if op.startswith("eval") and len(children) == 2:
            depth = op[4:]
            sequence, index = map(graph.find, children)
            theta = _member(graph, sequence, f"theta{depth}")
            if theta and len(theta["children"]) == 2:
                if graph.constant.get(index) == 0 and graph.union(node["id"], theta["children"][0]):
                    fired.append("eval-theta-at-zero")
                # Successor indices are represented as k + 1.
                successor = _member(graph, index, "+")
                if successor and len(successor["children"]) == 2:
                    left, right = successor["children"]
                    if graph.constant.get(graph.find(right)) == 1:
                        prior = left
                    elif graph.constant.get(graph.find(left)) == 1:
                        prior = right
                    else:
                        prior = None
                    if prior is not None:
                        unrolled = graph.add(
                            f"eval{depth}", [theta["children"][1], prior], depth=node["depth"]
                        )
                        if graph.union(node["id"], unrolled):
                            fired.append("eval-theta-successor")
            if not _contains_loop_value(graph, sequence, int(depth)) and graph.union(
                node["id"], sequence
            ):
                fired.append("loop-invariant-evaluation")
        if op in {"+", "-", "*", "<<"} and len(children) == 2:
            for side in (0, 1):
                theta = next(
                    (
                        n
                        for n in graph.nodes
                        if graph.find(n["id"]) == graph.find(children[side])
                        and n["op"].startswith("theta")
                        and len(n["children"]) == 2
                    ),
                    None,
                )
                invariant = children[1 - side]
                if theta is None or _contains_loop_value(graph, invariant, int(theta["op"][5:])):
                    continue
                args_base = (
                    [theta["children"][0], invariant]
                    if side == 0
                    else [invariant, theta["children"][0]]
                )
                args_step = (
                    [theta["children"][1], invariant]
                    if side == 0
                    else [invariant, theta["children"][1]]
                )
                base = graph.add(op, args_base, depth=node["depth"])
                step = graph.add(op, args_step, depth=node["depth"])
                moved = graph.add(
                    theta["op"], [base, step], value=theta["value"], depth=node["depth"]
                )
                if graph.union(node["id"], moved):
                    fired.append("operator-distributes-over-theta")
    return fired
