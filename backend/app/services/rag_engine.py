"""
RAG Engine - Library Indexing and Context Injection
Implements SRS Section 4: Script Generation Engine.
Flow:
1. Library Indexing - Scan custom enterprise libraries and create FAISS index
2. Example Script Indexing - Index real automation scripts for few-shot learning
3. Prompt Construction - Build mega-prompt with constraints + context + examples + task
4. Code Generation - Send to Ollama and receive Python script
5. Quality Guardrail - Validate output for production readiness
"""

import ast
import re
import hashlib
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


class LibraryIndexer:
    """
    Indexes custom enterprise libraries for RAG retrieval.
    Creates embeddings of method signatures and docstrings.
    Also indexes example scripts for few-shot learning.
    """
    
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents: List[Dict] = []

        # Separate storage for scripts
        self.script_docs: List[Dict] = []
        self.script_index = None
        self.script_embeddings = None

        self._initialized = False
    
    async def initialize(self):
        """Initialize the embedding model."""
        if self._initialized:
            return
        
        if FAISS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                self._initialized = True
                logger.info(f"Initialized embedding model: {settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self._initialized = False
        else:
            self._initialized = True  # Use keyword fallback
    
    def _parse_python_file(self, file_path: Path) -> List[Dict]:
        """
        Parse a Python file and extract classes, methods, and docstrings.
        Returns structured documents for indexing.
        """
        documents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            module_name = file_path.stem
            
            for node in tree.body:  # FIXED (correct parsing)
                if isinstance(node, ast.ClassDef):
                    class_doc = ast.get_docstring(node) or ""
                    documents.append({
                        "type": "class",
                        "name": node.name,
                        "module": module_name,
                        "docstring": class_doc,
                        "full_text": f"class {node.name}: {class_doc}"
                    })

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_doc = ast.get_docstring(item) or ""
                            args = [a.arg for a in item.args.args if a.arg != "self"]
                            signature = f"{item.name}({', '.join(args)})"

                            documents.append({
                                "type": "method",
                                "name": item.name,
                                "class_name": node.name,
                                "module": module_name,
                                "signature": signature,
                                "docstring": method_doc,
                                "full_text": f"{node.name}.{signature}: {method_doc}"
                            })

                elif isinstance(node, ast.FunctionDef):
                    func_doc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args]
                    signature = f"{node.name}({', '.join(args)})"

                    documents.append({
                        "type": "function",
                        "name": node.name,
                        "module": module_name,
                        "signature": signature,
                        "docstring": func_doc,
                        "full_text": f"{signature}: {func_doc}"
                    })

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

        return documents


    def _parse_example_script(self, file_path: Path) -> List[Dict]:
        """
        Parse a complete example test script for few-shot indexing.
        Extracts the full script content and its docstring as the description.
        """
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            docstring = ast.get_docstring(tree) or file_path.stem.replace("_", " ")

            documents.append({
                "type": "example_script",
                "name": file_path.stem,
                "module": "examples",
                "file_path": str(file_path),
                "docstring": docstring,
                "source_code": source,
                "full_text": f"Example test script - {docstring}: {source[:1500]}"
            })
        except Exception as e:
            logger.warning(f"Error parsing example script {file_path}: {e}")

        return documents

    async def index_library(self, library_path: Path, project_id: str) -> Dict:
        """
        Index an entire library folder plus example scripts.
        Returns metadata about the indexing process.
        """
        await self.initialize()
        
        library_path = Path(library_path)
        if not library_path.exists():
            raise ValueError(f"Library path does not exist: {library_path}")
        
        # Find all Python files in library
        python_files = list(library_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files in {library_path}")
        
        # Parse all library files
        all_documents = []
        for py_file in python_files:
            docs = self._parse_python_file(py_file)
            all_documents.extend(docs)

        # Also index the STB driver
        stb_driver_path = Path("backend/libs/stb/stb_driver.py")
        if stb_driver_path.exists():
            stb_docs = self._parse_python_file(stb_driver_path)
            all_documents.extend(stb_docs)
            logger.info(f"Indexed STB driver: {len(stb_docs)} documents")

        # Index example scripts for few-shot learning
        examples_dir = Path(r"C:\Users\khushi.bohra\Smart-script\smartscript-builder\backend\app\services\example_scripts")
        if examples_dir.exists():
            example_files = list(examples_dir.glob("*.py"))
            for ef in example_files:
                example_docs = self._parse_example_script(ef)
                all_documents.extend(example_docs)
            logger.info(f"Indexed {len(example_files)} example scripts")

        self.documents = all_documents
        logger.info(f"Extracted {len(all_documents)} documents from library + examples")
        
        # Create FAISS index if available
        if FAISS_AVAILABLE and self.embedding_model:
            texts = [doc["full_text"] for doc in all_documents]
            if texts:
                embeddings = self.embedding_model.encode(texts)
                
                # Create FAISS index
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings).astype('float32'))
                
                # Save index
                index_path = settings.FAISS_INDEX_PATH / f"{project_id}.index"
                faiss.write_index(self.index, str(index_path))
                logger.info(f"Saved FAISS index to {index_path}")
        
        return {
            "project_id": project_id,
            "library_path": str(library_path),
            "files_indexed": len(python_files),
            "documents_extracted": len(all_documents),
            "indexed_at": datetime.utcnow().isoformat(),
            "classes": len([d for d in all_documents if d["type"] == "class"]),
            "methods": len([d for d in all_documents if d["type"] == "method"]),
            "functions": len([d for d in all_documents if d["type"] == "function"]),
            "example_scripts": len([d for d in all_documents if d["type"] == "example_script"]),
        }
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search the indexed library for relevant methods/classes.
        Uses FAISS if available, otherwise keyword matching.
        """
        if not self.documents:
            return []
        
        if FAISS_AVAILABLE and self.index and self.embedding_model:
            # Vector search
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.index.search(
                np.array(query_embedding).astype('float32'), 
                min(top_k, len(self.documents))
            )
            
            results = []
            seen_texts = set()
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    # Deduplicate by full_text
                    if doc["full_text"] not in seen_texts:
                        doc["score"] = float(1 / (1 + dist))
                        results.append(doc)
                        seen_texts.add(doc["full_text"])
            
            return results
        else:
            # Keyword matching fallback
            query_terms = query.lower().split()
            scored_docs = []
            
            for doc in self.documents:
                text = doc["full_text"].lower()
                score = sum(1 for term in query_terms if term in text)
                if score > 0:
                    doc_copy = doc.copy()
                    doc_copy["score"] = score / len(query_terms)
                    scored_docs.append(doc_copy)
            
            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            return scored_docs[:top_k]

    def get_example_scripts(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve the most relevant example scripts for few-shot prompting.
        """

        # Step 1: Filter only example scripts
        script_docs = [d for d in self.documents if d.get("type") == "example_script"]

        if not script_docs:
            return []

        # Step 2: If FAISS available → do semantic search ONLY on scripts
        if FAISS_AVAILABLE and self.embedding_model:
            texts = [doc["full_text"] for doc in script_docs]
            embeddings = self.embedding_model.encode(texts)

            # Create temporary FAISS index for scripts
            dimension = embeddings.shape[1]
            temp_index = faiss.IndexFlatL2(dimension)
            temp_index.add(np.array(embeddings).astype('float32'))

            # Encode query
            query_embedding = self.embedding_model.encode([query])

            distances, indices = temp_index.search(
                np.array(query_embedding).astype('float32'),
                min(top_k, len(script_docs))
            )

            scripts = []
            for idx in indices[0]:
                doc = script_docs[idx]
                if doc.get("source_code"):
                    scripts.append(doc["source_code"])

            return scripts

        else:
            # Fallback: keyword search on scripts only
            query_terms = query.lower().split()
            scored_docs = []

            for doc in script_docs:
                text = doc["full_text"].lower()
                score = sum(1 for term in query_terms if term in text)
                if score > 0:
                    doc_copy = doc.copy()
                    doc_copy["score"] = score / len(query_terms)
                    scored_docs.append(doc_copy)

            scored_docs.sort(key=lambda x: x["score"], reverse=True)

            return [d["source_code"] for d in scored_docs[:top_k] if d.get("source_code")]


