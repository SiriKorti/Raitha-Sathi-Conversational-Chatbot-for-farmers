import { useState, useRef, useCallback, useEffect } from 'react';
import { voiceService } from '../services/voiceService';

/**
 * Custom hook for Text-to-Speech audio synthesis and playback.
 * Calls the real backend /api/voice/synthesize, manages HTML5 Audio element,
 * tracks playing ID, loading state, and revokes Blob Object URLs on unmount.
 */
export const useAudioPlayer = () => {
  const [playingMessageId, setPlayingMessageId] = useState(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [audioError, setAudioError] = useState(null);

  const audioRef = useRef(null);
  const currentObjectUrlRef = useRef(null);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (currentObjectUrlRef.current) {
      URL.revokeObjectURL(currentObjectUrlRef.current);
      currentObjectUrlRef.current = null;
    }
    setPlayingMessageId(null);
    setIsLoadingAudio(false);
  }, []);

  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [stopAudio]);

  const playText = useCallback(
    async (messageId, text) => {
      if (!text || !text.trim()) return;

      // If already playing this message, toggle stop
      if (playingMessageId === messageId) {
        stopAudio();
        return;
      }

      // Stop any existing audio first
      stopAudio();
      setAudioError(null);
      setPlayingMessageId(messageId);
      setIsLoadingAudio(true);

      try {
        const objectUrl = await voiceService.synthesizeAudio(text);
        currentObjectUrlRef.current = objectUrl;

        const audio = new Audio(objectUrl);
        audioRef.current = audio;

        audio.onended = () => {
          stopAudio();
        };

        audio.onerror = (e) => {
          console.error('Audio playback error:', e);
          setAudioError('Audio playback failed.');
          stopAudio();
        };

        setIsLoadingAudio(false);
        await audio.play();
      } catch (err) {
        console.error('Failed to synthesize audio:', err);
        setAudioError(err.message || 'Failed to synthesize speech.');
        stopAudio();
      }
    },
    [playingMessageId, stopAudio]
  );

  return {
    playingMessageId,
    isLoadingAudio,
    audioError,
    playText,
    stopAudio,
  };
};
