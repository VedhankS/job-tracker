
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Deployed backend URLs
const AUTH_API_URL = "https://job-tracker-r0ko.onrender.com";
const JOBS_API_URL = "https://job-tracker-api-0uwo.onrender.com";
const AI_API_URL = "https://job-tracker-ai-exzg.onrender.com";

// Default API URL for compatibility
const API_BASE = JOBS_API_URL;

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(
    localStorage.getItem('token') || null
  );

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  const login = (newToken) => setToken(newToken);

  const logout = () => setToken(null);

  // Route requests to the correct deployed backend
  const authFetch = async (endpoint, options = {}) => {
    let baseURL;

    if (endpoint.startsWith('/ai/')) {
      baseURL = AI_API_URL;
    } else {
      baseURL = JOBS_API_URL;
    }

    const isFormData =
      typeof FormData !== 'undefined' &&
      options.body instanceof FormData;

    const headers = {
      ...(isFormData
        ? {}
        : { 'Content-Type': 'application/json' }),
      ...(token
        ? { 'Authorization': `Bearer ${token}` }
        : {}),
      ...options.headers,
    };

    const response = await fetch(
      `${baseURL}${endpoint}`,
      {
        ...options,
        headers,
      }
    );

    if (response.status === 401) {
      logout();
      throw new Error("Session expired. Please log in again");
    }

    return response;
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        login,
        logout,
        authFetch,
        API_BASE,
        AUTH_API_URL,
        JOBS_API_URL,
        AI_API_URL,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
