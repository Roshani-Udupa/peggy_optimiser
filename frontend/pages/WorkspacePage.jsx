import { ArrowRight, Check, CheckCircle2, CircleHelp, Pause, Play, RotateCcw, Sparkles, TriangleAlert, Workflow } from 'lucide-react';
import { EXPLANATIONS, PASS_LABELS, WORKSPACE_TABS } from './constants';

function Workspace(props) {
  const explanation = EXPLANATIONS[props.tab];
  return (
    <main className="workspace-page page-enter">
      <div className="workspace-heading"><div><div className="eyebrow">INTERACTIVE JAVA OPTIMIZATION WALKTHROUGH</div><h1>Follow the program through each stage.</h1></div><button className="button-primary run-button" onClick={props.optimize} disabled={props.busy}>{props.busy ? <span className="spinner" /> : <Play size={15} />}{props.busy ? 'Working' : 'Optimize Java'}</button></div>
      <div className="stage-progress">{WORKSPACE_TABS.map((item, index) => <button key={item.id} className={props.tab === item.id ? 'current' : props.result && WORKSPACE_TABS.findIndex((x) => x.id === props.tab) > index ? 'done' : ''} onClick={() => props.setTab(item.id)}><span>{props.result && WORKSPACE_TABS.findIndex((x) => x.id === props.tab) > index ? <Check size={12} /> : `0${index + 1}`}</span><i /></button>)}</div>
      <div className="workspace-tabs" role="tablist" aria-label="Optimization stages">
        {WORKSPACE_TABS.map(({ id, label, icon: Icon }) => <button role="tab" aria-selected={props.tab === id} key={id} className={props.tab === id ? 'selected' : ''} onClick={() => props.setTab(id)}><Icon size={15} />{label}</button>)}
      </div>
      <div className="stage-intro"><div className="stage-number">{explanation.number}</div><div><h2>{explanation.title}</h2><p>{explanation.body}</p></div><span className="stage-count">STAGE {explanation.number} / 05</span></div>
      {props.error && <div className="error-banner"><TriangleAlert size={16} /><span>{props.error}</span><button onClick={() => props.setTab('source')}>Review source</button></div>}
      <div className="tab-content" key={props.tab}>
        {props.tab === 'source' && <SourceStage {...props} />}
        {props.tab === 'comparison' && <ComparisonStage {...props} />}
        {props.tab === 'saturation' && <SaturationStage {...props} />}
        {props.tab === 'extraction' && <ExtractionStage {...props} />}
        {props.tab === 'validation' && <ValidationStage {...props} />}
      </div>
      <div className="stage-navigation"><button className="button-quiet" onClick={() => props.setTab(WORKSPACE_TABS[Math.max(0, WORKSPACE_TABS.findIndex((item) => item.id === props.tab) - 1)].id)} disabled={props.tab === 'source'}>Previous stage</button><button className="button-primary" onClick={() => props.setTab(WORKSPACE_TABS[Math.min(WORKSPACE_TABS.length - 1, WORKSPACE_TABS.findIndex((item) => item.id === props.tab) + 1)].id)} disabled={props.tab === 'validation'}>Next stage <ArrowRight size={15} /></button></div>
    </main>
  );
}

function SourceStage({ code, setCode, examples, result, passOrder, setPassOrder, optimize, busy }) {
  return <div className="stage-grid source-grid">
    <section className="panel source-panel"><div className="panel-heading"><div><span className="panel-kicker">INPUT</span><h3>Java source</h3></div><select aria-label="Choose an example" onChange={(event) => { const sample = examples.find((item) => item.name === event.target.value); if (sample) setCode(sample.code); }}><option value="">Choose a Java example</option>{examples.map((item) => <option value={item.name} key={item.name}>{item.name.replaceAll('_', ' ')}</option>)}</select></div><textarea spellCheck="false" aria-label="Java source code" value={code} onChange={(event) => setCode(event.target.value)} /><div className="source-options"><label>Traditional pass order<select value={passOrder} onChange={(event) => setPassOrder(event.target.value)}><option value="standard">Algebraic simplification first</option><option value="reversed">Strength reduction first</option></select></label></div><div className="source-bottom"><span>Supported subset: integer and boolean methods, branches, loops, and simple array or field access</span><button className="button-primary" onClick={optimize} disabled={busy}><Sparkles size={14} /> Run pipeline</button></div></section>
    <section className="panel graph-panel"><div className="panel-heading"><div><span className="panel-kicker">TRANSLATION</span><h3>Program Expression Graph</h3></div><span className="small-counter">{result?.peg?.length || 0} values</span></div>{result ? <PegGraph nodes={result.peg} /> : <GraphPlaceholder />}<div className="graph-key"><Legend color="violet" title="Loop sequence" text="Carries a changing value" /><Legend color="pink" title="Branch merge" text="Chooses a branch result" /><Legend color="blue" title="Memory state" text="Connects reads and writes" /></div></section>
    {result && <div className="inline-summary"><CheckCircle2 size={16} /><span>Java parsed successfully. The optimizer created {result.peg.length} graph values and {result.snapshots.length} saturation snapshots.</span><button onClick={() => document.querySelector('.workspace-tabs button:nth-child(2)')?.click()}>Compare strategies <ArrowRight size={13} /></button></div>}
  </div>;
}

