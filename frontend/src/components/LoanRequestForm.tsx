/**
 * SYSTEM ROLE:
 * You are building a borrower loan request form.
 *
 * PROJECT:
 * CreditBridge Frontend
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { submitLoanRequest } from '../api/borrower';

export default function LoanRequestForm() {
  const [amount, setAmount] = useState('');
  const [purpose, setPurpose] = useState('');
  const [error, setError] = useState('');
  
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ amount, purpose }: { amount: number; purpose: string }) =>
      submitLoanRequest(amount, purpose),
    onSuccess: () => {
      // Invalidate borrower decisions to refresh dashboard
      queryClient.invalidateQueries({ queryKey: ['borrowerDecisions'] });
      
      // Reset form
      setAmount('');
      setPurpose('');
      setError('');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to submit loan request');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const amountNum = parseFloat(amount);
    
    if (!amount || amountNum <= 0) {
      setError('Please enter a valid loan amount greater than 0');
      return;
    }

    if (!purpose.trim()) {
      setError('Please enter the purpose of the loan');
      return;
    }

    mutation.mutate({ amount: amountNum, purpose: purpose.trim() });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Apply for a Loan</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Loan Amount */}
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
            Loan Amount (BDT)
          </label>
          <input
            type="number"
            id="amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Enter amount"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={mutation.isPending}
          />
        </div>

        {/* Purpose */}
        <div>
          <label htmlFor="purpose" className="block text-sm font-medium text-gray-700 mb-2">
            Purpose
          </label>
          <select
            id="purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={mutation.isPending}
          >
            <option value="">Select purpose</option>
            <option value="Business">Business</option>
            <option value="Education">Education</option>
            <option value="Medical">Medical</option>
            <option value="Emergency">Emergency</option>
            <option value="Home Improvement">Home Improvement</option>
            <option value="Agriculture">Agriculture</option>
            <option value="Personal">Personal</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Success Message */}
        {mutation.isSuccess && mutation.data && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            <p className="font-semibold">Loan request submitted successfully!</p>
            {mutation.data.credit_decision && (
              <>
                <p className="text-sm mt-1">
                  Credit Score: <span className="font-bold">{mutation.data.credit_decision.ai_signals?.final_credit_score || 'N/A'}</span>
                </p>
                <p className="text-sm">
                  Decision: <span className="font-bold capitalize">{mutation.data.credit_decision.policy_decision?.decision || 'pending'}</span>
                </p>
                <p className="text-sm">
                  Risk Level: <span className="font-bold capitalize">{mutation.data.credit_decision.ai_signals?.risk_level || 'N/A'}</span>
                </p>
                {mutation.data.credit_decision.ai_signals?.fraud_score !== undefined && (
                  <p className="text-sm">
                    Fraud Score: <span className="font-bold">{mutation.data.credit_decision.ai_signals.fraud_score.toFixed(2)}</span>
                  </p>
                )}
              </>
            )}
            {mutation.data.loan_request && (
              <p className="text-xs mt-2 text-green-600">
                Request ID: {mutation.data.loan_request.id}
              </p>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {mutation.isPending ? 'Submitting...' : 'Submit Loan Request'}
        </button>
      </form>
    </div>
  );
}
