def rewrite(graph):
    fired = []
    for node in graph.nodes:
        if (
            node["op"] == "inlinecandidate"
            and len(node["children"]) == 2
            and graph.union(node["children"][0], node["children"][1])
        ):
            fired.append("method-inline")
    return fired
