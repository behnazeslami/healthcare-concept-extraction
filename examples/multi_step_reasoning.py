"""
Agent learning from feedback example
"""

import requests

BASE_URL = "http://127.0.0.1:8002"

def example_with_feedback():
    print("=" * 80)
    print("Example: Agent Learning from Feedback")
    print("=" * 80)
    
    # First request
    request_data = {
        "clinical_text": "Patient complains of epigastric discomfort after meals.",
        "record_id": "TEST_001"
    }
    
    response = requests.post(f"{BASE_URL}/reason", json=request_data)
    result = response.json()
    
    print(f"\nAgent predicted: {result['extracted_concepts']}")
    
    # Provide feedback
    feedback = {
        "record_id": "TEST_001",
        "clinical_text": request_data["clinical_text"],
        "predicted_concepts": result["extracted_concepts"],
        "correct_concepts": ["Epigastric Pain", "Dyspepsia", "Postprandial Discomfort"],
        "user_notes": "More specific GI terms needed"
    }
    
    response = requests.post(f"{BASE_URL}/feedback", json=feedback)
    print(f"\nFeedback response: {response.json()}")

if __name__ == "__main__":
    example_with_feedback()