"""
RAG Engine v2 - Library Indexing, Example Scripts, and Context Retrieval
Implements SRS Section 4: Script Generation Engine.

Upgrades:
- Example script indexing from example_scripts/ folder
- Structured document extraction
- Improved search with combined method + example retrieval
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
    """

    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents: List[Dict] = []
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

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_doc = ast.get_docstring(node) or ""
                    class_info = {
                        "type": "class",
                        "name": node.name,
                        "module": module_name,
                        "file_path": str(file_path),
                        "docstring": class_doc,
                        "methods": [],
                        "full_text": f"class {node.name}: {class_doc}"
                    }

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_doc = ast.get_docstring(item) or ""
                            args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                            signature = f"{item.name}({', '.join(args)})"

                            method_info = {
                                "type": "method",
                                "name": item.name,
                                "class_name": node.name,
                                "module": module_name,
                                "signature": signature,
                                "docstring": method_doc,
                                "full_text": f"{node.name}.{signature}: {method_doc}"
                            }
                            class_info["methods"].append(method_info)
                            documents.append(method_info)

                    documents.append(class_info)

                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                ):
                    func_doc = ast.get_docstring(node) or ""
                    args = [arg.arg for arg in node.args.args]
                    signature = f"{node.name}({', '.join(args)})"

                    documents.append({
                        "type": "function",
                        "name": node.name,
                        "module": module_name,
                        "signature": signature,
                        "docstring": func_doc,
                        "full_text": f"{signature}: {func_doc}"
                    })

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

        return documents

    async def index_library(self, library_path: Path, project_id: str) -> Dict:
        """
        Index an entire library folder.
        Returns metadata about the indexing process.
        """
        await self.initialize()

        library_path = Path(library_path)
        if not library_path.exists():
            raise ValueError(f"Library path does not exist: {library_path}")

        python_files = list(library_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files in {library_path}")

        all_documents = []
        for py_file in python_files:
            docs = self._parse_python_file(py_file)
            all_documents.extend(docs)

        self.documents = all_documents
        logger.info(f"Extracted {len(all_documents)} documents from library")

        if FAISS_AVAILABLE and self.embedding_model:
            texts = [doc["full_text"] for doc in all_documents]
            if texts:
                embeddings = self.embedding_model.encode(texts)

                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings).astype('float32'))

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
            "functions": len([d for d in all_documents if d["type"] == "function"])
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search the indexed library for relevant methods/classes.
        Uses FAISS if available, otherwise keyword matching.
        """
        if not self.documents:
            return []

        if FAISS_AVAILABLE and self.index and self.embedding_model:
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.index.search(
                np.array(query_embedding).astype('float32'),
                min(top_k, len(self.documents))
            )

            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(1 / (1 + dist))
                    results.append(doc)

            return results
        else:
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


class ExampleScriptLoader:
    """
    Loads and indexes example test scripts for few-shot prompting.
    Scans the example_scripts/ directory for .py files.
    """

    def __init__(self, scripts_dir: Optional[Path] = None):
        self.scripts_dir = scripts_dir or Path("example_scripts")
        self._cache: List[Dict[str, str]] = []

    def load_examples(self) -> List[Dict[str, str]]:
        """
        Load all example scripts from the scripts directory.
        Returns list of {"description": "...", "code": "..."}
        """
        if self._cache:
            return self._cache

        if not self.scripts_dir.exists():
            logger.warning(f"Example scripts directory not found: {self.scripts_dir}")
            return []

        examples = []
        for py_file in sorted(self.scripts_dir.glob("*.py")):
            try:
                code = py_file.read_text(encoding='utf-8')
                description = self._extract_description(code)
                examples.append({
                    "filename": py_file.name,
                    "description": description,
                    "code": code
                })
                logger.info(f"Loaded example script: {py_file.name} - {description}")
            except Exception as e:
                logger.warning(f"Failed to load example {py_file}: {e}")

        self._cache = examples
        logger.info(f"Loaded {len(examples)} example scripts for few-shot prompting")
        return examples

    @staticmethod
    def _extract_description(code: str) -> str:
        """Extract the test case description from script docstring."""
        match = re.search(r'Test Case Description:\s*(.+)', code)
        if match:
            return match.group(1).strip()
        # Fallback: try module docstring
        match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if match:
            first_line = match.group(1).strip().split('\n')[0]
            return first_line[:100]
        return "Example test script"

    def find_relevant_examples(
        self,
        query: str,
        max_examples: int = 2
    ) -> List[Dict[str, str]]:
        """
        Find the most relevant example scripts for a given query.
        Uses simple keyword matching (FAISS overkill for <20 examples).
        """
        examples = self.load_examples()
        if not examples:
            return []

        query_terms = set(query.lower().split())
        scored = []

        for ex in examples:
            text = f"{ex['description']} {ex['code']}".lower()
            score = sum(1 for term in query_terms if term in text)
            scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:max_examples]]


class CodeGuardrail:
    """
    Static analysis layer to validate LLM-generated code.
    Checks: syntax, forbidden imports, dangerous patterns, size limits.
    """

    def __init__(self):
        self.forbidden_imports = set(settings.FORBIDDEN_IMPORTS)
        self.max_size = settings.MAX_SCRIPT_SIZE

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated Python code.
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        if len(code.encode('utf-8')) > self.max_size:
            errors.append(f"Code exceeds maximum size of {self.max_size} bytes")

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors

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

        return len(errors) == 0, errors

    def extract_code_from_response(self, response: str) -> str:
        """Extract Python code from Ollama response."""
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return response.strip()


# Global instances
library_indexer = LibraryIndexer()
example_loader = ExampleScriptLoader()
code_guardrail = CodeGuardrail()
