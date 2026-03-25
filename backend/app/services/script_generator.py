"""
Script Generator Service
Orchestrates RAG Engine + Ollama + Code Guardrail
Implements the complete flow from SRS Section 4.
"""

import time
from typing import Optional, List
from pathlib import Path
from loguru import logger

from app.services.rag_engine import library_indexer, prompt_builder, code_guardrail
from app.services.ollama_client import ollama_client
from app.models.schemas import ScriptGenerationRequest, ScriptGenerationResponse


class ScriptGenerator:
    """
    Main service for AI-powered test script generation.
    
    Flow:
    1. Load library index for the project
    2. Search for relevant methods using RAG
    3. Build mega-prompt with constraints + context + task
    4. Generate code via Ollama
    5. Validate with code guardrail
    """
    
    async def generate(
        self,
        request: ScriptGenerationRequest,
        library_path: Optional[Path] = None
    ) -> ScriptGenerationResponse:
        """
        Generate a test script from natural language description.
        
        Args:
            request: Script generation request with description and config
            library_path: Path to project's enterprise library
        
        Returns:
            ScriptGenerationResponse with code and validation results
        """
        start_time = time.time()
        
        # Step 1: Index library if path provided
        if library_path:
            try:
                await library_indexer.index_library(library_path, request.project_id)
            except Exception as e:
                logger.warning(f"Library indexing failed: {e}")
        
        # Step 2: Search for relevant context
        context = library_indexer.search(request.description, top_k=10)
        context_names = [
            f"{doc.get('class_name', '')}.{doc.get('name', doc.get('signature', ''))}"
            for doc in context
        ]
        logger.info(f"RAG retrieved {len(context)} relevant documents")
        
        # Step 3: Build the mega-prompt
        prompt = prompt_builder.build_prompt(
            user_description=request.description,
            library_context=context,
            device_type=request.device_type.value,
            platform=request.platform.value,
            test_type=request.test_type.value
        )
        
        # Step 4: Generate code via Ollama
        try:
            response = await ollama_client.generate(
                prompt=prompt,
                temperature=0.3  # Lower temperature for more deterministic code
            )
            
            # Extract code from response
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
        
        # Step 5: Validate with guardrail
        is_valid, validation_errors = code_guardrail.validate(script_code)
        
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
