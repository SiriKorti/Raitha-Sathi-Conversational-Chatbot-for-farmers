import { apiClient } from './apiClient';

/**
 * ⚠️ BACKEND DEPENDENT SERVICE:
 * The backend conversation memory manager currently persists diary events under
 * `data/user_profiles/{session_id}_profile.json`, but dedicated REST endpoints
 * (e.g. GET/POST /api/farm/diary/{userId}) have not yet been added to app/api/routes/farm.py.
 *
 * This client defines the contract so the UI is ready to hook up to the real API
 * without modifying UI components once the backend routes are exposed.
 */

export const diaryService = {
  getEntries: async (userId = 'user_123') => {
    try {
      return await apiClient.get(`/api/farm/diary/${userId}`);
    } catch (err) {
      console.warn('[diaryService] Backend REST API `/api/farm/diary` is not yet mounted on server.', err);
      // Return null to allow UI to show graceful "Backend Dependent" state
      return null;
    }
  },

  addEntry: async (userId = 'user_123', entryData) => {
    try {
      return await apiClient.post(`/api/farm/diary/${userId}`, entryData);
    } catch (err) {
      console.warn('[diaryService] Backend REST API `/api/farm/diary` is not yet mounted on server.', err);
      throw err;
    }
  }
};
