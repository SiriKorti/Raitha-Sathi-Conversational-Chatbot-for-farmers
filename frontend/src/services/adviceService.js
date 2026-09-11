import { apiClient } from './apiClient';

export const adviceService = {
  /**
   * Fetch all saved advice records for a user, sorted newest first.
   * @param {string} userId
   * @returns {Promise<{status: string, user_id: string, count: number, advice: Array}>}
   */
  getSavedAdvice: async (userId = 'user_123') => {
    return await apiClient.get(`/api/farm/advice/saved/${userId}`);
  },

  /**
   * Persist an already-generated advice record under a user.
   * @param {string} userId
   * @param {{ content: string, user_query?: string, crop?: string, topic?: string, source?: string, provider?: string }} advicePayload
   * @returns {Promise<{status: string, message: string, data: object}>}
   */
  saveAdvice: async (userId = 'user_123', advicePayload) => {
    return await apiClient.post(`/api/farm/advice/saved/${userId}`, advicePayload);
  },

  /**
   * Delete a saved advice record by ID for a user.
   * @param {string} userId
   * @param {string} adviceId
   * @returns {Promise<{status: string, message: string, advice_id: string}>}
   */
  deleteSavedAdvice: async (userId = 'user_123', adviceId) => {
    return await apiClient.delete(`/api/farm/advice/saved/${userId}/${adviceId}`);
  },
};
