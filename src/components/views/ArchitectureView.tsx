import {
  BookOpen,
  Database,
  Brain,
  Search,
  Code2,
  Layers,
  FolderPlus,
  ArrowRight,
  Zap,
  Shield,
  GitBranch,
} from 'lucide-react';
import { MermaidDiagram } from '@/components/architecture/MermaidDiagram';
import { CodeBlock } from '@/components/architecture/CodeBlock';

/* ─── Section wrapper ─── */
function Section({
  id,
  icon: Icon,
  number,
  title,
  children,
}: {
  id: string;
  icon: React.ElementType;
  number: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 border border-primary/20">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
          <span className="text-[10px] font-mono text-primary uppercase tracking-widest">
            Section {number}
          </span>
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
        </div>
      </div>
      <div className="ml-[52px] space-y-6 text-sm leading-relaxed text-muted-foreground">
        {children}
      </div>
    </section>
  );
}

/* ─── Mini nav pill ─── */
const TOC_ITEMS = [
  { id: 'overview', label: 'System Overview' },
  { id: 'rag', label: 'RAG Engine' },
  { id: 'faiss', label: 'FAISS' },
  { id: 'llm', label: 'LLM Integration' },
  { id: 'generation', label: 'Script Generation' },
  { id: 'scalability', label: 'Scalability' },
];

/* ─── Diagrams (Mermaid) ─── */
const END_TO_END_FLOW = `graph TD
  A["🧑 User Input\\n(Natural Language)"] -->|describe test| B["📡 FastAPI\\n/scripts/generate"]
  B --> C{"Project has\\nlibrary indexed?"}
  C -->|Yes| D["🔍 RAG Engine\\nRetrieve Context"]
  C -->|No| E["⚠ Skip RAG\\nUse base prompt"]
  D --> F["📝 Prompt Builder\\nMega-Prompt Construction"]
  E --> F
  F --> G["🤖 Ollama LLM\\n(Mistral 7B / Llama3)"]
  G --> H["🛡 Code Guardrail\\nAST Validation"]
  H -->|Valid| I["✅ Generated Script\\nReturned to UI"]
  H -->|Invalid| J["❌ Rejected\\nValidation Errors"]
  J -->|retry| G

  style A fill:#1e293b,stroke:#2dd4bf,color:#e2e8f0
  style D fill:#1e293b,stroke:#7c3aed,color:#e2e8f0
  style G fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
  style H fill:#1e293b,stroke:#ef4444,color:#e2e8f0
  style I fill:#1e293b,stroke:#22c55e,color:#e2e8f0`;

const RAG_PIPELINE = `graph LR
  subgraph Ingestion["📥 Ingestion Pipeline"]
    A["Python Source\\n(.py files)"] -->|AST Parse| B["Extract Classes\\nMethods & Docstrings"]
    B -->|Chunk| C["Structured\\nDocuments"]
    C -->|Encode| D["sentence-transformers\\nall-MiniLM-L6-v2"]
    D -->|Store| E["FAISS Index\\n(IndexFlatL2)"]
  end

  subgraph Retrieval["🔍 Retrieval Pipeline"]
    F["User Query"] -->|Encode| G["Query\\nEmbedding"]
    G -->|L2 Search| E
    E -->|Top-K| H["Ranked\\nDocuments"]
  end

  H --> I["Prompt\\nAugmentation"]

  style A fill:#1e293b,stroke:#64748b,color:#e2e8f0
  style E fill:#1e293b,stroke:#7c3aed,color:#e2e8f0
  style I fill:#1e293b,stroke:#2dd4bf,color:#e2e8f0`;

const FAISS_FLOW = `graph TD
  A["Raw Documents\\n(method signatures + docstrings)"] --> B["SentenceTransformer\\n.encode()"]
  B --> C["384-dim Float32\\nEmbedding Vectors"]
  C --> D["faiss.IndexFlatL2\\n(dimension=384)"]
  D --> E["Serialized Index\\n.index file per project"]

  F["Search Query"] --> G["Query Embedding\\n(384-dim)"]
  G -->|"index.search(q, k=5)"| D
  D --> H["Distances + Indices"]
  H --> I["similarity = 1/(1+distance)"]
  I --> J["Top-K Ranked Results"]

  style D fill:#1e293b,stroke:#7c3aed,color:#e2e8f0
  style I fill:#1e293b,stroke:#2dd4bf,color:#e2e8f0`;

