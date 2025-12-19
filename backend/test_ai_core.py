from app.ai.registry import get_ensemble

ensemble = get_ensemble()

input_data = {
    "borrower": {"gender": "female", "region": "Dhaka"},
    "loan": {"requested_amount": 12000}
}

result = ensemble.run(input_data)
print(result.keys())
