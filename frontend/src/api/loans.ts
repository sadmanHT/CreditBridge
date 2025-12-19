/**
 * Loan API functions for CreditBridge Frontend
 */

import apiClient from './client';

export interface LoanRequest {
  requested_amount: number;
  purpose: string;
}

export interface LoanRequestResponse {
  loan_request: {
    id: string;
    borrower_id: string;
    requested_amount: number;
    purpose: string;
    status: string;
    created_at: string;
  };
  credit_decision: {
    id: string;
    loan_request_id: string;
    credit_score: number;
    decision: 'approved' | 'rejected';
    explanation: string;
    created_at: string;
  };
  background_task_queued: boolean;
}

/**
 * Submit a new loan request
 * @param requestedAmount - Amount requested in BDT
 * @param purpose - Purpose of the loan
 * @returns Promise with loan request and credit decision
 */
export const submitLoanRequest = async (
  requestedAmount: number,
  purpose: string
): Promise<LoanRequestResponse> => {
  const response = await apiClient.post<LoanRequestResponse>('/loans/request', {
    requested_amount: requestedAmount,
    purpose: purpose,
  });
  
  return response.data;
};
