"""
FNOL (First Notice of Loss) Claims Processing Agent
Extracts key fields, validates data, and routes claims based on rules.
"""

import json
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ClaimRoute(Enum):
    """Routing destinations for claims"""
    FAST_TRACK = "Fast-Track Processing"
    MANUAL_REVIEW = "Manual Review Required"
    SPECIALIST_QUEUE = "Specialist Queue (Injury)"
    FRAUD_INVESTIGATION = "Fraud Investigation"


@dataclass
class ExtractedFields:
    """Data structure for extracted FNOL fields"""
    policy_number: str = None
    policyholder_name: str = None
    effective_dates: str = None
    incident_date: str = None
    incident_time: str = None
    incident_location: str = None
    incident_description: str = None
    claimant_name: str = None
    third_parties: List[str] = None
    claimant_contact: str = None
    asset_type: str = None
    asset_id: str = None
    estimated_damage: float = None
    claim_type: str = None
    attachments: List[str] = None
    police_report: str = None
    injuries: str = None

    def to_dict(self):
        """Convert to dictionary, excluding None values"""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


class FNOLProcessor:
    """Main processor for FNOL documents"""

    # Mandatory fields that must be present
    MANDATORY_FIELDS = [
        'policy_number',
        'policyholder_name',
        'incident_date',
        'incident_location',
        'incident_description',
        'claimant_name',
        'claim_type',
        'estimated_damage'
    ]

    # Fraud detection keywords
    FRAUD_KEYWORDS = ['fraud', 'staged', 'inconsistent', 'suspicious', 'contradictions']

    # Damage threshold (in dollars)
    FAST_TRACK_THRESHOLD = 25000

    def __init__(self):
        """Initialize the processor"""
        pass

    def process_document(self, file_path: str) -> Dict:
        """
        Process a single FNOL document
        
        Args:
            file_path: Path to the FNOL document
            
        Returns:
            Dictionary with extracted fields, missing fields, routing decision, and reasoning
        """
        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract fields
        extracted = self._extract_fields(content)

        # Identify missing mandatory fields
        missing_fields = self._identify_missing_fields(extracted)

        # Apply routing rules
        route, reasoning = self._determine_route(extracted, missing_fields, content)

        # Format output
        result = {
            "extractedFields": extracted.to_dict(),
            "missingFields": missing_fields,
            "recommendedRoute": route.value,
            "reasoning": reasoning
        }

        return result

    def _extract_fields(self, content: str) -> ExtractedFields:
        """Extract all relevant fields from document content"""
        fields = ExtractedFields()

        # Policy Information
        fields.policy_number = self._extract_field(
            content, r'POLICY\s+NUMBER:\s*([A-Za-z0-9\-]+)'
        )
        fields.policyholder_name = self._extract_field(
            content, r'INSURED\s+NAME:\s*([A-Za-z\s]+?)(?=\n|MAILING)'
        )
        fields.effective_dates = self._extract_field(
            content, r'EFFECTIVE\s+DATE[S]?:\s*([^\n]+)'
        )

        # Incident Information
        fields.incident_date = self._extract_field(
            content, r'DATE\s+OF\s+LOSS:\s*(\d{2}/\d{2}/\d{4})'
        )
        fields.incident_time = self._extract_field(
            content, r'TIME\s+OF\s+LOSS:\s*(\d{2}:\d{2})'
        )
        fields.incident_location = self._extract_field(
            content, r'LOSS\s+LOCATION:.*?STREET:\s*([^\n]+)'
        )
        fields.incident_description = self._extract_field(
            content, r'ACCIDENT\s+DESCRIPTION:\s*([^\n]+(?:\n(?!OTHER|CLAIM TYPE|STATUS)[^\n]*)*)'
        )

        # Involved Parties
        fields.claimant_name = self._extract_field(
            content, r'CLAIMANT\s+NAME:\s*([A-Za-z\s]+?)(?=\n|PRIMARY)'
        )

        # Extract third parties (other vehicle info or owners)
        third_parties = []
        other_owner = self._extract_field(
            content, r'OTHER\s+VEHICLE\s+OWNER:\s*([^\n]+)'
        )
        if other_owner and 'NOT PROVIDED' not in other_owner.upper():
            third_parties.append(other_owner)

        # Extract witness information
        witnesses = re.findall(
            r'WITNESS\s+\d+\s+NAME:\s*([A-Za-z\s]+?)(?=\n)',
            content
        )
        third_parties.extend([w for w in witnesses if 'NOT PROVIDED' not in w.upper()])

        fields.third_parties = third_parties if third_parties else None

        # Contact Details
        fields.claimant_contact = self._extract_field(
            content, r'PRIMARY\s+CONTACT\s+PHONE:\s*([^\n]+)'
        )

        # Asset Details
        fields.asset_type = self._extract_field(
            content, r'BODY\s+TYPE:\s*([A-Za-z\s]+)'
        )
        
        vin = self._extract_field(content, r'VIN:\s*([A-Za-z0-9]+)')
        plate = self._extract_field(content, r'PLATE\s+NUMBER:\s*([A-Za-z0-9\-]+)')
        fields.asset_id = f"VIN: {vin}, Plate: {plate}" if vin or plate else None

        # Damage Information
        damage_str = self._extract_field(
            content, r'ESTIMATED\s+DAMAGE\s+AMOUNT:\s*\$?([\d,]+\.?\d*)'
        )
        if damage_str:
            try:
                fields.estimated_damage = float(damage_str.replace(',', ''))
            except ValueError:
                fields.estimated_damage = None

        # Claim Type
        fields.claim_type = self._extract_field(
            content, r'CLAIM\s+TYPE:\s*([A-Za-z\s]+)'
        )

        # Attachments
        attachments_text = self._extract_field(
            content, r'ATTACHMENTS:\s*([^\n]+)'
        )
        if attachments_text:
            fields.attachments = [a.strip() for a in attachments_text.split(',')]

        # Police Report
        fields.police_report = self._extract_field(
            content, r'POLICE\s+CONTACTED:\s*(Yes|No)'
        )

        # Injuries
        injury_info = self._extract_field(
            content, r'INJURY\s+(?:DESCRIPTION|INFORMATION|STATUS):\s*([^\n]+(?:\n(?!OTHER|CLAIM TYPE)[^\n]*)*)'
        )
        fields.injuries = injury_info if injury_info else None

        return fields

    def _extract_field(self, content: str, pattern: str) -> str:
        """
        Extract a single field using regex pattern
        
        Args:
            content: Document content
            pattern: Regex pattern to match
            
        Returns:
            Extracted value or None
        """
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value and 'NOT PROVIDED' not in value.upper():
                return value
        return None

    def _identify_missing_fields(self, extracted: ExtractedFields) -> List[str]:
        """
        Identify missing mandatory fields
        
        Args:
            extracted: Extracted fields object
            
        Returns:
            List of missing field names
        """
        missing = []
        for field_name in self.MANDATORY_FIELDS:
            value = getattr(extracted, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_name.replace('_', ' ').title())
        
        return missing

    def _determine_route(
        self,
        extracted: ExtractedFields,
        missing_fields: List[str],
        content: str
    ) -> Tuple[ClaimRoute, str]:
        """
        Determine claim routing based on rules
        
        Args:
            extracted: Extracted fields
            missing_fields: List of missing mandatory fields
            content: Original document content
            
        Returns:
            Tuple of (route, reasoning)
        """
        reasoning_parts = []

        # Rule 1: Check for fraud indicators
        fraud_detected = self._check_fraud_indicators(content)
        if fraud_detected:
            reasoning_parts.append(f"Fraud indicators detected: {fraud_detected}")
            return ClaimRoute.FRAUD_INVESTIGATION, " ".join(reasoning_parts)

        # Rule 2: Check for missing mandatory fields
        if missing_fields:
            reasoning_parts.append(
                f"Missing mandatory fields: {', '.join(missing_fields)}"
            )
            return ClaimRoute.MANUAL_REVIEW, " ".join(reasoning_parts)

        # Rule 3: Check for injury claims
        if extracted.claim_type and 'injury' in extracted.claim_type.lower():
            reasoning_parts.append("Claim type is injury-related.")
            return ClaimRoute.SPECIALIST_QUEUE, " ".join(reasoning_parts)

        if extracted.injuries and 'yes' in extracted.injuries.lower():
            reasoning_parts.append("Injuries reported in claim.")
            return ClaimRoute.SPECIALIST_QUEUE, " ".join(reasoning_parts)

        # Rule 4: Check damage threshold for fast-track
        if extracted.estimated_damage is not None:
            if extracted.estimated_damage < self.FAST_TRACK_THRESHOLD:
                reasoning_parts.append(
                    f"Estimated damage (${extracted.estimated_damage:,.2f}) is below "
                    f"fast-track threshold of ${self.FAST_TRACK_THRESHOLD:,.2f}. "
                    "All mandatory fields present. No fraud indicators or injuries."
                )
                return ClaimRoute.FAST_TRACK, " ".join(reasoning_parts)
            else:
                reasoning_parts.append(
                    f"Estimated damage (${extracted.estimated_damage:,.2f}) exceeds "
                    f"fast-track threshold of ${self.FAST_TRACK_THRESHOLD:,.2f}. "
                    "Requires manual review for complex claims."
                )
                return ClaimRoute.MANUAL_REVIEW, " ".join(reasoning_parts)

        # Default: Manual review
        reasoning_parts.append("Unable to determine routing due to insufficient data.")
        return ClaimRoute.MANUAL_REVIEW, " ".join(reasoning_parts)

    def _check_fraud_indicators(self, content: str) -> str:
        """
        Check for fraud indicators in document
        
        Args:
            content: Document content
            
        Returns:
            Description of fraud indicators found, or empty string
        """
        found_keywords = []
        for keyword in self.FRAUD_KEYWORDS:
            if keyword.lower() in content.lower():
                found_keywords.append(keyword)

        return ", ".join(found_keywords) if found_keywords else ""


