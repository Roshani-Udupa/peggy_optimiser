import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowRight, BookOpen } from 'lucide-react';
import './style.css';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import WorkspacePage from './pages/WorkspacePage';
import { PAPER_URL } from './pages/constants';

const DEFAULT_CODE = `public class LoopStrengthReduction {
    static void use(int value) { }

    static void run(int n) {
        int i = 0;
        while (i < n) {
            use(i * 5);
            i = i + 1;
        }
    }
}`;

async function readJson(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`The service returned ${response.status} with a non-JSON response. Check that the Java optimizer service is running.`);
  }
}



function App() {
  const [page, setPage] = useState('home');
  const [tab, setTab] = useState('source');
  const [code, setCode] = useState(DEFAULT_CODE);
  const [examples, setExamples] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [passOrder, setPassOrder] = useState('standard');

  useEffect(() => {
    fetch('/api/examples').then(readJson).then(setExamples).catch(() => setExamples([]));
  }, []);

  const snapshots = result?.snapshots || [];
  useEffect(() => {
    if (!playing || snapshots.length < 2) return undefined;
    const timer = window.setInterval(() => {
      setIteration((current) => (current + 1) % snapshots.length);
    }, 1100);
    return () => window.clearInterval(timer);
  }, [playing, snapshots.length]);

  async function optimize() {
    setBusy(true);
    setError('');
    setPlaying(false);
    try {
      const order = passOrder === 'standard'
        ? ['peephole', 'algebraic', 'constant fold', 'strength reduction', 'LICM']
        : ['strength reduction', 'peephole', 'LICM', 'algebraic', 'constant fold'];
      const response = await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, traditional_order: order }),
      });
      const data = await readJson(response);
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
      setResult(data);
      setIteration(0);
      setTab('source');
    } catch (cause) {
      setError(String(cause));
    } finally {
      setBusy(false);
    }
  }

  function navigate(next) {
    setPage(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => navigate('home')} aria-label="Peggy Optimiser home">
          <span className="brand-mark">P</span><span>Peggy <i>Optimiser</i></span>
        </button>
        <nav className="main-nav" aria-label="Main navigation">
          <button className={page === 'home' ? 'active' : ''} onClick={() => navigate('home')}>Overview</button>
          <button className={page === 'workspace' ? 'active' : ''} onClick={() => navigate('workspace')}>Workspace</button>
          <button className={page === 'about' ? 'active' : ''} onClick={() => navigate('about')}>About</button>
        </nav>
        <a className="paper-link top-paper" href={PAPER_URL} target="_blank" rel="noreferrer">
          <BookOpen size={15} /> <span>Read the paper</span> <ArrowRight size={13} />
        </a>
      </header>

      {page === 'home' && <HomePage onOpen={() => navigate('workspace')} onAbout={() => navigate('about')} />}
      {page === 'about' && <AboutPage />}
      {page === 'workspace' && (
        <WorkspacePage
          tab={tab} setTab={setTab} code={code} setCode={setCode} examples={examples}
          result={result} error={error} busy={busy} optimize={optimize} snapshots={snapshots}
          iteration={iteration} setIteration={setIteration} playing={playing} setPlaying={setPlaying}
          passOrder={passOrder} setPassOrder={setPassOrder}
        />
      )}
      <footer className="site-footer">
        <span>PEGGY OPTIMISER <b>·</b> AN INTERACTIVE EQUALITY-SATURATION EXPLORER</span>
        <a href={PAPER_URL} target="_blank" rel="noreferrer">Tate, Stepp, Tatlock, and Lerner <ArrowRight size={12} /></a>
      </footer>
    </div>
  );
}



createRoot(document.getElementById('root')).render(<App />);
