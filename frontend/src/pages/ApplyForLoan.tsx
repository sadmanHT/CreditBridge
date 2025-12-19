/**
 * Apply for Loan Page
 * 
 * Allows borrowers to submit loan requests with AI-powered instant decisions
 */

import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitLoanRequest } from '../api/loans';

export default function ApplyForLoan() {
  const navigate = useNavigate();
  const [amount, setAmount] = useState<string>('');
  const [purpose, setPurpose] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);
  const [decision, setDecision] = useState<any>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setSuccess(false);

    try {
      const amountNum = parseFloat(amount);
      if (isNaN(amountNum) || amountNum <= 0) {
        throw new Error('Please enter a valid loan amount');
      }

      if (!purpose.trim()) {
        throw new Error('Please specify the loan purpose');
      }

      const response = await submitLoanRequest(amountNum, purpose);
      setDecision(response.credit_decision);
      setSuccess(true);
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate('/dashboard/borrower');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit loan request');
    } finally {
      setLoading(false);
    }
  };

  // Success state
  if (success && decision) {
    const isApproved = decision.decision === 'approved';
    return (
      <div className="max-w-2xl mx-auto">
        <div className={`bg-white rounded-lg shadow-xl p-8 border-4 ${isApproved ? 'border-green-500' : 'border-red-500'}`}>
          <div className="text-center">
            {isApproved ? (
              <svg className="mx-auto h-24 w-24 text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="mx-auto h-24 w-24 text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            
            <h2 className={`text-3xl font-bold mb-4 ${isApproved ? 'text-green-700' : 'text-red-700'}`}>
              {isApproved ? 'Loan Approved!' : 'Loan Not Approved'}
            </h2>
            
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <p className="text-sm text-gray-600 mb-2">Credit Score</p>
              <p className="text-5xl font-bold text-gray-900">{decision.credit_score}</p>
            </div>
            
            <p className="text-gray-600 mb-6">
              {isApproved 
                ? 'Congratulations! Your loan application has been approved. Redirecting to dashboard...'
                : 'Your loan application was not approved at this time. You can view the detailed explanation in your dashboard.'}
            </p>
            
            <button
              onClick={() => navigate('/dashboard/borrower')}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 transition font-semibold"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Apply for a Loan</h1>
      <p className="text-gray-600 mb-6">Get an instant AI-powered credit decision</p>
      
      <div className="bg-white rounded-lg shadow-lg p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Loan Amount */}
          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
              Loan Amount (BDT) *
            </label>
            <input
              type="number"
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              min="1"
              step="1"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition text-lg"
              placeholder="e.g., 25000"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Enter the amount you wish to borrow</p>
          </div>

          {/* Loan Purpose */}
          <div>
            <label htmlFor="purpose" className="block text-sm font-medium text-gray-700 mb-2">
              Loan Purpose *
            </label>
            <select
              id="purpose"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
              disabled={loading}
            >
              <option value="">Select a purpose</option>
              <option value="business">Business</option>
              <option value="education">Education</option>
              <option value="medical">Medical</option>
              <option value="emergency">Emergency</option>
              <option value="home_improvement">Home Improvement</option>
              <option value="agriculture">Agriculture</option>
              <option value="personal">Personal</option>
              <option value="other">Other</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Why do you need this loan?</p>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">Instant AI Decision</p>
                <p>Your application will be processed instantly using our AI credit scoring system. You'll receive a decision within seconds.</p>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed text-lg"
          >
            {loading ? 'Processing...' : 'Submit Loan Application'}
          </button>
        </form>
      </div>
    </div>
  );
}
