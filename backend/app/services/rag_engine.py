"""
RAG Engine - Library Indexing, Prompt Construction, and Code Guardrail.
Implements SRS Section 4: Script Generation Engine.

Flow:
1. Library Indexing - AST-parse enterprise libs → FAISS vector index
2. Example Script Indexing - Index real scripts for few-shot learning
3. Prompt Construction - Lean mega-prompt (context + examples + task)
4. Code Guardrail - AST-based quality + security validation
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np
from loguru import logger

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available - using keyword matching fallback")

from app.config import settings


# ---------------------------------------------------------------------------
# Resolve example scripts directory relative to this file (cross-platform)
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_EXAMPLES_DIR = _THIS_DIR / "example_scripts"


class LibraryIndexer:
    """
    Indexes enterprise Python libraries + example scripts into a FAISS index
    for semantic retrieval during prompt construction.
    """

    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents: List[Dict] = []
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    async def initialize(self):
        if self._initialized:
            return
        if FAISS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                self._initialized = True
                logger.info(f"Embedding model loaded: {settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        else:
            self._initialized = True  # keyword fallback

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_python_file(file_path: Path) -> List[Dict]:
        """AST-parse a Python file → list of class/method/function documents."""
        documents: List[Dict] = []
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            module = file_path.stem

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    cls_doc = ast.get_docstring(node) or ""
                    documents.append({
                        "type": "class", "name": node.name,
                        "module": module, "docstring": cls_doc,
                        "full_text": f"class {node.name}: {cls_doc}",
                    })
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            mdoc = ast.get_docstring(item) or ""
                            args = [a.arg for a in item.args.args if a.arg != "self"]
                            sig = f"{item.name}({', '.join(args)})"
                            documents.append({
                                "type": "method", "name": item.name,
                                "class_name": node.name, "module": module,
                                "signature": sig, "docstring": mdoc,
                                "full_text": f"{node.name}.{sig}: {mdoc}",
                            })

                elif isinstance(node, ast.FunctionDef):
                    fdoc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args]
                    sig = f"{node.name}({', '.join(args)})"
                    documents.append({
                        "type": "function", "name": node.name,
                        "module": module, "signature": sig,
                        "docstring": fdoc,
                        "full_text": f"{sig}: {fdoc}",
                    })
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        return documents

    @staticmethod
    def _parse_example_script(file_path: Path) -> List[Dict]:
        """Parse a complete example script for few-shot indexing."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree) or file_path.stem.replace("_", " ")
            return [{
                "type": "example_script",
                "name": file_path.stem,
                "module": "examples",
                "file_path": str(file_path),
                "docstring": docstring,
                "source_code": source,
                "full_text": f"Example - {docstring}: {source[:1500]}",
            }]
        except Exception as e:
            logger.warning(f"Error parsing example script {file_path}: {e}")
            return []

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def index_library(self, library_path: Path, project_id: str) -> Dict:
        await self.initialize()
        library_path = Path(library_path)
        if not library_path.exists():
            raise ValueError(f"Library path does not exist: {library_path}")

        python_files = list(library_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files in {library_path}")

        all_docs: List[Dict] = []
        for pf in python_files:
            all_docs.extend(self._parse_python_file(pf))

        # Also index STB driver if present
        stb_driver = Path("backend/libs/stb/stb_driver.py")
        if stb_driver.exists():
            stb_docs = self._parse_python_file(stb_driver)
            all_docs.extend(stb_docs)
            logger.info(f"Indexed STB driver: {len(stb_docs)} docs")

        # Index example scripts (cross-platform path)
        if _EXAMPLES_DIR.exists():
            for ef in _EXAMPLES_DIR.glob("*.py"):
                all_docs.extend(self._parse_example_script(ef))
            logger.info(f"Indexed example scripts from {_EXAMPLES_DIR}")

        self.documents = all_docs
        logger.info(f"Total documents indexed: {len(all_docs)}")

        # Build FAISS index
        if FAISS_AVAILABLE and self.embedding_model and all_docs:
            texts = [d["full_text"] for d in all_docs]
            embeddings = self.embedding_model.encode(texts)
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(np.array(embeddings, dtype="float32"))

            idx_path = settings.FAISS_INDEX_PATH / f"{project_id}.index"
            faiss.write_index(self.index, str(idx_path))
            logger.info(f"FAISS index saved: {idx_path}")

        return {
            "project_id": project_id,
            "library_path": str(library_path),
            "files_indexed": len(python_files),
            "documents_extracted": len(all_docs),
            "indexed_at": datetime.utcnow().isoformat(),
            "classes": sum(1 for d in all_docs if d["type"] == "class"),
            "methods": sum(1 for d in all_docs if d["type"] == "method"),
            "functions": sum(1 for d in all_docs if d["type"] == "function"),
            "example_scripts": sum(1 for d in all_docs if d["type"] == "example_script"),
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        if not self.documents:
            return []

        if FAISS_AVAILABLE and self.index and self.embedding_model:
            qe = self.embedding_model.encode([query])
            dists, idxs = self.index.search(np.array(qe, dtype="float32"), min(top_k, len(self.documents)))
            seen, results = set(), []
            for idx, dist in zip(idxs[0], dists[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    if doc["full_text"] not in seen:
                        doc["score"] = float(1 / (1 + dist))
                        results.append(doc)
                        seen.add(doc["full_text"])
            return results

        # Keyword fallback
        terms = query.lower().split()
        scored = []
        for doc in self.documents:
            txt = doc["full_text"].lower()
            sc = sum(1 for t in terms if t in txt)
            if sc > 0:
                d = doc.copy()
                d["score"] = sc / len(terms)
                scored.append(d)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def get_example_scripts(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Return the most relevant example scripts for few-shot prompting."""
        scripts = [d for d in self.documents if d.get("type") == "example_script"]
        if not scripts:
            return []

        if FAISS_AVAILABLE and self.embedding_model:
            texts = [d["full_text"] for d in scripts]
            embs = self.embedding_model.encode(texts)
            dim = embs.shape[1]
            tmp = faiss.IndexFlatL2(dim)
            tmp.add(np.array(embs, dtype="float32"))
            qe = self.embedding_model.encode([query])
            _, idxs = tmp.search(np.array(qe, dtype="float32"), min(top_k, len(scripts)))
            return [
                {"description": scripts[i].get("docstring", "Example"), "code": scripts[i]["source_code"]}
                for i in idxs[0] if scripts[i].get("source_code")
            ]

        # Keyword fallback
        terms = query.lower().split()
        scored = []
        for d in scripts:
            sc = sum(1 for t in terms if t in d["full_text"].lower())
            if sc > 0:
                scored.append((sc, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"description": d.get("docstring", "Example"), "code": d["source_code"]}
            for _, d in scored[:top_k] if d.get("source_code")
        ]


# ═══════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════

class PromptBuilder:
    """
    Builds a lean, high-signal prompt for Ollama.
    Token budget strategy:
      - System rules: ~300 tokens (compact, no duplication)
      - RAG schema: dynamic (only retrieved methods)
      - Few-shot: 1-2 executeTestCase() bodies (~400 tokens each)
      - Template: shown once, not repeated
      - Task: user description verbatim
    """

    # Compact system instruction — every sentence earns its tokens
    SYSTEM_PROMPT = (
        "You are an expert STB automation engineer. "
        "Generate ONLY valid, executable Python. No markdown, no explanations. "
        "Use ONLY the APIs listed below — never invent methods. "
        "Every function must contain real logic — no `pass`, no placeholders. "
        "Return (True, msg) on success, (False, msg) on failure."
    )

    # ── Schema builder ─────────────────────────────────────────────────

    @staticmethod
    def build_library_schema(library_context: List[Dict]) -> str:
        if not library_context:
            return ""

        groups: Dict[str, List[str]] = {}
        standalone: List[str] = []

        for doc in library_context:
            dtype = doc.get("type", "")
            if dtype == "method":
                cls = doc.get("class_name", "unknown")
                sig = doc.get("signature", doc.get("name", ""))
                ds = doc.get("docstring", "")[:100]
                groups.setdefault(cls, []).append(f"  {sig}  # {ds}" if ds else f"  {sig}")
            elif dtype == "class":
                cls = doc.get("name", "unknown")
                ds = doc.get("docstring", "")[:100]
                groups.setdefault(cls, [])
                if ds:
                    groups[cls].insert(0, f"  # {ds}")
            elif dtype == "function":
                sig = doc.get("signature", doc.get("name", ""))
                ds = doc.get("docstring", "")[:80]
                standalone.append(f"{sig}  # {ds}" if ds else sig)

        lines = ["[RETRIEVED API REFERENCE]"]
        for cls, methods in sorted(groups.items()):
            lines.append(f"\n{cls}:")
            lines.extend(methods)
        if standalone:
            lines.append("\nStandalone:")
            lines.extend(standalone)
        return "\n".join(lines)

    # ── Few-shot builder ───────────────────────────────────────────────

    @staticmethod
    def _extract_execute_function(code: str) -> str:
        if not code:
            return ""
        m = re.search(r"(def\s+executeTestCase\s*\(.*?\):[\s\S]*?)(?=\n\ndef |\Z)", code)
        return m.group(1).strip() if m else ""

    @staticmethod
    def build_few_shot_section(example_scripts: List[Dict[str, str]]) -> str:
        if not example_scripts:
            return ""
        parts = ["[EXAMPLES — replicate this pattern]"]
        for i, ex in enumerate(example_scripts[:2], 1):
            body = PromptBuilder._extract_execute_function(ex.get("code", ""))
            if body:
                desc = ex.get("description", f"Example {i}")
                parts.append(f"\n# Example {i}: {desc}\n{body}")
        return "\n".join(parts)

    # ── Main prompt ────────────────────────────────────────────────────

    @staticmethod
    def build_prompt(
        user_description: str,
        library_context: List[Dict],
        device_type: str,
        platform: str,
        test_type: str,
        example_scripts: Optional[List[Dict[str, str]]] = None,
    ) -> str:

        schema = PromptBuilder.build_library_schema(library_context)
        examples = PromptBuilder.build_few_shot_section(example_scripts or [])

        prompt = f"""{PromptBuilder.SYSTEM_PROMPT}

{schema}

[ALLOWED APIs — use ONLY these]
action: home(), submenu(name), kinder(), liveTV(), tuneChannel(ch), setResolution(res)
stb_rcu: send(button), sendmulti(commands, delay)
tv: connect(), show(), saveVideo(name), saveframe(name), closescreen(), shutdown()
stb: connect()
screen: image_to_text(), read_text() — for UI validation only


[CONFIG] device={device_type} | platform={platform} | test_type={test_type}

[TASK]
{user_description}

[RULES]
1. Start from known state (action.home()).
2. time.sleep(2) after navigation, time.sleep(1) after RCU commands.
3. Validate UI state with screen.* before proceeding.
4. Return (True, "msg") or (False, "error reason").
5. Preconditions checked at top of executeTestCase().

[TEMPLATE — output must match exactly]

from src.stb_lib.stb import *
import time

def executeTestCase():
    \"\"\"<describe test>\"\"\"
    # Step 1: Navigate and validate
    # Step 2: Perform action
    # Step N: Assert result
    return True, "Test passed"

def test_generated(extra):
    testoutputname = __name__
    try:
        action.useVision(True)
        if connection_type == "telnet":
            assert stb.connect()
        assert tv.connect()
        tv.show()
        tv.saveVideo(testoutputname)
        status, msg = executeTestCase()
        assert status, msg
        print("Test Case Passed")
    except Exception as e:
        print("Test Case Failed")
        tv.saveframe(testoutputname)
        extra.append(extras.video("file:Videos\\\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\\\" + testoutputname + ".png"))
        raise
    finally:
        tv.closescreen()
        tv.shutdown()
        time.sleep(10)

if __name__ == "__main__":
    test_generated('')

Output ONLY the Python script. No markdown fences, no explanation."""

        logger.info(f"Prompt built: {len(prompt)} chars")
        return prompt

    # ── Self-correction prompt ─────────────────────────────────────────

    @staticmethod
    def build_correction_prompt(
        original_script: str,
        validation_errors: List[str],
        user_description: str,
    ) -> str:
        errors = "\n".join(f"- {e}" for e in validation_errors)
        return f"""{PromptBuilder.SYSTEM_PROMPT}

The script below FAILED validation. Fix ALL errors and regenerate.

```python
{original_script}
```

Errors:
{errors}

Task: {user_description}

Output ONLY the corrected Python script."""

    # ── Failure analysis prompt ────────────────────────────────────────

    @staticmethod
    def build_failure_analysis_prompt(error_traceback: str) -> str:
        return f"""Explain this test failure in one simple sentence for a non-technical user:

{error_traceback}

Response (one sentence):"""


# ═══════════════════════════════════════════════════════════════════════════
# CODE GUARDRAIL
# ═══════════════════════════════════════════════════════════════════════════

class CodeGuardrail:
    """
    AST-based validation for LLM-generated scripts.
    Checks: syntax, forbidden imports, dangerous patterns, production quality.
    """

    def __init__(self):
        self.forbidden_imports = set(settings.FORBIDDEN_IMPORTS)
        self.max_size = settings.MAX_SCRIPT_SIZE

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not code or not code.strip():
            return False, ["Generated code is empty"]

        if len(code.encode("utf-8")) > self.max_size:
            errors.append(f"Code exceeds {self.max_size} bytes")

        # Syntax check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error line {e.lineno}: {e.msg}"]

        # Forbidden imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in self.forbidden_imports:
                        errors.append(f"Forbidden import: '{mod}'")
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                if mod in self.forbidden_imports:
                    errors.append(f"Forbidden import: '{mod}'")

        # Dangerous patterns
        for pattern, msg in [
            (r"exec\s*\(", "exec() forbidden"),
            (r"eval\s*\(", "eval() forbidden"),
            (r"__import__\s*\(", "__import__() forbidden"),
            (r"compile\s*\(", "compile() forbidden"),
            (r"open\s*\([^)]*['\"]w", "File writing forbidden"),
        ]:
            if re.search(pattern, code):
                errors.append(msg)

        # Quality checks
        self._check_quality(tree, code, errors)

        return len(errors) == 0, errors

    @staticmethod
    def _check_quality(tree: ast.AST, code: str, errors: List[str]):
        """Enforce production patterns: no pass, no empty functions, assertions required, teardown present."""
        has_assert = False
        # Match actual teardown pattern used in the template
        has_teardown = ("tv.closescreen()" in code or "tv.shutdown()" in code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Filter out docstring-only bodies
                real_body = [
                    n for n in node.body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, (ast.Constant, ast.Str)))
                ]
                if not real_body:
                    errors.append(f"Empty function: '{node.name}()' has no logic")
                elif len(real_body) == 1 and isinstance(real_body[0], ast.Pass):
                    errors.append(f"Placeholder: '{node.name}()' contains only `pass`")

            if isinstance(node, ast.Assert):
                has_assert = True

        if not has_assert:
            errors.append("No assertions — script must include `assert` statements")

        if not has_teardown:
            errors.append("Missing teardown — must call tv.closescreen() or tv.shutdown() in finally block")

    def extract_code_from_response(self, response: str) -> str:
        """Extract Python code from LLM response, stripping markdown fences."""
        m = re.search(r"```python\s*(.*?)\s*```", response, re.DOTALL)
        if m:
            return m.group(1).strip()
        m = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
        if m:
            return m.group(1).strip()
        return response.strip()


# ── Global instances ───────────────────────────────────────────────────────
library_indexer = LibraryIndexer()
prompt_builder = PromptBuilder()
code_guardrail = CodeGuardrail()