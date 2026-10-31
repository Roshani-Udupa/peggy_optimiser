import time

import pulp


def extract(graph, root, time_limit=5):
    start = time.perf_counter()
    pulp4_api = hasattr(pulp.LpProblem, "add_variable")
    if pulp4_api:
        solver = pulp.COIN_CMD(msg=False, timeLimit=time_limit)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit)
        if not solver.available():
            solver = pulp.COIN_CMD(msg=False, timeLimit=time_limit)
    if not solver.available():
        raise RuntimeError(
            "No CBC executable is available. From backend/, run 'uv sync --reinstall' "
            "to install the solver for this Python version, then restart the API."
        )
    roots = sorted({graph.find(i) for i in range(len(graph.parent))})
    model = pulp.LpProblem("peggy_extract", pulp.LpMinimize)

    def new_variable(name):
        if pulp4_api:
            return model.add_variable(name, cat="Binary")
        return pulp.LpVariable(name, cat="Binary")

    cvars = {c: new_variable(f"c_{c}") for c in roots}
    nvars = {n["id"]: new_variable(f"n_{n['id']}") for n in graph.nodes}
    for c in roots:
        members = [n["id"] for n in graph.nodes if graph.find(n["id"]) == c]
        if members:
            model += pulp.lpSum(nvars[x] for x in members) >= cvars[c]
        for n in graph.nodes:
            if graph.find(n["id"]) == c:
                for child in n["children"]:
                    model += nvars[n["id"]] <= cvars[graph.find(child)]
    model += cvars[graph.find(root)] == 1
    costs = {
        "*": 5,
        "/": 10,
        "+": 2,
        "-": 2,
        "<<": 1,
        "arrayload": 8,
        "fieldload": 8,
        "arraystore": 10,
        "fieldstore": 10,
        "invoke": 12,
        "phi": 1,
        "heapproj": 0,
        "valueproj": 0,
        "sigma": 0,
        "param": 0,
        "const": 0,
        "undef": 0,
    }

    def node_cost(node):
        op_cost = costs.get(node["op"], 20 if node["op"].startswith("pass") else 1)
        return op_cost * (20 ** min(node.get("depth", 0), 4))

    model += pulp.lpSum(nvars[node["id"]] * node_cost(node) for node in graph.nodes)
    stats = model.solve(solver)
    selected = [n["id"] for n in graph.nodes if (nvars[n["id"]].value() or 0) > 0.5]
    constraints = model.constraints
    if callable(constraints):
        constraints = constraints()
    status = stats.status.name if hasattr(stats, "status") else pulp.LpStatus[model.status]
    variables = stats.num_variables if hasattr(stats, "num_variables") else len(model.variables())
    constraint_count = (
        stats.num_constraints if hasattr(stats, "num_constraints") else len(constraints)
    )
    objective = stats.objective if hasattr(stats, "objective") else pulp.value(model.objective)
    return {
        "selected": selected,
        "objective": objective,
        "status": status,
        "solver_ms": round((time.perf_counter() - start) * 1000, 2),
        "variables": variables,
        "constraints": constraint_count,
        "solver": stats.solver if hasattr(stats, "solver") else type(solver).__name__,
    }
