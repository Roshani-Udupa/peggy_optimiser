import { ArrowRight, BookOpen, CheckCircle2, CircleHelp, Network, Sparkles, Workflow } from 'lucide-react';
import { PAPER_URL } from './constants';

function About() {
  return (
    <main className="about-page page-enter">
      <section className="about-hero">
        <div className="eyebrow">THE PROJECT, THE METHOD, THE EVIDENCE</div>
        <h1>Optimization as a<br /><em>shared search.</em></h1>
        <p>This project turns the paper’s central idea into an explorable Java-source optimizer: keep equivalent computations together, then select a result after their interactions are visible.</p>
        <a className="button-primary paper-button" href={PAPER_URL} target="_blank" rel="noreferrer"><BookOpen size={16} /> View the original paper PDF <ArrowRight size={15} /></a>
      </section>

      <section className="about-section problem-section">
        <SectionHeading index="01" kicker="THE PROBLEM" title="A good rewrite can close a better path." />
        <div className="problem-layout">
          <div className="problem-copy">
            <p>Traditional compilers run optimizations in sequence. Each pass changes the program it receives, so an early choice can hide a transformation that would have helped later.</p>
            <p>For example, rewriting <code>i * 5</code> as shifts and additions makes one multiplication cheaper. Inside a loop, that can hide the larger opportunity: update the loop value by five and use the value directly.</p>
            <div className="note-card"><CircleHelp size={17} /><span><b>Two related problems</b> Pass order affects what can still match, while local cost decisions cannot see benefits that appear after other transformations.</span></div>
          </div>
          <PhaseOrderDiagram />
        </div>
      </section>

      <section className="about-section method-section">
        <SectionHeading index="02" kicker="THE IMPLEMENTATION" title="One pipeline, from Java text to a chosen program." />
        <p className="section-intro">Each stage has a different job. The graph keeps the options; the solver chooses among them.</p>
        <PipelineDiagram />
        <div className="method-grid">
          <MethodCard number="01" title="Parse a Java method" text="Read a supported class and method, then build an expression and statement tree from assignments, branches, loops, calls, and simple array or field operations." icon={BookOpen} />
          <MethodCard number="02" title="Build a value graph" text="Substitute local assignments. Use conditional merges for branches, loop sequences for carried values, and a shared heap value for memory effects." icon={Workflow} />
          <MethodCard number="03" title="Collect equal forms" text="Pattern-triggered rules add equivalent nodes. Union-find groups equivalent values, and rebuilding restores equivalence through operators." icon={Network} />
          <MethodCard number="04" title="Select and check" text="A binary integer program minimizes estimated operator cost. A separate check compares graph roots and tries bounded interpreter samples." icon={CheckCircle2} />
        </div>
      </section>

      <section className="about-section graph-section">
        <SectionHeading index="03" kicker="HOW TO READ THE GRAPHS" title="A node is a value. A connection is a dependency." />
        <div className="graph-explainer">
          <div className="graph-explainer-copy"><h3>Program Expression Graph</h3><p>Operations point to the values they consume. A loop sequence records its first value and its next value; a conditional merge chooses a value based on a condition.</p><div className="legend-list"><Legend color="violet" title="Loop sequence" text="Values carried between iterations" /><Legend color="pink" title="Conditional merge" text="The selected branch value" /><Legend color="blue" title="Shared heap" text="Memory state passed to reads and writes" /></div></div>
          <IllustrativePeg />
        </div>
        <div className="equivalence-explainer">
          <div><h3>Equivalence classes keep alternatives together</h3><p>When two nodes are proven equal, they share one class. The class can then offer more than one operator form to later rules and to the cost model.</p></div>
          <MiniEquivalenceGraph />
        </div>
      </section>

      <section className="about-section results-section">
        <SectionHeading index="04" kicker="RESULTS REPORTED IN THE PAPER" title="A useful search can be expensive to run." />
        <p className="section-intro">These figures are from the paper’s Peggy evaluation, not measurements of this prototype.</p>
        <div className="paper-results">
          <div className="results-chart"><h3>Average time per method</h3><p>Milliseconds reported for the four main stages</p><ResultBar label="Java bytecode to value graph" value={13.9} max={1500} display="13.9 ms" color="violet" /><ResultBar label="Equality saturation" value={87.4} max={1500} display="87.4 ms" color="pink" /><ResultBar label="Binary solver selection" value={1499} max={1500} display="1,499 ms" color="fuchsia" /><ResultBar label="Value graph back to control flow" value={52.8} max={1500} display="52.8 ms" color="blue" /></div>
          <div className="result-facts"><Fact value="2,461" label="Java methods in the benchmark set" /><Fact value="84%" label="methods saturated without reaching the expression limit" /><Fact value="6×" label="average total time compared with the baseline compiler" /><p>The paper reports that solver selection took most of the time. It also used a breadth-first processing limit for the remaining methods.</p><a href={PAPER_URL} target="_blank" rel="noreferrer">Read the methods and results in the paper <ArrowRight size={13} /></a></div>
        </div>
      </section>
    </main>
  );
}

