"""
Script Generator Service
Orchestrates RAG Engine + Ollama + Code Guardrail

Staged Pipeline:
  Stage 0: Structure user input via lightweight LLM
  Stage 1: Extract intents + retrieve context via hybrid RAG
  Stage 2: Generate script via Ollama with constraint-driven prompt
  Stage 3: Validate with quality + hallucination guardrails
  Stage 4: Auto-correct (1 retry) if validation fails
"""

import time
from typing import Optional, Set
from pathlib import Path
from loguru import logger

from app.services.rag_engine import (
    library_indexer, prompt_builder, code_guardrail,
    extract_intents, CORE_API_SET,
)
from app.services.ollama_client import ollama_client
from app.services.config_manager import config_manager
from app.services.llm_formatter import structure_test_scenario
from app.models.schemas import ScriptGenerationRequest, ScriptGenerationResponse, DeviceType


MAX_RETRIES = 1


def _build_dynamic_api_set(context: list) -> Set[str]:
    """Extract a flat set of 'ClassName.method_name' from RAG results for hallucination checking."""
    apis: Set[str] = set()
    for doc in context:
        if doc.get("type") == "method":
            cls = doc.get("class_name", "")
            name = doc.get("name", "")
            if cls and name:
                apis.add(f"{cls}.{name}")
        elif doc.get("type") == "function":
            name = doc.get("name", "")
            if name:
                apis.add(name)
    return apis


class ScriptGenerator:
    """
    Main service for AI-powered test script generation.
    """

    async def generate(
        self,
        request: ScriptGenerationRequest,
        library_path: Optional[Path] = None,
        project_name: Optional[str] = None,
    ) -> ScriptGenerationResponse:
        start_time = time.time()

        # Stage 0: Structure user input
        structured_description = await structure_test_scenario(request.description)
        logger.info(f"Structured description:\n{structured_description[:300]}")

        # Stage 1a: Extract intents
        intents = extract_intents(structured_description)
        logger.info(f"Detected intents: {intents}")

        # Stage 1b: Index library if path provided
        if library_path:
            try:
                await library_indexer.index_library(library_path, request.project_id)
            except Exception as e:
                logger.warning(f"Library indexing failed: {e}")

        # Stage 1c: Hybrid retrieval (embedding + keyword + intent)
        context = library_indexer.search(structured_description, top_k=6, intents=intents)
        context_names = [
            f"{doc.get('class_name', '')}.{doc.get('name', doc.get('signature', ''))}"
            for doc in context
        ]
        logger.info(f"RAG retrieved {len(context)} docs: {context_names}")

        # Build dynamic API set for hallucination checking
        dynamic_apis = _build_dynamic_api_set(context)
        allowed_apis = CORE_API_SET | dynamic_apis

        # Stage 1d: Retrieve few-shot examples
        example_scripts = library_indexer.get_example_scripts(request.description, top_k=3)
        logger.info(f"Retrieved {len(example_scripts)} example scripts")

        # Stage 2: Build constraint-driven prompt
        prompt = prompt_builder.build_prompt(
            user_description=structured_description,
            library_context=context,
            device_type=request.device_type.value,
            platform=request.platform.value,
            test_type=request.test_type.value,
            example_scripts=example_scripts,
            intents=intents,
        )

        # Stage 2b: Inject STB environment configuration
        if request.device_type == DeviceType.STB and project_name:
            config_manager.update_stb_config(
                project_name=project_name,
                stb_model=request.stb_model,
                stb_type=request.stb_type,
                stb_ip=request.stb_ip,
                rcu_type=request.rcu_type,
                rcu_ip=request.rcu_ip,
                smart_plug_enabled=request.smart_plug_enabled,
                smart_plug_ip=request.smart_plug_ip,
                hdmi_index=request.hdmi_capture_index,
            )
            env_summary = config_manager.get_environment_summary(project_name)
            prompt += f"\n\n{env_summary}\n"
            logger.info(f"Injected STB config for {project_name}")

        # Stage 3: Generate via Ollama
        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=8192,
            )
            logger.info(f"Prompt size: {len(prompt)} chars")
            script_code = code_guardrail.extract_code_from_response(response)
        except TimeoutError as e:
            logger.error(f"Ollama timed out: {e}")
            return ScriptGenerationResponse(
                script_code="",
                is_valid=False,
                validation_errors=[
                    "LLM generation timed out (504). Model may be too large or prompt too complex."
                ],
                rag_context_used=context_names,
                generation_time_ms=(time.time() - start_time) * 1000,
                status_code=504,
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return ScriptGenerationResponse(
                script_code="",
                is_valid=False,
                validation_errors=[f"Code generation failed: {str(e)}"],
                rag_context_used=context_names,
                generation_time_ms=(time.time() - start_time) * 1000,
            )

        # Stage 4: Validate (quality + hallucination)
        is_valid, validation_errors = code_guardrail.validate(script_code, dynamic_apis=dynamic_apis)
        logger.info(f"Validation: valid={is_valid}, errors={validation_errors}")

        # Stage 5: Self-correction (1 retry)
        if not is_valid and script_code.strip():
            for attempt in range(MAX_RETRIES):
                logger.info(f"Self-correction attempt {attempt + 1}/{MAX_RETRIES}")
                correction_prompt = prompt_builder.build_correction_prompt(
                    original_script=script_code,
                    validation_errors=validation_errors,
                    user_description=request.description,
                    allowed_apis=allowed_apis,
                )
                try:
                    correction_response = await ollama_client.generate(
                        prompt=correction_prompt,
                        temperature=0.2,
                        max_tokens=8192,
                    )
                    corrected_code = code_guardrail.extract_code_from_response(correction_response)
                    is_valid, validation_errors = code_guardrail.validate(
                        corrected_code, dynamic_apis=dynamic_apis
                    )

                    if is_valid:
                        script_code = corrected_code
                        logger.info("Self-correction succeeded")
                        break
                    else:
                        script_code = corrected_code
                        logger.warning(f"Correction attempt {attempt + 1} errors: {validation_errors}")
                except Exception as e:
                    logger.error(f"Self-correction failed: {e}")
                    break

        generation_time = (time.time() - start_time) * 1000
        logger.info(f"Script generated in {generation_time:.2f}ms, valid: {is_valid}")

        return ScriptGenerationResponse(
            script_code=script_code,
            is_valid=is_valid,
            validation_errors=validation_errors if validation_errors else None,
            rag_context_used=context_names,
            generation_time_ms=generation_time,
        )

    async def analyze_failure(self, error_traceback: str) -> str:
        prompt = prompt_builder.build_failure_analysis_prompt(error_traceback)
        try:
            response = await ollama_client.generate(
                prompt=prompt, temperature=0.5, max_tokens=100,
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Failure analysis failed: {e}")
            return "The test encountered an unexpected error. Please review the logs for details."


# Global instance
script_generator = ScriptGenerator()
