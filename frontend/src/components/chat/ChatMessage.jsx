import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Volume2, Square, Copy, Check, Sparkles, User, Database, AlertCircle, Bookmark, BookmarkCheck } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import './ChatMessage.css';

export const ChatMessage = ({
  message,
  userQuery = '',
  isSaved = false,
  onSaveAdvice,
  onPlayAudio,
  isPlayingAudio,
  isLoadingAudio,
  onStopAudio,
}) => {
  const { language } = useLanguage();
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [localSaved, setLocalSaved] = useState(isSaved);

  useEffect(() => {
    setLocalSaved(isSaved);
  }, [isSaved]);

  const handleCopy = async () => {
    if (!message.content) return;
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const handleSave = async () => {
    if (localSaved || isSaving || !onSaveAdvice) return;
    setIsSaving(true);
    try {
      const success = await onSaveAdvice(message, userQuery);
      if (success) {
        setLocalSaved(true);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleAudioToggle = () => {
    if (isPlayingAudio) {
      onStopAudio();
    } else {
      onPlayAudio(message.id, message.content);
    }
  };

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`chat-message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="avatar user-avatar">
            <User size={18} />
          </div>
        ) : (
          <div className="avatar sathi-avatar">
            <span className="sathi-emoji">🌾</span>
          </div>
        )}
      </div>

      <div className="message-content-wrapper">
        <div className="message-header-meta">
          <span className="sender-name">{isUser ? 'You / ನೀವು' : 'Raitha Sathi / ರೈತ ಸಾಥಿ'}</span>
          {formattedTime && <span className="message-time">{formattedTime}</span>}
        </div>

        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {isUser ? (
            <p className="user-text">{message.content}</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && (
          <div className="message-actions-bar">
            {/* Audio Listen / Stop */}
            <button
              type="button"
              className={`action-btn audio-btn ${isPlayingAudio ? 'playing' : ''}`}
              onClick={handleAudioToggle}
              disabled={isLoadingAudio}
              title={isPlayingAudio ? (language === 'kn' ? 'ಧ್ವನಿ ನಿಲ್ಲಿಸಿ' : 'Stop Audio') : (language === 'kn' ? 'ಉತ್ತರ ಕೇಳಿ' : 'Listen to Answer')}
            >
              {isLoadingAudio ? (
                <span className="audio-loading-spinner" />
              ) : isPlayingAudio ? (
                <>
                  <Square size={14} className="playing-icon" />
                  <span className="equalizer-bars">
                    <span className="bar bar-1"></span>
                    <span className="bar bar-2"></span>
                    <span className="bar bar-3"></span>
                  </span>
                  <span>{language === 'kn' ? 'ನಿಲ್ಲಿಸಿ' : 'Stop'}</span>
                </>
              ) : (
                <>
                  <Volume2 size={15} />
                  <span>{language === 'kn' ? 'ಕೇಳಿ' : 'Listen'}</span>
                </>
              )}
            </button>

            {/* Copy Button */}
            <button
              type="button"
              className="action-btn copy-btn"
              onClick={handleCopy}
              title={language === 'kn' ? 'ಪ್ರತಿಕ್ರಿಯೆ ನಕಲಿಸಿ' : 'Copy response'}
            >
              {copied ? (
                <>
                  <Check size={14} className="copied-icon" />
                  <span className="copied-text">{language === 'kn' ? 'ನಕಲಿಸಲಾಗಿದೆ ✓' : 'Copied ✓'}</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>{language === 'kn' ? 'ನಕಲಿಸಿ' : 'Copy'}</span>
                </>
              )}
            </button>

            {/* Save / Bookmark Button */}
            <button
              type="button"
              className={`action-btn save-btn ${localSaved ? 'saved' : ''}`}
              onClick={handleSave}
              disabled={isSaving || localSaved}
              title={localSaved ? (language === 'kn' ? 'ಉಳಿಸಲಾಗಿದೆ' : 'Saved') : (language === 'kn' ? 'ಸಲಹೆ ಉಳಿಸಿ' : 'Save advice')}
              aria-label={localSaved ? 'Advice already saved' : 'Save this advice to bookmarks'}
            >
              {isSaving ? (
                <>
                  <span className="save-loading-spinner" />
                  <span>{language === 'kn' ? 'ಉಳಿಸಲಾಗುತ್ತಿದೆ...' : 'Saving...'}</span>
                </>
              ) : localSaved ? (
                <>
                  <BookmarkCheck size={14} className="saved-icon" />
                  <span className="saved-text">{language === 'kn' ? 'ಉಳಿಸಲಾಗಿದೆ' : 'Saved'}</span>
                </>
              ) : (
                <>
                  <Bookmark size={14} />
                  <span>{language === 'kn' ? 'ಉಳಿಸಿ' : 'Save'}</span>
                </>
              )}
            </button>

            {/* Grounding / Source Badge */}
            {message.source === 'database' && (
              <span className="source-badge db-badge" title="Grounded in verified agricultural database">
                <Database size={12} />
                <span>{language === 'kn' ? 'ದೃಢೀಕೃತ ಮಾಹಿತಿ' : 'Verified Data'}</span>
              </span>
            )}
            {message.source === 'rag' && (
              <span className="source-badge rag-badge" title="Derived from agricultural research knowledge base">
                <Sparkles size={12} />
                <span>{language === 'kn' ? 'RAG ದೃಢೀಕೃತ' : 'RAG Verified'}</span>
              </span>
            )}
            {message.source === 'llm' && (
              <span className="source-badge llm-badge" title="Generated by Gemini Agricultural AI model">
                <Sparkles size={12} />
                <span>{language === 'kn' ? 'Gemini AI ದೃಢೀಕೃತ' : 'Gemini AI Verified'}</span>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
