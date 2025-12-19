/**
 * SYSTEM ROLE:
 * You are implementing frontend authentication
 * for a fintech application.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK FOR COPILOT AGENT:
 * Implement a login API function that:
 * 1. Calls POST /api/v1/auth/login
 * 2. Accepts email + password
 * 3. Returns access_token
 *
 * CONSTRAINTS:
 * - Use Axios client
 * - No hardcoded URLs
 *
 * OUTPUT:
 * - login(email, password) function
 */

import apiClient from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
  };
}

/**
 * Login user with email and password
 * @param email - User email address
 * @param password - User password
 * @returns Promise with access token and user data
 */
export const login = async (email: string, password: string): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/login', {
    email,
    password,
  });
  
  return response.data;
};

/**
 * Store authentication token in localStorage
 * @param token - JWT access token
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

/**
 * Get authentication token from localStorage
 * @returns JWT access token or null
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Remove authentication token from localStorage
 */
export const clearAuthToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};

/**
 * Check if user is authenticated
 * @returns true if token exists
 */
export const isAuthenticated = (): boolean => {
  return getAuthToken() !== null;
};