function ComparisonStage({ result, snapshots, iteration, setIteration, playing, setPlaying }) {
  return <div className="stage-grid compare-grid">
    <section className="panel compare-panel traditional-panel"><div className="panel-heading"><div><span className="panel-kicker">SEQUENCE OF REPLACEMENTS</span><h3>Traditional optimizer</h3></div><span className="small-counter">one program at a time</span></div><p className="panel-description">Every pass receives the previous pass’s output. Try changing pass order in Source and graph, then compare the trail.</p>{result ? <><pre className="code-result">{result.traditional.code}</pre><div className="pass-list">{result.traditional.steps.map((step, index) => <div className="pass-row" key={`${step.pass}-${index}`}><span className="pass-index">{String(index + 1).padStart(2, '0')}</span><div><b>{PASS_LABELS[step.pass] || step.pass}</b><code>{step.code}</code></div><small>estimated cost {step.cost}</small></div>)}</div></> : <EmptyState title="Run Java source to see the pass sequence" text="Each row will show what changed and the estimated cost after that pass." />}</section>
    <section className="panel compare-panel saturation-panel"><div className="panel-heading"><div><span className="panel-kicker">EQUIVALENT FORMS STAY AVAILABLE</span><h3>Equality saturation</h3></div><span className="small-counter purple-counter">{result ? `${result.snapshots.length} sweeps` : 'ready to compare'}</span></div><p className="panel-description">One iteration is a complete sweep through the rewrite families. Sweeps continue until a sweep adds no new equalities, or a configured iteration or graph-size limit is reached.</p>{result && <p className="panel-description">This run stopped at <b>{result.saturation?.stop_reason?.replaceAll('_', ' ')}</b>{result.saturation?.stop_reason === 'iteration_limit' ? ` (${result.saturation.iteration_limit} sweeps)` : ''}{result.saturation?.stop_reason === 'node_limit' ? ` (${result.saturation.node_limit} graph values)` : ''}. Larger inputs can take more sweeps; the resource limits bound graph growth and runtime.</p>}{result ? <><SaturationControls snapshots={snapshots} iteration={iteration} setIteration={setIteration} playing={playing} setPlaying={setPlaying} /><ResultGraph snapshots={snapshots} iteration={iteration} /></> : <EqualityDiagram />}</section>
    <div className="compare-callout"><Sparkles size={16} /><span><b>What to look for:</b> a cheaper local expression can hide an optimization that needs the original structure. Equalities preserve both paths until extraction.</span></div>
  </div>;
}

function SaturationStage({ result, snapshots, iteration, setIteration, playing, setPlaying }) {
  const snapshot = snapshots[iteration];
  return <div className="stage-grid saturation-detail-grid">
    <section className="panel saturation-main"><div className="panel-heading"><div><span className="panel-kicker">RULES ADD NODES AND MERGE CLASSES</span><h3>Equivalence graph growth</h3></div><span className="small-counter">{snapshot ? `${snapshot.nodes.length} graph values` : 'awaiting source'}</span></div>{result ? <><SaturationControls snapshots={snapshots} iteration={iteration} setIteration={setIteration} playing={playing} setPlaying={setPlaying} /><ClassGraph snapshot={snapshot} /></> : <EmptyState title="The graph will appear here" text="Run Java source to inspect the graph after each equality-saturation iteration." />}</section>
    <aside className="panel iteration-aside"><span className="panel-kicker">WHY IT CHANGED</span><h3>Iteration notes</h3>{snapshot ? <><div className="iteration-number">{String(snapshot.iteration).padStart(2, '0')}</div><p className="iteration-caption">This is sweep {snapshot.iteration} through the rewrite families. It applies patterns to the graph built by earlier sweeps; it is not a fixed two-iteration algorithm.</p><div className="rule-list">{snapshot.fired.length ? snapshot.fired.map((rule) => <div className="rule-item" key={rule}><span><Check size={12} /></span>{rule.replaceAll('-', ' ')}</div>) : <div className="quiet-note">No new equality was found in this sweep, so the graph reached a fixed point.</div>}</div><div className="graph-stat"><span>Value classes</span><b>{Object.keys(snapshot.classes).length}</b></div><div className="graph-stat"><span>Graph values</span><b>{snapshot.nodes.length}</b></div></> : <EmptyState title="No iteration log yet" text="The log will name the rules that fired when you run the pipeline." />}</aside>
    <div className="compare-callout"><CircleHelp size={16} /><span><b>How to read a class:</b> a solid box holds one known form. A dashed box holds several equal forms. Every form points to the classes that supply its inputs.</span></div>
  </div>;
}

