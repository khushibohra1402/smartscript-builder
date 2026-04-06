"""
Prompt Builder v2 - Structured Mega-Prompt Construction
Implements few-shot prompting, library schema injection, and step-based generation.

Pipeline: User Description → Library Schema → Few-Shot Examples → Structured Prompt
"""

import re
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger


class PromptBuilder:
    """
    Constructs structured mega-prompts for Ollama with:
    1. Strict rules and constraints
    2. Structured library method registry (schema injection)
    3. Few-shot example scripts
    4. Step-based reasoning before code generation
    5. User task description
    """

    SYSTEM_PROMPT = """You are an expert Python automation test script generator for an enterprise STB (Set-Top Box) testing platform.

## ABSOLUTE RULES — VIOLATION = INVALID SCRIPT
1. ONLY use objects and methods from the ALLOWED METHODS section below.
2. NEVER import os, subprocess, sys, shutil, pathlib, socket, or requests.
3. NEVER invent or hallucinate method names — if a method is not listed below, do NOT use it.
4. Always follow the executeTestCase() → test_XXXX(extra) pattern shown in examples.
5. Return ONLY Python code. No explanations, no markdown.

## CODE STRUCTURE RULES
- Define executeTestCase() that returns (True/False, "message")
- Use descriptive print() statements before each action
- Check return values and return (False, "error msg") on failure
- Use time.sleep() between UI interactions
- Handle locked content with screen.isLiveTVLocked() + action.unlockContent()
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
    def _extract_execute_function(code: str) -> Optional[str]:
        """Extract just the executeTestCase() function from a full script."""
        match = re.search(
            r'(def executeTestCase\(\):.+?)(?=\ndef test_|\Z)',
            code,
            re.DOTALL
        )
        if match:
            return match.group(1).rstrip()
        return None

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
        prompt = f"""{PromptBuilder.SYSTEM_PROMPT}

{schema_section}

{examples_section}

## CONSTRAINTS
- Device Type: {device_type}
- Platform: {platform}
- Test Type: {test_type}
- Import: from src.stb_lib.stb import *
- Follow the executeTestCase() pattern from examples above

## TASK
{user_description}

## STEP-BY-STEP PLAN
Write test steps as Python comments inside the function.
Do NOT output reasoning outside the code.

## Generated Python Code:
Write only the Python script below.
Do not use markdown formatting.


## REQUIRED SCRIPT TEMPLATE

The generated script MUST follow this structure exactly:

from src.stb_lib.stb import *

def executeTestCase():

    print("Starting test")

    # Step 1
    if not condition:
        return False, "error"

    # Step 2
    if not condition:
        return False, "error"

    return True, ""


Before writing the code:

1. Review the ALLOWED METHODS section
2. Only use those methods
3. If a required method is missing, skip the step instead of inventing one



## UI INTERACTION RULES

- Add time.sleep(2) after navigation actions
- Add time.sleep(1) after UI interactions
- Always validate screen state before performing actions




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


# Global instance
prompt_builder = PromptBuilder()