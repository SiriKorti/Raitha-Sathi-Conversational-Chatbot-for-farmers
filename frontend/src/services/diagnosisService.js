/**
 * diagnosisService.js — Frontend API client for Visual Crop Diagnosis
 *
 * Routes multipart form requests to the isolated /api/vision/diagnose backend endpoint.
 */

import { apiClient } from './apiClient';

export const diagnosisService = {
  /**
   * Send a plant image and optional context to the backend for visual diagnosis.
   *
   * @param {File|Blob} imageFile - The selected or camera-captured image file.
   * @param {string} [cropName] - Optional name of the crop (e.g. Tomato, Ragi).
   * @param {string} [symptoms] - Optional symptom description or context.
   * @param {string} [language] - Target language ('kn' for Kannada, 'en' for English).
   * @returns {Promise<Object>} Structured diagnosis result from backend.
   */
  diagnoseImage: async (imageFile, cropName = '', symptoms = '', language = 'kn') => {
    if (!imageFile) {
      throw new Error('Please select or capture an image to analyze.');
    }

    const formData = new FormData();
    formData.append('image', imageFile);

    if (cropName && cropName.trim()) {
      formData.append('crop_name', cropName.trim());
    }
    if (symptoms && symptoms.trim()) {
      formData.append('symptoms', symptoms.trim());
    }
    if (language) {
      formData.append('language', language);
    }

    return await apiClient.postFormData('/api/vision/diagnose', formData, {
      timeoutMs: 40000, // Vision model reasoning timeout
    });
  },
};