function ExtractionStage({ result }) {
  return <div className="stage-grid extract-grid">
    <section className="panel extraction-panel"><div className="panel-heading"><div><span className="panel-kicker">GLOBAL COST DECISION</span><h3>Binary integer solver</h3></div><span className={`status-pill ${result?.extraction.status === 'Optimal' ? 'status-good' : ''}`}>{result?.extraction.status || 'awaiting run'}</span></div><p className="panel-description">The solver chooses graph values whose dependencies are included. The objective favors lower-cost operations and gives loop work a larger weight.</p>{result ? <><CostDiagram extraction={result.extraction} /><div className="selected-nodes"><span className="panel-kicker">SELECTED GRAPH VALUES</span><p>{result.extraction.selected.length ? result.extraction.selected.join(', ') : 'No values were selected by the solver.'}</p></div></> : <EmptyState title="No solver result yet" text="The binary model and its statistics will appear after you run a program." />}</section>
    <aside className="panel cost-aside"><span className="panel-kicker">COST MODEL</span><h3>Work inside loops matters more</h3><div className="cost-equation"><span>operator estimate</span><b>×</b><span>20 <sup>loop depth</sup></span></div><div className="cost-bars"><div><span>Outside a loop</span><i style={{ '--bar': '14%' }} /></div><div><span>One loop deep</span><i style={{ '--bar': '47%' }} /></div><div><span>Two loops deep</span><i style={{ '--bar': '100%' }} /></div></div><p>The paper scales node costs by loop depth so work repeated on every iteration is less attractive.</p></aside>
  </div>;
}

function ValidationStage({ result, optimize, busy }) {
  const valid = result?.validation?.equivalent;
  return <div className="stage-grid validate-grid">
    <section className="panel validation-panel"><div className="panel-heading"><div><span className="panel-kicker">TRANSLATION VALIDATION</span><h3>Compare input and generated output</h3></div>{result && <span className={`validation-badge ${valid ? 'valid' : 'invalid'}`}>{valid ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}{result.validation.message}</span>}</div><div className="program-pair"><div><span>INPUT METHOD</span><pre>{result?.source || 'Run a Java method to begin validation.'}</pre></div><ArrowRight className="pair-arrow" size={20} /><div><span>GENERATED JAVA OUTPUT</span><pre>{result?.code || 'The generated output will appear here.'}</pre></div></div><div className="validation-details"><div className="validation-detail"><b>{result?.validation.samples ?? '—'}</b><span>interpreter samples compared</span></div><div className="validation-detail"><b>{result ? (result.validation.equivalent ? 'Roots merged' : 'Not proven') : '—'}</b><span>graph-based check</span></div><button className="button-primary validation-run" onClick={optimize} disabled={busy}>{busy ? 'Checking…' : 'Run check again'} <RotateCcw size={12} /></button></div></section>
  </div>;
}

function PegGraph({ nodes }) {
  const visible = nodes.slice(0, 32);
  const columns = 4;
  const cellW = 172;
  const cellH = 76;
  const height = Math.max(210, Math.ceil(visible.length / columns) * cellH);
  const positions = new Map(visible.map((node, index) => [node.id, { x: 15 + (index % columns) * cellW, y: 12 + Math.floor(index / columns) * cellH }]));
  return <div className="peg-graph-wrap"><svg className="peg-graph" viewBox={`0 0 ${columns * cellW} ${height}`} role="img" aria-label="Program Expression Graph with operation dependencies">
    {visible.flatMap((node) => (node.children || []).filter((child) => positions.has(child)).map((child, edgeIndex) => { const from = positions.get(child); const to = positions.get(node.id); return <path key={`${node.id}-${child}-${edgeIndex}`} className="live-edge" d={`M${from.x + 62} ${from.y + 50} C${from.x + 75} ${from.y + 76}, ${to.x + 75} ${to.y - 4}, ${to.x + 75} ${to.y + 8}`} />; }))}
    {visible.map((node) => { const position = positions.get(node.id); const op = node.op.toLowerCase(); const theme = op.startsWith('theta') || op.startsWith('eval') || op.startsWith('pass') ? 'violet' : op === 'phi' ? 'pink' : op.includes('load') || op.includes('store') || op === 'sigma' || op.includes('proj') ? 'blue' : 'neutral'; return <g key={node.id} className={`live-node ${theme}`} transform={`translate(${position.x},${position.y})`}><rect width="145" height="48" rx="10" /><text x="11" y="20">{nodeLabel(node.op)}</text><text className="live-node-detail" x="11" y="36">{node.value ?? (node.children?.length ? `depends on ${node.children.length} values` : 'input value')}</text></g>; })}
  </svg>{nodes.length > visible.length && <p className="graph-overflow">Showing the first {visible.length} of {nodes.length} graph values.</p>}</div>;
}

