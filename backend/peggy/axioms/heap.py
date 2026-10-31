def _member(graph, class_id, op):
    root = graph.find(class_id)
    return next(
        (node for node in graph.nodes if graph.find(node["id"]) == root and node["op"] == op),
        None,
    )


def _same_array_address(graph, load, store):
    return graph.find(load["children"][1]) == graph.find(store["children"][1]) and graph.find(
        load["children"][2]
    ) == graph.find(store["children"][2])


def _different_array_address(graph, load, store):
    if graph.find(load["children"][1]) != graph.find(store["children"][1]):
        return False
    load_index = graph.constant.get(graph.find(load["children"][2]))
    store_index = graph.constant.get(graph.find(store["children"][2]))
    return load_index is not None and store_index is not None and load_index != store_index


def rewrite(graph):
    fired = []
    for node in list(graph.nodes):
        if node["op"] == "arrayload" and len(node["children"]) == 3:
            stored = _member(graph, node["children"][0], "arraystore")
            if stored:
                if _same_array_address(graph, node, stored):
                    if graph.union(node["id"], stored["children"][3]):
                        fired.append("load-after-store-same-array-address")
                elif _different_array_address(graph, node, stored):
                    replacement = graph.add(
                        "arrayload",
                        [stored["children"][0], node["children"][1], node["children"][2]],
                        depth=node["depth"],
                    )
                    if graph.union(node["id"], replacement):
                        fired.append("load-skips-different-array-index")
        elif node["op"] == "fieldload" and len(node["children"]) == 2:
            stored = _member(graph, node["children"][0], "fieldstore")
            if stored:
                same_receiver = graph.find(node["children"][1]) == graph.find(stored["children"][1])
                if same_receiver and node["value"] == stored["value"]:
                    if graph.union(node["id"], stored["children"][2]):
                        fired.append("load-after-store-same-field")
                elif same_receiver and node["value"] != stored["value"]:
                    replacement = graph.add(
                        "fieldload",
                        [stored["children"][0], node["children"][1]],
                        value=node["value"],
                        depth=node["depth"],
                    )
                    if graph.union(node["id"], replacement):
                        fired.append("load-skips-different-field")
        elif node["op"] == "arraystore" and len(node["children"]) == 4:
            previous = _member(graph, node["children"][0], "arraystore")
            if previous and _same_array_address(graph, node, previous):
                collapsed = graph.add(
                    "arraystore",
                    [previous["children"][0], *node["children"][1:]],
                    depth=node["depth"],
                )
                if graph.union(node["id"], collapsed):
                    fired.append("consecutive-array-stores-collapse")
        elif node["op"] == "fieldstore" and len(node["children"]) == 3:
            previous = _member(graph, node["children"][0], "fieldstore")
            same_field = previous and node["value"] == previous["value"]
            same_receiver = same_field and graph.find(node["children"][1]) == graph.find(
                previous["children"][1]
            )
            if same_receiver:
                collapsed = graph.add(
                    "fieldstore",
                    [previous["children"][0], *node["children"][1:]],
                    value=node["value"],
                    depth=node["depth"],
                )
                if graph.union(node["id"], collapsed):
                    fired.append("consecutive-field-stores-collapse")
    return fired
