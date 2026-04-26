"""
Self-Correction Tool - Detects and corrects agent's own errors
Enables agent to validate and refine its own outputs
"""

import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class SelfCorrectionTool:
    """
    Enables agent to detect and correct its own extraction errors.
    Checks for contradictions, hallucinations, and inconsistencies.
    """
    
    def __init__(self):
        """Initialize self-correction tool"""
        pass
    
    def detect_errors(self, concepts: List[str], clinical_text: str, 
                     main_note: Optional[str] = None) -> Dict:
        """
        Detect potential errors in extracted concepts.
        
        Returns:
            {
                'has_errors': bool,
                'error_types': List[str],
                'problematic_concepts': List[str],
                'confidence_penalty': float
            }
        """
        errors = {
            'has_errors': False,
            'error_types': [],
            'problematic_concepts': [],
            'confidence_penalty': 0.0
        }
        
        # Check 1: Hallucinations (concepts not in text)
        hallucinated = self._detect_hallucinations(concepts, clinical_text, main_note)
        if hallucinated:
            errors['has_errors'] = True
            errors['error_types'].append('hallucination')
            errors['problematic_concepts'].extend(hallucinated)
            errors['confidence_penalty'] += 0.2
        
        # Check 2: Contradictions within concepts
        contradictions = self._detect_contradictions(concepts)
        if contradictions:
            errors['has_errors'] = True
            errors['error_types'].append('contradiction')
            errors['problematic_concepts'].extend(contradictions)
            errors['confidence_penalty'] += 0.15
        
        # Check 3: Overly generic concepts
        generic = self._detect_generic_concepts(concepts)
        if generic:
            errors['has_errors'] = True
            errors['error_types'].append('generic')
            errors['problematic_concepts'].extend(generic)
            errors['confidence_penalty'] += 0.1
        
        return errors
    
    def correct_errors(self, concepts: List[str], errors: Dict, 
                      clinical_text: str) -> Dict:
        """
        Correct detected errors.
        
        Returns:
            {
                'corrected_concepts': List[str],
                'corrections_made': List[str],
                'confidence_recovery': float
            }
        """
        corrected = concepts.copy()
        corrections = []
        
        # Remove hallucinated concepts
        if 'hallucination' in errors['error_types']:
            for concept in errors['problematic_concepts']:
                if concept in corrected:
                    corrected.remove(concept)
                    corrections.append(f"Removed hallucinated concept: {concept}")
        
        # Remove contradictory concepts (keep first occurrence)
        if 'contradiction' in errors['error_types']:
            seen = set()
            filtered = []
            for concept in corrected:
                if concept not in errors['problematic_concepts'] or concept not in seen:
                    filtered.append(concept)
                    seen.add(concept)
                else:
                    corrections.append(f"Removed contradictory concept: {concept}")
            corrected = filtered
        
        # Remove overly generic concepts if specific ones exist
        if 'generic' in errors['error_types'] and len(corrected) > 2:
            for concept in errors['problematic_concepts']:
                if concept in corrected and len(corrected) > 2:
                    corrected.remove(concept)
                    corrections.append(f"Removed generic concept: {concept}")
        
        # Confidence recovery based on corrections
        confidence_recovery = min(0.15, len(corrections) * 0.05)
        
        return {
            'corrected_concepts': corrected,
            'corrections_made': corrections,
            'confidence_recovery': confidence_recovery
        }
    
    def _detect_hallucinations(self, concepts: List[str], clinical_text: str, 
                               main_note: Optional[str] = None) -> List[str]:
        """Detect concepts not present in text or context"""
        hallucinated = []
        combined_text = clinical_text.lower()
        if main_note:
            combined_text += " " + main_note.lower()
        
        for concept in concepts:
            concept_words = set(concept.lower().split())
            text_words = set(combined_text.split())
            if not (concept_words & text_words):
                hallucinated.append(concept)
        
        return hallucinated
    
    def _detect_contradictions(self, concepts: List[str]) -> List[str]:
        """Detect contradictory concepts"""
        contradictions = []
        
        opposites = [
            (['hypertension', 'high blood pressure'], ['hypotension', 'low blood pressure']),
            (['tachycardia', 'rapid heart'], ['bradycardia', 'slow heart']),
            (['hyperglycemia', 'high blood sugar'], ['hypoglycemia', 'low blood sugar'])
        ]
        
        concepts_lower = [c.lower() for c in concepts]
        
        for positive, negative in opposites:
            has_positive = any(any(p in c for p in positive) for c in concepts_lower)
            has_negative = any(any(n in c for n in negative) for c in concepts_lower)
            
            if has_positive and has_negative:
                for concept in concepts:
                    c_lower = concept.lower()
                    if any(n in c_lower for n in negative):
                        contradictions.append(concept)
        
        return contradictions
    
    def _detect_generic_concepts(self, concepts: List[str]) -> List[str]:
        """Detect overly generic concepts"""
        generic_terms = [
            'symptom', 'condition', 'disease', 'problem', 'issue', 'disorder',
            'patient', 'clinical', 'medical', 'health'
        ]
        
        generic = []
        for concept in concepts:
            if concept.lower() in generic_terms:
                generic.append(concept)
            elif len(concept) < 4:
                generic.append(concept)
        
        return generic