const SCALABILITY_FLOW = `graph TD
  A["🆕 New Project Created"] --> B["Upload Enterprise\\nLibrary Folder"]
  B --> C["POST /projects/\\n{id}/index"]
  C --> D["AST Parse\\nAll .py Files"]
  D --> E["Extract Documents\\n(classes, methods, functions)"]
  E --> F["SentenceTransformer\\n.encode(texts)"]
  F --> G["faiss.IndexFlatL2\\n(dimension)"]
  G --> H["faiss.write_index\\n→ {project_id}.index"]
  H --> I["✅ Project Ready\\nfor Generation"]

  J["Existing Index"] -.->|"No retrain needed"| G

  style A fill:#1e293b,stroke:#2dd4bf,color:#e2e8f0
  style H fill:#1e293b,stroke:#7c3aed,color:#e2e8f0
  style I fill:#1e293b,stroke:#22c55e,color:#e2e8f0`;

/* ─── Code Snippets ─── */
const FAISS_INDEX_CODE = `# rag_engine.py — LibraryIndexer.index_library()
async def index_library(self, library_path: Path, project_id: str) -> Dict:
    """Index an entire enterprise library folder into FAISS."""
    await self.initialize()

    # 1. Discover all Python source files
    python_files = list(library_path.rglob("*.py"))

    # 2. AST-parse each file → extract classes, methods, docstrings
    all_documents = []
    for py_file in python_files:
        docs = self._parse_python_file(py_file)   # ast.parse + walk
        all_documents.extend(docs)

    self.documents = all_documents

    # 3. Generate embeddings with sentence-transformers
    texts = [doc["full_text"] for doc in all_documents]
    embeddings = self.embedding_model.encode(texts)   # shape: (N, 384)

    # 4. Create FAISS L2 index and add vectors
    dimension = embeddings.shape[1]                    # 384
    self.index = faiss.IndexFlatL2(dimension)
    self.index.add(np.array(embeddings).astype('float32'))

    # 5. Persist index to disk (one file per project)
    index_path = settings.FAISS_INDEX_PATH / f"{project_id}.index"
    faiss.write_index(self.index, str(index_path))

    return { "documents_extracted": len(all_documents), ... }`;

const FAISS_SEARCH_CODE = `# rag_engine.py — LibraryIndexer.search()
def search(self, query: str, top_k: int = 5) -> List[Dict]:
    """Retrieve the most relevant library documents for a query."""

    # 1. Encode the user's natural-language query
    query_embedding = self.embedding_model.encode([query])

    # 2. FAISS L2 nearest-neighbour search
    distances, indices = self.index.search(
        np.array(query_embedding).astype('float32'),
        min(top_k, len(self.documents))
    )

    # 3. Convert L2 distance → similarity score
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        doc = self.documents[idx].copy()
        doc["score"] = float(1 / (1 + dist))   # higher = more similar
        results.append(doc)

    return results`;

const PROMPT_BUILD_CODE = `# rag_engine.py — PromptBuilder.build_prompt()
@staticmethod
def build_prompt(user_description, library_context, device_type, platform, test_type):
    """Construct the mega-prompt sent to Ollama."""

    # 1. Format retrieved library methods as context
    context_lines = ["### Available Library Methods:"]
    for doc in library_context:
        if doc["type"] == "method":
            context_lines.append(
                f"- {doc['class_name']}.{doc['signature']}: {doc['docstring'][:100]}"
            )

    # 2. Assemble: System Prompt + Constraints + Context + Task
    prompt = f"""{SYSTEM_PROMPT}

### Constraints:
- Device Type: {device_type}
- Platform: {platform}
- Only use methods from 'enterprise_lib.{device_type}'

{context_text}

### Task:
{user_description}

### Generated Python Test Script:
\\\`\\\`\\\`python
"""
    return prompt`;

const GUARDRAIL_CODE = `# rag_engine.py — CodeGuardrail.validate()
def validate(self, code: str) -> Tuple[bool, List[str]]:
    """Static analysis: syntax check + forbidden import detection."""
    errors = []

    # 1. Verify valid Python syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return False, errors

    # 2. Walk AST for forbidden imports (os, subprocess, sys, ...)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module in self.forbidden_imports:
                    errors.append(f"Forbidden import: '{module}'")

    # 3. Regex scan for dangerous patterns (exec, eval, __import__)
    dangerous = [(r'exec\\s*\\(', "exec() forbidden"), ...]
    for pattern, msg in dangerous:
        if re.search(pattern, code):
            errors.append(msg)

    return len(errors) == 0, errors`;