class PromptBuilder:
    """
    Constructs the mega-prompt for Ollama with:
    1. Strict constraints (enforce real code, no placeholders)
    2. Library context (relevant methods from RAG)
    3. Few-shot examples (real enterprise scripts)
    4. Task (user's natural language description)
    """
    
    SYSTEM_PROMPT = """You are a Senior Python Automation Architect specializing in enterprise STB automation testing.

Generate a production-grade automation test script using the enterprise automation framework.

Structure must include:

1. Metadata header (author, description, prerequisites)
2. Imports
3. executeTestCase() → core logic
4. test_<name>() → wrapper
5. main block

You may include:
- logging (print)
- global variables
- reporting logic (Excel, file writing)
- assertions

The script must use enterprise APIs such as:

action.home()
action.submenu()
action.kinder()
action.liveTV()
action.tuneChannel()
action.setResolution()
stb_rcu.send()
stb_rcu.sendmulti()
tv.connect()
tv.show()
tv.saveVideo()

Do NOT generate:
driver.connect()
driver.press()
setup()
teardown()
test classes

Use the structure shown in the example scripts.
"""
    @staticmethod
    def build_library_schema(library_context: List[Dict]) -> str:
        """
        Build a structured method registry from RAG-retrieved documents.
        Groups methods by class for clarity.
        """
        if not library_context:
            return "No library methods available."

        # Group by class/object name
        groups: Dict[str, List[str]] = {}
        standalone: List[str] = []

        for doc in library_context:
            doc_type = doc.get("type", "")
            if doc_type == "method":
                class_name = doc.get("class_name", "unknown")
                sig = doc.get("signature", doc.get("name", ""))
                docstring = doc.get("docstring", "")[:120]
                entry = f"  - {sig}: {docstring}" if docstring else f"  - {sig}"
                groups.setdefault(class_name, []).append(entry)
            elif doc_type == "class":
                class_name = doc.get("name", "unknown")
                docstring = doc.get("docstring", "")[:120]
                groups.setdefault(class_name, [])
                if docstring:
                    groups[class_name].insert(0, f"  # {docstring}")
            elif doc_type == "function":
                sig = doc.get("signature", doc.get("name", ""))
                docstring = doc.get("docstring", "")[:80]
                standalone.append(f"- {sig}: {docstring}" if docstring else f"- {sig}")

        lines = ["## ALLOWED METHODS (use ONLY these)"]
        for cls, methods in sorted(groups.items()):
            lines.append(f"\n### {cls}")
            lines.extend(methods)

        if standalone:
            lines.append("\n### Standalone Functions")
            lines.extend(standalone)

        return "\n".join(lines)

    @staticmethod
    def build_few_shot_section(example_scripts: List[Dict[str, str]]) -> str:
        """
        Build few-shot examples section from loaded example scripts.
        Each entry: {"description": "...", "code": "..."}
        """
        if not example_scripts:
            return ""

        lines = ["## EXAMPLE SCRIPTS (follow this pattern exactly)"]
        for i, ex in enumerate(example_scripts[:2], 1):  # Max 2 examples to save tokens
            desc = ex.get("description", f"Example {i}")
            code = ex.get("code", "")
            # Only include the executeTestCase function to save context
            exec_func = PromptBuilder._extract_execute_function(code)
            if exec_func:
                lines.append(f"\n### Example {i}: {desc}")
                lines.append(f"```python\n{exec_func}\n```")

        return "\n".join(lines)

    @staticmethod
    def build_prompt(
        user_description: str,
        library_context: List[Dict],
        device_type: str,
        platform: str,
        test_type: str,
        example_scripts: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build the complete structured mega-prompt.

        Sections:
        1. SYSTEM PROMPT (rules)
        2. ALLOWED METHODS (library schema)
        3. EXAMPLE SCRIPTS (few-shot)
        4. CONSTRAINTS (device/platform/type)
        5. TASK (user description)
        """
        # Section 1: Library schema
        schema_section = PromptBuilder.build_library_schema(library_context)

        # Section 2: Few-shot examples
        examples_section = PromptBuilder.build_few_shot_section(example_scripts or [])

        # Section 3: Build complete prompt
        prompt = f"""
{PromptBuilder.SYSTEM_PROMPT}

{schema_section}

{examples_section}

==================================================
TEST CONFIGURATION
==================================================

Device Type: {device_type}
Platform: {platform}
Test Type: {test_type}

==================================================
ALLOWED ENTERPRISE AUTOMATION METHODS
==================================================

Navigation / Actions
- action.home()
- action.submenu(menu_name)
- action.kinder()
- action.liveTV()
- action.tuneChannel(channel_number)
- action.setResolution(resolution)

Remote Control
- stb_rcu.send(button)
- stb_rcu.sendmulti(commands, delay)

TV Control
- tv.connect()
- tv.show()
- tv.saveVideo(name)
- tv.saveframe(name)
- tv.closescreen()
- tv.shutdown()

Connection
- stb.connect()

Use enterprise automation APIs available in the framework, including:
- action.*, stb_rcu.*, tv.*
- screen.*, OCR utilities, frame comparison utilities
- OpenCV (cv2) where required for frame validation

Prefer existing APIs, but you may combine them creatively.
==================================================
TASK
==================================================

{user_description}

==================================================
IMPLEMENTATION RULES
==================================================

1. Follow the enterprise script structure exactly.
2. Implement real logic inside executeTestCase().
3. Each test step must contain executable automation code.
4. Do NOT use placeholders like "condition".
5. You may use global variables (e.g., result dictionaries) to store intermediate data such as timing metrics.
6. Use time.sleep() where required for UI stability.
7. Return False with an error message if validation fails.
8. Return True when the test succeeds.

==================================================
UI INTERACTION RULES
==================================================

- Add time.sleep(2) after navigation actions.
- Add time.sleep(1) after UI interactions.
- Always verify UI state before performing the next action.

==================================================
REQUIRED SCRIPT TEMPLATE
==================================================

The generated script MUST follow this structure exactly.

from src.stb_lib.stb import *
import time


def executeTestCase():

    # Step 1
    # implement automation step

    # Step 2
    # implement automation step

    # Step 3
    # implement automation step

    return True  # or False


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

        extra.append(extras.video("file:Videos\\" + testoutputname + ".mp4"))
        extra.append(extras.image("file:Images\\" + testoutputname + ".png"))

        raise

    finally:

        tv.closescreen()
        tv.shutdown()
        time.sleep(10)


if __name__ == "__main__":
    test_generated('')

==================================================
OUTPUT REQUIREMENTS
==================================================

Generate ONLY the Python script.

Do NOT:
- explain the code
- output markdown
- output reasoning

Return only valid executable Python code.
"""

        return prompt
    
    @staticmethod
    def build_correction_prompt(
        original_script: str,
        validation_errors: List[str],
        user_description: str,
    ) -> str:
        """
        Build a self-correction prompt when the first attempt fails validation.
        """
        errors_text = "\n".join(f"- {e}" for e in validation_errors)
        return f"""{PromptBuilder.SYSTEM_PROMPT}

The following script was generated but FAILED quality validation:

```python
{original_script}
```

Validation errors:
{errors_text}

Original task: {user_description}

Fix ALL validation errors and regenerate a complete, production-grade script.
Every function must have real logic — no `pass` statements.
Include assertions, logging, setup/teardown, and OCR validation.

### Corrected Python Test Script:
```python
"""

    @staticmethod
    def build_failure_analysis_prompt(error_traceback: str) -> str:
        """
        Build prompt for AI Failure Analyst (SRS Section 5.2).
        Translates technical errors to non-technical explanations.
        """
        return f"""You are a helpful assistant explaining test failures to non-technical users.

Translate this technical error into a 1-sentence explanation:

```
{error_traceback}
```

Provide a simple, friendly explanation of what went wrong, without technical jargon.
Response (one sentence only):"""


class CodeGuardrail:
    """
    Static analysis layer to validate LLM-generated code.
    Checks for syntax, forbidden imports, dangerous patterns,
    AND production quality (no pass, no empty functions, assertions present).
    """
    
    def __init__(self):
        self.forbidden_imports = set(settings.FORBIDDEN_IMPORTS)
        self.max_size = settings.MAX_SCRIPT_SIZE
    
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated Python code for both security and quality.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not code or not code.strip():
            return False, ["Generated code is empty"]

        # Check size
        if len(code.encode('utf-8')) > self.max_size:
            errors.append(f"Code exceeds maximum size of {self.max_size} bytes")
        
        # Check syntax
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors
        
        # Check for forbidden imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in self.forbidden_imports:
                        errors.append(f"Forbidden import: '{module}'")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in self.forbidden_imports:
                        errors.append(f"Forbidden import: '{module}'")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'exec\s*\(', "Use of exec() is forbidden"),
            (r'eval\s*\(', "Use of eval() is forbidden"),
            (r'__import__\s*\(', "Use of __import__() is forbidden"),
            (r'compile\s*\(', "Use of compile() is forbidden"),
            (r'open\s*\([^)]*[\'"]w', "Writing to files is forbidden"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                errors.append(message)

        # === QUALITY CHECKS ===
        self._check_quality(tree, code, errors)
        
        return len(errors) == 0, errors

    def _check_quality(self, tree: ast.AST, code: str, errors: List[str]):
        """Check for production quality: no pass, no empty functions, assertions present."""
        has_assert = False
        has_disconnect = "disconnect" in code

        for node in ast.walk(tree):
            # Check for `pass` in function bodies (placeholder detection)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                # Skip docstring-only check
                real_body = [
                    n for n in body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, (ast.Constant, ast.Str)))
                ]
                if len(real_body) == 0:
                    errors.append(f"Empty function body: '{node.name}()' has no logic")
                elif len(real_body) == 1 and isinstance(real_body[0], ast.Pass):
                    errors.append(f"Placeholder function: '{node.name}()' contains only `pass`")

            if isinstance(node, ast.Assert):
                has_assert = True

        if not has_assert:
            errors.append("No assertions found — script must include `assert` statements for validation")

        if not has_disconnect:
            errors.append("Missing teardown — script should call `driver.disconnect()` in finally block")
    
    def extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from Ollama response.
        Handles markdown code blocks.
        """
        # Try to extract from markdown code block
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try generic code block
        code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Return as-is if no code block found
        return response.strip()


# Global instances
library_indexer = LibraryIndexer()
prompt_builder = PromptBuilder()
code_guardrail = CodeGuardrail()