import { apiClient } from './apiClient';

export const authService = {
  login: async (credentials) => {
    try {
      return await apiClient.post('/api/auth/login', credentials);
    } catch (err) {
      console.warn('[authService] Login error:', err);
      throw err;
    }
  },

  register: async (userData) => {
    try {
      return await apiClient.post('/api/auth/register', userData);
    } catch (err) {
      console.warn('[authService] Register error:', err);
      throw err;
    }
  },

  logout: async () => {
    try {
      return await apiClient.post('/api/auth/logout', {});
    } catch (err) {
      console.warn('[authService] Logout error:', err);
      return { status: 'success' };
    }
  },

  deleteAccount: async (identifier) => {
    try {
      return await apiClient.delete(`/api/auth/account/${encodeURIComponent(identifier)}`);
    } catch (err) {
      console.warn('[authService] Delete account error:', err);
      throw err;
    }
  },

  forgotPassword: async (email) => {
    try {
      return await apiClient.post('/api/auth/forgot-password', { email });
    } catch (err) {
      console.warn('[authService] Forgot password error:', err);
      throw err;
    }
  },

  getCurrentUser: async () => {
    try {
      return await apiClient.get('/api/auth/me');
    } catch {
      return null;
    }
  }
};
