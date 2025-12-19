"""
Test FraudDetector Abstract Interface
Verifies the production-grade fraud detection interface
"""

from app.ai.fraud import FraudDetector
from typing import Dict, Any


class SimpleFraudDetector(FraudDetector):
    """Simple implementation of FraudDetector for testing."""
    
    @property
    def name(self) -> str:
        """Return detector name."""
        return "SimpleFraudDetector-v1.0"
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk.
        
        Returns required format:
        {
            "fraud_score": float,
            "flags": list[str],
            "explanation": list[str]
        }
        """
        # Simple logic for testing
        borrower = input_data.get("borrower", {})
        loan = input_data.get("loan", {})
        
        fraud_score = 0.0
        flags = []
        explanation = []
        
        # Check 1: High loan amount
        amount = loan.get("amount", 0)
        if amount > 100000:
            fraud_score += 0.5
            flags.append("high_amount")
            explanation.append(f"Loan amount {amount} exceeds threshold")
        
        # Check 2: Unknown region
        region = borrower.get("region", "").lower()
        if region in ["unknown", ""]:
            fraud_score += 0.3
            flags.append("unknown_region")
            explanation.append("Borrower region is unknown")
        
        # Clamp fraud_score to [0.0, 1.0]
        fraud_score = min(fraud_score, 1.0)
        
        return {
            "fraud_score": fraud_score,
            "flags": flags,
            "explanation": explanation
        }


def test_fraud_detector_interface():
    """Test FraudDetector abstract interface."""
    
    print("="*70)
    print("FRAUDDETECTOR INTERFACE TEST")
    print("="*70)
    
    # Create detector instance
    detector = SimpleFraudDetector()
    
    # Test 1: Detector name property
    print(f"\n🔍 Test 1: Detector name property")
    print(f"   Name: {detector.name}")
    assert detector.name == "SimpleFraudDetector-v1.0"
    print(f"   ✅ Name property working")
    
    # Test 2: Low-risk evaluation
    print(f"\n🔍 Test 2: Low-risk evaluation")
    input_data_low = {
        "borrower": {"region": "Dhaka"},
        "loan": {"amount": 25000}
    }
    
    result_low = detector.evaluate(input_data_low)
    
    print(f"   Input: {input_data_low}")
    print(f"   Result: {result_low}")
    
    # Verify required keys
    assert "fraud_score" in result_low, "Missing fraud_score"
    assert "flags" in result_low, "Missing flags"
    assert "explanation" in result_low, "Missing explanation"
    
    # Verify types
    assert isinstance(result_low["fraud_score"], (int, float)), "fraud_score must be numeric"
    assert isinstance(result_low["flags"], list), "flags must be list"
    assert isinstance(result_low["explanation"], list), "explanation must be list"
    
    # Verify fraud_score range
    assert 0.0 <= result_low["fraud_score"] <= 1.0, "fraud_score must be in [0.0, 1.0]"
    
    print(f"   Fraud Score: {result_low['fraud_score']:.2f}")
    print(f"   Flags: {result_low['flags']}")
    print(f"   Explanation: {result_low['explanation']}")
    print(f"   ✅ Low-risk evaluation working")
    
    # Test 3: High-risk evaluation
    print(f"\n🔍 Test 3: High-risk evaluation")
    input_data_high = {
        "borrower": {"region": "Unknown"},
        "loan": {"amount": 150000}
    }
    
    result_high = detector.evaluate(input_data_high)
    
    print(f"   Input: {input_data_high}")
    print(f"   Result: {result_high}")
    
    # Verify fraud score is higher
    assert result_high["fraud_score"] > result_low["fraud_score"], "High-risk should have higher score"
    
    # Verify flags are present
    assert len(result_high["flags"]) > 0, "High-risk should have flags"
    
    # Verify explanations are present
    assert len(result_high["explanation"]) > 0, "High-risk should have explanations"
    
    print(f"   Fraud Score: {result_high['fraud_score']:.2f}")
    print(f"   Flags: {result_high['flags']}")
    print(f"   Explanation: {result_high['explanation']}")
    print(f"   ✅ High-risk evaluation working")
    
    # Test 4: Output format validation
    print(f"\n🔍 Test 4: Output format validation")
    
    def validate_output(result: Dict[str, Any]) -> bool:
        """Validate output format."""
        # Check required keys
        if not all(key in result for key in ["fraud_score", "flags", "explanation"]):
            return False
        
        # Check types
        if not isinstance(result["fraud_score"], (int, float)):
            return False
        if not isinstance(result["flags"], list):
            return False
        if not isinstance(result["explanation"], list):
            return False
        
        # Check fraud_score range
        if not (0.0 <= result["fraud_score"] <= 1.0):
            return False
        
        # Check list elements are strings
        if not all(isinstance(f, str) for f in result["flags"]):
            return False
        if not all(isinstance(e, str) for e in result["explanation"]):
            return False
        
        return True
    
    assert validate_output(result_low), "Low-risk output format invalid"
    assert validate_output(result_high), "High-risk output format invalid"
    
    print(f"   ✅ Output format validation passed")
    
    # Test 5: Legacy compatibility
    print(f"\n🔍 Test 5: Legacy compatibility check")
    from app.ai.fraud import BaseFraudDetector, FraudDetectionResult
    
    print(f"   BaseFraudDetector imported: {BaseFraudDetector is not None}")
    print(f"   FraudDetectionResult imported: {FraudDetectionResult is not None}")
    print(f"   ✅ Legacy classes still available")
    
    print(f"\n{'='*70}")
    print(f"✅ ALL TESTS PASSED")
    print(f"{'='*70}")
    print(f"""
Summary:
  ✅ FraudDetector abstract class working
  ✅ name property implemented correctly
  ✅ evaluate() method returns correct format
  ✅ Output contains fraud_score (0.0-1.0)
  ✅ Output contains flags (list[str])
  ✅ Output contains explanation (list[str])
  ✅ Legacy classes still available (backward compatibility)

Required Output Format:
{{
    "fraud_score": float,     # 0.0–1.0
    "flags": list[str],       # List of fraud flags
    "explanation": list[str]  # Human-readable explanations
}}

Example Output:
{result_high}
""")
    print("="*70)


if __name__ == "__main__":
    test_fraud_detector_interface()
