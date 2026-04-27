"""
Concept Extractor Tool - Healthcare Agentic AI System
Extracts 1-3 most appropriate clinical concepts from text using local LLM inference.

Following copilot-instructions.md patterns:
- Prompt template with context injection (main_note + chunk + concepts)
- Local LLM inference with standard parameters
- Response extraction and validation
- Returns 1-3 most fitting concepts
"""

# Disable flash_attention before importing transformers to avoid compatibility issues
import os
os.environ['FLASH_ATTENTION_SKIP_DUPLICATE_CHECK'] = '1'

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import logging
from typing import List, Dict, Optional
import re
import time

logger = logging.getLogger(__name__)

class ConceptExtractorTool:
    """
    LLM-based concept extraction following copilot-instructions.md.
    
    Core data flow:
    1. Input: CSV chunk + candidate concepts
    2. Processing: Zero-shot LLM inference (local model, no API calls)
    3. Output: 1-3 most fitting concepts with confidence score
    """
    
    def __init__(self, model_path: str, device: str = "auto"):
        """
        Initialize following copilot-instructions MODEL LOADING PATTERN.
        
        Standard setup: torch_dtype=torch.bfloat16, device_map="auto", low_cpu_mem_usage=True
        
        Args:
            model_path: Path to local LLM (7B/13B/70B)
            device: CUDA device (auto = device_map="auto")
        """
        self.model_path = model_path
        self.device = device
        self.tokenizer = None
        self.model = None
        self.pipe = None
        
        self._load_model()
    
    def _load_model(self):
        """
        Load model following copilot-instructions MODEL LOADING PATTERN:
        - torch_dtype=torch.bfloat16 for memory optimization
        - device_map="auto" for automatic GPU placement
        - low_cpu_mem_usage=True for large models
        """
        logger.info(f"Loading ConceptExtractorTool model from {self.model_path}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with copilot-instructions standard pattern
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,  # Memory optimization per copilot-instructions
            device_map="auto",  # Automatic multi-GPU splitting
            low_cpu_mem_usage=True,
            attn_implementation="eager"  # Disable flash_attention for compatibility
        )
        
        # Create pipeline for inference
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )
        
        logger.info(f"ConceptExtractorTool model loaded on device: {self.pipe.device}")
    
    def extract(self, clinical_text: str, main_note: Optional[str] = None,
                candidate_concepts: Optional[List[str]] = None,
                temperature: float = 0.1) -> Dict:
        """
        Extract clinical concepts from text.
        If candidate_concepts is provided, select the most fitting from the list.
        If not, extract all relevant concepts present in the text (open extraction).
        """
        start_time = time.time()

        # Build prompt for open or guided extraction
        prompt = self._build_prompt(clinical_text, main_note, candidate_concepts)
        logger.debug(f"Built prompt (length={len(prompt)})")

        try:
            outputs = self.pipe(
                prompt,
                do_sample=True,
                top_k=10,
                temperature=temperature,
                top_p=0.95,
                max_new_tokens=1024,  # Allow many tokens for comprehensive extraction
                max_length=None,  # Avoid conflict with max_new_tokens
                repetition_penalty=1.2,
                eos_token_id=self.tokenizer.eos_token_id
            )
            generated_text = outputs[0]['generated_text']
            logger.debug(f"Generated text (length={len(generated_text)})")
            response = self._extract_response(generated_text, prompt)
            logger.debug(f"Extracted response: '{response}'")
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                'concepts': [],
                'raw_response': str(e),
                'confidence': 0.0
            }

        # Parse concepts from response
        concepts = self._parse_concepts(response, candidate_concepts, clinical_text)
        confidence = self._compute_confidence(concepts, candidate_concepts, clinical_text)
        
        runtime = time.time() - start_time
        logger.info(f"Extraction: {len(concepts)} concepts (target 1-3), confidence={confidence}, runtime={runtime:.2f}s")
        
        # CUDA DEVICE MANAGEMENT from copilot-instructions: clear cache between batches
        torch.cuda.empty_cache()
        
        return {
            'concepts': concepts,
            'raw_response': response,
            'confidence': confidence
        }
    
    def _build_prompt(self, chunk: str, main_note: Optional[str] = None,
                      concepts: Optional[List[str]] = None) -> str:
        """
        Build prompt for open or guided concept extraction.
        If concepts is provided, ask for the most fitting from the list.
        If not, ask for all relevant concepts present in the text.
        """
        context = main_note if main_note else "General clinical assessment"
        if concepts:
            concepts_str = ", ".join(concepts)
            system_prompt = f"""Referring to the main note: {context}
Consider the given text fragment and the list of suggested concepts:
Chunk: {chunk}
Concepts: {concepts_str}
Question: Please identify the 1-3 most fitting concepts for the provided chunk = '{chunk}'.
Instructions:
- Return ONLY the concept names, separated by commas or as a list.
"""
        else:
            system_prompt = f"""Referring to the main note: {context}
Consider the following clinical text fragment:
Chunk: {chunk}

Task: Extract ONLY medical/clinical/healthcare concepts that are EXPLICITLY MENTIONED. 

RULES (STRICT):
- Extract ONLY: diagnoses, symptoms, signs, vital signs, laboratory findings, medications, treatments, procedures, medical conditions
- Do NOT extract: contextual details, lifestyle information, objects, time/location references, or non-medical descriptors
- Only extract concepts that have direct medical/clinical significance
- Do NOT infer related conditions
- Do NOT add concepts from background knowledge
- Return ONLY concept names separated by commas, no explanations

Extract ONLY what is explicitly in the text:
"""
        # Build messages for chat template
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        # Apply tokenizer's chat template for automatic formatting (copilot-instructions pattern)
        # Handles Llama 3, Mistral, or any HF model's native format
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt
    
    def _extract_response(self, generated_text: str, prompt: str) -> str:
        """
        Extract response after prompt following copilot-instructions pattern.
        
        Response = generated_text minus the original prompt prefix.
        
        For Llama 3: response comes after the chat template wrapping.
        For Mistral: response comes after [/INST] marker.
        
        Args:
            generated_text: Full generated text from model
            prompt: Original prompt sent to model
        
        Returns:
            Just the generated response part
        """
        # Remove prompt prefix
        if prompt in generated_text:
            response = generated_text[len(prompt):].strip()
            logger.debug(f"Removed prompt prefix, response length: {len(response)}")
            return response
        
        # Fallback: return last part
        logger.warning("Could not find prompt in generated_text, using fallback")
        return generated_text[-256:].strip()
    
    def _parse_concepts(self, response: str, candidates: Optional[List[str]] = None,
                       clinical_text: str = "") -> List[str]:
        """
        Parse 1-3 concepts from LLM response.
        
        Strategy following copilot-instructions OUTPUT PATTERN:
        1. Match response against candidate list (STRICT - must be candidates)
        2. Try comma-separated, line-separated, or individual names
        3. Return 1-3 matching candidates (don't extract free-form text)
        4. Validate that concepts appear in clinical text
        
        Args:
            response: LLM response (should name 1-3 concepts)
            candidates: Candidate concepts from CSV
            clinical_text: Original text for validation
        
        Returns:
            List of 1-3 extracted concept names
        """
        concepts = []
        response = response.strip()
        
        if not response:
            logger.warning("Empty response from LLM")
            return concepts
        
        logger.debug(f"Parsing response: '{response}'")
        
        # CRITICAL: Only match against candidates (copilot-instructions pattern)
        if candidates:
            response_lower = response.lower()
            
            # Strategy 1: Try to find multiple concepts separated by commas
            # Response might be: "Dyspnea, Asthma Exacerbation, Bronchospasm"
            if ',' in response:
                parts = [p.strip() for p in response.split(',')]
                logger.debug(f"Split by comma into {len(parts)} parts")
                
                for part in parts:
                    part_lower = part.lower()
                    
                    # Try exact match
                    for candidate in candidates:
                        if part_lower == candidate.lower():
                            logger.info(f"Comma-separated exact match: {candidate}")
                            concepts.append(candidate)
                            break
                    
                    # If not exact, try substring
                    if not concepts or concepts[-1] != part:
                        for candidate in candidates:
                            if candidate.lower() in part_lower:
                                logger.info(f"Comma-separated substring match: {candidate}")
                                concepts.append(candidate)
                                break
            
            # Strategy 2: If no comma-separated matches, try individual candidates
            if not concepts:
                # Sort by length (longest first) to avoid partial matches
                sorted_candidates = sorted(candidates, key=len, reverse=True)
                
                for candidate in sorted_candidates:
                    if candidate.lower() in response_lower:
                        logger.info(f"Substring match: {candidate}")
                        concepts.append(candidate)
            
            # Strategy 3: Word-level match (important words overlap)
            if not concepts:
                response_words = set(word.lower() for word in response.split() if len(word) > 3)
                
                for candidate in candidates:
                    candidate_words = set(word.lower() for word in candidate.split())
                    if candidate_words and (candidate_words & response_words):  # Intersection
                        logger.info(f"Word-level match: {candidate}")
                        concepts.append(candidate)
                        if len(concepts) >= 3:  # Limit to 3
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_concepts = []
            for c in concepts:
                if c.lower() not in seen:
                    seen.add(c.lower())
                    unique_concepts.append(c)
            concepts = unique_concepts
        
        # Fallback: extract free-form if candidates not provided or no match
        if not concepts and not candidates:
            logger.warning("No candidates provided, attempting free-form extraction")
            # Clean response: remove category headers and explanations
            cleaned = re.sub(
                r'^(the |a |an |answer is |concept is |best |most fitting|extracted concepts)',
                '',
                response,
                flags=re.IGNORECASE
            ).strip()
            
            # Remove category headers (lines ending with colon, alone on their line)
            lines = cleaned.split('\n')
            filtered_lines = []
            for line in lines:
                line = line.strip()
                # Skip category headers like "Demographics:", "Acute symptoms:", etc.
                if line and not re.match(r'^[A-Za-z\s/]+:\s*$', line):
                    filtered_lines.append(line)
            cleaned = ' '.join(filtered_lines)
            
            # Try comma-separated
            if ',' in cleaned:
                parts = [p.strip() for p in cleaned.split(',')]
                # Accept all reasonable-length concepts (not just 3)
                concepts = [p for p in parts if 3 <= len(p) <= 150]
            else:
                # Single concept or line-based
                line = re.sub(r'[\'"\.,:;!?]+$', '', cleaned).strip()
                if 3 <= len(line) <= 150:
                    concepts.append(line)
        
        # Deduplicate while preserving order
        seen = set()
        unique_concepts = []
        for c in concepts:
            c_lower = c.lower().strip()
            if c_lower and c_lower not in seen:
                seen.add(c_lower)
                unique_concepts.append(c)
        concepts = unique_concepts
        # Do NOT limit to 1-3 concepts in open extraction mode
        
        # VALIDATION: Filter out concepts not appearing in clinical text
        # Use ONLY word-boundary matching - no manual lists
        if clinical_text:
            clinical_text_lower = clinical_text.lower()
            validated_concepts = []
            
            for concept in concepts:
                concept_lower = concept.lower().strip()
                
                # Dynamic word-boundary matching - concept must appear as complete word(s) in text
                pattern = r'\b' + re.escape(concept_lower) + r'\b'
                if re.search(pattern, clinical_text_lower):
                    validated_concepts.append(concept)
                    logger.debug(f"✓ Concept '{concept}' found in text")
                else:
                    logger.warning(f"✗ Concept '{concept}' NOT found in text - removing")
            
            concepts = validated_concepts
        
        logger.info(f"Parsed {len(concepts)} concepts from response")
        
        return concepts
    
    def _compute_confidence(self, concepts: List[str], candidates: Optional[List[str]] = None,
                           clinical_text: str = "") -> float:
        """
        Compute confidence score following copilot-instructions OUTPUT PATTERN.
        
        Factors:
        - Candidate match (40%): all extracted concepts are from CSV candidates
        - Text presence (40%): all concepts appear in original text
        - Count (20%): 1-3 concepts is ideal (not too few, not too many)
        
        Args:
            concepts: Extracted concepts
            candidates: Original candidate list
            clinical_text: Original clinical text
        
        Returns:
            Confidence 0-1
        """
        if not concepts:
            return 0.0
        
        confidence = 0.0
        
        # Factor 1: Candidate match (40% weight)
        if candidates:
            if all(c in candidates for c in concepts):
                candidate_score = 1.0  # All extracted are candidates
            elif any(c in candidates for c in concepts):
                candidate_score = 0.6  # Some are candidates
            else:
                candidate_score = 0.0  # None are candidates
            confidence += candidate_score * 0.4
            logger.debug(f"Candidate match score: {candidate_score:.2f}")
        else:
            confidence += 0.2  # Partial if no candidates provided
        
        # Factor 2: Text presence (40% weight)
        text_lower = clinical_text.lower()
        text_matches = sum(1 for c in concepts if c.lower() in text_lower)
        text_score = text_matches / len(concepts) if concepts else 0.0
        confidence += text_score * 0.4
        logger.debug(f"Text presence score: {text_score:.2f}")
        
        # Factor 3: Ideal count is 1-3 (20% weight)
        count = len(concepts)
        if 1 <= count <= 3:
            count_score = 1.0  # Perfect count
        elif count == 4:
            count_score = 0.7  # Slightly over
        else:
            count_score = 0.3  # Too many
        confidence += count_score * 0.2
        logger.debug(f"Count score (1-3 ideal): {count_score:.2f}")
        
        return round(confidence, 3)
    
    def cleanup(self):
        """
        Cleanup following copilot-instructions CUDA DEVICE MANAGEMENT pattern.
        
        Between batches: clear cache and optionally sleep.
        """
        logger.info("Cleaning up ConceptExtractorTool resources")
        
        if self.pipe is not None:
            del self.pipe.model
            del self.pipe.tokenizer
        
        if self.model is not None:
            del self.model
        
        if self.tokenizer is not None:
            del self.tokenizer
        
        # CUDA management from copilot-instructions: clear cache between batches
        torch.cuda.empty_cache()
        
        logger.info("ConceptExtractorTool cleanup complete")