/* ─── Main View ─── */
export function ArchitectureView() {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="max-w-5xl mx-auto p-6 lg:p-10 space-y-16">
      {/* Hero */}
      <header className="space-y-4 animate-slide-up">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" />
          <span className="text-xs font-mono text-primary uppercase tracking-widest">
            Technical Reference
          </span>
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold text-foreground">
          SmartScript Builder —{' '}
          <span className="gradient-text">Architecture</span>
        </h1>
        <p className="text-muted-foreground max-w-2xl">
          A deep-dive into the RAG-powered, local-first automation framework. From natural
          language input to validated, executable test scripts — all running on your machine.
        </p>

        {/* TOC pills */}
        <nav className="flex flex-wrap gap-2 pt-2">
          {TOC_ITEMS.map((t) => (
            <button
              key={t.id}
              onClick={() => scrollTo(t.id)}
              className="px-3 py-1.5 text-xs font-medium rounded-full border border-border/60 text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors"
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      {/* ─── 1. System Overview ─── */}
      <Section id="overview" icon={Layers} number="01" title="System Overview">
        <p>
          The SmartScript Builder is a <strong className="text-foreground">3-tier, local-first</strong> application.
          The React frontend captures user intent, the FastAPI backend orchestrates the
          RAG pipeline, and a local Ollama instance runs the LLM — all without leaving your network.
        </p>
        <div className="flex flex-wrap gap-3 py-2">
          {['React 18 + Vite', 'FastAPI (Python 3.10+)', 'Ollama (7B LLM)', 'SQLite', 'FAISS', 'sentence-transformers'].map((t) => (
            <span key={t} className="px-3 py-1 rounded-lg bg-secondary text-secondary-foreground text-xs font-mono">
              {t}
            </span>
          ))}
        </div>
        <MermaidDiagram chart={END_TO_END_FLOW} title="End-to-End Flow" />
        <div className="glass-card p-5 space-y-3">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-primary" /> Step-by-Step Walkthrough
          </h4>
          <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
            <li><strong className="text-foreground">User Input</strong> — A natural-language description is entered in the Execute Test panel (e.g. <em>"Login to Gmail and verify inbox count"</em>).</li>
            <li><strong className="text-foreground">API Endpoint</strong> — The frontend POSTs to <code className="font-mono text-primary text-xs">/scripts/generate</code> with the description, project ID, device type, and platform.</li>
            <li><strong className="text-foreground">RAG Retrieval</strong> — The <code className="font-mono text-xs text-accent">LibraryIndexer</code> searches the project's FAISS index for relevant enterprise library methods.</li>
            <li><strong className="text-foreground">Prompt Construction</strong> — The <code className="font-mono text-xs text-accent">PromptBuilder</code> assembles a mega-prompt: system constraints + retrieved context + task.</li>
            <li><strong className="text-foreground">LLM Generation</strong> — The prompt is sent to the local Ollama server which streams back a Python test script.</li>
            <li><strong className="text-foreground">Code Guardrail</strong> — The <code className="font-mono text-xs text-accent">CodeGuardrail</code> validates syntax (AST parse) and blocks forbidden imports before returning the script.</li>
          </ol>
        </div>
      </Section>

      {/* ─── 2. RAG Engine ─── */}
      <Section id="rag" icon={Search} number="02" title="The RAG Engine">
        <p>
          Retrieval-Augmented Generation lets the LLM reference <strong className="text-foreground">proprietary enterprise
          libraries</strong> it was never trained on. Instead of fine-tuning, we inject relevant context into the
          prompt at query time.
        </p>

        <div className="glass-card p-5 space-y-4">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Database className="w-4 h-4 text-accent" /> Document Chunking Strategy
          </h4>
          <p>
            Unlike traditional text-splitting RAG, SmartScript uses <strong className="text-foreground">AST-based structural chunking</strong>.
            Each Python file is parsed with <code className="font-mono text-xs text-primary">ast.parse()</code>, and the tree is walked
            to extract semantically meaningful units:
          </p>
          <ul className="list-disc list-inside space-y-1.5">
            <li><strong className="text-foreground">Class documents</strong> — Class name + docstring + list of methods</li>
            <li><strong className="text-foreground">Method documents</strong> — Class context + method signature + arguments + docstring</li>
            <li><strong className="text-foreground">Function documents</strong> — Standalone function signature + docstring</li>
          </ul>
          <p>
            Each document's <code className="font-mono text-xs text-primary">full_text</code> field concatenates the signature
            with its docstring, creating a single semantic unit optimized for embedding similarity.
          </p>
        </div>

        <MermaidDiagram chart={RAG_PIPELINE} title="Ingestion → Retrieval Pipeline" />

        <div className="glass-card p-5 space-y-3">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-primary" /> Retrieval Logic
          </h4>
          <p>
            At query time, the user's description is encoded into the same 384-dimensional
            vector space. FAISS performs an exact L2 nearest-neighbour search and returns
            the top-K most similar library documents. These are injected into the prompt
            as <code className="font-mono text-xs text-primary">### Available Library Methods</code>.
          </p>
          <p>
            A <strong className="text-foreground">keyword-matching fallback</strong> activates when FAISS or sentence-transformers
            are not installed, ensuring the system degrades gracefully.
          </p>
        </div>
      </Section>

      {/* ─── 3. FAISS ─── */}
      <Section id="faiss" icon={Database} number="03" title="The Role of FAISS">
        <p>
          <strong className="text-foreground">FAISS (Facebook AI Similarity Search)</strong> is a library optimised for
          billion-scale similarity search over dense vectors. SmartScript uses it because:
        </p>
        <ul className="list-disc list-inside space-y-1.5">
          <li><strong className="text-foreground">Speed</strong> — <code className="font-mono text-xs text-primary">IndexFlatL2</code> performs brute-force L2 on CPU in microseconds for our document sizes (&lt;10K vectors).</li>
          <li><strong className="text-foreground">Zero infrastructure</strong> — No database server; the index is a single file per project.</li>
          <li><strong className="text-foreground">Exact search</strong> — For enterprise libraries (hundreds, not billions of methods), exact search is preferred over approximate to avoid recall loss.</li>
          <li><strong className="text-foreground">Persistence</strong> — <code className="font-mono text-xs text-primary">faiss.write_index / read_index</code> serialise to disk, enabling per-project isolation.</li>
        </ul>

        <MermaidDiagram chart={FAISS_FLOW} title="FAISS Vector Search Pipeline" />

        <div className="glass-card p-5 space-y-3">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Zap className="w-4 h-4 text-warning" /> How Similarity is Calculated
          </h4>
          <p>
            FAISS computes the <strong className="text-foreground">Euclidean (L2) distance</strong> between the query
            vector <em>q</em> and every stored vector <em>v<sub>i</sub></em>:
          </p>
          <div className="bg-muted/40 rounded-lg p-4 font-mono text-sm text-center text-foreground">
            d(q, v) = √( Σ (q<sub>j</sub> − v<sub>j</sub>)² ) &nbsp;&nbsp;for j = 1…384
          </div>
          <p>
            The raw distance is converted to a <strong className="text-foreground">similarity score</strong> via:
          </p>
          <div className="bg-muted/40 rounded-lg p-4 font-mono text-sm text-center text-foreground">
            similarity = 1 / (1 + distance)
          </div>
          <p>
            A similarity of <strong className="text-foreground">1.0</strong> means identical vectors; values approach
            <strong className="text-foreground"> 0</strong> as vectors diverge. The top-K documents with the highest
            similarity are returned.
          </p>
        </div>

        <CodeBlock
          code={FAISS_INDEX_CODE}
          language="python"
          title="FAISS Indexing — Source Code"
          fileName="rag_engine.py"
        />
        <CodeBlock
          code={FAISS_SEARCH_CODE}
          language="python"
          title="FAISS Retrieval — Source Code"
          fileName="rag_engine.py"
        />
      </Section>

      {/* ─── 4. LLM Integration ─── */}
      <Section id="llm" icon={Brain} number="04" title="LLM Integration & Prompt Augmentation">
        <p>
          The local Ollama instance hosts a quantised 7B parameter model (Mistral or Llama 3).
          The key innovation is the <strong className="text-foreground">mega-prompt structure</strong> that constrains
          the LLM's output to only use verified enterprise library methods.
        </p>

        <div className="glass-card p-5 space-y-3">
          <h4 className="text-sm font-semibold text-foreground">Prompt Anatomy</h4>
          <div className="space-y-2">
            {[
              { label: 'System Prompt', desc: 'Strict rules: only use enterprise_lib, no forbidden imports, return Python only', color: 'bg-destructive/20 border-destructive/30' },
              { label: 'Constraints', desc: 'Device type (web/mobile), platform (chrome/android), test type (functional/regression)', color: 'bg-warning/20 border-warning/30' },
              { label: 'RAG Context', desc: 'Top-K library methods retrieved from FAISS, formatted as method signatures with docstrings', color: 'bg-accent/20 border-accent/30' },
              { label: 'User Task', desc: 'The natural-language test description provided by the user', color: 'bg-primary/20 border-primary/30' },
            ].map((s) => (
              <div key={s.label} className={`flex items-start gap-3 p-3 rounded-lg border ${s.color}`}>
                <ArrowRight className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <strong className="text-foreground text-xs">{s.label}</strong>
                  <p className="text-xs text-muted-foreground mt-0.5">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <CodeBlock
          code={PROMPT_BUILD_CODE}
          language="python"
          title="Prompt Construction — Source Code"
          fileName="rag_engine.py"
        />
      </Section>

      {/* ─── 5. Script Generation ─── */}
      <Section id="generation" icon={Code2} number="05" title="Script Generation & Guardrail">
        <p>
          Once Ollama returns the generated Python script, it passes through the{' '}
          <strong className="text-foreground">Code Guardrail</strong> — a static analysis layer that prevents
          malicious or unsafe code from ever reaching the execution engine.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Code2, title: 'Syntax Check', desc: 'ast.parse() ensures valid Python before proceeding' },
            { icon: Shield, title: 'Import Blocklist', desc: 'AST walk detects os, subprocess, sys, shutil, socket, requests' },
            { icon: Zap, title: 'Pattern Scan', desc: 'Regex catches exec(), eval(), __import__(), file writes' },
          ].map((g) => (
            <div key={g.title} className="glass-card p-4 space-y-2">
              <g.icon className="w-5 h-5 text-primary" />
              <h4 className="text-sm font-semibold text-foreground">{g.title}</h4>
              <p className="text-xs text-muted-foreground">{g.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock
          code={GUARDRAIL_CODE}
          language="python"
          title="Code Guardrail — Source Code"
          fileName="rag_engine.py"
        />

        <p>
          If validation fails, the errors are returned to the frontend and the script is
          either rejected or re-generated with adjusted constraints. Successfully validated
          scripts can be saved as <strong className="text-foreground">TestCase</strong> records in SQLite or
          executed immediately via the automation adapters (Playwright / Appium).
        </p>
      </Section>

      {/* ─── 6. Scalability ─── */}
      <Section id="scalability" icon={FolderPlus} number="06" title="Scalability — Adding New Projects">
        <p>
          A critical design goal is that <strong className="text-foreground">adding a new project never requires
          retraining the embedding model</strong>. The sentence-transformer model is frozen; only the
          FAISS index grows.
        </p>

        <MermaidDiagram chart={SCALABILITY_FLOW} title="New Project Ingestion Workflow" />

        <div className="glass-card p-5 space-y-3">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" /> Isolation & Independence
          </h4>
          <ul className="list-disc list-inside space-y-1.5">
            <li>Each project gets its own <code className="font-mono text-xs text-primary">{'{project_id}.index'}</code> file — projects never share indices.</li>
            <li>Indexing is triggered via <code className="font-mono text-xs text-primary">POST /projects/{'{id}'}/index</code> and runs asynchronously.</li>
            <li>Re-indexing a project simply overwrites the previous index file — no schema migration or downtime.</li>
            <li>The embedding model (<code className="font-mono text-xs text-primary">all-MiniLM-L6-v2</code>) loads once at startup and is shared across all projects.</li>
            <li>For large enterprise libraries (&gt;1000 methods), FAISS supports <code className="font-mono text-xs text-primary">IndexIVFFlat</code> for approximate search — a one-line swap.</li>
          </ul>
        </div>
      </Section>

      {/* Footer */}
      <footer className="border-t border-border/40 pt-8 pb-4 text-center text-xs text-muted-foreground">
        SmartScript Builder v1.1 — Technical Architecture Reference
        <br />
        <span className="text-[10px]">
          RAG Engine · FAISS · Ollama · FastAPI · React 18 · Local-First
        </span>
      </footer>
    </div>
  );
}
