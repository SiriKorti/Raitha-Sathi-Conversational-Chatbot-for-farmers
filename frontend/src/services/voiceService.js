import { apiClient } from './apiClient';

export const voiceService = {
  transcribeAudio: async (audioBlob, language = 'kn') => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    if (language) {
      formData.append('language', language);
    }
    const data = await apiClient.postFormData('/api/voice/transcribe', formData);
    return data.text;
  },

  synthesizeAudio: async (text) => {
    const blob = await apiClient.post('/api/voice/synthesize', { text });
    return URL.createObjectURL(blob);
  }
};
