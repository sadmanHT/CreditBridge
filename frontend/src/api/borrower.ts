/**
 * SYSTEM ROLE:
 * You are implementing borrower-facing API calls
 * for a fintech frontend.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * CONSTRAINTS:
 * - Use Axios client
 * - JWT-authenticated
 */

import apiClient from './client';

export interface BorrowerDecision {
  loan_request_id: string;
  decision: 'approved' | 'rejected' | 'pending';
  score: number;
  timestamp: string;
  reasoning?: string;
}

export interface BorrowerDecisionsResponse {
  decisions: BorrowerDecision[];
  total: number;
}

export interface LoanExplanation {
  loan_request_id: string;
  decision: string;
  credit_score: number;
  summary: string;
  key_points: string[];
  language: string;
}

/**
 * Fetch borrower-related credit decisions
 * @returns Promise with list of borrower decisions
 */
export const fetchBorrowerDecisions = async (): Promise<BorrowerDecisionsResponse> => {
  const response = await apiClient.get<BorrowerDecisionsResponse>('/compliance/decisions');
  return response.data;
};

/**
 * Fetch detailed explanation for a specific loan decision
 * @param loanRequestId - The ID of the loan request
 * @param lang - Language code for explanation (default: 'en')
 * @returns Promise with loan explanation details
 */
export const fetchLoanExplanation = async (
  loanRequestId: string,
  lang: string = 'en'
): Promise<LoanExplanation> => {
  const response = await apiClient.get<LoanExplanation>(
    `/explanations/loan/${loanRequestId}`,
    {
      params: { lang }
    }
  );
  return response.data;
};

export interface LoanRequest {
  requested_amount: number;
  purpose: string;
}

export interface LoanRequestResponse {
  loan_request: {
    id: string;
    borrower_id: string;
    user_id: string;
    requested_amount: number;
    purpose: string;
    status: string;
    created_at: string;
    audit_logged: boolean;
  };
  credit_decision: {
    id: string;
    ai_signals: {
      base_credit_score: number;
      trust_score: number;
      trust_boost: number;
      final_credit_score: number;
      fraud_score: number;
      fraud_flags: string[];
      risk_level: string;
      flag_risk: boolean;
    };
    policy_decision: {
      decision: string;
      reasons: string[];
      policy_version: string;
    };
    explanation: any;
    model_version: string;
    created_at: string;
  };
  background_task_queued: boolean;
}

/**
 * Submit a new loan request
 * @param amount - The requested loan amount
 * @param purpose - The purpose of the loan
 * @returns Promise with loan request and credit decision
 */
export const submitLoanRequest = async (
  amount: number,
  purpose: string
): Promise<LoanRequestResponse> => {
  const response = await apiClient.post<LoanRequestResponse>('/loans/request', {
    requested_amount: amount,
    purpose: purpose
  });
  return response.data;
};
