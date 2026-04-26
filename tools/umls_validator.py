"""
UMLS Validator Tool - Validates concepts against UMLS terminology
Follows project integration pattern from 02_CUI + Concepts/ notebooks
"""

import requests
import logging
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

class UMLSValidatorTool:
    """
    Validates and enriches concepts using UMLS terminology.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize UMLS validator.
        
        Args:
            api_key: UMLS API key (https://uts.nlm.nih.gov/uts/)
        """
        self.api_key = api_key
        self.base_url = "https://uts-ws.nlm.nih.gov/rest"
        self.version = "current"
    
    def validate(self, concepts: List[str]) -> Dict:
        """
        Validate concepts against UMLS and return enriched results with CUI and SNOMED CT codes.
        
        Returns:
            {
                'validated_concepts': List[str],
                'cui_mappings': Dict[str, Dict] with keys: cui, snomed_ct (list), preferred_name, found,
                'confidence_boost': float,
                'validation_rate': float
            }
        """
        if not self.api_key:
            logger.warning("UMLS API key not provided. Skipping validation.")
            return {
                'validated_concepts': concepts,
                'cui_mappings': {},
                'confidence_boost': 0.0,
                'validation_rate': 0.0
            }
        
        validated = []
        cui_mappings = {}
        
        for concept in concepts:
            cui_data = self._search_umls_with_codes(concept)
            if cui_data and cui_data.get('found'):
                validated.append(concept)
                cui_mappings[concept] = cui_data
            time.sleep(0.05)  # Rate limiting
        
        validation_rate = len(validated) / len(concepts) if concepts else 0.0
        confidence_boost = validation_rate * 0.2  # Up to +0.2
        
        logger.info(f"UMLS validation: {len(validated)}/{len(concepts)} concepts validated")
        
        return {
            'validated_concepts': validated if validated else concepts,
            'cui_mappings': cui_mappings,
            'confidence_boost': confidence_boost,
            'validation_rate': validation_rate
        }
    
    def _search_umls_with_codes(self, concept: str) -> Optional[Dict]:
        """
        Search UMLS for concept and return CUI, SNOMED CT codes, and preferred name.
        Follows project API integration pattern (02_CUI + Concepts/).
        
        Returns:
            {
                'cui': str,
                'snomed_ct': List[str],
                'preferred_name': str,
                'found': bool
            }
        """
        try:
            url = f"{self.base_url}/search/{self.version}"
            params = {
                'string': concept,
                'apiKey': self.api_key,
                'returnIdType': 'concept'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('result', {}).get('results', [])
                if results:
                    cui = results[0].get('ui')
                    preferred_name = results[0].get('name', concept)
                    
                    # Get SNOMED CT codes for this CUI
                    snomed_codes = self._get_snomed_ct_codes(cui)
                    
                    return {
                        'cui': cui,
                        'snomed_ct': snomed_codes,
                        'preferred_name': preferred_name,
                        'found': True
                    }
            
            return {
                'cui': None,
                'snomed_ct': [],
                'preferred_name': concept,
                'found': False
            }
        
        except Exception as e:
            logger.error(f"UMLS search error for '{concept}': {e}")
            return {
                'cui': None,
                'snomed_ct': [],
                'preferred_name': concept,
                'found': False
            }
    
    def _get_snomed_ct_codes(self, cui: str) -> List[str]:
        """
        Get SNOMED CT codes for a given CUI.
        Follows project 03_CUI + SCTID + Concept/ pattern.
        
        Returns:
            List of SNOMED CT concept IDs
        """
        try:
            url = f"{self.base_url}/content/{self.version}/CUI/{cui}/atoms"
            params = {
                'apiKey': self.api_key,
                'sabs': 'SNOMEDCT_US'  # Filter for SNOMED CT US edition
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                atoms = data.get('result', [])
                
                # Extract SNOMED CT codes from atoms
                snomed_codes = []
                seen = set()
                for atom in atoms:
                    code = atom.get('code')
                    if code and code not in seen:
                        snomed_codes.append(code)
                        seen.add(code)
                
                return snomed_codes[:5]  # Return up to 5 codes
            
            return []
        
        except Exception as e:
            logger.error(f"Error fetching SNOMED CT codes for CUI {cui}: {e}")
            return []
    
    def _search_umls(self, concept: str) -> Optional[str]:
        """
        Search UMLS for concept and return CUI if found.
        Follows project API integration pattern.
        """
        try:
            url = f"{self.base_url}/search/{self.version}"
            params = {
                'string': concept,
                'apiKey': self.api_key,
                'returnIdType': 'concept'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get('result', {}).get('results', [])
                if results:
                    return results[0].get('ui')
            
            return None
        
        except Exception as e:
            logger.error(f"UMLS search error for '{concept}': {e}")
            return None
    
    def get_synonyms(self, cui: str) -> List[str]:
        """Get synonyms for a CUI (for concept expansion)"""
        try:
            url = f"{self.base_url}/content/{self.version}/CUI/{cui}/atoms"
            params = {'apiKey': self.api_key}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                atoms = data.get('result', [])
                return [atom.get('name') for atom in atoms[:5]]
            
            return []
        
        except Exception as e:
            logger.error(f"Error fetching synonyms for CUI {cui}: {e}")
            return []