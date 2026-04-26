"""
Phenotyping Tool - Hierarchical concept clustering and expansion
Follows project pattern from phenotyping/ directory
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class PhenotypingTool:
    """
    Expands concepts using hierarchical clustering relationships.
    Simulates project's phenotyping pipeline (see phenotyping/phenotyping_clustering.py).
    """
    
    def __init__(self):
        """Initialize phenotyping tool"""
        self.hierarchy = self._load_hierarchy()
    
    def _load_hierarchy(self) -> Dict:
        """
        Load concept hierarchy (simulated).
        In production: load from phenotyping pipeline outputs.
        """
        return {
            # Respiratory concepts
            'Shortness of Breath': ['Dyspnea', 'Respiratory Distress', 'Breathing Difficulty'],
            'Asthma': ['Bronchial Asthma', 'Asthmatic Bronchitis'],
            'COPD': ['Chronic Obstructive Pulmonary Disease', 'Emphysema', 'Chronic Bronchitis'],
            
            # Cardiovascular concepts
            'Chest Pain': ['Angina', 'Chest Discomfort', 'Thoracic Pain'],
            'Tachycardia': ['Rapid Heart Rate', 'Increased Heart Rate'],
            'Hypertension': ['High Blood Pressure', 'Elevated Blood Pressure'],
            
            # Gastrointestinal concepts
            'Abdominal Pain': ['Stomach Pain', 'Gastric Pain'],
            'Nausea': ['Feeling Sick', 'Queasiness'],
            
            # Neurological concepts
            'Headache': ['Cephalalgia', 'Head Pain'],
            'Dizziness': ['Vertigo', 'Lightheadedness']
        }
    
    def expand_concepts(self, concepts: List[str]) -> Dict:
        """
        Expand concepts using hierarchical relationships.
        
        Returns:
            {
                'expanded_concepts': List[str],
                'related_mappings': Dict[str, List[str]],
                'confidence_adjustment': float
            }
        """
        expanded = set(concepts)
        mappings = {}
        
        for concept in concepts:
            related = self._find_related(concept)
            if related:
                expanded.update(related)
                mappings[concept] = related
        
        # Confidence decreases slightly with expansion (less specific)
        confidence_adjustment = -0.05 * (len(expanded) - len(concepts)) / len(concepts) if concepts else 0.0
        
        return {
            'expanded_concepts': list(expanded),
            'related_mappings': mappings,
            'confidence_adjustment': max(confidence_adjustment, -0.15)
        }
    
    def _find_related(self, concept: str) -> List[str]:
        """Find related concepts in hierarchy"""
        if concept in self.hierarchy:
            return self.hierarchy[concept]
        
        # Fuzzy matching
        for key, related in self.hierarchy.items():
            if concept.lower() in key.lower() or key.lower() in concept.lower():
                return related
        
        return []
    
    def cluster_concepts(self, concepts: List[str]) -> Dict[str, List[str]]:
        """
        Group concepts into semantic clusters.
        Simulates phenotyping pipeline's clustering logic.
        """
        clusters = {
            'Respiratory': [],
            'Cardiovascular': [],
            'Gastrointestinal': [],
            'Neurological': [],
            'Other': []
        }
        
        respiratory_keywords = ['breath', 'respiratory', 'lung', 'asthma', 'copd', 'cough']
        cardiovascular_keywords = ['heart', 'cardiac', 'blood pressure', 'chest pain', 'tachycardia']
        gi_keywords = ['abdominal', 'stomach', 'nausea', 'gastric']
        neuro_keywords = ['headache', 'dizziness', 'neurological']
        
        for concept in concepts:
            concept_lower = concept.lower()
            if any(kw in concept_lower for kw in respiratory_keywords):
                clusters['Respiratory'].append(concept)
            elif any(kw in concept_lower for kw in cardiovascular_keywords):
                clusters['Cardiovascular'].append(concept)
            elif any(kw in concept_lower for kw in gi_keywords):
                clusters['Gastrointestinal'].append(concept)
            elif any(kw in concept_lower for kw in neuro_keywords):
                clusters['Neurological'].append(concept)
            else:
                clusters['Other'].append(concept)
        
        return {k: v for k, v in clusters.items() if v}