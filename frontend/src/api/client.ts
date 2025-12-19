/**
 * SYSTEM ROLE:
 * You are setting up a frontend API client
 * for a fintech dashboard application.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK FOR COPILOT AGENT:
 * Implement an Axios client that:
 * 1. Talks to FastAPI backend
 * 2. Attaches JWT token from localStorage
 * 3. Handles 401 errors cleanly
 *
 * CONSTRAINTS:
 * - No hardcoded tokens
 * - Backend base URL configurable
 *
 * OUTPUT:
 * - Reusable Axios instance
 */

import axios, { AxiosError } from 'axios';

// Base URL - configurable via environment variable
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Create Axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor - attach JWT token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 errors cleanly
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear stored token
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      
      // Redirect to login page if not already there
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
