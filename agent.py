"""
Core Agentic AI Engine - ReACT (Reasoning + Acting) Pattern
Implements autonomous decision-making, tool use, and self-correction
"""

import logging
import time
from typing import Dict, Optional

from models import (
    AgenticRequest, AgenticResponse, AgentState, ReasoningStep,
    AgentGoal, ToolName, UMLSEnrichmentData
)
from tools import (
    ConceptExtractorTool, UMLSValidatorTool, PhenotypingTool,
    MemoryTool, SelfCorrectionTool
)
from config import AgentConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthcareAgenticAI:
    """
    True Agentic AI for clinical concept extraction.
    
    Implements:
    - Autonomous decision-making (tool selection based on confidence/goal)
    - Multi-step reasoning (ReACT pattern)
    - Self-correction (error detection and fixing)
    - Learning from feedback (few-shot memory)
    - Goal-directed behavior (accuracy/speed/coverage optimization)
    """

    def __init__(self, model_size: str = "8B", umls_api_key: Optional[str] = None):
        """
        Initialize agentic AI system following project patterns.
        
        Args:
            model_size: Model size (8B, 7B, etc.)
            umls_api_key: UMLS API key for validation (optional)
        """
        self.config = AgentConfig()
        self.model_size = model_size

        logger.info("Initializing agent tools...")
        model_path = self.config.get_model_path(model_size)

        # Initialize tools following project patterns
        self.tools = {
            'concept_extractor': ConceptExtractorTool(model_path, device="auto"),
            'umls_validator': UMLSValidatorTool(umls_api_key),
            'phenotyping': PhenotypingTool(),
            'memory': MemoryTool(),
            'self_correction': SelfCorrectionTool()
        }

        logger.info(f"Agentic AI initialized successfully with {model_size} model")

    async def reason(self, request: AgenticRequest) -> AgenticResponse:
        """
        Main agentic reasoning loop - ReACT pattern.
        
        The agent autonomously decides:
        1. What tools to use
        2. When to stop reasoning
        3. Whether to self-correct
        4. How to optimize for the goal
        """
        start_time = time.time()

        # Initialize agent state
        state = AgentState(
            current_step=0,
            concepts=[],
            confidence=0.0,
            reasoning_log=[],
            tools_used=[],
            goal=request.goal,
            cui_mappings={}
        )

        logger.info(
            f"Starting agentic reasoning for record {request.record_id}. "
            f"Goal: {request.goal}, Max steps: {request.max_reasoning_steps}"
        )

        # Step 1: Always extract initial concepts (mandatory first action)
        state = await self._step_extract_concepts(state, request)

        # Reasoning loop: agent decides next action based on state
        # Note: state.current_step is already 1 after extraction
        while state.current_step < request.max_reasoning_steps:
            next_action = self._decide_next_action(state, request)

            if next_action == "STOP":
                state.current_step += 1
                state.reasoning_log.append(ReasoningStep(
                    step_number=state.current_step,
                    thought="✓ Agent conclusion: All critical steps complete. Analysis finished.",
                    action="STOP",
                    observation=f"Final extraction: {len(state.concepts)} concepts validated with high confidence ({state.confidence:.2%})",
                    confidence=state.confidence
                ))
                break

            # Execute decided action
            state.current_step += 1
            if next_action == "validate_umls" and ToolName.UMLS_VALIDATOR in request.enable_tools:
                state = await self._step_validate_umls(state, request)

            elif next_action == "analyze_concepts" and ToolName.UMLS_VALIDATOR in request.enable_tools:
                state = await self._step_analyze_concepts(state, request)

            elif next_action == "expand_phenotyping" and ToolName.PHENOTYPING in request.enable_tools:
                state = await self._step_expand_phenotyping(state, request)

            elif next_action == "self_correct" and ToolName.SELF_CORRECTION in request.enable_tools:
                state = await self._step_self_correct(state, request)

            elif next_action == "learn_from_memory" and ToolName.MEMORY in request.enable_tools:
                state = await self._step_learn_from_memory(state, request)
            else:
                # No valid action, stop reasoning
                break

        runtime = time.time() - start_time

        # Build final response (follows project output column naming)
        umls_enrichment = None
        if state.cui_mappings:
            umls_enrichment = state.cui_mappings
            logger.info(f"Including {len(umls_enrichment)} CUI mappings in response")
        
        logger.info(f"State CUI mappings: {len(state.cui_mappings)}")
        
        response = AgenticResponse(
            status="success",
            record_id=request.record_id,
            extracted_concepts=state.concepts,
            confidence=state.confidence,
            reasoning_chain=state.reasoning_log,
            tools_used=state.tools_used,
            self_corrected="self_correction" in state.tools_used,
            learned_from_memory="memory" in state.tools_used,
            total_reasoning_steps=state.current_step,
            script_runtime=runtime,  # Follows project convention: Script_Runtime column
            model_used=self.config.get_model_path(self.model_size),
            goal=request.goal.value,
            umls_enrichment=umls_enrichment
        )

        logger.info(
            f"Agentic reasoning complete. Record: {request.record_id}, "
            f"Steps: {state.current_step}, Concepts: {len(state.concepts)}, "
            f"Confidence: {state.confidence:.3f}, Runtime: {runtime:.2f}s"
        )

        return response

    def _decide_next_action(self, state: AgentState, request: AgenticRequest) -> str:
        """
        Agent's autonomous decision-making logic with enhanced multi-step reasoning.
        
        Returns action name: "validate_umls", "analyze_concepts", "self_correct",
                            "learn_from_memory", "expand_phenotyping", or "STOP"
        """
        # Step 2: Always validate UMLS first (most critical for accuracy)
        if "umls_validator" not in state.tools_used:
            return "validate_umls"

        # Step 3: Analyze and categorize concepts by type
        if "analyze_concepts" not in state.tools_used:
            return "analyze_concepts"

        # Step 4: Self-check for contradictions and errors
        if "self_correct" not in state.tools_used:
            return "self_correct"

        # Step 5: Goal: MAXIMIZE_ACCURACY - aggressive expansion
        if request.goal == AgentGoal.MAXIMIZE_ACCURACY:
            if state.confidence < self.config.CONFIDENCE_THRESHOLD_HIGH:
                if "expand_phenotyping" not in state.tools_used:
                    return "expand_phenotyping"
                if "learn_from_memory" not in state.tools_used:
                    return "learn_from_memory"
            return "STOP"

        # Goal: MAXIMIZE_COVERAGE - prioritize expansion
        if request.goal == AgentGoal.MAXIMIZE_COVERAGE:
            if "expand_phenotyping" not in state.tools_used:
                return "expand_phenotyping"
            if "learn_from_memory" not in state.tools_used:
                return "learn_from_memory"
            return "STOP"

        # Goal: MAXIMIZE_SPEED - stop after basics
        if request.goal == AgentGoal.MAXIMIZE_SPEED:
            return "STOP"

        # Goal: BALANCED (default) - selective expansion
        if len(state.concepts) < 10:
            if "expand_phenotyping" not in state.tools_used:
                return "expand_phenotyping"
        
        if state.confidence < 0.8:
            if "learn_from_memory" not in state.tools_used:
                return "learn_from_memory"

        return "STOP"

    async def _step_extract_concepts(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 1: Extract initial concepts using LLM (follows project pattern)"""
        logger.info("Agent action: Extracting initial concepts...")

        # Use deterministic temperature for accuracy, creative for coverage
        temperature = 0.1 if request.goal == AgentGoal.MAXIMIZE_ACCURACY else 0.3

        result = self.tools['concept_extractor'].extract(
            request.clinical_text,
            request.main_note,
            request.candidate_concepts,
            temperature=temperature
        )

        state.concepts = result['concepts']
        state.confidence = result['confidence']
        state.tools_used.append('concept_extractor')
        state.current_step = 1  # Set to 1 after extraction

        state.reasoning_log.append(ReasoningStep(
            step_number=1,
            thought="🔍 Agent starting: Extracting medical concepts from clinical note using LLM.",
            action="RUN concept_extractor",
            observation=(
                f"✓ Extracted {len(state.concepts)} concepts: "
                f"{', '.join(state.concepts[:3])}{'...' if len(state.concepts) > 3 else ''}"
            ),
            confidence=state.confidence
        ))

        return state

    async def _step_validate_umls(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 2: Validate concepts with UMLS (follows project 02_CUI pattern)"""
        logger.info("Agent decision: Validating extracted concepts with UMLS database...")

        result = self.tools['umls_validator'].validate(state.concepts)

        # Store CUI mappings for response
        state.cui_mappings = result['cui_mappings']
        
        # Only accept concepts that mapped to UMLS (have valid CUI)
        state.concepts = list(result['cui_mappings'].keys())
        state.confidence += result['confidence_boost']
        state.tools_used.append('umls_validator')

        validated_count = len(state.concepts)
        total_extracted = len(result['validated_concepts']) if 'validated_concepts' in result else len(state.concepts)

        state.reasoning_log.append(ReasoningStep(
            step_number=state.current_step,
            thought=f"🔍 Agent validating: Cross-referencing {len(result.get('validated_concepts', state.concepts))} concepts against UMLS medical terminology database.",
            action="RUN umls_validator",
            observation=(
                f"✓ Matched {validated_count} to UMLS. CUI codes retrieved. "
                f"Confidence +{result['confidence_boost']:.2%} → {state.confidence:.2%}"
            ),
            confidence=state.confidence
        ))

        return state

    async def _step_analyze_concepts(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 3: Analyze and categorize extracted concepts by medical type"""
        logger.info("Agent decision: Analyzing concept categories and relationships...")

        # Categorize concepts by type
        categories = {
            'diagnoses': [],
            'symptoms': [],
            'medications': [],
            'procedures': [],
            'findings': [],
            'other': []
        }

        # Simple categorization based on concept characteristics
        for concept in state.concepts:
            concept_lower = concept.lower()
            if any(x in concept_lower for x in ['disease', 'disorder', 'syndrome', 'diabetes', 'asthma', 'hypertension']):
                categories['diagnoses'].append(concept)
            elif any(x in concept_lower for x in ['pain', 'fever', 'cough', 'wheezing', 'ache', 'feeling']):
                categories['symptoms'].append(concept)
            elif any(x in concept_lower for x in ['inhaler', 'corticosteroid', 'medication', 'drug', 'beta-agonist']):
                categories['medications'].append(concept)
            elif any(x in concept_lower for x in ['ventilation', 'examination', 'scan', 'imaging', 'test']):
                categories['procedures'].append(concept)
            elif any(x in concept_lower for x in ['saturation', 'pressure', 'rate', 'value', 'result']):
                categories['findings'].append(concept)
            else:
                categories['other'].append(concept)

        # Count non-empty categories
        active_categories = sum(1 for v in categories.values() if v)
        
        state.tools_used.append('analyze_concepts')

        observation_text = "Concept categories: "
        category_list = []
        for cat_name, concepts in categories.items():
            if concepts:
                category_list.append(f"{len(concepts)} {cat_name}")
        observation_text += ", ".join(category_list) if category_list else "All concepts mixed"

        state.reasoning_log.append(ReasoningStep(
            step_number=state.current_step,
            thought=f"📊 Agent analyzing: Categorizing {len(state.concepts)} concepts by clinical type for better understanding.",
            action="ANALYZE concepts",
            observation=observation_text,
            confidence=state.confidence
        ))

        return state

    async def _step_expand_phenotyping(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 4/5: Expand concepts using phenotyping hierarchy (follows project phenotyping/ pattern)"""
        logger.info("Agent decision: Expanding concepts with hierarchical phenotyping...")

        result = self.tools['phenotyping'].expand_concepts(state.concepts)

        original_count = len(state.concepts)
        state.concepts = result['expanded_concepts']
        state.confidence += result['confidence_adjustment']
        state.tools_used.append('phenotyping')

        added_count = len(state.concepts) - original_count

        state.reasoning_log.append(ReasoningStep(
            step_number=state.current_step,
            thought=f"🧬 Agent expanding: Using hierarchical phenotyping to discover related clinical concepts.",
            action="RUN phenotyping",
            observation=(
                f"✓ Added {added_count} related concepts. "
                f"Total now: {len(state.concepts)} | {len(result.get('related_mappings', []))} mappings found"
            ),
            confidence=state.confidence
        ))

        return state

    async def _step_self_correct(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 3/4: Detect and correct agent's own errors"""
        logger.info("Agent decision: Self-checking for contradictions and errors...")

        errors = self.tools['self_correction'].detect_errors(
            state.concepts,
            request.clinical_text,
            request.main_note
        )

        if errors['has_errors']:
            correction = self.tools['self_correction'].correct_errors(
                state.concepts,
                errors,
                request.clinical_text
            )

            corrected_count = len([c for c in state.concepts if c not in correction['corrected_concepts']])
            state.concepts = correction['corrected_concepts']
            state.confidence += correction['confidence_recovery']
            state.tools_used.append('self_correction')

            state.reasoning_log.append(ReasoningStep(
                step_number=state.current_step,
                thought=f"⚠️ Agent self-correcting: Detected {len(errors.get('error_types', []))} potential issues. Applying corrections...",
                action="RUN self_correction",
                observation=(
                    f"✓ Corrected {corrected_count} error(s): {', '.join(errors.get('error_types', [])[:2])}. "
                    f"Confidence recovery: +{correction.get('confidence_recovery', 0):.2%}"
                ),
                confidence=state.confidence
            ))
        else:
            state.reasoning_log.append(ReasoningStep(
                step_number=state.current_step,
                thought="✓ Agent self-checking: Validated for contradictions and inconsistencies.",
                action="CHECK self_correction",
                observation="No errors detected. All concepts logically consistent.",
                confidence=state.confidence
            ))
            state.tools_used.append('self_correction')

        return state

    async def _step_learn_from_memory(self, state: AgentState, request: AgenticRequest) -> AgentState:
        """Step 5/6: Learn from similar past examples (few-shot learning)"""
        logger.info("Agent decision: Querying memory for similar clinical cases...")

        similar = self.tools['memory'].retrieve_similar(request.clinical_text, top_k=3)

        if similar:
            learned_concepts = set()
            for example in similar:
                learned_concepts.update(
                    example.get('concepts', []) or example.get('correct_concepts', [])
                )

            original_count = len(state.concepts)
            new_from_memory = [c for c in learned_concepts if c not in state.concepts]
            state.concepts.extend(new_from_memory)

            if len(state.concepts) > original_count:
                state.confidence += 0.05
                state.tools_used.append('memory')

                state.reasoning_log.append(ReasoningStep(
                    step_number=state.current_step,
                    thought=f"🧠 Agent learning: Found {len(similar)} similar cases. Extracting insights from memory.",
                    action="RUN memory",
                    observation=(
                        f"✓ Added {len(new_from_memory)} new concept(s) from past examples. "
                        f"Total concepts: {len(state.concepts)} | Confidence +5%"
                    ),
                    confidence=state.confidence
                ))
            else:
                state.reasoning_log.append(ReasoningStep(
                    step_number=state.current_step,
                    thought="Agent checked memory but found no new concepts to add.",
                    action="SKIP memory",
                    observation=f"Found {len(similar)} similar cases but all concepts already extracted.",
                    confidence=state.confidence
                ))
                state.tools_used.append('memory')
        else:
            state.reasoning_log.append(ReasoningStep(
                step_number=state.current_step,
                thought="Agent checked memory but no similar clinical cases found.",
                action="SKIP memory",
                observation="No similar past examples in memory database. Proceeding with extracted concepts.",
                confidence=state.confidence
            ))
            state.tools_used.append('memory')

        return state

    async def provide_feedback(self, feedback: Dict):
        """
        Learn from user feedback - stores correction in memory for future few-shot learning.
        
        Args:
            feedback: Dict with clinical_text, predicted_concepts, correct_concepts, user_notes
        """
        self.tools['memory'].store_feedback(
            feedback['clinical_text'],
            feedback['predicted_concepts'],
            feedback['correct_concepts'],
            feedback.get('user_notes')
        )
        logger.info(f"Agent learned from feedback for record: {feedback.get('record_id', 'N/A')}")

    def cleanup(self):
        """Cleanup resources following project CUDA management pattern"""
        logger.info("Cleaning up agent resources...")
        self.tools['concept_extractor'].cleanup()
        
        # Clear GPU cache (project pattern: call between batches)
        import torch
        torch.cuda.empty_cache()
        
        logger.info("Agent cleanup complete")