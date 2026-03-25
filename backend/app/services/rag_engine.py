"""
RAG Engine - Library Indexing and Context Injection
Implements SRS Section 4: Script Generation Engine.

Flow:
1. Library Indexing - Scan custom enterprise libraries and create FAISS index
2. Prompt Construction - Build mega-prompt with constraints + context + task
3. Code Generation - Send to Ollama and receive Python script
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
                # Extract class definitions
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
                    
                    # Extract methods
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
                
                # Extract standalone functions
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
        
        # Find all Python files
        python_files = list(library_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files in {library_path}")
        
        # Parse all files
        all_documents = []
        for py_file in python_files:
            docs = self._parse_python_file(py_file)
            all_documents.extend(docs)
        
        self.documents = all_documents
        logger.info(f"Extracted {len(all_documents)} documents from library")
        
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
            # Vector search
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.index.search(
                np.array(query_embedding).astype('float32'), 
                min(top_k, len(self.documents))
            )
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(1 / (1 + dist))  # Convert distance to similarity
                    results.append(doc)
            
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


class PromptBuilder:
    """
    Constructs the mega-prompt for Ollama with:
    1. Constraints (only use enterprise_lib)
    2. Context (relevant library methods from RAG)
    3. Task (user's natural language description)
    """
    
    SYSTEM_PROMPT = """You are an expert Python automation test script generator.
You MUST follow these strict rules:

1. ONLY use classes and methods from the provided enterprise library context.
2. NEVER import os, subprocess, sys, shutil, pathlib, socket, or requests.
3. Generate complete, runnable Python test classes.
4. Include proper setup() and teardown() methods.
5. Use descriptive variable names and add comments.
6. Handle exceptions gracefully with try/except blocks.
7. Return ONLY the Python code, no explanations."""

    @staticmethod
    def build_prompt(
        user_description: str,
        library_context: List[Dict],
        device_type: str,
        platform: str,
        test_type: str
    ) -> str:
        """
        Build the complete prompt for Ollama.
        
        Args:
            user_description: Natural language test description
            library_context: Retrieved library methods from RAG
            device_type: 'web' or 'mobile'
            platform: 'chrome', 'firefox', 'android', etc.
            test_type: 'functional', 'regression', etc.
        """
        # Format library context
        context_lines = ["### Available Library Methods:"]
        for doc in library_context:
            if doc["type"] == "method":
                context_lines.append(
                    f"- {doc['class_name']}.{doc['signature']}: {doc['docstring'][:100]}"
                )
            elif doc["type"] == "class":
                context_lines.append(f"- class {doc['name']}: {doc['docstring'][:100]}")
            elif doc["type"] == "function":
                context_lines.append(f"- {doc['signature']}: {doc['docstring'][:100]}")
        
        context_text = "\n".join(context_lines)
        
        # Build the complete prompt
        prompt = f"""{PromptBuilder.SYSTEM_PROMPT}

### Constraints:
- Device Type: {device_type}
- Platform: {platform}
- Test Type: {test_type}
- Only use methods from 'enterprise_lib.{device_type}'

{context_text}

### Task:
{user_description}

### Generated Python Test Script:
```python
"""
        
        return prompt
    
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
    Implements SRS Section 4: Code Guardrail.
    
    Checks:
    1. Python syntax is valid (ast.parse)
    2. No forbidden imports
    3. Code size limits
    """
    
    def __init__(self):
        self.forbidden_imports = set(settings.FORBIDDEN_IMPORTS)
        self.max_size = settings.MAX_SCRIPT_SIZE
    
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated Python code.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
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
        
        return len(errors) == 0, errors
    
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
