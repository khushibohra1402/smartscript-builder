"""
Script Generator v2 - Orchestrates upgraded RAG pipeline.

Flow:
1. Load library index + example scripts
2. Search for relevant methods (RAG) + find relevant examples
3. Build structured mega-prompt (schema + few-shot + task)
4. Generate code via Ollama (extended 16K context)
5. Validate with code guardrail + library validator
6. Return script with warnings
"""

import time
from typing import Optional, List
from pathlib import Path
from loguru import logger

from app.services.rag_engine import library_indexer, example_loader, code_guardrail
from app.services.prompt_builder import prompt_builder
from app.services.library_validator import library_validator
from app.services.ollama_client import ollama_client
from app.models.schemas import ScriptGenerationRequest, ScriptGenerationResponse


class ScriptGenerator:
    """
    Main service for AI-powered test script generation.
    Uses the upgraded v2 pipeline with few-shot prompting and library validation.
    """

    async def generate(
        self,
        request: ScriptGenerationRequest,
        library_path: Optional[Path] = None
    ) -> ScriptGenerationResponse:
        """Generate a test script from natural language description."""
        start_time = time.time()

        # Step 1: Index library if path provided
        if library_path:
            try:
                await library_indexer.index_library(library_path, request.project_id)
            except Exception as e:
                logger.warning(f"Library indexing failed: {e}")

        # Step 2: RAG retrieval — methods + examples
        context = library_indexer.search(request.description, top_k=15)
        context_names = [
            f"{doc.get('class_name', '')}.{doc.get('name', doc.get('signature', ''))}"
            for doc in context
        ]
        logger.info(f"RAG retrieved {len(context)} relevant documents")

        # Step 3: Find relevant example scripts for few-shot
        relevant_examples = example_loader.find_relevant_examples(
            request.description, max_examples=2
        )
        logger.info(f"Found {len(relevant_examples)} relevant example scripts")

        # Step 4: Build structured mega-prompt
        prompt = prompt_builder.build_prompt(
            user_description=request.description,
            library_context=context,
            device_type=request.device_type.value,
            platform=request.platform.value,
            test_type=request.test_type.value,
            example_scripts=relevant_examples
        )

        # Step 5: Generate via Ollama with extended context
        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=4096,
                num_ctx=16384  # Extended context window
            )
            script_code = code_guardrail.extract_code_from_response(response)

        except TimeoutError as e:
            logger.error(f"Ollama generation timed out: {e}")
            return ScriptGenerationResponse(
                script_code="",
                is_valid=False,
                validation_errors=[
                    "LLM generation timed out (504). "
                    "The model may be too large for current hardware or the prompt too complex."
                ],
                rag_context_used=context_names,
                generation_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return ScriptGenerationResponse(
                script_code="",
                is_valid=False,
                validation_errors=[f"Code generation failed: {str(e)}"],
                rag_context_used=context_names,
                generation_time_ms=(time.time() - start_time) * 1000
            )

        # Step 6: Code guardrail validation (syntax + forbidden imports)
        is_valid, validation_errors = code_guardrail.validate(script_code)

        # Step 7: Library validator (warn on unrecognized methods)
        _, _, lib_warnings = library_validator.validate(script_code, library_indexer.documents)

        # Merge warnings into validation_errors for visibility
        all_issues = list(validation_errors) if validation_errors else []
        if lib_warnings:
            all_issues.extend([f"⚠ {w}" for w in lib_warnings])

        generation_time = (time.time() - start_time) * 1000
        logger.info(
            f"Script generated in {generation_time:.0f}ms | "
            f"valid={is_valid} | warnings={len(lib_warnings)}"
        )

        return ScriptGenerationResponse(
            script_code=script_code,
            is_valid=is_valid,
            validation_errors=all_issues if all_issues else None,
            rag_context_used=context_names,
            generation_time_ms=generation_time
        )

    async def analyze_failure(self, error_traceback: str) -> str:
        """Use Ollama to translate technical errors to user-friendly messages."""
        prompt = prompt_builder.build_failure_analysis_prompt(error_traceback)

        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=100
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Failure analysis failed: {e}")
            return "The test encountered an unexpected error. Please review the logs for details."


# Global instance
script_generator = ScriptGenerator()
