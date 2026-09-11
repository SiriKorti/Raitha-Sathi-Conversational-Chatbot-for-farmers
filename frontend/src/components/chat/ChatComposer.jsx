import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Mic, Square, X, AlertCircle } from 'lucide-react';
import { useAudioRecorder } from '../../utils/useAudioRecorder';
import { voiceService } from '../../services/voiceService';
import { useToast } from '../../context/ToastContext';
import { useLanguage } from '../../context/LanguageContext';
import './ChatComposer.css';

export const ChatComposer = ({ onSendMessage, isLoading, placeholder }) => {
  const { language } = useLanguage();
  const [inputText, setInputText] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const textareaRef = useRef(null);
  const { showToast } = useToast();

  const {
    isRecording,
    recordingDuration,
    error: recorderError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecorder();

  const recognitionRef = useRef(null);
  const [isWebSpeechActive, setIsWebSpeechActive] = useState(false);
  const [interimSpeech, setInterimSpeech] = useState('');
  const baseSpeechRef = useRef('');

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [inputText]);

  // Clean up recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  const handleSend = () => {
    const trimmed = inputText.trim();
    if (!trimmed || isLoading || isRecording || isWebSpeechActive || isTranscribing) return;
    onSendMessage(trimmed);
    setInputText('');
    baseSpeechRef.current = '';
    setInterimSpeech('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startFallbackRecording = async () => {
    try {
      await startRecording();
    } catch (err) {
      showToast(err.message || 'Microphone access failed.', 'error');
    }
  };

  const handleStartMic = async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language === 'kn' ? 'kn-IN' : 'en-IN';

        baseSpeechRef.current = inputText.trim() ? `${inputText.trim()} ` : '';
        setInterimSpeech('');

        recognition.onstart = () => {
          setIsWebSpeechActive(true);
        };

        recognition.onresult = (event) => {
          let interim = '';
          let final = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0]?.transcript || '';
            if (event.results[i].isFinal) {
              final += transcript;
            } else {
              interim += transcript;
            }
          }
          if (final) {
            baseSpeechRef.current += (baseSpeechRef.current ? '' : '') + final.trim() + ' ';
            setInputText(baseSpeechRef.current.trim());
          }
          setInterimSpeech(interim);
        };

        recognition.onerror = (event) => {
          console.warn('Web Speech error, using audio recorder fallback:', event.error);
          setIsWebSpeechActive(false);
          setInterimSpeech('');
          if (event.error !== 'aborted' && event.error !== 'no-speech') {
            startFallbackRecording();
          }
        };

        recognition.onend = () => {
          setIsWebSpeechActive(false);
          setInterimSpeech('');
        };

        recognitionRef.current = recognition;
        recognition.start();
        return;
      } catch (err) {
        console.warn('SpeechRecognition initialization failed:', err);
      }
    }

    // Fallback for browsers without native Web Speech API
    startFallbackRecording();
  };

  const handleStopMic = async () => {
    if (isWebSpeechActive && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsWebSpeechActive(false);
      setInterimSpeech('');
      showToast(
        language === 'kn' ? 'ಧ್ವನಿ ತಕ್ಷಣ ದಾಖಲಾಗಿದೆ!' : 'Voice captured in real time!',
        'success'
      );
      return;
    }

    // MediaRecorder Fallback
    try {
      setIsTranscribing(true);
      const audioBlob = await stopRecording();
      if (audioBlob && audioBlob.size > 0) {
        showToast(language === 'kn' ? 'ಧ್ವನಿ ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ...' : 'Transcribing speech...', 'info');
        const transcribedText = await voiceService.transcribeAudio(audioBlob, language);
        if (transcribedText && transcribedText.trim()) {
          setInputText((prev) => {
            const prefix = prev.trim() ? `${prev.trim()} ` : '';
            return `${prefix}${transcribedText.trim()}`;
          });
          showToast(language === 'kn' ? 'ಧ್ವನಿ ಪಠ್ಯಕ್ಕೆ ಪರಿವರ್ತನೆಯಾಗಿದೆ!' : 'Speech transcribed!', 'success');
        } else {
          showToast(language === 'kn' ? 'ಯಾವುದೇ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ.' : 'No speech detected.', 'warning');
        }
      }
    } catch (err) {
      console.error('STT failed:', err);
      showToast(err.message || 'Failed to transcribe speech.', 'error');
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleCancelMic = () => {
    if (isWebSpeechActive && recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // ignore
      }
      setIsWebSpeechActive(false);
      setInterimSpeech('');
    }
    cancelRecording();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const isVoiceActive = isRecording || isWebSpeechActive;
  const isOverLimit = inputText.length > 2000;
  const canSend = inputText.trim().length > 0 && !isLoading && !isOverLimit && !isVoiceActive && !isTranscribing;

  return (
    <div className="chat-composer-container">
      {/* Voice Recording Active Overlay */}
      {isVoiceActive && (
        <div className="recording-overlay glass-panel">
          <div className="recording-status">
            <span className="recording-pulse-dot" />
            <span className="recording-text">
              {interimSpeech
                ? `🎙️ ${interimSpeech}`
                : language === 'kn'
                ? 'ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಆಗುತ್ತಿದೆ... ಮಾತನಾಡಿ'
                : 'Listening live... Speak now'}
            </span>
            {isRecording && <span className="recording-timer">{formatTime(recordingDuration)}</span>}
          </div>

          <div className="recording-actions">
            <button
              type="button"
              className="recording-cancel-btn"
              onClick={handleCancelMic}
              title="Cancel recording"
            >
              <X size={16} />
              <span>Cancel</span>
            </button>

            <button
              type="button"
              className="recording-stop-btn"
              onClick={handleStopMic}
              title="Stop and transcribe"
            >
              <Square size={14} className="stop-icon" />
              <span>Done / ಮುಗಿಸಿ</span>
            </button>
          </div>
        </div>
      )}

      {/* Transcribing Status Indicator (used only during fallback) */}
      {isTranscribing && (
        <div className="transcribing-banner glass-panel">
          <span className="composer-spinner" />
          <span>{language === 'kn' ? 'ಧ್ವನಿ ಪಠ್ಯಕ್ಕೆ ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ...' : 'Converting voice to text...'}</span>
        </div>
      )}

      {/* Main Composer Box */}
      <div className={`composer-box ${isVoiceActive ? 'hidden' : ''} ${isOverLimit ? 'has-error' : ''}`}>
        <textarea
          ref={textareaRef}
          className="composer-textarea"
          rows={1}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            placeholder ||
            (language === 'kn'
              ? 'ನಿಮ್ಮ ಬೆಳೆ, ಕೃಷಿ ಚಿಂತೆಗಳು ಅಥವಾ ಯಾವುದೇ ಪ್ರಶ್ನೆಯನ್ನು ಸಾಥಿ ಬಳಿ ಕೇಳಿ...'
              : 'Ask about your crops, farming decisions, or talk to Sathi...')
          }
          disabled={isLoading || isTranscribing}
          aria-label="Ask Sathi message input"
        />

        <div className="composer-bottom-toolbar">
          <div className="toolbar-left">
            {/* Mic STT Button */}
            <button
              type="button"
              className="composer-btn mic-btn"
              onClick={handleStartMic}
              disabled={isLoading || isTranscribing}
              title={language === 'kn' ? 'ಧ್ವನಿ ಮೂಲಕ ಮಾತನಾಡಿ' : 'Speak in Kannada or English'}
              aria-label="Voice input"
            >
              <Mic size={18} />
              <span className="mic-btn-label">{language === 'kn' ? 'ಧ್ವನಿ' : 'Voice'}</span>
            </button>

            {/* Character counter */}
            {inputText.length > 500 && (
              <span className={`char-counter ${isOverLimit ? 'limit-exceeded' : ''}`}>
                {inputText.length}/2000
              </span>
            )}
          </div>

          <div className="toolbar-right">
            {/* Send Button */}
            <button
              type="button"
              className={`composer-btn send-btn ${canSend ? 'active' : ''}`}
              onClick={handleSend}
              disabled={!canSend}
              title={language === 'kn' ? 'ಕಳುಹಿಸಿ (Enter)' : 'Send message (Enter)'}
              aria-label="Send message"
            >
              {isLoading ? <span className="composer-spinner" /> : <ArrowUp size={18} strokeWidth={2.5} />}
            </button>
          </div>
        </div>
      </div>

      <div className="composer-sub-hint">
        {language === 'kn' ? (
          <span>ಕಳುಹಿಸಲು <strong>Enter ↵</strong> ಒತ್ತಿ, ಹೊಸ ಸಾಲಿಗೆ <strong>Shift + Enter</strong> ಒತ್ತಿ</span>
        ) : (
          <span>Press <strong>Enter ↵</strong> to send, <strong>Shift + Enter</strong> for new line</span>
        )}
      </div>
    </div>
  );
};
