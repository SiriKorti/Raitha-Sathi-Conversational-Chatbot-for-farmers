import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { PanelLeft, Plus, ArrowDown, Sparkles, RefreshCw, AlertTriangle } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { useAudioPlayer } from '../../utils/useAudioPlayer';
import { adviceService } from '../../services/adviceService';
import { ChatMessage } from '../../components/chat/ChatMessage';
import { ChatComposer } from '../../components/chat/ChatComposer';
import { ChatEmptyState } from '../../components/chat/ChatEmptyState';
import { ChatHistorySidebar } from '../../components/chat/ChatHistorySidebar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import './ChatPage.css';

// Composite identity helper to prevent false positive saved states on identical assistant text
const getAdviceCompositeKey = (userQuery, content) => {
  const normalizedQuery = (userQuery || '').trim();
  const normalizedContent = (content || '').trim();
  return `${normalizedQuery}:::${normalizedContent}`;
};

export const ChatPage = () => {
  const location = useLocation();
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();
  const userId = user?.id || 'user_123';

  const {
    sessionId,
    messages,
    isLoading,
    isLoadingHistory,
    error,
    createNewChat,
    selectSession,
    sendMessage,
  } = useChat();

  const { t, language } = useLanguage();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const [savedSignatures, setSavedSignatures] = useState(new Set());

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const handledPromptRef = useRef(null);

  // Preload saved advice for current user using composite (user_query + content) identity
  useEffect(() => {
    let isMounted = true;
    const loadSavedAdvice = async () => {
      try {
        const res = await adviceService.getSavedAdvice(userId);
        if (isMounted && res && Array.isArray(res.advice)) {
          const sigs = new Set(
            res.advice.map((item) => getAdviceCompositeKey(item.user_query, item.content))
          );
          setSavedSignatures(sigs);
        }
      } catch (err) {
        console.error('Failed to preload saved advice state:', err);
      }
    };
    loadSavedAdvice();
    return () => {
      isMounted = false;
    };
  }, [userId]);

  // Consume prompt passed from navigation (Home Quick Search, Crop Explorer, Schemes, Weather, Mandi, Explore, Diagnosis)
  useEffect(() => {
    const prompt = location.state?.prompt;
    const navKey = location.key || prompt;
    if (prompt && handledPromptRef.current !== navKey) {
      handledPromptRef.current = navKey;
      sendMessage(prompt);
      // Clear state to avoid re-triggering on history navigations / page refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.key, location.state, sendMessage]);

  // Handle direct URL deep-linking /chat/:conversationId
  useEffect(() => {
    if (conversationId && conversationId !== sessionId) {
      selectSession(conversationId).catch(() => {
        showToast(
          language === 'kn'
            ? 'ಸಂಭಾಷಣೆ ಲಭ್ಯವಿಲ್ಲ ಅಥವಾ ಪ್ರವೇಶ ನಿರಾಕರಿಸಲಾಗಿದೆ.'
            : 'Conversation not found or access denied.',
          'warning'
        );
        navigate('/chat', { replace: true });
      });
    }
  }, [conversationId, sessionId, selectSession, showToast, language, navigate]);

  const handleNewChat = async () => {
    const newId = await createNewChat();
    if (newId) {
      navigate(`/chat/${newId}`);
    } else {
      navigate('/chat');
    }
  };

  const {
    playingMessageId,
    isLoadingAudio,
    playText,
    stopAudio,
  } = useAudioPlayer();

  // Scroll detection
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    setShowScrollBottom(distanceFromBottom > 120);
  };

  const scrollToBottom = useCallback((smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    }
  }, []);

  // Auto-scroll when new messages arrive (only if already near bottom)
  useEffect(() => {
    if (!showScrollBottom) {
      scrollToBottom(true);
    }
  }, [messages, isLoading, showScrollBottom, scrollToBottom]);

  const handleSendPrompt = (text) => {
    sendMessage(text);
  };

  const handleRetryLast = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      sendMessage(lastUserMsg.content);
    }
  };

  const handleSaveAdvice = useCallback(
    async (message, userQuery) => {
      try {
        const payload = {
          content: message.content,
          user_query: userQuery || null,
          crop: message.metadata?.state?.crop_name || null,
          topic: message.metadata?.state?.intent || null,
          source: message.source || null,
          provider: message.provider || null,
        };
        const res = await adviceService.saveAdvice(userId, payload);
        if (res && (res.status === 'success' || res.data)) {
          showToast(t('saved.save_success') || 'Advice saved successfully!', 'success');
          const savedKey = getAdviceCompositeKey(userQuery, message.content);
          setSavedSignatures((prev) => new Set([...prev, savedKey]));
          return true;
        }
        throw new Error(res?.message || 'Failed to save advice');
      } catch (err) {
        console.error('Save advice error:', err);
        showToast(err.message || 'Failed to save advice. Please try again.', 'error');
        return false;
      }
    },
    [userId, showToast, t]
  );

  return (
    <div className="chat-page-layout">
      {/* Desktop History Sidebar */}
      {isSidebarOpen && (
        <div className="desktop-history-wrapper">
          <ChatHistorySidebar />
        </div>
      )}

      {/* Mobile History Drawer */}
      {isMobileDrawerOpen && (
        <>
          <div
            className="mobile-drawer-backdrop"
            onClick={() => setIsMobileDrawerOpen(false)}
          />
          <ChatHistorySidebar
            isMobile={true}
            onCloseMobile={() => setIsMobileDrawerOpen(false)}
          />
        </>
      )}

      {/* Main Chat Conversation Viewport */}
      <div className="chat-main-viewport">
        {/* Top Chat Bar with Header & Mobile Triggers */}
        <header className="chat-top-header">
          <div className="header-left-actions">
            <button
              type="button"
              className="sidebar-toggle-btn desktop-only"
              onClick={() => setIsSidebarOpen((prev) => !prev)}
              title={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              <PanelLeft size={18} />
            </button>
            <button
              type="button"
              className="mobile-menu-btn mobile-only"
              onClick={() => setIsMobileDrawerOpen(true)}
              title="Open chat history"
            >
              <PanelLeft size={18} />
            </button>
          </div>

          <div className="chat-title-group">
            <h1 className="chat-header-title">
              <span className="title-brand">{language === 'kn' ? 'ರೈತ ಸಾಥಿ' : t('app.name')}</span>
              <span className="title-divider">—</span>
              <span className="title-sub">
                {language === 'kn' ? 'ಕೃಷಿ AI ಸಹಾಯಕ' : t('nav.chat')}
              </span>
            </h1>
            <p className="chat-header-desc">
              {language === 'kn' ? 'ರೈತರಿಗಾಗಿ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಕೃಷಿ ಸಹಾಯಕ' : t('app.tagline')}
            </p>
          </div>

          <div className="header-right-actions">
            <button
              type="button"
              className="header-new-chat-btn"
              onClick={handleNewChat}
              title={language === 'kn' ? 'ಹೊಸ ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ' : 'Start a new chat'}
            >
              <Plus size={16} />
              <span>{language === 'kn' ? 'ಹೊಸ ಸಂಭಾಷಣೆ' : 'New Chat'}</span>
            </button>
          </div>
        </header>

        {/* Scrollable Message Feed Area */}
        <div
          ref={scrollContainerRef}
          className="chat-messages-scroll-area"
          onScroll={handleScroll}
        >
          {isLoadingHistory ? (
            <div className="chat-loading-history">
              <LoadingSpinner size="large" label="Loading conversation history..." />
            </div>
          ) : messages.length === 0 ? (
            <ChatEmptyState onSelectPrompt={handleSendPrompt} />
          ) : (
            <div className="chat-messages-feed">
              {messages.map((msg, index) => {
                const precedingUserMsg =
                  msg.role === 'assistant'
                    ? [...messages.slice(0, index)].reverse().find((m) => m.role === 'user')
                    : null;
                const userQuery = precedingUserMsg ? precedingUserMsg.content : '';
                const isSaved = savedSignatures.has(
                  getAdviceCompositeKey(userQuery, msg.content)
                );

                return (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    userQuery={userQuery}
                    isSaved={isSaved}
                    onSaveAdvice={handleSaveAdvice}
                    isPlayingAudio={playingMessageId === msg.id}
                    isLoadingAudio={isLoadingAudio && playingMessageId === msg.id}
                    onPlayAudio={playText}
                    onStopAudio={stopAudio}
                  />
                );
              })}

              {/* Live Generation Indicator */}
              {isLoading && (
                <div className="chat-generating-indicator">
                  <div className="avatar sathi-avatar">
                    <span className="sathi-emoji">🌾</span>
                  </div>
                  <div className="generating-bubble surface-card">
                    <span className="generating-pulse-dot" />
                    <span>{language === 'kn' ? '🌾 ಯೋಚಿಸುತ್ತಿದ್ದೇನೆ...' : '🌾 Thinking...'}</span>
                  </div>
                </div>
              )}

              {/* Error Banner */}
              {error && !isLoading && (
                <div className="chat-error-banner surface-card">
                  <div className="error-banner-content">
                    <AlertTriangle size={18} className="error-icon" />
                    <span>{error}</span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary retry-btn"
                    onClick={handleRetryLast}
                  >
                    <RefreshCw size={14} />
                    <span>Retry / ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ</span>
                  </button>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Floating Scroll To Bottom Button */}
        {showScrollBottom && (
          <button
            type="button"
            className="scroll-to-bottom-btn"
            onClick={() => scrollToBottom(true)}
            title="Scroll to bottom"
          >
            <ArrowDown size={18} />
          </button>
        )}

        {/* Sticky Chat Composer at Bottom */}
        <div className="chat-footer-composer">
          <ChatComposer
            onSendMessage={handleSendPrompt}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};
