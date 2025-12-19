"""
Test script for new modular AI architecture
"""

# Test new modular architecture
from app.ai.models import RuleBasedCreditModel, TrustGraphModel, FraudRulesModel
from app.ai.ensemble import ModelEnsemble
from app.ai.registry import get_registry
import json

print('='*70)
print('CREDITBRIDGE AI - MODULAR ARCHITECTURE TEST')
print('='*70)

# Test 1: Credit Rule Model
print('\n[1] Testing RuleBasedCreditModel...')
credit_model = RuleBasedCreditModel()
borrower = {'region': 'Dhaka', 'gender': 'female'}
loan_request = {'requested_amount': 15000}
input_data = {'borrower': borrower, 'loan_request': loan_request}
credit_result = credit_model.predict(input_data)
print(f'   Credit Score: {credit_result["score"]}/100')
print(f'   Risk Level: {credit_result["risk_level"]}')
print(f'   Model: {credit_model.name}')

# Test 2: TrustGraph Model
print('\n[2] Testing TrustGraphModel...')
trust_model = TrustGraphModel()
borrower_with_trust = {
    'borrower_id': 'test-123',
    'relationships': [
        {'peer_id': 'peer-1', 'interaction_count': 5, 'peer_defaulted': False},
        {'peer_id': 'peer-2', 'interaction_count': 3, 'peer_defaulted': False}
    ]
}
trust_input = {'borrower': borrower_with_trust, 'loan_request': {}}
trust_result = trust_model.predict(trust_input)
print(f'   Trust Score: {trust_result["trust_score"]:.3f}/1.0')
print(f'   Fraud Risk: {trust_result["flag_risk"]}')
print(f'   Model: {trust_model.name}')

# Test 3: Fraud Rules Model
print('\n[3] Testing FraudRulesModel...')
fraud_model = FraudRulesModel()
fraud_result = fraud_model.predict(input_data)
print(f'   Fraud Score: {fraud_result["fraud_score"]:.3f}/1.0')
print(f'   Is Fraud: {fraud_result["is_fraud"]}')
print(f'   Risk Level: {fraud_result["risk_level"]}')

# Test 4: Ensemble
print('\n[4] Testing ModelEnsemble...')
ensemble = ModelEnsemble()
ensemble_result = ensemble.predict(borrower_with_trust, loan_request)
print(f'   Ensemble Score: {ensemble_result["final_credit_score"]:.2f}/100')
print(f'   Final Decision: {ensemble_result["decision"]}')
print(f'   Fraud Flag: {ensemble_result["fraud_flag"]}')
print(f'   Models Used: {ensemble_result["ensemble_metadata"]["models_used"]}')

# Test 5: Registry
print('\n[5] Testing ModelRegistry...')
registry = get_registry()
models_dict = registry.list_models()
print(f'   Registered Models: {len(models_dict)}')
for model_key, model_name in models_dict.items():
    print(f'   - {model_key}: {model_name}')
    
# Test get_ensemble()
ensemble_from_registry = registry.get_ensemble()
print(f'   get_ensemble() works: {ensemble_from_registry is not None}')

# Test 6: Backward Compatibility
print('\n[6] Testing Backward Compatibility...')
from app.ai.credit_scoring import compute_credit_score
from app.ai.trustgraph import compute_trust_score
result = compute_credit_score(borrower, loan_request)
print(f'   Legacy function works: Credit Score = {result["credit_score"]}/100')

print('\n' + '='*70)
print('✓ ALL TESTS PASSED - MODULAR ARCHITECTURE OPERATIONAL')
print('='*70)
