const params = new URLSearchParams(window.location.search);
export const token = params.get('token') || '';

// Use empty string to rely on the browser's current origin (relative path)
export const BASE_URL = '';

export const apiClient = async (endpoint: string, options: RequestInit = {}) => {
  const url = new URL(endpoint, window.location.origin);
  url.searchParams.append('token', token);

  const response = await fetch(url.toString(), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
};
