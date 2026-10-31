from peggy.axioms import arithmetic, heap, inline, phi, theta


def saturate(graph, iterations=8, node_limit=400):
    snapshots = []
    families = (arithmetic, phi, theta, heap, inline)
    stop_reason = "iteration_limit"
    for i in range(iterations):
        fired = []
        for family in families:
            fired.extend(family.rewrite(graph))
            if len(graph.nodes) >= node_limit:
                break
        graph.rebuild()
        snapshots.append(
            {
                "iteration": i + 1,
                "nodes": [dict(n) for n in graph.nodes],
                "classes": {str(k): v[:] for k, v in graph.classes.items() if graph.find(k) == k},
                "fired": list(dict.fromkeys(fired)),
            }
        )
        if len(graph.nodes) >= node_limit:
            stop_reason = "node_limit"
            break
        if not fired:
            stop_reason = "fixed_point"
            break
    return snapshots, {
        "stop_reason": stop_reason,
        "iteration_limit": iterations,
        "node_limit": node_limit,
    }
