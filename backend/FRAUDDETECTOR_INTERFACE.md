# FraudDetector Interface - Quick Reference

## Production-Grade Abstract Interface

### Definition
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class FraudDetector(ABC):
    """Abstract base class for fraud detection strategies."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get detector name for identification."""
        pass
    
    @abstractmethod
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk.
        
        REQUIRED OUTPUT FORMAT:
        {
            "fraud_score": float,     # 0.0–1.0
            "flags": list[str],       # Detected fraud flags
            "explanation": list[str]  # Human-readable explanations
        }
        """
        pass
```

## Usage Example

### Implementing a Custom Detector
```python
from app.ai.fraud import FraudDetector
from typing import Dict, Any

class MyFraudDetector(FraudDetector):
    """Custom fraud detector implementation."""
    
    @property
    def name(self) -> str:
        """Return detector name."""
        return "MyFraudDetector-v1.0"
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk.
        
        Args:
            input_data: Dict containing all input data
                       e.g., {"borrower": {...}, "loan": {...}}
        
        Returns:
            Dict with fraud_score, flags, and explanation
        """
        borrower = input_data.get("borrower", {})
        loan = input_data.get("loan", {})
        
        # Your fraud detection logic here
        fraud_score = 0.0
        flags = []
        explanation = []
        
        # Example: Check loan amount
        amount = loan.get("amount", 0)
        if amount > 100000:
            fraud_score += 0.5
            flags.append("high_amount")
            explanation.append(f"Loan amount {amount} exceeds threshold")
        
        # Example: Check region
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
```

### Using the Detector
```python
# Create detector instance
detector = MyFraudDetector()

# Get detector name
print(detector.name)  # Output: "MyFraudDetector-v1.0"

# Evaluate fraud risk
result = detector.evaluate({
    "borrower": {"region": "Unknown"},
    "loan": {"amount": 150000}
})

print(result)
# Output:
# {
#     "fraud_score": 0.8,
#     "flags": ["high_amount", "unknown_region"],
#     "explanation": [
#         "Loan amount 150000 exceeds threshold",
#         "Borrower region is unknown"
#     ]
# }
```

## Output Format Specification

### Required Keys
1. **fraud_score** (float)
   - Range: 0.0 to 1.0
   - 0.0 = No fraud risk
   - 1.0 = Maximum fraud risk

2. **flags** (list[str])
   - List of fraud flag identifiers
   - Examples: `["high_amount", "velocity_check", "fraud_ring"]`
   - Empty list if no flags detected

3. **explanation** (list[str])
   - Human-readable explanations
   - One explanation per detected issue
   - Examples:
     - `"Loan amount 150000 exceeds threshold"`
     - `"Multiple applications in short timeframe"`
     - `"High default rate in peer network"`

### Example Outputs

**Low Risk:**
```json
{
    "fraud_score": 0.0,
    "flags": [],
    "explanation": []
}
```

**Medium Risk:**
```json
{
    "fraud_score": 0.45,
    "flags": ["high_amount"],
    "explanation": ["Loan amount 75000 exceeds threshold"]
}
```

**High Risk:**
```json
{
    "fraud_score": 0.8,
    "flags": ["high_amount", "unknown_region", "suspicious_pattern"],
    "explanation": [
        "Loan amount 200000 exceeds threshold",
        "Borrower region is unknown",
        "Vague purpose for large loan"
    ]
}
```

## Requirements Checklist

✅ Abstract class `FraudDetector` using `abc.ABC`
✅ Required property: `name` (returns str)
✅ Required method: `evaluate(input_data: dict) -> dict`
✅ Output includes `fraud_score` (float, 0.0–1.0)
✅ Output includes `flags` (list[str])
✅ Output includes `explanation` (list[str])
✅ No implementation logic in base class
✅ Clean Python code

## Legacy Support

For backward compatibility, the following classes are still available:
- `BaseFraudDetector` - Legacy abstract base class
- `FraudDetectionResult` - Legacy result dataclass

New code should use `FraudDetector` interface defined above.

## Files

- **base.py** - FraudDetector abstract class + legacy classes
- **rule_engine.py** - Rule-based fraud detector (legacy)
- **trustgraph_adapter.py** - Trust graph fraud detector (legacy)
- **engine.py** - Fraud detection engine (legacy)

## Integration

```python
from app.ai.fraud import FraudDetector

# Implement your detector
class MyDetector(FraudDetector):
    @property
    def name(self) -> str:
        return "MyDetector-v1.0"
    
    def evaluate(self, input_data: dict) -> dict:
        return {
            "fraud_score": 0.5,
            "flags": ["flag1"],
            "explanation": ["Explanation 1"]
        }

# Use it
detector = MyDetector()
result = detector.evaluate({"borrower": {...}, "loan": {...}})
```
