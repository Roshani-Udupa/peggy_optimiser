from peggy.axioms.arithmetic import rewrite
from peggy.axioms.heap import rewrite as rewrite_heap
from peggy.axioms.inline import rewrite as rewrite_inline
from peggy.egraph.graph import EGraph
from peggy.parser.parser import parse
from peggy.peg.translator import to_peg
from peggy.saturation.engine import saturate
from peggy.traditional.optimizer import _cost
from peggy.validation.validator import validate


def test_while_translation_has_theta_eval_pass():
    _, nodes = to_peg(parse("i = 0; while (i < n) { i = i + 1; }"))
    kinds = {n["op"].split("0")[0] for n in nodes}
    assert "theta" in kinds and "eval" in kinds and "pass" in kinds


def test_egraph_merge_and_constant_fold():
    graph = EGraph()
    a = graph.add("const", value=2)
    b = graph.add("const", value=3)
    c = graph.add("+", [a, b])
    assert "constant-fold" in rewrite(graph)
    graph.rebuild()
    assert graph.constant[graph.find(c)] == 5


def test_java_class_and_for_loop_translation():
    source = """
    public class Loop {
        static int run(int limit) {
            int sum = 0;
            for (int i = 0; i < limit; i++) { sum = sum + i; }
            return sum;
        }
    }
    """
    program = parse(source)
    _, nodes = to_peg(program)
    ops = {node["op"] for node in nodes}
    assert program.entry_name == "run"
    assert program.parameters == ["limit"]
    assert "theta0" in ops and "eval0" in ops and "pass0" in ops
    theta_names = {node["value"] for node in nodes if node["op"] == "theta0"}
    assert theta_names == {"sum", "i"}


def test_java_array_load_after_store():
    graph = EGraph()
    heap = graph.add("sigma", value="entry")
    array = graph.add("param", value="values")
    index = graph.add("const", value=0)
    value = graph.add("const", value=7)
    stored_heap = graph.add("arraystore", [heap, array, index, value])
    loaded_value = graph.add("arrayload", [stored_heap, array, index])
    assert "load-after-store-same-array-address" in rewrite_heap(graph)
    assert graph.find(loaded_value) == graph.find(value)


def test_java_method_inline_equality_is_created():
    source = """
    public class Inline {
        static int twice(int value) { return value * 2; }
        static int run(int input) { return twice(input); }
    }
    """
    _, nodes = to_peg(parse(source))
    graph = EGraph()
    graph.import_peg(nodes)
    assert "method-inline" in rewrite_inline(graph)


def test_heap_operations_have_nonzero_traditional_cost():
    source = """
    public class HeapRedundantLoad {
        static int run(int[] values) {
            values[0] = 3;
            values[0] = 5;
            return values[0];
        }
    }
    """
    assert _cost(source) == 44


def test_saturation_reports_fixed_point_after_no_change_sweep():
    graph = EGraph()
    heap = graph.add("sigma", value="entry")
    array = graph.add("param", value="values")
    index = graph.add("const", value=0)
    first = graph.add("const", value=3)
    second = graph.add("const", value=5)
    first_store = graph.add("arraystore", [heap, array, index, first])
    final_store = graph.add("arraystore", [first_store, array, index, second])
    load = graph.add("arrayload", [final_store, array, index])
    graph.add("return", [load])

    snapshots, status = saturate(graph)

    assert status["stop_reason"] == "fixed_point"
    assert len(snapshots) == 2
    assert snapshots[0]["fired"]
    assert snapshots[1]["fired"] == []


def test_peg_import_keeps_distinct_effect_nodes_until_rebuild():
    _, nodes = to_peg(parse("values[0] = 3; values[0] = 5; return values[0];"))
    graph = EGraph()
    ids = graph.import_peg(nodes)
    stores = [node for node in graph.nodes if node["op"] == "arraystore"]
    assert len(stores) == 2
    assert graph.find(stores[0]["id"]) != graph.find(stores[1]["id"])
    program_id = next(node["id"] for node in nodes if node["op"] == "program")
    program_node = next(node for node in graph.nodes if node["id"] == ids[program_id])
    final_heap_class = graph.find(program_node["children"][-1])
    assert any(
        graph.find(node["id"]) == final_heap_class and node["op"] == "arraystore"
        for node in graph.nodes
    )


def test_interpreter_checks_loop_program_and_finds_counterexample():
    loop = """
    public class Loop {
        static int run(int n) {
            int i = 0;
            while (i < n) { i = i + 1; }
            return i;
        }
    }
    """
    same = validate(loop, loop, roots_merged=True)
    assert same["equivalent"]
    assert same["samples"] == 8

    original = "public class Values { static int run(int x) { return x + 1; } }"
    changed = "public class Values { static int run(int x) { return x + 2; } }"
    mismatch = validate(original, changed)
    assert not mismatch["equivalent"]
    assert mismatch["message"] == "Not proven: interpreter counterexample"