def process_all_documents(input_dir: str, output_dir: str) -> None:
    """
    Process all FNOL documents in a directory
    
    Args:
        input_dir: Directory containing FNOL documents
        output_dir: Directory to save processed results
    """
    import os

    processor = FNOLProcessor()

    # Get all txt files
    fnol_files = [
        f for f in os.listdir(input_dir)
        if f.startswith('FNOL_') and f.endswith('.txt')
    ]

    results = []

    for file_name in sorted(fnol_files):
        file_path = os.path.join(input_dir, file_name)
        print(f"\nProcessing {file_name}...")

        result = processor.process_document(file_path)
        results.append({
            "document": file_name,
            "result": result
        })

        # Save individual result
        output_file = os.path.join(
            output_dir,
            file_name.replace('.txt', '_RESULT.json')
        )
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"  Recommended Route: {result['recommendedRoute']}")
        if result['missingFields']:
            print(f"  Missing Fields: {', '.join(result['missingFields'])}")

    # Save summary report
    summary_file = os.path.join(output_dir, 'PROCESSING_SUMMARY.json')
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nProcessing complete. Results saved to {output_dir}")
    print(f"Processed {len(fnol_files)} documents.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # Default paths
        input_dir = "fnol_documents"
        output_dir = "output"

    process_all_documents(input_dir, output_dir)
