import { CheckCircle2, GitBranch, Layers3, Network, Workflow } from 'lucide-react';
export const PAPER_URL = 'https://cseweb.ucsd.edu/~lerner/papers/lmcs11-eqsat.pdf';
export const WORKSPACE_TABS = [
  { id: 'source', label: 'Source and graph', icon: Workflow },
  { id: 'comparison', label: 'Two strategies', icon: GitBranch },
  { id: 'saturation', label: 'Collect equalities', icon: Network },
  { id: 'extraction', label: 'Choose a program', icon: Layers3 },
  { id: 'validation', label: 'Check correctness', icon: CheckCircle2 },
];
export const EXPLANATIONS = {
  source: {
    number: '01', title: 'Translate Java into a value graph',
    body: 'Assignments become references to values. Branches become conditional merge nodes. Loop-carried values become sequences, and array or field operations use one shared heap value.',
  },
  comparison: {
    number: '02', title: 'Compare destructive passes with equality reasoning',
    body: 'The traditional path replaces one form with another at each pass. The equality path keeps equivalent forms together so later rules can use whichever form helps.',
  },
  saturation: {
    number: '03', title: 'Add equal forms until the search stops',
    body: 'Each rule looks for a pattern, adds an equivalent expression, and merges their equivalence classes. The original expression remains available throughout.',
  },
  extraction: {
    number: '04', title: 'Choose the least costly connected program',
    body: 'A binary integer model chooses graph nodes and the value classes they depend on. The objective estimates operator cost and increases the weight of work inside nested loops.',
  },
  validation: {
    number: '05', title: 'Check the result against the input',
    body: 'The validator compares the input and generated result in one equality graph, then checks executable arithmetic cases with randomized inputs.',
  },
};

export const PASS_LABELS = {
  peephole: 'Peephole simplification',
  algebraic: 'Algebraic simplification',
  'constant fold': 'Constant folding',
  'strength reduction': 'Strength reduction',
  LICM: 'Loop-invariant code motion',
};

