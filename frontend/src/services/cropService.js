import { apiClient } from './apiClient';

export const cropService = {
  getCrops: async () => {
    return await apiClient.get('/api/admin/crops');
  }
};
