"""
Complete Example: UMLS Enrichment with Agent Output
Demonstrates integrating UMLS enrichment into agent responses
"""

import asyncio
import pandas as pd
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent import HealthcareAgenticAI
from models import AgenticRequest, AgentGoal, ToolName
from tools.umls_enricher import UMLSEnricher
from config import AgentConfig


class EnrichedAgentPipeline:
    """
    Complete pipeline: Agent Reasoning + UMLS Enrichment
    Takes clinical text, extracts concepts, and enriches with UMLS metadata
    """

    def __init__(self, model_size: str = "8B"):
        """Initialize agent and enricher"""
        self.agent = HealthcareAgenticAI(
            model_size=model_size,
            umls_api_key=AgentConfig.get_umls_api_key()
        )
        self.enricher = UMLSEnricher(
            api_key=AgentConfig.get_umls_api_key()
        )

    async def process_with_enrichment(
        self,
        clinical_text: str,
        main_note: Optional[str] = None,
        goal: AgentGoal = AgentGoal.BALANCED,
        enrich_concepts: bool = True
    ) -> Dict:
        """
        Process clinical text with agent and optionally enrich concepts with UMLS.

        Args:
            clinical_text: Clinical text to process
            main_note: Optional main note for context
            goal: Agent optimization goal
            enrich_concepts: Whether to enrich extracted concepts with UMLS data

        Returns:
            Dictionary with agent response and enrichment data
        """

        # Step 1: Run agent reasoning
        request = AgenticRequest(
            clinical_text=clinical_text,
            main_note=main_note,
            goal=goal,
            enable_tools=[
                ToolName.CONCEPT_EXTRACTOR,
                ToolName.UMLS_VALIDATOR
            ],
            max_reasoning_steps=5
        )

        print("=" * 80)
        print("STEP 1: Agent Reasoning")
        print("=" * 80)

        response = await self.agent.reason(request)

        print(f"✓ Extracted {len(response.extracted_concepts)} concepts")
        print(f"  Confidence: {response.confidence:.3f}")
        print(f"  Runtime: {response.script_runtime:.2f}s")

        result = {
            'agent_response': response,
            'enrichment': None
        }

        # Step 2: Enrich concepts with UMLS
        if enrich_concepts and response.extracted_concepts:
            print("\n" + "=" * 80)
            print("STEP 2: UMLS Enrichment")
            print("=" * 80)

            enrichment_data = self.enricher.enrich_concepts(
                response.extracted_concepts,
                include_semantic_types=True,
                include_snomed_ct=True,
                include_synonyms=True
            )

            print(f"✓ Enriched {len(enrichment_data)} concepts")
            print(f"  Success rate: {self.enricher._calculate_success_rate(enrichment_data):.2%}")

            result['enrichment'] = enrichment_data

        return result

    def enrich_agent_output_dataframe(
        self,
        df: pd.DataFrame,
        concept_column: str = "extracted_concepts"
    ) -> pd.DataFrame:
        """
        Enrich agent output DataFrame with UMLS metadata.

        Args:
            df: DataFrame with agent output
            concept_column: Column name containing concepts

        Returns:
            DataFrame with enrichment columns added
        """

        # Extract all unique concepts
        concepts = []
        for concept_list in df[concept_column]:
            if isinstance(concept_list, list):
                concepts.extend(concept_list)
            else:
                # Handle string representation of list
                concepts.append(str(concept_list))

        concepts = list(set(concepts))

        print(f"Enriching {len(concepts)} unique concepts from agent output...")

        # Enrich concepts
        enriched_data = self.enricher.enrich_concepts(
            concepts,
            include_semantic_types=True,
            include_snomed_ct=True
        )

        # Create enrichment columns
        df_enriched = df.copy()

        # For each row, get all CUIs and metadata for extracted concepts
        def get_concept_metadata(concepts_list, metadata_key):
            if not isinstance(concepts_list, list):
                return ""
            metadata_list = []
            for concept in concepts_list:
                if concept in enriched_data:
                    value = enriched_data[concept].get(metadata_key, '')
                    if value:
                        if isinstance(value, list):
                            metadata_list.append('|'.join(value))
                        else:
                            metadata_list.append(str(value))
            return '; '.join(metadata_list)

        df_enriched['CUI_List'] = df_enriched[concept_column].apply(
            lambda x: get_concept_metadata(x, 'cui')
        )
        df_enriched['Preferred_Names'] = df_enriched[concept_column].apply(
            lambda x: get_concept_metadata(x, 'preferred_name')
        )
        df_enriched['Semantic_Types'] = df_enriched[concept_column].apply(
            lambda x: get_concept_metadata(x, 'semantic_types')
        )
        df_enriched['SNOMED_CT_Codes'] = df_enriched[concept_column].apply(
            lambda x: get_concept_metadata(x, 'snomed_ct_codes')
        )

        return df_enriched


