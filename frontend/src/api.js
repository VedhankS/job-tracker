export const API_URL = '';

export const fetchWithAuth = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
  return response;
};
