# Peggy Optimiser

An interactive compiler explorer that translates a supported Java source subset into PEG form, records equality-saturation steps, and compares them with destructive optimisation passes.

## Architecture

```mermaid
flowchart TB
    A["Java Source Program"]

    subgraph FRONTEND["1. Frontend and Representation"]
        direction LR
        B["Lexer / Parser / AST"]
        C["Java to PEG Translator"]
        D["Program Expression Graph"]
        E["E-Graph Construction<br/>Equivalence Classes · Union-Find · Rebuild"]

        B --> C --> D --> E
    end

    subgraph OPT["2. Equality Saturation and Optimization"]
        direction LR
        F["Rewrite Rules<br/>Arithmetic · Conditional<br/>Loop · Heap · Inlining"]
        G["Iterative Saturation<br/>Resource-Bounded"]
        H["Pseudo-Boolean<br/>Extraction"]
        I["Lowest-Cost<br/>Equivalent Graph"]

        F --> G --> H --> I
    end

    subgraph OUTPUT["3. Code Generation"]
        direction LR
        J["Java Code Reconstruction"]
        K["Optimized Java Program"]

        J --> K
    end

    A --> B
    E --> F
    G -. "Updated Equivalences" .-> E
    I --> J

    subgraph VALIDATION["4. Translation Validation"]
        direction LR
        L["Shared E-Graph<br/>Root Equivalence Check"]
        M["Randomized Interpreter<br/>Comparison"]
        N["Validation Result"]

        L --> N
        M --> N
    end

    D --> L
    K --> L
    A --> M
    K --> M

    classDef input fill:#E8EEF7,stroke:#496A96,color:#172D4D,stroke-width:1.5px
    classDef frontend fill:#EAF2FA,stroke:#527DA8,color:#183653,stroke-width:1.2px
    classDef optimization fill:#F1ECFA,stroke:#8265A8,color:#382750,stroke-width:1.2px
    classDef generation fill:#E8F3F1,stroke:#4D8A7D,color:#173D36,stroke-width:1.2px
    classDef validation fill:#EDF5EF,stroke:#648B70,color:#24452D,stroke-width:1.2px
    classDef result fill:#DCEFE4,stroke:#39845B,color:#17452C,stroke-width:2px

    class A input
    class B,C,D,E frontend
    class F,G,H,I optimization
    class J,K generation
    class L,M validation
    class N result

    style FRONTEND fill:#F7FAFE,stroke:#9BB3CF,stroke-width:1.5px
    style OPT fill:#FAF8FD,stroke:#B3A0CE,stroke-width:1.5px
    style OUTPUT fill:#F5FAF8,stroke:#91B9AE,stroke-width:1.5px
    style VALIDATION fill:#F5FAF5,stroke:#A0BBA4,stroke-width:1.5px
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
