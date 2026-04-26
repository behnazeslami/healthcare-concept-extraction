"""
Basic usage examples for Healthcare Agentic AI
"""

import requests

BASE_URL = "http://127.0.0.1:8002"

def example_basic_reasoning():
    print("=" * 80)
    print("Example 1: Basic Agentic Reasoning")
    print("=" * 80)
    
    request_data = {
        "clinical_text": "Patient presents with shortness of breath, chest pain, and persistent cough. History of asthma and COPD.",
        "main_note": "58-year-old male with chronic respiratory conditions",
        "goal": "balanced",
        "enable_tools": ["concept_extractor", "umls_validator"],
        "max_reasoning_steps": 5
    }
    
    response = requests.post(f"{BASE_URL}/reason", json=request_data)
    result = response.json()
    
    print(f"\nStatus: {result['status']}")
    print(f"Extracted Concepts: {result['extracted_concepts']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Tools Used: {result['tools_used']}")
    print(f"Self-corrected: {result['self_corrected']}")
    print(f"Runtime: {result['script_runtime']:.2f}s")
    
    print("\n" + "="*80)
    print("Reasoning Chain:")
    print("="*80)
    for step in result['reasoning_chain']:
        print(f"\nStep {step['step_number']}:")
        print(f"  Thought: {step['thought']}")
        print(f"  Action: {step['action']}")
        print(f"  Observation: {step['observation']}")
        print(f"  Confidence: {step['confidence']:.3f}")

if __name__ == "__main__":
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"Server status: {health.json()}")
    except:
        print("ERROR: Server not running. Start with: python server.py")
        exit(1)
    
    example_basic_reasoning()