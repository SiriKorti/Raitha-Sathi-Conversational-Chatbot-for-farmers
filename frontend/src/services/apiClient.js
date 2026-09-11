/**
 * Centralized API Client for Raitha Sathi Backend (FastAPI :8000)
 * All network calls in frontend-new must route through this client.
 */

const DEFAULT_TIMEOUT_MS = 90000;

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function request(endpoint, options = {}) {
  const {
    method = 'GET',
    body = null,
    headers = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    isFormData = false,
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const requestHeaders = { ...headers };
  const token = localStorage.getItem('raitha_auth_token');
  if (token && !requestHeaders['Authorization'] && !requestHeaders['authorization']) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    method,
    signal: controller.signal,
    headers: requestHeaders,
  };

  if (body) {
    if (isFormData) {
      config.body = body;
    } else {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(body);
    }
  }

  try {
    const url = endpoint.startsWith('http') ? endpoint : endpoint;
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    // Handle Blob or binary responses (like MP3 TTS)
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('audio/') || contentType.includes('application/octet-stream')) {
      if (!response.ok) {
        throw new ApiError(`Audio request failed with status ${response.status}`, response.status);
      }
      return await response.blob();
    }

    // Parse JSON
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const errorMessage = data?.detail || data?.message || `Server error (${response.status})`;
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out. Please check your connection.', 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Network connection failed. Is the backend running?', 0);
  }
}

export const apiClient = {
  get: (endpoint, headers = {}) => request(endpoint, { method: 'GET', headers }),
  post: (endpoint, body, headers = {}) => request(endpoint, { method: 'POST', body, headers }),
  delete: (endpoint, headers = {}) => request(endpoint, { method: 'DELETE', headers }),
  postFormData: (endpoint, formData, headers = {}) => request(endpoint, { method: 'POST', body: formData, isFormData: true, headers }),
  
  // Health check for system telemetry
  checkHealth: async () => {
    try {
      return await request('/health', { timeoutMs: 4000 });
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  }
};
