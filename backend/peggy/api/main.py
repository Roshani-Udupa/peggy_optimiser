from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from peggy.codegen.generator import generate
from peggy.egraph.graph import EGraph
from peggy.extraction.solver import extract
from peggy.parser.parser import ParseError, parse
from peggy.peg.translator import to_peg
from peggy.saturation.engine import saturate
from peggy.traditional.optimizer import optimise as traditional
from peggy.validation.validator import validate

app = FastAPI(title="Peggy Optimiser API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Request(BaseModel):
    code: str
    traditional_order: list[str] = [
        "peephole",
        "algebraic",
        "constant fold",
        "strength reduction",
        "LICM",
    ]
    iterations: int = 8
    node_limit: int = 400


@app.get("/api/examples")
def examples():
    root = Path(__file__).resolve().parents[3] / "examples"
    return [
        {"name": p.name.removesuffix(".java.txt"), "code": p.read_text(encoding="utf-8")}
        for p in sorted(root.glob("*.java.txt"))
    ]


@app.post("/api/optimize")
def optimize(req: Request):
    try:
        program = parse(req.code)
        _peg, nodes = to_peg(program)
    except (ParseError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        graph = EGraph()
        ids = graph.import_peg(nodes)
        peg_root_id = next(n["id"] for n in nodes if n["op"] == "program")
        root = ids[peg_root_id]
        snapshots, saturation = saturate(graph, req.iterations, req.node_limit)
        extraction = extract(graph, root)
        traditional_code, steps = traditional(req.code, req.traditional_order)
        result_code = generate(req.code)
        original_graph = EGraph()
        original_ids = original_graph.import_peg(nodes)
        output_program = parse(result_code)
        _, output_nodes = to_peg(output_program)
        output_ids = original_graph.import_peg(output_nodes)
        original_root = original_ids[peg_root_id]
        output_peg_root = next(n["id"] for n in output_nodes if n["op"] == "program")
        output_root = output_ids[output_peg_root]
        same_peg = len(nodes) == len(output_nodes) and all(
            {key: value for key, value in left.items() if key != "id"}
            == {key: value for key, value in right.items() if key != "id"}
            for left, right in zip(nodes, output_nodes)
        )
        if same_peg:
            for left, right in zip(nodes, output_nodes):
                original_graph.union(original_ids[left["id"]], output_ids[right["id"]])
            original_graph.rebuild()
        roots_merged_at_import = original_graph.find(original_root) == original_graph.find(
            output_root
        )
        validation_snapshots, _ = saturate(original_graph, req.iterations, req.node_limit)
        roots_merged = original_graph.find(original_root) == original_graph.find(output_root)
        validation_iteration = len(validation_snapshots) or 1
        validation = validate(req.code, result_code, roots_merged=roots_merged)
        if roots_merged:
            merged_iteration = 0 if roots_merged_at_import else validation_iteration
            validation["message"] = f"Equivalent: roots merged in iteration {merged_iteration}"
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {exc}") from exc
    return {
        "source": req.code,
        "peg": nodes,
        "snapshots": snapshots,
        "saturation": saturation,
        "traditional": {"code": traditional_code, "steps": steps},
        "extraction": extraction,
        "code": result_code,
        "validation": validation,
    }
