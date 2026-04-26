"""
Pydantic models for agentic AI requests and responses
Defines data structures for agent reasoning, tool use, and feedback
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentGoal(str, Enum):
    """Agent optimization goals - determines reasoning strategy"""
    MAXIMIZE_ACCURACY = "maximize_accuracy"
    MAXIMIZE_SPEED = "maximize_speed"
    MAXIMIZE_COVERAGE = "maximize_coverage"
    BALANCED = "balanced"

class ToolName(str, Enum):
    """Available agent tools"""
    CONCEPT_EXTRACTOR = "concept_extractor"
    UMLS_VALIDATOR = "umls_validator"
    PHENOTYPING = "phenotyping"
    SELF_CORRECTION = "self_correction"
    MEMORY = "memory"

class ReasoningStep(BaseModel):
    """Single step in agent's reasoning chain (ReACT pattern)"""
    step_number: int
    thought: str  # Agent's reasoning: "Why am I doing this?"
    action: str  # Tool/action taken: "RUN umls_validator"
    observation: str  # Result of action: "Validated 5/5 concepts"
    confidence: float  # Confidence after this step

class UMLSEnrichmentData(BaseModel):
    """UMLS enrichment data for a single concept"""
    concept: str
    cui: Optional[str] = None
    preferred_name: str
    semantic_types: List[str] = []
    snomed_ct_codes: List[str] = []
    synonyms: List[str] = []
    found: bool = False
    confidence: float = 0.0
    error: Optional[str] = None

class AgenticRequest(BaseModel):
    """Request for agentic concept extraction"""
    clinical_text: str = Field(..., description="Clinical text chunk to process")
    main_note: Optional[str] = Field(None, description="Main note context for reference")
    candidate_concepts: Optional[List[str]] = Field(None, description="Suggested concepts to guide extraction")
    record_id: Optional[str] = Field(None, description="Record identifier for tracking")
    goal: AgentGoal = Field(AgentGoal.BALANCED, description="Agent optimization goal")
    enable_tools: List[ToolName] = Field(
        default=[ToolName.CONCEPT_EXTRACTOR, ToolName.UMLS_VALIDATOR],
        description="Tools agent can use"
    )
    max_reasoning_steps: int = Field(5, description="Maximum ReACT iterations")

class AgenticResponse(BaseModel):
    """Response from agentic concept extraction with full transparency"""
    status: str
    record_id: Optional[str]
    
    # Final results
    extracted_concepts: List[str]
    confidence: float
    
    # Agentic reasoning transparency (key differentiator from traditional pipelines)
    reasoning_chain: List[ReasoningStep]  # Full thought process
    tools_used: List[str]  # Tools agent decided to use
    self_corrected: bool  # Did agent correct itself?
    learned_from_memory: bool  # Did agent use past examples?
    
    # Metadata
    total_reasoning_steps: int
    script_runtime: float  # Follows project output column naming
    model_used: str
    goal: str
    
    # UMLS Enrichment (from UMLSEnricher tool)
    umls_enrichment: Optional[Dict[str, Any]] = None  # Contains CUI, preferred_name, snomed_ct, etc.
    
    # Optional enrichment (from tools)
    umls_codes: Optional[Dict[str, str]] = None
    phenotyping_hierarchy: Optional[Dict[str, Any]] = None
    
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    """Feedback for agent learning (enables improvement over time)"""
    record_id: str
    clinical_text: str
    predicted_concepts: List[str]
    correct_concepts: List[str]
    user_notes: Optional[str] = None

class AgentState(BaseModel):
    """Internal agent state during reasoning (not exposed externally)"""
    current_step: int = 0
    concepts: List[str] = []
    confidence: float = 0.0
    reasoning_log: List[ReasoningStep] = []
    tools_used: List[str] = []
    needs_validation: bool = False
    needs_expansion: bool = False
    needs_correction: bool = False
    goal: AgentGoal = AgentGoal.BALANCED
    cui_mappings: Dict[str, Dict] = {}  # Stores CUI enrichment data