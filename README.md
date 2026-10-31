# Peggy Optimiser

An interactive compiler explorer that translates a supported Java source subset into PEG form, records equality-saturation steps, and compares them with destructive optimisation passes.

## Architecture

```mermaid
flowchart TB
  Source[Java source program]

  subgraph EqualitySaturation[Equality saturation pipeline]
    direction TB
    FrontEnd[Lexer, parser, and abstract syntax tree]
    Translator[Java to Program Expression Graph translator]
    PEG[Program Expression Graph]
    EGraph[Equivalence classes, union-find, and congruence rebuild]
    Analyses[Arithmetic · conditional · loop · heap · inlining rules]
    Saturator[Iterative saturation with resource bounds]
    Solver[Pseudo-Boolean extraction model]
    Best[Lowest-cost selected graph]
    Reconstruct[Java code reconstruction]

    FrontEnd --> Translator --> PEG --> EGraph
    EGraph --> Analyses --> Saturator
    Saturator -->|updated equivalences| EGraph
    Saturator -->|fixed-point graph| Solver --> Best --> Reconstruct
  end

  subgraph Comparison[Traditional optimization]
    Passes[Ordered destructive passes]
    TraditionalResult[Traditional Java result]
    Passes --> TraditionalResult
  end

  Source --> FrontEnd
  Source --> Passes
  Source --> InputPEG[Original PEG]
  Reconstruct --> Optimized[Optimized Java result]

  subgraph Validation[Translation validation]
    GraphCheck[Shared equivalence-graph root check]
    Interpreter[Randomized interpreter comparison]
  end

  InputPEG --> GraphCheck
  Optimized --> GraphCheck
  Source --> Interpreter
  Optimized --> Interpreter

  classDef source fill:#21152d,stroke:#bd7bea,color:#f7eaff,stroke-width:2px
  classDef graph fill:#171d2c,stroke:#82a8e8,color:#e6efff
  classDef rewrite fill:#291729,stroke:#e084d2,color:#fff0fb
  classDef solver fill:#291d32,stroke:#c287ee,color:#f6eaff
  classDef validation fill:#14251f,stroke:#7ac79c,color:#e7fff0
  class Source,TraditionalResult,Optimized source
  class PEG,EGraph,InputPEG graph
  class Analyses,Saturator,Passes rewrite
  class Solver,Best,Reconstruct solver
  class GraphCheck,Interpreter validation
```

## Run

```powershell
cd backend
uv sync --extra dev
uv run uvicorn peggy.api.main:app --reload
```

The backend selects a compatible PuLP major version for the active Python: PuLP 3 on Python 3.10–3.11 and PuLP 4 with its CBC extra on Python 3.12+. If an existing environment reports that CBC cannot be executed, stop the API, run `uv sync --reinstall` from `backend/`, and restart it.

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Backend and frontend

`backend/peggy` separates the lexer/parser and AST, PEG translation, hash-consed union-find e-graph, rewrite families, saturation snapshots, PuLP/CBC extraction, traditional passes, validation, and FastAPI. The React/Vite frontend consumes only `/api` JSON through the Vite proxy. Sample programs live in `examples/`.

## Pipeline

The parser reads Java class and method wrappers, method parameters and calls, scalar assignments, branches, `while` and `for` loops, and simple array and field accesses. The PEG translator substitutes scalar definitions, merges branch values with φ, represents loop-carried scalars and heap state with θ/eval/pass, and threads a single σ heap through array/field operations and unknown calls. Pure, straight-line methods in the same class receive an inlining equality. The e-graph stores equalities with union-find and rebuilds congruence. PuLP sends a binary model to CBC for extraction. A separate ordered pass pipeline generates traditional snapshots.

## What this project does

Peggy Optimiser is an interactive Java source optimizer inspired by Tate, Stepp, Tatlock, and Lerner's equality-saturation work. Instead of committing to each rewrite immediately, it records equivalent expressions in a shared e-graph, then uses a binary optimization model to choose a low-cost representation. The workspace puts the traditional pass sequence and equality-saturation pipeline side by side, and reports graph growth, extraction statistics, generated Java, and validation evidence. Its parser focuses on Java methods using integer expressions, branches, loops, calls, and simple arrays or fields.
