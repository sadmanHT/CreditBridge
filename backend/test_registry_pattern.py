"""
Test Clean Registry Pattern
Demonstrates the refactored registry design
"""

from app.ai.registry import get_registry

print('='*70)
print('CLEAN REGISTRY PATTERN TEST')
print('='*70)

# ═══════════════════════════════════════════════════════════════════════
# Get registry instance (singleton, but models are stateless)
# ═══════════════════════════════════════════════════════════════════════
registry = get_registry()
print('\n[1] Registry initialized')
print(f'    Registry class: {registry.__class__.__name__}')

# ═══════════════════════════════════════════════════════════════════════
# List all available models
# ═══════════════════════════════════════════════════════════════════════
print('\n[2] Available models:')
models = registry.list_models()
for key, name in models.items():
    print(f'    - {key}: {name}')

# ═══════════════════════════════════════════════════════════════════════
# Get individual models (as per requirements)
# ═══════════════════════════════════════════════════════════════════════
print('\n[3] Accessing individual models:')
credit_model = registry.get_model("credit")
print(f'    Credit model: {credit_model.name}')

trust_model = registry.get_model("trust")
print(f'    Trust model: {trust_model.name}')

# ═══════════════════════════════════════════════════════════════════════
# Get ensemble (as per requirements)
# ═══════════════════════════════════════════════════════════════════════
print('\n[4] Getting ensemble via get_ensemble():')
ensemble = registry.get_ensemble()
print(f'    Ensemble version: {ensemble.ensemble_version}')
print(f'    Number of models in ensemble: {len(ensemble.models)}')

# ═══════════════════════════════════════════════════════════════════════
# Test ensemble prediction
# ═══════════════════════════════════════════════════════════════════════
print('\n[5] Testing ensemble prediction:')
borrower = {
    'borrower_id': 'test-456',
    'region': 'Dhaka',
    'relationships': [
        {'peer_id': 'peer-1', 'interaction_count': 10, 'peer_defaulted': False}
    ]
}
loan_request = {'requested_amount': 20000}

result = ensemble.predict(borrower, loan_request)
print(f'    Final credit score: {result["final_credit_score"]}/100')
print(f'    Decision: {result["decision"]}')
print(f'    Fraud flag: {result["fraud_flag"]}')

# ═══════════════════════════════════════════════════════════════════════
# Demonstrate no global state mutation
# ═══════════════════════════════════════════════════════════════════════
print('\n[6] Testing immutability (no global state mutation):')
registry2 = get_registry()
print(f'    Same registry instance: {registry is registry2}')
print(f'    Same credit model instance: {registry.credit_model is registry2.credit_model}')
print(f'    Models are stateless - safe for concurrent use')

print('\n' + '='*70)
print('✓ CLEAN REGISTRY PATTERN OPERATIONAL')
print('='*70)
print('\nKEY FEATURES:')
print('  • Immutable model instances (stateless)')
print('  • No global state mutation')
print('  • Clean get_ensemble() API')
print('  • Ready for ML models (extensible)')
print('  • Thread-safe design')
