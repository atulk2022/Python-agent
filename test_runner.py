#!/usr/bin/env python3
"""
Test runner for FNOL Claims Processing Agent
Runs the agent on sample documents and displays results
"""

import sys
import os
import json

# Handle Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fnol_processor import process_all_documents, FNOLProcessor


def print_results_summary():
    """Print a formatted summary of processing results"""
    summary_file = os.path.join('output', 'PROCESSING_SUMMARY.json')

    if not os.path.exists(summary_file):
        print("No summary file found. Run process_all_documents first.")
        return

    with open(summary_file, 'r') as f:
        results = json.load(f)

    print("\n" + "="*80)
    print("FNOL CLAIMS PROCESSING - RESULTS SUMMARY")
    print("="*80)

    route_counts = {}

    for item in results:
        doc_name = item['document']
        result = item['result']
        route = result['recommendedRoute']

        route_counts[route] = route_counts.get(route, 0) + 1

        print(f"\n{'-'*80}")
        print(f"Document: {doc_name}")
        print(f"{'-'*80}")
        print(f"Route: {route}")
        print(f"Reasoning: {result['reasoning']}")

        if result['missingFields']:
            print(f"Missing Fields: {', '.join(result['missingFields'])}")

        if result['extractedFields']:
            print(f"Key Extracted Fields:")
            fields = result['extractedFields']
            print(f"  - Policy Number: {fields.get('policy_number', 'N/A')}")
            print(f"  - Policyholder: {fields.get('policyholder_name', 'N/A')}")
            print(f"  - Claim Type: {fields.get('claim_type', 'N/A')}")
            print(f"  - Estimated Damage: ${fields.get('estimated_damage', 0):,.2f}")

    print(f"\n{'='*80}")
    print("ROUTING DISTRIBUTION")
    print(f"{'='*80}")
    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")

    print(f"\nTotal Documents Processed: {len(results)}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    import os

    # Ensure directories exist
    os.makedirs('output', exist_ok=True)

    print("\n" + "="*80)
    print("AUTONOMOUS INSURANCE CLAIMS PROCESSING AGENT")
    print("FNOL (First Notice of Loss) Document Processor")
    print("="*80 + "\n")

    # Process all documents
    print("Starting document processing...\n")
    process_all_documents('fnol_documents', 'output')

    # Print summary
    print_results_summary()
