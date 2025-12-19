from app.ai.explainability import TrustGraphExplainer
import json

explainer = TrustGraphExplainer()

# Test 1: Normal scenario
print("=" * 60)
print("Test 1: Normal Peer Network")
print("=" * 60)
input_data = {
    'borrower': {
        'peers': [
            {'peer_id': 'P1', 'repaid': True, 'interactions': 12},
            {'peer_id': 'P2', 'repaid': True, 'interactions': 8},
            {'peer_id': 'P3', 'repaid': False, 'interactions': 5}
        ]
    }
}
model_output = {'trust_score': 0.75, 'flag_risk': False}
result = explainer.explain(input_data, model_output)

print(f"Type: {result.get('type')}")
print(f"Trust Score: {result.get('trust_score')}")
print(f"Risk Flag: {result.get('risk_flag')}")
print(f"Confidence: {result.get('confidence')}")
print("\nGraph Insights:")
for insight in result.get('graph_insights', []):
    print(f"  - {insight['insight']} ({insight['impact']})")

# Test 2: Fraud ring scenario
print("\n" + "=" * 60)
print("Test 2: Fraud Ring Detection")
print("=" * 60)
input_data_fraud = {
    'borrower': {
        'peers': [
            {'peer_id': 'P1', 'repaid': False, 'interactions': 5},
            {'peer_id': 'P2', 'repaid': False, 'interactions': 3}
        ]
    }
}
model_output_fraud = {'trust_score': 0.3, 'flag_risk': True}
result_fraud = explainer.explain(input_data_fraud, model_output_fraud)

print(f"Type: {result_fraud.get('type')}")
print(f"Trust Score: {result_fraud.get('trust_score')}")
print(f"Risk Flag: {result_fraud.get('risk_flag')}")
print(f"Confidence: {result_fraud.get('confidence')}")
print("\nGraph Insights:")
for insight in result_fraud.get('graph_insights', []):
    print(f"  - {insight['insight']} ({insight['impact']})")
    if 'alert' in insight:
        print(f"    ⚠️  ALERT: {insight['alert']}")

# Test 3: No peers
print("\n" + "=" * 60)
print("Test 3: No Peer Network")
print("=" * 60)
input_data_no_peers = {'borrower': {'peers': []}}
model_output_no_peers = {'trust_score': 0.5, 'flag_risk': False}
result_no_peers = explainer.explain(input_data_no_peers, model_output_no_peers)

print(f"Type: {result_no_peers.get('type')}")
print(f"Trust Score: {result_no_peers.get('trust_score')}")
print(f"Confidence: {result_no_peers.get('confidence')}")
print("\nGraph Insights:")
for insight in result_no_peers.get('graph_insights', []):
    print(f"  - {insight['insight']} ({insight['impact']})")

print("\n" + "=" * 60)
print("✓ All TrustGraphExplainer tests completed")
print("=" * 60)
