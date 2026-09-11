import { apiClient } from './apiClient';

export const chatService = {
  createNewSession: async () => {
    const data = await apiClient.post('/api/chat/new');
    return data.session_id;
  },

  sendMessage: async ({ sessionId, message, language = 'kn', isVoiceMode = false }) => {
    return await apiClient.post('/api/chat', {
      session_id: sessionId,
      message,
      language,
      is_voice_mode: isVoiceMode,
    });
  },

  getHistory: async (sessionId) => {
    return await apiClient.get(`/api/chat/history/${sessionId}`);
  },

  getSessions: async () => {
    return await apiClient.get('/api/chat/sessions');
  },

  closeSession: async (sessionId) => {
    return await apiClient.delete(`/api/chat/session/${sessionId}`);
  },

  getActiveCount: async () => {
    return await apiClient.get('/api/chat/sessions/count');
  }
};
