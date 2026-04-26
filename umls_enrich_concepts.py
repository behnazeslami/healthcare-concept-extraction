"""
UMLS Enrichment Pipeline - Standalone Utility
Processes CSV files with mapped concepts and enriches them with UMLS metadata.

Usage:
    python umls_enrich_concepts.py \
        --input input.csv \
        --output output_enriched.csv \
        --concept-column "Concepts" \
        --api-key "your_umls_api_key"

Features:
    - Reads CSVs with mapped concepts
    - Fetches CUI, Preferred Names, Semantic Types, SNOMED CT codes
    - Supports batch processing
    - Outputs enriched data in CSV and JSON formats
    - Follows project conventions for output columns
"""

import argparse
import logging
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools.umls_enricher import UMLSEnricher
from config import AgentConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UMLSEnrichmentPipeline:
    """Pipeline for enriching concepts with UMLS metadata"""

    def __init__(self, api_key: str):
        """Initialize enrichment pipeline"""
        self.enricher = UMLSEnricher(api_key=api_key)
        logger.info("UMLS Enrichment Pipeline initialized")

    def process_csv(
        self,
        input_path: str,
        output_path: str,
        concept_column: str = "Concepts",
        batch_size: int = 50,
        include_semantic_types: bool = True,
        include_snomed_ct: bool = True,
        include_synonyms: bool = False
    ) -> pd.DataFrame:
        """
        Process CSV file and enrich concepts with UMLS metadata.

        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            concept_column: Name of column containing concepts
            batch_size: Batch size for logging
            include_semantic_types: Whether to fetch semantic types
            include_snomed_ct: Whether to fetch SNOMED CT codes
            include_synonyms: Whether to fetch alternative names

        Returns:
            Enriched DataFrame
        """
        logger.info(f"Reading input CSV: {input_path}")

        # Read input CSV
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")

        # Validate concept column exists
        if concept_column not in df.columns:
            logger.error(f"Column '{concept_column}' not found in CSV")
            raise ValueError(f"Column '{concept_column}' not found in CSV")

        # Extract unique concepts
        concepts = df[concept_column].dropna().unique().tolist()
        logger.info(f"Found {len(concepts)} unique concepts to enrich")

        # Enrich concepts
        enriched_data = self.enricher.enrich_concepts(
            concepts,
            batch_size=batch_size,
            include_semantic_types=include_semantic_types,
            include_snomed_ct=include_snomed_ct,
            include_synonyms=include_synonyms
        )

        # Create enrichment DataFrame
        enrichment_df = pd.DataFrame.from_dict(enriched_data, orient='index')

        # Add enrichment columns to original DataFrame
        df_enriched = df.copy()

        # Map enrichment data to rows
        df_enriched['CUI'] = df_enriched[concept_column].map(
            lambda x: enriched_data.get(x, {}).get('cui') if pd.notna(x) else None
        )
        df_enriched['Preferred_Name'] = df_enriched[concept_column].map(
            lambda x: enriched_data.get(x, {}).get('preferred_name') if pd.notna(x) else None
        )
        df_enriched['Semantic_Types'] = df_enriched[concept_column].map(
            lambda x: '|'.join(enriched_data.get(x, {}).get('semantic_types', [])) if pd.notna(x) else None
        )
        df_enriched['SNOMED_CT_Codes'] = df_enriched[concept_column].map(
            lambda x: '|'.join(enriched_data.get(x, {}).get('snomed_ct_codes', [])) if pd.notna(x) else None
        )
        df_enriched['UMLS_Found'] = df_enriched[concept_column].map(
            lambda x: enriched_data.get(x, {}).get('found') if pd.notna(x) else False
        )
        df_enriched['UMLS_Confidence'] = df_enriched[concept_column].map(
            lambda x: enriched_data.get(x, {}).get('confidence', 0.0) if pd.notna(x) else 0.0
        )

        # Save enriched CSV
        df_enriched.to_csv(output_path, index=False)
        logger.info(f"Enriched CSV saved to {output_path}")

        # Save detailed enrichment JSON
        json_output_path = output_path.replace('.csv', '_detailed.json')
        self.enricher.to_json(enriched_data, json_output_path)
        logger.info(f"Detailed enrichment saved to {json_output_path}")

        # Save summary
        self._save_summary(enriched_data, output_path)

        return df_enriched

    def _save_summary(self, enriched_data: dict, output_path: str) -> None:
        """Save enrichment summary statistics"""
        total = len(enriched_data)
        found = sum(1 for e in enriched_data.values() if e.get('found'))
        success_rate = found / total if total > 0 else 0

        summary_path = output_path.replace('.csv', '_summary.txt')

        with open(summary_path, 'w') as f:
            f.write("UMLS Enrichment Summary\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total Concepts: {total}\n")
            f.write(f"Successfully Mapped: {found}\n")
            f.write(f"Success Rate: {success_rate:.2%}\n")
            f.write(f"Output Files: {output_path}\n")

        logger.info(f"Summary saved to {summary_path}")

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        concept_column: str = "Concepts",
        pattern: str = "*.csv"
    ) -> None:
        """
        Process all CSV files in a directory.

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            concept_column: Name of concept column
            pattern: File pattern to match
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        csv_files = list(input_path.glob(pattern))
        logger.info(f"Found {len(csv_files)} CSV files in {input_dir}")

        for csv_file in csv_files:
            logger.info(f"\nProcessing: {csv_file.name}")
            try:
                output_file = output_path / f"{csv_file.stem}_enriched.csv"
                self.process_csv(
                    str(csv_file),
                    str(output_file),
                    concept_column=concept_column
                )
                logger.info(f"✓ Successfully processed {csv_file.name}")
            except Exception as e:
                logger.error(f"✗ Error processing {csv_file.name}: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enrich healthcare concepts with UMLS metadata"
    )

    parser.add_argument(
        '--input',
        type=str,
        help='Path to input CSV file or directory'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to output CSV file or directory'
    )
    parser.add_argument(
        '--concept-column',
        type=str,
        default='Concepts',
        help='Name of column containing concepts (default: Concepts)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='UMLS API key (uses config default if not provided)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for logging (default: 50)'
    )
    parser.add_argument(
        '--include-semantic-types',
        action='store_true',
        default=True,
        help='Include semantic types (default: True)'
    )
    parser.add_argument(
        '--include-snomed-ct',
        action='store_true',
        default=True,
        help='Include SNOMED CT codes (default: True)'
    )
    parser.add_argument(
        '--include-synonyms',
        action='store_true',
        default=False,
        help='Include alternative names/synonyms'
    )
    parser.add_argument(
        '--mode',
        choices=['file', 'directory'],
        default='file',
        help='Process single file or directory'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input or not args.output:
        logger.error("Input and output paths are required")
        parser.print_help()
        sys.exit(1)

    # Get API key
    api_key = args.api_key or AgentConfig.get_umls_api_key()
    if not api_key:
        logger.error("UMLS API key not found. Provide --api-key or configure in config.py")
        sys.exit(1)

    # Initialize pipeline
    pipeline = UMLSEnrichmentPipeline(api_key=api_key)

    try:
        if args.mode == 'file':
            logger.info(f"Processing single file: {args.input}")
            pipeline.process_csv(
                input_path=args.input,
                output_path=args.output,
                concept_column=args.concept_column,
                batch_size=args.batch_size,
                include_semantic_types=args.include_semantic_types,
                include_snomed_ct=args.include_snomed_ct,
                include_synonyms=args.include_synonyms
            )
        else:
            logger.info(f"Processing directory: {args.input}")
            pipeline.process_directory(
                input_dir=args.input,
                output_dir=args.output,
                concept_column=args.concept_column
            )

        logger.info("✓ Enrichment pipeline completed successfully")

    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
