"""
Detailed test of production-grade ensemble engine
"""

from app.ai.ensemble import ModelEnsemble
import json

# Create ensemble
ensemble = ModelEnsemble()

# Test data
borrower = {
    'borrower_id': 'test-123',
    'region': 'Dhaka',
    'relationships': [
        {'peer_id': 'peer-1', 'interaction_count': 5, 'peer_defaulted': False},
        {'peer_id': 'peer-2', 'interaction_count': 3, 'peer_defaulted': False}
    ]
}
loan_request = {'requested_amount': 15000}

# Run ensemble
result = ensemble.predict(borrower, loan_request)

# Display results
print('='*70)
print('PRODUCTION-GRADE ENSEMBLE ENGINE TEST')
print('='*70)
print(f'\n[PRIMARY OUTPUTS]')
print(f'Final Credit Score: {result["final_credit_score"]}/100')
print(f'Fraud Flag: {result["fraud_flag"]}')
print(f'Decision: {result["decision"]}')
print(f'Risk Level: {result["risk_level"]}')

print(f'\n[METADATA]')
print(f'Ensemble Version: {result["ensemble_metadata"]["version"]}')
print(f'Models Used: {", ".join(result["ensemble_metadata"]["models_used"])}')
print(f'\nWeights:')
for model, weight in result["ensemble_metadata"]["weights"].items():
    print(f'  {model}: {weight:.2f}')

print(f'\n[PER-MODEL OUTPUTS]')
for model_name, output in result["model_outputs"].items():
    print(f'\n{model_name}:')
    print(f'  {json.dumps(output, indent=2)}')

print(f'\n[EXPLANATION]')
print(f'Ensemble Summary: {result["explanation"]["ensemble_summary"]}')

print('\n' + '='*70)
print('✓ ENSEMBLE ENGINE OPERATIONAL')
print('='*70)
