export const API_URL = 'http://localhost:8000';

export const fetchWithAuth = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'applicaton/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = 'Bearer ${token}';
  }
  const response = await fetch('${API_URL}${endpoint}', {
    ...options, headers
  });
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
  return response;
};
