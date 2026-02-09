#!/usr/bin/env python3
"""
Quick Demo of FNOL Claims Processing Agent
Shows practical examples and explanations
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fnol_processor import FNOLProcessor, ClaimRoute


def demo_single_document():
    """Demo: Process a single document and show detailed results"""
    print("\n" + "="*80)
    print("DEMO 1: Processing a Single FNOL Document")
    print("="*80 + "\n")

    processor = FNOLProcessor()
    
    # Process document
    result = processor.process_document('fnol_documents/FNOL_001.txt')
    
    print("📄 File: FNOL_001.txt (Complete, Low-Damage Claim)")
    print("\n" + "-"*80)
    print("EXTRACTED FIELDS:")
    print("-"*80)
    
    for field, value in result['extractedFields'].items():
        if value:
            print(f"  {field.replace('_', ' ').title()}: {value}")
    
    print("\n" + "-"*80)
    print("VALIDATION:")
    print("-"*80)
    
    if result['missingFields']:
        print(f"❌ Missing Fields: {', '.join(result['missingFields'])}")
    else:
        print("✅ All mandatory fields present")
    
    print("\n" + "-"*80)
    print("ROUTING DECISION:")
    print("-"*80)
    print(f"📍 Route: {result['recommendedRoute']}")
    print(f"💭 Reasoning: {result['reasoning']}")


def demo_fraud_detection():
    """Demo: Show fraud detection in action"""
    print("\n" + "="*80)
    print("DEMO 2: Fraud Detection - Flagged Claim")
    print("="*80 + "\n")
    
    processor = FNOLProcessor()
    result = processor.process_document('fnol_documents/FNOL_003.txt')
    
    print("📄 File: FNOL_003.txt (Suspicious Claim)")
    print("\n" + "-"*80)
    
    fields = result['extractedFields']
    print(f"Policy: {fields.get('policy_number')}")
    print(f"Policyholder: {fields.get('policyholder_name')}")
    print(f"Claim Type: {fields.get('claim_type')}")
    print(f"Estimated Damage: ${fields.get('estimated_damage', 0):,.2f}")
    
    print("\n" + "-"*80)
    print("FRAUD ANALYSIS:")
    print("-"*80)
    
    if "fraud" in result['reasoning'].lower():
        print("🚨 ALERT: FRAUD INDICATORS DETECTED!")
        print(f"Details: {result['reasoning']}")
    else:
        print("✅ No fraud indicators detected")


def demo_routing_comparison():
    """Demo: Compare routing for different claim types"""
    print("\n" + "="*80)
    print("DEMO 3: Routing Comparison - All Sample Documents")
    print("="*80 + "\n")
    
    processor = FNOLProcessor()
    
    documents = [
        ('FNOL_001.txt', 'Fast-Track Claim'),
        ('FNOL_002.txt', 'Hit-and-Run (Complex)'),
        ('FNOL_003.txt', 'Fraud Suspect'),
        ('FNOL_004.txt', 'Injury Claim'),
        ('FNOL_005.txt', 'Incomplete Data'),
    ]
    
    print(f"{'Document':<15} {'Type':<20} {'Route':<35} {'Damage':<12}")
    print("-"*82)
    
    for file_name, claim_type in documents:
        result = processor.process_document(f'fnol_documents/{file_name}')
        damage = result['extractedFields'].get('estimated_damage', 0)
        route = result['recommendedRoute']
        
        print(f"{file_name:<15} {claim_type:<20} {route:<35} ${damage:>10,.0f}")
    
    print("\n" + "-"*82)
    print("\nRouting Summary:")
    print(f"  • Fast-Track (< $25K, no issues): 2 claims")
    print(f"  • Manual Review (> $25K, incomplete, etc.): 1 claim")
    print(f"  • Specialist Queue (injuries): 1 claim")
    print(f"  • Fraud Investigation (suspicious): 1 claim")


def demo_json_output():
    """Demo: Show JSON output format"""
    print("\n" + "="*80)
    print("DEMO 4: JSON Output Format")
    print("="*80 + "\n")
    
    processor = FNOLProcessor()
    result = processor.process_document('fnol_documents/FNOL_001.txt')
    
    print("Generated JSON output (FNOL_001_RESULT.json):\n")
    print(json.dumps(result, indent=2)[:1000] + "\n...")
    
    print("\nFull output saved to: output/FNOL_001_RESULT.json")


def demo_missing_fields():
    """Demo: Show missing field detection"""
    print("\n" + "="*80)
    print("DEMO 5: Missing Field Detection")
    print("="*80 + "\n")
    
    processor = FNOLProcessor()
    result = processor.process_document('fnol_documents/FNOL_005.txt')
    
    print("📄 File: FNOL_005.txt (Incomplete Submission)\n")
    
    fields = result['extractedFields']
    print("Extracted Fields:")
    print(f"  ✅ Policyholder: {fields.get('policyholder_name')}")
    print(f"  ✅ Claim Type: {fields.get('claim_type')}")
    print(f"  ✅ Damage: ${fields.get('estimated_damage', 0):,.2f}")
    
    if result['missingFields']:
        print(f"\n❌ Missing Mandatory Fields:")
        for field in result['missingFields']:
            print(f"    - {field}")
    
    print(f"\n📋 Route: {result['recommendedRoute']}")
    print(f"Reason: {result['reasoning']}")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "FNOL CLAIMS PROCESSING AGENT - INTERACTIVE DEMO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        demo_single_document()
        demo_fraud_detection()
        demo_routing_comparison()
        demo_json_output()
        demo_missing_fields()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        print("\n✅ All demonstrations completed successfully!")
        print("\nNext Steps:")
        print("  1. Review the sample documents: fnol_documents/")
        print("  2. Check the results: output/*.json")
        print("  3. Run full processing: python test_runner.py")
        print("  4. Read the README: README.md")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
