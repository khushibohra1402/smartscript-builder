"""
RAG Engine - Library Indexing, Prompt Construction, and Code Guardrail.

Flow:
1. Library Indexing - AST-parse enterprise libs → FAISS vector index (with API tags)
2. Example Script Indexing - Index real scripts for few-shot learning
3. Intent-Aware Hybrid Retrieval - embedding + keyword + intent scoring
4. Prompt Construction - Strict CORE/DYNAMIC API constraint prompt
5. Code Guardrail - AST validation + hallucination detection
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
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

_THIS_DIR = Path(__file__).resolve().parent
_EXAMPLES_DIR = _THIS_DIR / "example_scripts"


# ═══════════════════════════════════════════════════════════════════════════
# CORE API REGISTRY — always available, never removed from prompt
# ═══════════════════════════════════════════════════════════════════════════

CORE_APIS: Dict[str, List[str]] = {
    "action":   ["home()", "submenu(name)", "liveTV()", "tuneChannel(ch)", "kinder()", "useVision(flag)"],
    "stb_rcu":  ["send(button)", "sendmulti(commands, delay)"],
    "tv":       ["connect()", "show()", "saveVideo(name)", "saveframe(name)", "closescreen()", "shutdown()"],
    "stb":      ["connect()"],
    "screen":   ["read_text()", "image_to_text()"],
}

# Flat set for fast lookup: {"action.home", "action.submenu", ...}
CORE_API_SET: Set[str] = set()
for _obj, _methods in CORE_APIS.items():
    for _m in _methods:
        CORE_API_SET.add(f"{_obj}.{_m.split('(')[0]}")


# ═══════════════════════════════════════════════════════════════════════════
# INTENT SYSTEM — maps keywords → API tags for retrieval boosting
# ═══════════════════════════════════════════════════════════════════════════

# Tags assigned during indexing
API_TAG_KEYWORDS: Dict[str, List[str]] = {
    "navigation":    ["home", "menu", "submenu", "navigate", "screen", "page", "settings", "back"],
    "playback":      ["play", "pause", "rewind", "forward", "trick", "timeshift", "stream", "live", "channel"],
    "validation":    ["check", "verify", "validate", "assert", "compare", "text", "ocr", "version", "read"],
    "remote_input":  ["remote", "rcu", "button", "key", "send", "press", "ok", "up", "down", "left", "right"],
    "recording":     ["record", "schedule", "pvr", "recording", "timer", "aufnahme"],
    "setup":         ["connect", "setup", "init", "config", "resolution", "vision"],
}

# Intent → APIs to always inject when intent is detected
INTENT_API_BOOST: Dict[str, List[str]] = {
    "navigation":   ["action.home", "action.submenu"],
    "playback":     ["action.liveTV", "action.tuneChannel", "stb_rcu.send"],
    "validation":   ["screen.read_text", "screen.image_to_text"],
    "remote_input": ["stb_rcu.send", "stb_rcu.sendmulti"],
    "recording":    ["action.submenu", "stb_rcu.sendmulti", "screen.read_text"],
    "setup":        ["tv.connect", "stb.connect", "action.useVision"],
}

# Workflow bundles — injected into prompt when intent matches
WORKFLOW_BUNDLES: Dict[str, str] = {
    "navigation": (
        "Navigation Flow:\n"
        "1. action.home() → start from known state\n"
        "2. action.submenu(target) → navigate to section\n"
        "3. time.sleep(2) → wait for UI\n"
        "4. screen.read_text() → validate arrival"
    ),
    "playback": (
        "Playback Flow:\n"
        "1. action.home()\n"
        "2. action.liveTV() → enter live TV\n"
        "3. action.tuneChannel(ch) → tune to channel\n"
        "4. time.sleep(3) → wait for stream\n"
        "5. screen.read_text() → validate playback state"
    ),
    "validation": (
        "Validation Flow:\n"
        "1. Navigate to target screen\n"
        "2. time.sleep(2) → wait for render\n"
        "3. text = screen.read_text() → capture UI text\n"
        "4. assert expected_value in text → verify"
    ),
    "recording": (
        "Recording Flow:\n"
        "1. action.home()\n"
        "2. action.submenu('recordings') or navigate via EPG\n"
        "3. stb_rcu.sendmulti([commands], delay) → interact\n"
        "4. screen.read_text() → validate recording state"
    ),
    "remote_input": (
        "Remote Control Flow:\n"
        "1. stb_rcu.send(button) → single press\n"
        "2. stb_rcu.sendmulti([buttons], delay) → sequence\n"
        "3. time.sleep(1) → wait for response\n"
        "4. screen.read_text() → validate result"
    ),
}


def extract_intents(text: str) -> List[str]:
    """Extract intent tags from user description using keyword matching."""
    text_lower = text.lower()
    intents = []
    for tag, keywords in API_TAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            intents.append(tag)
    return intents or ["navigation"]  # default intent


def _assign_api_tags(doc: Dict) -> List[str]:
    """Assign intent tags to an indexed document based on its content."""
    text = f"{doc.get('name', '')} {doc.get('docstring', '')} {doc.get('full_text', '')}".lower()
    tags = []
    for tag, keywords in API_TAG_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    return tags or ["general"]


# ═══════════════════════════════════════════════════════════════════════════
# LIBRARY INDEXER
# ═══════════════════════════════════════════════════════════════════════════

class LibraryIndexer:
    """
    Indexes enterprise Python libraries + example scripts into FAISS.
    Each document is tagged with intent categories for hybrid retrieval.
    """

    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents: List[Dict] = []
        self._initialized = False

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
            self._initialized = True

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_python_file(file_path: Path) -> List[Dict]:
        documents: List[Dict] = []
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            module = file_path.stem

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    cls_doc = ast.get_docstring(node) or ""
                    doc = {
                        "type": "class", "name": node.name,
                        "module": module, "docstring": cls_doc,
                        "full_text": f"class {node.name}: {cls_doc}",
                    }
                    doc["tags"] = _assign_api_tags(doc)
                    documents.append(doc)

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            mdoc = ast.get_docstring(item) or ""
                            args = [a.arg for a in item.args.args if a.arg != "self"]
                            sig = f"{item.name}({', '.join(args)})"
                            mdoc_entry = {
                                "type": "method", "name": item.name,
                                "class_name": node.name, "module": module,
                                "signature": sig, "docstring": mdoc,
                                "full_text": f"{node.name}.{sig}: {mdoc}",
                            }
                            mdoc_entry["tags"] = _assign_api_tags(mdoc_entry)
                            documents.append(mdoc_entry)

                elif isinstance(node, ast.FunctionDef):
                    fdoc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args]
                    sig = f"{node.name}({', '.join(args)})"
                    fdoc_entry = {
                        "type": "function", "name": node.name,
                        "module": module, "signature": sig,
                        "docstring": fdoc,
                        "full_text": f"{sig}: {fdoc}",
                    }
                    fdoc_entry["tags"] = _assign_api_tags(fdoc_entry)
                    documents.append(fdoc_entry)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        return documents

    @staticmethod
    def _parse_example_script(file_path: Path) -> List[Dict]:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree) or file_path.stem.replace("_", " ")
            doc = {
                "type": "example_script",
                "name": file_path.stem,
                "module": "examples",
                "file_path": str(file_path),
                "docstring": docstring,
                "source_code": source,
                "full_text": f"Example - {docstring}: {source[:1500]}",
            }
            doc["tags"] = _assign_api_tags(doc)
            return [doc]
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

        stb_driver = Path("backend/libs/stb/stb_driver.py")
        if stb_driver.exists():
            stb_docs = self._parse_python_file(stb_driver)
            all_docs.extend(stb_docs)
            logger.info(f"Indexed STB driver: {len(stb_docs)} docs")

        if _EXAMPLES_DIR.exists():
            for ef in _EXAMPLES_DIR.glob("*.py"):
                all_docs.extend(self._parse_example_script(ef))
            logger.info(f"Indexed example scripts from {_EXAMPLES_DIR}")

        self.documents = all_docs
        logger.info(f"Total documents indexed: {len(all_docs)}")

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
    # Hybrid Retrieval: 0.6*embedding + 0.2*keyword + 0.2*intent_tag
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10, intents: Optional[List[str]] = None) -> List[Dict]:
        """
        Hybrid search combining:
        - 0.6 * FAISS embedding similarity
        - 0.2 * keyword overlap
        - 0.2 * intent tag match
        """
        if not self.documents:
            return []

        intents = intents or extract_intents(query)
        query_terms = set(query.lower().split())

        # --- Embedding scores ---
        emb_scores = np.zeros(len(self.documents))
        if FAISS_AVAILABLE and self.index and self.embedding_model:
            qe = self.embedding_model.encode([query])
            k = min(len(self.documents), max(top_k * 3, 30))  # over-retrieve
            dists, idxs = self.index.search(np.array(qe, dtype="float32"), k)
            for idx, dist in zip(idxs[0], dists[0]):
                if 0 <= idx < len(self.documents):
                    emb_scores[idx] = 1.0 / (1.0 + dist)

        # --- Keyword + intent scores ---
        kw_scores = np.zeros(len(self.documents))
        intent_scores = np.zeros(len(self.documents))

        for i, doc in enumerate(self.documents):
            # Keyword overlap
            doc_terms = set(doc["full_text"].lower().split())
            overlap = len(query_terms & doc_terms)
            if query_terms:
                kw_scores[i] = overlap / len(query_terms)

            # Intent tag match
            doc_tags = set(doc.get("tags", []))
            if intents and doc_tags:
                intent_scores[i] = len(set(intents) & doc_tags) / len(intents)

        # --- Combined score ---
        combined = 0.6 * emb_scores + 0.2 * kw_scores + 0.2 * intent_scores

        # Rank and deduplicate
        ranked_idxs = np.argsort(-combined)
        results = []
        seen = set()
        for idx in ranked_idxs:
            if combined[idx] <= 0:
                break
            doc = self.documents[idx]
            key = doc["full_text"]
            if key not in seen:
                d = doc.copy()
                d["score"] = float(combined[idx])
                results.append(d)
                seen.add(key)
            if len(results) >= top_k:
                break

        return results

    def get_example_scripts(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
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
    Builds a strict, constraint-driven prompt with:
    - CORE APIs (always available)
    - DYNAMIC APIs (from RAG — preferred)
    - Workflow bundles (intent-aware execution patterns)
    - Few-shot examples (executeTestCase bodies)
    """

    SYSTEM_PROMPT = (
        "You are an expert STB automation engineer. "
        "Generate ONLY valid, executable Python. No markdown, no explanations.\n"
        "STRICT: Use ONLY APIs listed under CORE and DYNAMIC sections. "
        "NEVER invent methods. If no suitable API exists, use stb_rcu.send().\n"
        "Every function must contain real logic — no `pass`, no placeholders.\n"
        "Return (True, msg) on success, (False, msg) on failure."
    )

    @staticmethod
    def _build_core_api_section() -> str:
        lines = ["[CORE APIs — always available]"]
        for obj, methods in CORE_APIS.items():
            lines.append(f"  {obj}: {', '.join(methods)}")
        return "\n".join(lines)

    @staticmethod
    def build_library_schema(library_context: List[Dict]) -> str:
        """Build DYNAMIC API section from RAG-retrieved docs."""
        if not library_context:
            return "[DYNAMIC APIs — none retrieved]"

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

        lines = ["[DYNAMIC APIs — prefer these over CORE when available]"]
        for cls, methods in sorted(groups.items()):
            lines.append(f"\n{cls}:")
            lines.extend(methods)
        if standalone:
            lines.append("\nStandalone:")
            lines.extend(standalone)
        return "\n".join(lines)

    @staticmethod
    def _build_workflow_section(intents: List[str]) -> str:
        """Inject relevant workflow bundles based on detected intents."""
        bundles = []
        for intent in intents:
            if intent in WORKFLOW_BUNDLES:
                bundles.append(WORKFLOW_BUNDLES[intent])
        if not bundles:
            return ""
        return "[EXECUTION PATTERNS — follow these flows]\n\n" + "\n\n".join(bundles)

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

    @staticmethod
    def build_prompt(
        user_description: str,
        library_context: List[Dict],
        device_type: str,
        platform: str,
        test_type: str,
        example_scripts: Optional[List[Dict[str, str]]] = None,
        intents: Optional[List[str]] = None,
    ) -> str:

        core_section = PromptBuilder._build_core_api_section()
        dynamic_section = PromptBuilder.build_library_schema(library_context)
        examples = PromptBuilder.build_few_shot_section(example_scripts or [])
        intents = intents or extract_intents(user_description)
        workflow_section = PromptBuilder._build_workflow_section(intents)

        prompt = f"""{PromptBuilder.SYSTEM_PROMPT}

{core_section}

{dynamic_section}

[API RULES]
1. Prefer DYNAMIC APIs over CORE when available.
2. NEVER invent APIs not in CORE or DYNAMIC sections.
3. If no suitable API exists → use stb_rcu.send(button) as fallback.
4. Follow usage exactly as described — respect preconditions.

{workflow_section}

{examples}

[CONFIG] device={device_type} | platform={platform} | test_type={test_type}

[TASK]
{user_description}

[RULES]
1. Start from known state: action.home()
2. time.sleep(2) after navigation, time.sleep(1) after RCU commands.
3. Validate UI state with screen.read_text() before proceeding.
4. Return (True, "msg") on success, (False, "error") on failure.
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

        logger.info(f"Prompt built: {len(prompt)} chars, intents={intents}")
        return prompt

    # ── Self-correction prompt (includes allowed APIs) ─────────────────

    @staticmethod
    def build_correction_prompt(
        original_script: str,
        validation_errors: List[str],
        user_description: str,
        allowed_apis: Optional[Set[str]] = None,
    ) -> str:
        errors = "\n".join(f"- {e}" for e in validation_errors)
        api_note = ""
        if allowed_apis:
            api_note = f"\n\nAllowed APIs: {', '.join(sorted(allowed_apis))}"
        return f"""{PromptBuilder.SYSTEM_PROMPT}