function SectionHeading({ index, kicker, title }) {
  return <div className="section-heading"><span className="section-index">{index}</span><div><div className="eyebrow">{kicker}</div><h2>{title}</h2></div></div>;
}

function MethodCard({ number, title, text, icon: Icon }) {
  return <article className="method-card"><span className="method-number">{number}</span><Icon size={17} /><h3>{title}</h3><p>{text}</p></article>;
}

function PhaseOrderDiagram() {
  return <div className="phase-diagram">
    <div className="phase-row phase-loses"><span className="phase-label">ONE CHOSEN PATH</span><div className="phase-box">i × 5<small>inside the loop</small></div><ArrowRight size={17} /><div className="phase-box">(i &lt;&lt; 2) + i<small>local rewrite</small></div><div className="blocked-mark"><span>×</span><small>loop rule<br />may no longer match</small></div></div>
    <div className="phase-divider"><span>THE SAME EXPRESSION, KEPT AS OPTIONS</span></div>
    <div className="phase-row phase-keeps"><span className="phase-label">SHARED OPTIONS</span><div className="option-stack"><span>i × 5</span><span>(i &lt;&lt; 2) + i</span><span>loop-step form</span></div><ArrowRight size={17} /><div className="phase-box picked">lowest estimated cost<small>chosen at the end</small></div></div>
  </div>;
}

function PipelineDiagram() {
  const stages = [
    ['01', 'Java method', 'source text'], ['02', 'Value graph', 'explicit data flow'],
    ['03', 'Equivalence graph', 'many equal forms'], ['04', 'Binary selection', 'global cost choice'],
    ['05', 'Validation', 'compare the result'],
  ];
  return <div className="pipeline-diagram">{stages.map(([number, title, sub], index) => <div className="pipeline-node" key={number}><span>{number}</span><b>{title}</b><small>{sub}</small>{index < stages.length - 1 && <ArrowRight className="pipeline-arrow" size={16} />}</div>)}</div>;
}

function IllustrativePeg() {
  return <div className="illustrative-peg"><svg viewBox="0 0 600 300" role="img" aria-label="A loop sequence feeds a multiplication that is used in a call"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#9c72c7" /></marker></defs><path className="diagram-edge" d="M180 135 C240 90 265 85 320 105" markerEnd="url(#arrow)"/><path className="diagram-edge" d="M180 230 C240 260 265 230 320 210" markerEnd="url(#arrow)"/><path className="diagram-edge" d="M420 105 C470 105 475 145 505 150" markerEnd="url(#arrow)"/><path className="diagram-edge" d="M420 210 C470 205 475 170 505 165" markerEnd="url(#arrow)"/><GraphNode x="40" y="105" title="loop sequence" detail="first: 0" theme="violet"/><GraphNode x="40" y="200" title="next value" detail="previous + 1" theme="violet"/><GraphNode x="320" y="75" title="multiply" detail="loop value × 5" theme="pink"/><GraphNode x="320" y="180" title="loop condition" detail="loop value &lt; limit" theme="blue"/><GraphNode x="505" y="125" title="method call" detail="use(value)" theme="neutral"/></svg><div className="diagram-caption">Illustrative graph based on the paper’s loop example. Arrows point from an input value to the operation that uses it.</div></div>;
}

function GraphNode({ x, y, title, detail, theme }) {
  return <g className={`svg-node ${theme}`} transform={`translate(${x},${y})`}><rect width="112" height="58" rx="12" /><text x="12" y="23" className="svg-node-title">{title}</text><text x="12" y="42" className="svg-node-detail">{detail}</text></g>;
}

function MiniEquivalenceGraph() {
  return <div className="mini-egraph"><div className="mini-class"><span>ONE VALUE CLASS</span><b>equivalent choices</b><div><code>multiply by 8</code><code>shift left by 3</code><code>constant result</code></div></div><ArrowRight size={18} /><div className="mini-cost"><Sparkles size={15} /><b>cost model</b><span>select one connected program</span></div></div>;
}

function ResultBar({ label, value, max, display, color }) {
  return <div className="result-bar"><div><span>{label}</span><b>{display}</b></div><div className="bar-track"><i className={color} style={{ width: `${Math.max(2, (value / max) * 100)}%` }} /></div></div>;
}

function Fact({ value, label }) {
  return <div className="result-fact"><b>{value}</b><span>{label}</span></div>;
}

function Legend({ color, title, text }) {
  return <div className="legend-item"><i className={color} /><span><b>{title}</b><small>{text}</small></span></div>;
}

export default About;
