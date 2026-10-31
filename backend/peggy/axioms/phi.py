def rewrite(graph):
    fired = []
    for n in list(graph.nodes):
        if n["op"] == "phi" and len(n["children"]) == 3:
            c, a, b = map(graph.find, n["children"])
            if a == b and graph.union(n["id"], a):
                fired.append("phi-same-branch")
            if graph.constant.get(c) in (0, 1) and graph.union(
                n["id"], a if graph.constant[c] else b
            ):
                fired.append("phi-constant-condition")
            condition = next(
                (x for x in graph.nodes if graph.find(x["id"]) == c and x["op"] == "!"), None
            )
            if condition and len(condition["children"]) == 1:
                swapped = graph.add("phi", [condition["children"][0], b, a], depth=n["depth"])
                if graph.union(n["id"], swapped):
                    fired.append("phi-negated-condition")
        # Distribute a binary operator over a conditional operand.
        if n["op"] in {"+", "-", "*", "/", "<<", "<", "=="} and len(n["children"]) == 2:
            for side in (0, 1):
                child = graph.find(n["children"][side])
                choice = next(
                    (
                        x
                        for x in graph.nodes
                        if graph.find(x["id"]) == child
                        and x["op"] == "phi"
                        and len(x["children"]) == 3
                    ),
                    None,
                )
                if choice is None:
                    continue
                other = n["children"][1 - side]
                left_args = (
                    [choice["children"][1], other] if side == 0 else [other, choice["children"][1]]
                )
                right_args = (
                    [choice["children"][2], other] if side == 0 else [other, choice["children"][2]]
                )
                left = graph.add(n["op"], left_args, depth=n["depth"])
                right = graph.add(n["op"], right_args, depth=n["depth"])
                distributed = graph.add(
                    "phi", [choice["children"][0], left, right], depth=n["depth"]
                )
                if graph.union(n["id"], distributed):
                    fired.append("operator-distributes-over-phi")
    return fired