async def example_single_record():
    """Process a single clinical record with enrichment"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Single Record Processing")
    print("=" * 80)

    pipeline = EnrichedAgentPipeline(model_size="8B")

    clinical_text = """
    Patient presents with chest pain and shortness of breath.
    Has history of hypertension and diabetes mellitus.
    Currently on metformin and lisinopril.
    Physical exam shows elevated blood pressure and tachycardia.
    EKG shows ST elevation in anterior leads.
    """

    main_note = "75-year-old male with acute coronary syndrome"

    result = await pipeline.process_with_enrichment(
        clinical_text=clinical_text,
        main_note=main_note,
        goal=AgentGoal.MAXIMIZE_ACCURACY,
        enrich_concepts=True
    )

    # Display results
    response = result['agent_response']
    enrichment = result['enrichment']

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print("\nExtracted Concepts:")
    for concept in response.extracted_concepts:
        print(f"  - {concept}")

    if enrichment:
        print("\nENRICHMENT DATA:")
        for concept, data in enrichment.items():
            if data['found']:
                print(f"\n  Concept: {concept}")
                print(f"    CUI: {data['cui']}")
                print(f"    Preferred Name: {data['preferred_name']}")
                print(f"    Semantic Types: {', '.join(data['semantic_types'])}")
                print(f"    SNOMED CT Codes: {', '.join(data['snomed_ct_codes'][:3])}")
            else:
                print(f"\n  Concept: {concept} [NOT FOUND IN UMLS]")

    print("\nReasoning Chain:")
    for step in response.reasoning_chain:
        print(f"  Step {step.step_number}: {step.thought}")
        print(f"    → {step.action}")


async def example_batch_enrichment():
    """Process multiple records and save enriched results"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Batch Enrichment from CSV")
    print("=" * 80)

    # Create example agent output (normally from agent.py output)
    example_data = {
        'record_id': ['REC001', 'REC002', 'REC003'],
        'clinical_text': [
            'Patient with chest pain and shortness of breath',
            'Acute pneumonia with fever and cough',
            'Type 2 diabetes with hypertension'
        ],
        'extracted_concepts': [
            ['chest pain', 'shortness of breath', 'acute coronary syndrome'],
            ['pneumonia', 'fever', 'cough', 'respiratory infection'],
            ['diabetes', 'hypertension', 'metabolic disorder']
        ],
        'confidence': [0.85, 0.92, 0.88]
    }

    df_agent_output = pd.DataFrame(example_data)

    pipeline = EnrichedAgentPipeline(model_size="8B")

    # Enrich agent output
    df_enriched = pipeline.enrich_agent_output_dataframe(
        df_agent_output,
        concept_column='extracted_concepts'
    )

    # Save results
    output_path = Path(__file__).parent / "example_enriched_output.csv"
    df_enriched.to_csv(output_path, index=False)

    print(f"✓ Enriched {len(df_enriched)} records")
    print(f"  Saved to: {output_path}")

    # Display sample
    print("\nSample Output:")
    print(df_enriched[[
        'record_id', 'extracted_concepts', 'CUI_List', 'Semantic_Types'
    ]].head())


async def main():
    """Run examples"""
    print("\n" + "=" * 80)
    print("UMLS ENRICHMENT EXAMPLES - Healthcare Agentic AI")
    print("=" * 80)

    # Run single record example
    await example_single_record()

    # Run batch enrichment example
    await example_batch_enrichment()

    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
