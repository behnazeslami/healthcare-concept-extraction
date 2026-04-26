"""
Configuration and Tool Registry for Healthcare Agentic AI
Follows project conventions for model paths, CUDA devices, and inference parameters
"""

import os
from typing import Dict, Any

class AgentConfig:
    """Configuration for agentic AI system following project patterns"""
    
    # UMLS API key (embed here for direct access)
    UMLS_API_KEY = "5cfb8fad-810d-4f90-8ba0-b1f38ce3d41c"
    
    @classmethod
    def get_umls_api_key(cls) -> str:
        """Get UMLS API key from config"""
        return cls.UMLS_API_KEY
    
    # Model paths (following project structure)
    LLAMA_8B_PATH = "/home1/shared/Models/Llama-3.1-8B-Instruct"
    MISTRAL_7B_PATH = "/home1/shared/Models/Mistral-7B-Instruct-v0.3"
    
    # Device management (following project CUDA patterns)
    # 7B models: GPU 0, 13B models: GPU 1, 70B models: GPUs 2,3
    CUDA_DEVICE_7B = "0"
    CUDA_DEVICE_13B = "1"
    CUDA_DEVICE_70B = "2,3"
    
    # Inference parameters (following project defaults)
    TEMPERATURE_DETERMINISTIC = 0.001  # For maximum determinism
    TEMPERATURE_BALANCED = 0.1         # Standard balanced
    TEMPERATURE_CREATIVE = 0.3         # For varied responses
    TOP_K = 10
    TOP_P = 0.95
    MAX_NEW_TOKENS = 1024
    REPETITION_PENALTY = 1.2
    
    # Agentic behavior parameters
    CONFIDENCE_THRESHOLD_LOW = 0.4
    CONFIDENCE_THRESHOLD_MEDIUM = 0.7
    CONFIDENCE_THRESHOLD_HIGH = 0.9
    
    MAX_REASONING_STEPS = 5  # Maximum ReACT iterations
    ENABLE_SELF_CORRECTION = True
    ENABLE_LEARNING = True
    ENABLE_TOOL_USE = True
    
    # Tool priorities (agent decides based on confidence)
    TOOL_PRIORITY = {
        "concept_extractor": 1,  # Always run first
        "umls_validator": 2,     # Run if confidence < 0.7
        "phenotyping": 3,        # Run if sparse concepts
        "self_correction": 4,    # Run if contradictions detected
        "memory": 5              # Run if similar cases exist
    }
    
    # Batch processing (following project pattern from phenotyping/)
    BATCH_SIZE = 50
    SLEEP_BETWEEN_BATCHES = 1  # seconds
    
    # UMLS API (following project integration from 02_CUI + Concepts/)
    UMLS_API_BASE = "https://uts-ws.nlm.nih.gov/rest"
    UMLS_VERSION = "current"
    
    @classmethod
    def get_model_path(cls, model_size: str = "8B") -> str:
        """Get model path based on size"""
        if model_size == "8B":
            return cls.LLAMA_8B_PATH
        elif model_size == "7B":
            return cls.MISTRAL_7B_PATH
        else:
            raise ValueError(f"Unsupported model size: {model_size}")
    
    @classmethod
    def get_cuda_device(cls, model_size: str = "8B") -> str:
        """Get CUDA device following project conventions"""
        if model_size in ["7B", "8B"]:
            return cls.CUDA_DEVICE_7B
        elif model_size == "13B":
            return cls.CUDA_DEVICE_13B
        elif model_size == "70B":
            return cls.CUDA_DEVICE_70B
        else:
            return cls.CUDA_DEVICE_7B