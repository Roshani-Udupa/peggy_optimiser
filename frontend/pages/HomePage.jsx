import { ArrowDownRight, ArrowRight, ChevronRight, Sparkles } from 'lucide-react';

function Landing({ onOpen, onAbout }) {
  return (
    <main className="landing page-enter">
      <div className="landing-glow glow-one" /><div className="landing-glow glow-two" />
      <div className="hero-copy">
        <div className="eyebrow"><span className="pulse-dot" /> A VISUAL GUIDE TO COMPILER OPTIMIZATION</div>
        <h1>Keep every good<br /><em>idea in play.</em></h1>
        <p>See how an optimizer translates Java into a value graph, collects equivalent programs, and chooses a low-cost result at the end.</p>
        <div className="hero-actions">
          <button className="button-primary" onClick={onOpen}>Open the workspace <ArrowRight size={16} /></button>
          <button className="button-quiet" onClick={onAbout}>Explore the approach <ChevronRight size={15} /></button>
        </div>
      </div>
      <div className="hero-art" aria-label="Illustration of equivalent program forms joining into one graph">
        <div className="art-orbit orbit-a" /><div className="art-orbit orbit-b" />
        <div className="art-node art-source"><span>JAVA METHOD</span><code>value * 8 + 0</code></div>
        <div className="art-branch"><span>× 8</span><span>+ 0</span></div>
        <div className="art-node art-choice"><span>EQUIVALENT FORMS</span><div><code>value × 8</code><code>value &lt;&lt; 3</code></div></div>
        <div className="art-result"><Sparkles size={16} /><span>LOWER COST</span></div>
        <svg className="art-lines" viewBox="0 0 560 450" aria-hidden="true"><path d="M105 214 C170 214 165 135 244 135"/><path d="M105 214 C170 214 165 295 244 295"/><path d="M345 135 C415 135 402 214 468 214"/><path d="M345 295 C415 295 402 214 468 214"/></svg>
      </div>
      <button className="scroll-cue" onClick={onAbout}><span>THE IDEA IN ONE MINUTE</span><ArrowDownRight size={15} /></button>
    </main>
  );
}

export default Landing;