function nodeLabel(op) {
  if (op.startsWith('theta')) return 'loop sequence';
  if (op.startsWith('eval')) return 'value after loop';
  if (op.startsWith('pass')) return 'loop exit position';
  if (op === 'phi') return 'conditional merge';
  if (op === 'sigma') return 'shared heap';
  if (op === 'param') return 'method input';
  if (op === 'const') return 'constant';
  if (op === 'invoke') return 'method call';
  if (op === 'arrayload') return 'array read';
  if (op === 'arraystore') return 'array write';
  if (op === 'fieldload') return 'field read';
  if (op === 'fieldstore') return 'field write';
  return op;
}

function EmptyState({ title, text }) {
  return <div className="empty-state"><span><Workflow size={17} /></span><b>{title}</b><p>{text}</p></div>;
}

function EqualityDiagram() {
  return <div className="equality-diagram"><div className="eq-input">a × 8</div><span className="eq-link">↔</span><div className="eq-class"><small>SAME VALUE</small><b>a × 8</b><b>a &lt;&lt; 3</b></div><ArrowRight size={18} /><div className="eq-output">choose by cost</div></div>;
}

function SaturationControls({ snapshots = [], iteration = 0, setIteration = () => {}, playing = false, setPlaying = () => {} }) {
  if (!snapshots.length) return null;
  return <div className="saturation-controls"><button aria-label={playing ? 'Pause iterations' : 'Play iterations'} onClick={() => setPlaying(!playing)}>{playing ? <Pause size={14} /> : <Play size={14} />}</button><input type="range" min="0" max={Math.max(0, snapshots.length - 1)} value={iteration} onChange={(event) => { setPlaying(false); setIteration(Number(event.target.value)); }} /><span>Iteration {snapshots[iteration]?.iteration ?? 0} of {snapshots.length}</span></div>;
}

function ClassGraph({ snapshot }) {
  if (!snapshot) return <EmptyState title="No graph snapshot" text="No saturation iteration is available for this input." />;
  const classes = Object.entries(snapshot.classes || {});
  return <div className="class-graph">{classes.slice(0, 60).map(([id, members]) => <article key={id} className={`value-class ${members.length > 1 ? 'contains-equalities' : ''}`}><span className="class-label">VALUE CLASS {id}</span><div className="class-chips">{members.map((member) => { const node = snapshot.nodes[member]; return node && <span key={member} className={`class-chip ${node.op.startsWith('theta') ? 'chip-violet' : node.op === 'phi' ? 'chip-pink' : ''}`}>{nodeLabel(node.op)}{node.value !== null && node.value !== undefined ? ` · ${node.value}` : ''}</span>; })}</div><small>{members.length > 1 ? `${members.length} equivalent forms` : 'one known form'}</small></article>)}</div>;
}

function ResultGraph({ snapshots, iteration }) {
  const snapshot = snapshots[iteration];
  return snapshot ? <ClassGraph snapshot={snapshot} /> : <EmptyState title="No equivalence graph" text="The run did not produce an iteration snapshot." />;
}

function CostDiagram({ extraction }) {
  const selected = new Set(extraction.selected || []);
  const stages = ['Input graph', 'Binary choices', 'Lowest estimated cost'];
  return <div className="cost-diagram">{stages.map((stage, index) => <div className="cost-stage" key={stage}><span className="cost-stage-index">0{index + 1}</span><b>{stage}</b><small>{index === 0 ? `${extraction.selected.length} selected values` : index === 1 ? `${extraction.variables} choices · ${extraction.constraints} constraints` : `Objective ${extraction.objective ?? 'not available'}`}</small>{index < stages.length - 1 && <ArrowRight size={15} />}</div>)}<div className="selection-chips">{(extraction.selected || []).slice(0, 24).map((node) => <span key={node} className={selected.has(node) ? 'chosen' : ''}>value {node}</span>)}</div></div>;
}

function Legend({ color, title, text }) {
  return <div className="legend-item"><i className={color} /><span><b>{title}</b><small>{text}</small></span></div>;
}

function GraphPlaceholder() {
  return <div className="graph-placeholder"><div className="placeholder-line line-a" /><div className="placeholder-line line-b" /><div className="placeholder-node node-a">loop sequence</div><div className="placeholder-node node-b">conditional merge</div><div className="placeholder-node node-c">multiply</div><span>Run Java to build the live graph</span></div>;
}


export default Workspace;
