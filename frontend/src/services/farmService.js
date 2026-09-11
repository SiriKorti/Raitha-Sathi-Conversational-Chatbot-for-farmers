import { apiClient } from './apiClient';

export const farmService = {
  getProfile: async (userId = 'user_123') => {
    return await apiClient.get(`/api/farm/profile/${userId}`);
  },

  saveProfile: async (userId = 'user_123', profileData) => {
    return await apiClient.post(`/api/farm/profile/${userId}`, profileData);
  },

  getProgress: async (userId = 'user_123') => {
    return await apiClient.get(`/api/farm/progress/${userId}`);
  },

  saveProgress: async (userId = 'user_123', cropProgressData) => {
    return await apiClient.post(`/api/farm/progress/${userId}`, cropProgressData);
  },

  deleteCrop: async (userId = 'user_123', cropName) => {
    return await apiClient.delete(`/api/farm/progress/${userId}/${encodeURIComponent(cropName)}`);
  }
};


