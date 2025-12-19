/**
 * SYSTEM ROLE:
 * You are implementing auth helpers.
 *
 * TASK FOR COPILOT AGENT:
 * Implement helper functions:
 * - setToken(token)
 * - getToken()
 * - logout()
 *
 * Use localStorage
 */

/**
 * Store authentication token in localStorage
 * @param token - JWT access token
 */
export const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

/**
 * Retrieve authentication token from localStorage
 * @returns JWT access token or null if not found
 */
export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Remove authentication token and user data from localStorage
 * Effectively logs out the user
 */
export const logout = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};

/**
 * Check if user is currently authenticated
 * @returns true if token exists, false otherwise
 */
export const isLoggedIn = (): boolean => {
  return getToken() !== null;
};
