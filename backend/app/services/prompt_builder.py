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

    SYSTEM_PROMPT = """You are a Senior Python Automation Architect specializing in enterprise STB automation testing.

Generate a production-grade automation test script using the enterprise automation framework.

The generated script MUST strictly follow this architecture:

1. Metadata header
2. Import statement
3. executeTestCase() function
4. test_<TESTCASEID>() wrapper
5. main execution block

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

ONLY use the methods above.
DO NOT invent new APIs.

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
5. Do NOT invent APIs.
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

    return True, ""


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