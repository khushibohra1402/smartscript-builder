"""
Script Generator Service
Orchestrates RAG Engine + Ollama + Code Guardrail

Staged Pipeline:
  Stage 1: Retrieve context + few-shot examples via RAG
  Stage 2: Generate script via Ollama with mega-prompt
  Stage 3: Validate with quality guardrails
  Stage 4: Auto-correct (1 retry) if validation fails
"""

import time
from typing import Optional, List
from pathlib import Path
from loguru import logger

from app.services.rag_engine import library_indexer, prompt_builder, code_guardrail
from app.services.ollama_client import ollama_client
from app.services.config_manager import config_manager
from app.services.llm_formatter import structure_test_scenario
from app.models.schemas import ScriptGenerationRequest, ScriptGenerationResponse, DeviceType


MAX_RETRIES = 1  # Self-correction attempts


class ScriptGenerator:
    """
    Main service for AI-powered test script generation.
    
    Pipeline:
    1. Index library + example scripts
    2. RAG search for relevant methods + few-shot examples
    3. Build mega-prompt with constraints + context + examples + task
    4. Inject STB environment configuration when applicable
    5. Generate code via Ollama (with extended context window)
    6. Validate with quality guardrail
    7. If validation fails, auto-correct once
    """
    
    async def generate(
        self,
        request: ScriptGenerationRequest,
        library_path: Optional[Path] = None,
        project_name: Optional[str] = None,
    ) -> ScriptGenerationResponse:
        """
        Generate a test script from natural language description.
        """
        start_time = time.time()
        
        # Stage 0: Structure user input via lightweight LLM
        structured_description = await structure_test_scenario(request.description)
        logger.info(f"Structured description:\n{structured_description[:300]}")
        
        # Stage 1: Index library if path provided
        if library_path:
            try:
                await library_indexer.index_library(library_path, request.project_id)
            except Exception as e:
                logger.warning(f"Library indexing failed: {e}")
        
        # Stage 1b: Search for relevant context (use structured description for better RAG hits)
        context = library_indexer.search(structured_description, top_k=4)
        context_names = [
            f"{doc.get('class_name', '')}.{doc.get('name', doc.get('signature', ''))}"
            for doc in context
        ]
        logger.info(f"RAG retrieved {len(context)} relevant documents")

        # Stage 1c: Retrieve few-shot example scripts
        example_scripts = library_indexer.get_example_scripts(request.description, top_k=3)
        logger.info(f"Retrieved {len(example_scripts)} example scripts for few-shot prompting")
        
        # Stage 2: Build the mega-prompt
        prompt = prompt_builder.build_prompt(
            user_description=structured_description,
            library_context=context,
            device_type=request.device_type.value,
            platform=request.platform.value,
            test_type=request.test_type.value,
            example_scripts=example_scripts,
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
            logger.info(f"Injected STB environment config into prompt for {project_name}")
        
        # Stage 3: Generate code via Ollama
        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=8192,
            )
            logger.info(f"Prompt size: {len(prompt)} characters")
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
                status_code=504
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
        
        # Stage 4: Validate with quality guardrail
        is_valid, validation_errors = code_guardrail.validate(script_code)
        logger.info(f"Initial validation: valid={is_valid}, errors={validation_errors}")

        # Stage 5: Self-correction loop (1 retry if validation fails)
        if not is_valid and script_code.strip():
            for attempt in range(MAX_RETRIES):
                logger.info(f"Self-correction attempt {attempt + 1}/{MAX_RETRIES}")
                correction_prompt = prompt_builder.build_correction_prompt(
                    original_script=script_code,
                    validation_errors=validation_errors,
                    user_description=request.description,
                )
                try:
                    correction_response = await ollama_client.generate(
                        prompt=correction_prompt,
                        temperature=0.2,
                        max_tokens=8192
                    )
                    corrected_code = code_guardrail.extract_code_from_response(correction_response)
                    is_valid, validation_errors = code_guardrail.validate(corrected_code)
                    
                    if is_valid:
                        script_code = corrected_code
                        logger.info("Self-correction succeeded")
                        break
                    else:
                        script_code = corrected_code
                        logger.warning(f"Self-correction attempt {attempt + 1} still has errors: {validation_errors}")
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
            generation_time_ms=generation_time
        )
    
    async def analyze_failure(self, error_traceback: str) -> str:
        """
        Use Ollama to translate technical errors to user-friendly messages.
        Implements SRS Section 5.2: AI Failure Analyst.
        """
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