The script below FAILED validation. Fix ALL errors and regenerate.

```python
{original_script}
```

Errors:
{errors}{api_note}

Task: {user_description}

IMPORTANT: Do NOT use any API not listed in CORE or DYNAMIC sections.
Replace any hallucinated API with the nearest allowed alternative or stb_rcu.send().

Output ONLY the corrected Python script."""

    @staticmethod
    def build_failure_analysis_prompt(error_traceback: str) -> str:
        return f"""Explain this test failure in one simple sentence for a non-technical user:

{error_traceback}

Response (one sentence):"""


# ═══════════════════════════════════════════════════════════════════════════
# CODE GUARDRAIL + HALLUCINATION DETECTION
# ═══════════════════════════════════════════════════════════════════════════

class CodeGuardrail:
    """
    AST-based validation:
    - Syntax + forbidden imports + dangerous patterns
    - Production quality (no pass, assertions required, teardown)
    - Hallucination detection (reject APIs not in allowed set)
    """

    def __init__(self):
        self.forbidden_imports = set(settings.FORBIDDEN_IMPORTS)
        self.max_size = settings.MAX_SCRIPT_SIZE

    # ------------------------------------------------------------------
    # Hallucination detection
    # ------------------------------------------------------------------

    @staticmethod
    def extract_api_calls(code: str) -> Set[str]:
        """
        Extract all obj.method() calls from generated code via AST.
        Returns set like {"action.home", "stb_rcu.send", "screen.read_text"}.
        """
        calls: Set[str] = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    value = node.func.value
                    if isinstance(value, ast.Name):
                        calls.add(f"{value.id}.{node.func.attr}")
        except SyntaxError:
            pass
        return calls

    @staticmethod
    def detect_hallucinated_apis(
        code: str,
        dynamic_apis: Optional[Set[str]] = None,
    ) -> Tuple[List[str], Set[str]]:
        """
        Compare API calls in generated code against allowed set.
        Returns (list of hallucinated calls, full allowed set used).
        """
        # Build allowed set: CORE + dynamic
        allowed = set(CORE_API_SET)
        # Add common safe objects that aren't APIs
        safe_objects = {
            "time.sleep", "print", "extras.video", "extras.image",
            "self", "str.format", "str.split", "list.append",
        }
        allowed.update(safe_objects)

        if dynamic_apis:
            allowed.update(dynamic_apis)

        used = CodeGuardrail.extract_api_calls(code)

        # Only flag calls on known STB objects that aren't in allowed set
        stb_objects = {"action", "stb_rcu", "tv", "stb", "screen", "driver"}
        hallucinated = []
        for call in used:
            obj = call.split(".")[0]
            if obj in stb_objects and call not in allowed:
                hallucinated.append(call)

        return hallucinated, allowed

    # ------------------------------------------------------------------
    # Main validation
    # ------------------------------------------------------------------

    def validate(
        self,
        code: str,
        dynamic_apis: Optional[Set[str]] = None,
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not code or not code.strip():
            return False, ["Generated code is empty"]

        if len(code.encode("utf-8")) > self.max_size:
            errors.append(f"Code exceeds {self.max_size} bytes")

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

        # Hallucination check
        hallucinated, _ = self.detect_hallucinated_apis(code, dynamic_apis)
        if hallucinated:
            errors.append(
                f"Hallucinated APIs (not in allowed set): {', '.join(sorted(hallucinated))}. "
                f"Replace with allowed APIs or stb_rcu.send()."
            )

        return len(errors) == 0, errors

    @staticmethod
    def _check_quality(tree: ast.AST, code: str, errors: List[str]):
        has_assert = False
        has_teardown = ("tv.closescreen()" in code or "tv.shutdown()" in code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
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
            errors.append("Missing teardown — must call tv.closescreen() or tv.shutdown()")

    def extract_code_from_response(self, response: str) -> str:
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
