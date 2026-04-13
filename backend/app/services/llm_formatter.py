"""
LLM Test Case Formatter (Robust Version - Text आधारित)
"""

import re
from typing import Optional, Dict, List
from loguru import logger

from app.services.ollama_client import ollama_client


# 🔥 Updated prompt (TEXT instead of JSON)
STRUCTURING_PROMPT = """
Convert the test scenario into structured test case sections.

Return ONLY in this format:

Preconditions:
- ...

Steps:
1. ...
2. ...

Expected Results:
- ...

Rules:
- Do NOT return JSON
- Do NOT add extra sections
- Do NOT explain anything

Scenario:
{user_input}
"""


def parse_text_output(text: str) -> Optional[Dict[str, List[str]]]:
    """
    Parse structured text into dictionary.
    Much more reliable than JSON parsing for small models.
    """

    try:
        sections = {
            "preconditions": [],
            "test_steps": [],
            "expected_results": []
        }

        current = None

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            # Section detection
            if line.lower().startswith("preconditions"):
                current = "preconditions"
                continue
            elif line.lower().startswith("steps"):
                current = "test_steps"
                continue
            elif line.lower().startswith("expected"):
                current = "expected_results"
                continue

            # Bullet points
            if line.startswith("-") and current:
                sections[current].append(line[1:].strip())

            # Numbered steps
            elif re.match(r"\d+\.", line) and current == "test_steps":
                step = line.split(".", 1)[1].strip()
                sections[current].append(step)

        # ✅ Validation (non-empty)
        if all(sections.values()):
            return sections

        return None

    except Exception as e:
        logger.error(f"Parsing error: {e}")
        return None


def format_for_pipeline(structured: Dict[str, List[str]], original_scenario: str) -> str:
    """
    Convert structured data → pipeline format
    """
    lines = [f"Test Case: {original_scenario}", ""]

    lines.append("Preconditions:")
    for item in structured["preconditions"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("Steps:")
    for i, step in enumerate(structured["test_steps"], 1):
        lines.append(f"{i}. {step}")

    lines.append("")
    lines.append("Expected Results:")
    for item in structured["expected_results"]:
        lines.append(f"- {item}")

    return "\n".join(lines)


async def structure_test_scenario(scenario: str) -> str:
    """
    Main pipeline entry (robust + fast)
    """

    base_prompt = STRUCTURING_PROMPT.format(user_input=scenario)

    for attempt in range(3):
        prompt = base_prompt

        # 🔥 Strong retry reinforcement
        if attempt == 1:
            prompt += "\nSTRICT: Follow the format EXACTLY."
        elif attempt == 2:
            prompt += "\nCRITICAL: Do NOT output anything except the required sections."

        try:
            raw = await ollama_client.generate(
                prompt=prompt,
                temperature=0.0,   # deterministic
                max_tokens=300     # faster + avoids truncation
            )

            logger.info(f"Structuring attempt {attempt + 1}: {raw[:200]}")

            result = parse_text_output(raw)
            if result:
                logger.info("Test scenario structured successfully")
                return format_for_pipeline(result, scenario)

            logger.warning(f"Parsing failed (attempt {attempt + 1})")

        except TimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            continue

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            break

    logger.warning("Falling back to raw user input")
    return scenario