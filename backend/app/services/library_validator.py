"""
Library Validator - AST-based method call validation.
Warns on unrecognized method calls without rejecting the script.

Validates that generated code uses methods from the indexed library.
"""

import ast
import re
from typing import List, Dict, Tuple, Set
from loguru import logger


class LibraryValidator:
    """
    AST-based validator that extracts method calls from generated code
    and checks them against the indexed library registry.
    
    Mode: warn (not reject) on unrecognized calls.
    """

    def __init__(self):
        # Known safe objects/functions that don't need library validation
        self.safe_names: Set[str] = {
            "print", "len", "range", "str", "int", "float", "bool",
            "list", "dict", "set", "tuple", "enumerate", "zip",
            "isinstance", "hasattr", "getattr", "setattr",
            "True", "False", "None", "assert",
            "time.sleep", "pytest",
        }
        # Known safe module-level calls
        self.safe_prefixes: Set[str] = {
            "time.", "pytest.", "config.",
        }

    def extract_method_calls(self, code: str) -> List[str]:
        """
        Extract all object.method() calls from code using AST.
        Returns list of strings like 'action.home', 'screen.isContentPlaying'.
        """
        calls = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return calls

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = self._resolve_call(node.func)
                if call_str:
                    calls.append(call_str)

        return calls

    def _resolve_call(self, node) -> str:
        """Resolve an AST node to a dotted call string."""
        if isinstance(node, ast.Attribute):
            value_str = self._resolve_call(node.value)
            if value_str:
                return f"{value_str}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Name):
            return node.id
        return ""

    def build_registry(self, library_docs: List[Dict]) -> Set[str]:
        """
        Build a set of known method identifiers from indexed library documents.
        Returns set like {'action.home', 'screen.isContentPlaying', 'Browser.navigate'}
        """
        registry: Set[str] = set()

        for doc in library_docs:
            doc_type = doc.get("type", "")
            if doc_type == "method":
                class_name = doc.get("class_name", "")
                method_name = doc.get("name", "")
                if class_name and method_name:
                    registry.add(f"{class_name}.{method_name}")
                    # Also add lowercase variants for instance-style calls
                    registry.add(f"{class_name.lower()}.{method_name}")
            elif doc_type == "function":
                name = doc.get("name", "")
                if name:
                    registry.add(name)
            elif doc_type == "class":
                name = doc.get("name", "")
                if name:
                    registry.add(name)

        return registry

    def validate(
        self,
        code: str,
        library_docs: List[Dict]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate generated code against the library registry.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
            - is_valid: True (we only warn, never reject based on method calls)
            - errors: empty list (reserved for future strict mode)
            - warnings: list of unrecognized method calls
        """
        registry = self.build_registry(library_docs)
        calls = self.extract_method_calls(code)
        warnings: List[str] = []

        for call in calls:
            # Skip safe builtins and known prefixes
            if call in self.safe_names:
                continue
            if any(call.startswith(p) for p in self.safe_prefixes):
                continue
            # Skip simple function calls (no dot = likely builtin or local)
            if "." not in call:
                continue

            # Check against registry
            if call not in registry:
                # Also check if the method name alone matches (fuzzy)
                method_only = call.split(".")[-1]
                fuzzy_match = any(method_only == r.split(".")[-1] for r in registry)
                if fuzzy_match:
                    continue  # Method exists on a different class, likely OK
                warnings.append(f"Unrecognized method call: {call}")

        if warnings:
            logger.info(f"Library validator: {len(warnings)} unrecognized calls found")
            for w in warnings[:5]:
                logger.debug(f"  - {w}")

        return True, [], warnings


# Global instance
library_validator = LibraryValidator()