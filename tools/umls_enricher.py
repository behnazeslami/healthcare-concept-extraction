"""
UMLS Enricher Tool - Comprehensive concept enrichment from UMLS terminology
Fetches CUI, Preferred Name, Semantic Types, SNOMED CT codes, and more
Follows project integration pattern from 02_CUI + Concepts/ and 03_CUI + SCTID + Concept/ notebooks
"""

import requests
import logging
from typing import List, Dict, Optional, Tuple
import time
import json

logger = logging.getLogger(__name__)


class UMLSEnricher:
    """
    Comprehensive UMLS enrichment for clinical concepts.
    Fetches full metadata: CUI, Preferred Name, Semantic Types, SNOMED CT codes.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize UMLS enricher.

        Args:
            api_key: UMLS API key (https://uts.nlm.nih.gov/uts/)
        """
        self.api_key = api_key
        self.base_url = "https://uts-ws.nlm.nih.gov/rest"
        self.version = "current"
        self.rate_limit_delay = 0.1  # seconds between API calls

    def enrich_concepts(
        self,
        concepts: List[str],
        batch_size: int = 50,
        include_semantic_types: bool = True,
        include_snomed_ct: bool = True,
        include_synonyms: bool = False
    ) -> Dict[str, Dict]:
        """
        Enrich a list of concepts with full UMLS metadata.

        Args:
            concepts: List of concept strings
            batch_size: Number of concepts to process before logging
            include_semantic_types: Whether to fetch semantic types
            include_snomed_ct: Whether to fetch SNOMED CT codes
            include_synonyms: Whether to fetch alternative names

        Returns:
            Dictionary mapping concept -> enrichment data:
            {
                'concept': str,
                'cui': str or None,
                'preferred_name': str,
                'semantic_types': List[str],
                'snomed_ct_codes': List[str],
                'synonyms': List[str],
                'found': bool,
                'confidence': float  # Based on match quality
            }
        """
        if not self.api_key:
            logger.warning("UMLS API key not provided. Cannot enrich concepts.")
            return self._create_empty_enrichment(concepts)

        enriched_data = {}

        for idx, concept in enumerate(concepts):
            if idx % batch_size == 0:
                logger.info(f"Enriching concepts: {idx}/{len(concepts)}")

            enrichment = self._enrich_single_concept(
                concept,
                include_semantic_types=include_semantic_types,
                include_snomed_ct=include_snomed_ct,
                include_synonyms=include_synonyms
            )
            enriched_data[concept] = enrichment
            time.sleep(self.rate_limit_delay)

        logger.info(f"Enrichment complete. Success rate: {self._calculate_success_rate(enriched_data):.2%}")
        return enriched_data

    def _enrich_single_concept(
        self,
        concept: str,
        include_semantic_types: bool = True,
        include_snomed_ct: bool = True,
        include_synonyms: bool = False
    ) -> Dict:
        """
        Enrich a single concept with UMLS metadata.

        Returns enrichment dictionary with all available metadata.
        """
        try:
            # Step 1: Search for concept and get CUI
            search_result = self._search_concept(concept)

            if not search_result:
                return self._create_concept_enrichment(
                    concept, cui=None, found=False
                )

            cui = search_result['ui']
            preferred_name = search_result.get('name', concept)

            enrichment = self._create_concept_enrichment(
                concept,
                cui=cui,
                preferred_name=preferred_name,
                found=True,
                confidence=search_result.get('matchScore', 0.0)
            )

            # Step 2: Get semantic types
            if include_semantic_types:
                semantic_types = self._get_semantic_types(cui)
                enrichment['semantic_types'] = semantic_types

            # Step 3: Get SNOMED CT codes
            if include_snomed_ct:
                snomed_codes = self._get_snomed_ct_codes(cui)
                enrichment['snomed_ct_codes'] = snomed_codes

            # Step 4: Get synonyms (alternative names)
            if include_synonyms:
                synonyms = self._get_synonyms(cui)
                enrichment['synonyms'] = synonyms

            return enrichment

        except Exception as e:
            logger.error(f"Error enriching concept '{concept}': {e}")
            return self._create_concept_enrichment(
                concept, cui=None, found=False, error=str(e)
            )

    def _search_concept(self, concept: str) -> Optional[Dict]:
        """
        Search UMLS for a concept using the search endpoint.

        Returns first matching result or None if not found.
        """
        try:
            url = f"{self.base_url}/search/{self.version}"
            params = {
                'string': concept,
                'apiKey': self.api_key,
                'returnIdType': 'concept',
                'pageSize': 1
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('result', {}).get('results', [])
                if results:
                    return results[0]

            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout searching for concept '{concept}'")
            return None
        except Exception as e:
            logger.error(f"Error searching UMLS for '{concept}': {e}")
            return None

    def _get_semantic_types(self, cui: str) -> List[str]:
        """
        Get semantic types for a CUI.

        Semantic types describe the category of the concept
        (e.g., Disease or Syndrome, Procedure, Finding, etc.)
        """
        try:
            url = f"{self.base_url}/content/{self.version}/CUI/{cui}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})

                # SemanticTypes is a list of objects with TUI and STN
                semantic_types_info = result.get('semanticTypes', [])

                semantic_types = []
                for st in semantic_types_info:
                    # STN (Semantic Type Name) is the human-readable name
                    stn = st.get('stn')
                    if stn:
                        semantic_types.append(stn)

                return semantic_types

            return []

        except Exception as e:
            logger.error(f"Error fetching semantic types for CUI {cui}: {e}")
            return []

    def _get_snomed_ct_codes(self, cui: str) -> List[str]:
        """
        Get SNOMED CT codes for a CUI.

        Queries the atoms endpoint filtering for SNOMEDCT_US source.
        """
        try:
            url = f"{self.base_url}/content/{self.version}/CUI/{cui}/atoms"
            params = {
                'apiKey': self.api_key,
                'sabs': 'SNOMEDCT_US',  # Filter for SNOMED CT US edition
                'pageSize': 10
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                atoms = data.get('result', [])

                snomed_codes = []
                seen = set()

                for atom in atoms:
                    code = atom.get('code')
                    if code and code not in seen:
                        snomed_codes.append(code)
                        seen.add(code)

                return snomed_codes[:10]  # Return up to 10 codes

            return []

        except Exception as e:
            logger.error(f"Error fetching SNOMED CT codes for CUI {cui}: {e}")
            return []

    def _get_synonyms(self, cui: str) -> List[str]:
        """
        Get alternative names (synonyms) for a CUI.

        Returns preferred terms from different sources.
        """
        try:
            url = f"{self.base_url}/content/{self.version}/CUI/{cui}/atoms"
            params = {
                'apiKey': self.api_key,
                'pageSize': 10
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                atoms = data.get('result', [])

                synonyms = []
                seen = set()

                for atom in atoms:
                    name = atom.get('name')
                    if name and name not in seen:
                        synonyms.append(name)
                        seen.add(name)

                return synonyms[:5]  # Return up to 5 synonyms

            return []

        except Exception as e:
            logger.error(f"Error fetching synonyms for CUI {cui}: {e}")
            return []

    def _create_concept_enrichment(
        self,
        concept: str,
        cui: Optional[str] = None,
        preferred_name: Optional[str] = None,
        found: bool = False,
        semantic_types: Optional[List[str]] = None,
        snomed_ct_codes: Optional[List[str]] = None,
        synonyms: Optional[List[str]] = None,
        confidence: float = 0.0,
        error: Optional[str] = None
    ) -> Dict:
        """Create a standardized enrichment dictionary."""
        return {
            'concept': concept,
            'cui': cui,
            'preferred_name': preferred_name or concept,
            'semantic_types': semantic_types or [],
            'snomed_ct_codes': snomed_ct_codes or [],
            'synonyms': synonyms or [],
            'found': found,
            'confidence': confidence,
            'error': error
        }

    def _create_empty_enrichment(self, concepts: List[str]) -> Dict[str, Dict]:
        """Create empty enrichment for all concepts (API key not provided)."""
        return {
            concept: self._create_concept_enrichment(concept, found=False)
            for concept in concepts
        }

    def _calculate_success_rate(self, enriched_data: Dict[str, Dict]) -> float:
        """Calculate percentage of successfully enriched concepts."""
        if not enriched_data:
            return 0.0
        found_count = sum(1 for e in enriched_data.values() if e.get('found'))
        return found_count / len(enriched_data)

    def to_csv(self, enriched_data: Dict[str, Dict], filepath: str) -> None:
        """
        Export enriched data to CSV format.

        Args:
            enriched_data: Dictionary from enrich_concepts()
            filepath: Output CSV file path
        """
        import csv

        if not enriched_data:
            logger.warning("No data to export to CSV")
            return

        try:
            # Get all unique items (handle lists)
            rows = []
            for concept, enrichment in enriched_data.items():
                row = {
                    'Concept': enrichment['concept'],
                    'CUI': enrichment['cui'] or '',
                    'Preferred_Name': enrichment['preferred_name'],
                    'Semantic_Types': '|'.join(enrichment.get('semantic_types', [])),
                    'SNOMED_CT_Codes': '|'.join(enrichment.get('snomed_ct_codes', [])),
                    'Synonyms': '|'.join(enrichment.get('synonyms', [])),
                    'Found': enrichment['found'],
                    'Confidence': f"{enrichment.get('confidence', 0.0):.3f}",
                    'Error': enrichment.get('error', '')
                }
                rows.append(row)

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Concept', 'CUI', 'Preferred_Name', 'Semantic_Types',
                    'SNOMED_CT_Codes', 'Synonyms', 'Found', 'Confidence', 'Error'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Enriched data exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")

    def to_json(self, enriched_data: Dict[str, Dict], filepath: str) -> None:
        """
        Export enriched data to JSON format.

        Args:
            enriched_data: Dictionary from enrich_concepts()
            filepath: Output JSON file path
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(enriched_data, jsonfile, indent=2, ensure_ascii=False)
            logger.info(f"Enriched data exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
