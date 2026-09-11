import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, MessageSquare, Trash2, ArrowRight, Search, Plus, Clock } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import { PageHeader } from '../../components/common/PageHeader';
import { EmptyState } from '../../components/common/EmptyState';
import './HistoryPage.css';

export const HistoryPage = () => {
  const { sessions, selectSession, closeSession, createNewChat } = useChat();
  const { t, language } = useLanguage();
  const isKn = language === 'kn';
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = useMemo(() => {
    return (sessions || []).filter((s) => {
      if (!searchQuery.trim()) return true;
      return (s.title || '').toLowerCase().includes(searchQuery.toLowerCase());
    });
  }, [sessions, searchQuery]);

  const handleOpenSession = async (sessionId) => {
    await selectSession(sessionId);
    navigate(`/chat/${sessionId}`);
  };

  const handleNewChat = async () => {
    const newId = await createNewChat();
    if (newId) {
      navigate(`/chat/${newId}`);
    } else {
      navigate('/chat');
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    const confirmMsg = isKn
      ? 'ಈ ಸಂಭಾಷಣೆಯನ್ನು ಅಳಿಸಲು ನೀವು ಖಚಿತವಾಗಿ ಬಯಸುವಿರಾ?'
      : 'Are you sure you want to delete this conversation?';
    if (window.confirm(confirmMsg)) {
      await closeSession(sessionId);
    }
  };

  const formatSessionTime = (updatedAt) => {
    if (!updatedAt) return '';
    const date = new Date(updatedAt * 1000);
    return date.toLocaleDateString(isKn ? 'kn-IN' : 'en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="history-page-container">
      <PageHeader
        title={t('nav.history') || (isKn ? 'ಸಂಭಾಷಣೆ ಇತಿಹಾಸ' : 'Chat History')}
        subtitle={
          isKn
            ? 'ನಿಮ್ಮ ಹಿಂದಿನ ಕೃಷಿ ಸಂಭಾಷಣೆಗಳು ಮತ್ತು ಸಲಹೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.'
            : 'Access and continue your previous agricultural advisory sessions.'
        }
        icon={History}
        action={
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleNewChat}
          >
            <Plus size={16} />
            <span>{t('btn.new_chat') || (isKn ? 'ಹೊಸ ಸಂಭಾಷಣೆ' : 'New Conversation')}</span>
          </button>
        }
      />

      {/* Search and Filters Bar */}
      {sessions && sessions.length > 0 && (
        <div className="history-toolbar surface-card">
          <div className="history-search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="history-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isKn ? 'ವಿಷಯದ ಮೂಲಕ ಹುಡುಕಿ...' : 'Search conversations by topic...'}
            />
          </div>
          <span className="history-count-badge">
            {filteredSessions.length} {isKn ? 'ಸಂಭಾಷಣೆಗಳು' : filteredSessions.length === 1 ? 'session' : 'sessions'}
          </span>
        </div>
      )}

      {/* Sessions Grid / List */}
      {!sessions || sessions.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title={isKn ? 'ಯಾವುದೇ ಸಂಭಾಷಣೆಗಳಿಲ್ಲ' : 'No Conversation History'}
          description={
            isKn
              ? 'ಇನ್ನೂ ಯಾವುದೇ ಕೃಷಿ ಸಂಭಾಷಣೆಗಳನ್ನು ದಾಖಲಿಸಲಾಗಿಲ್ಲ. ಸಾಥಿ ಜೊತೆ ಮೊದಲ ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ!'
              : 'You have no active conversation sessions recorded yet. Start a new conversation with Sathi!'
          }
          actionLabel={isKn ? 'ಹೊಸ ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ' : 'Start New Chat'}
          onAction={handleNewChat}
        />
      ) : filteredSessions.length === 0 ? (
        <div className="no-search-results surface-card">
          <p>
            {isKn
              ? `"${searchQuery}" ಹುಡುಕಾಟಕ್ಕೆ ಯಾವುದೇ ಸಂಭಾಷಣೆ ಕಂಡುಬಂದಿಲ್ಲ.`
              : `No conversations matched your search query "${searchQuery}".`}
          </p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setSearchQuery('')}
          >
            {isKn ? 'ಹುಡುಕಾಟ ತೆರವುಗೊಳಿಸಿ' : 'Clear Search Filter'}
          </button>
        </div>
      ) : (
        <div className="history-sessions-grid">
          {filteredSessions.map((sess) => (
            <div
              key={sess.id}
              className="history-card glass-panel glass-panel-hover"
              onClick={() => handleOpenSession(sess.id)}
            >
              <div className="history-card-header">
                <div className="card-icon">
                  <MessageSquare size={18} />
                </div>
                <div className="card-header-meta">
                  <span className="card-session-id">ID: {sess.id.slice(0, 8)}...</span>
                  <div className="card-time">
                    <Clock size={12} />
                    <span>{formatSessionTime(sess.updated_at)}</span>
                  </div>
                </div>
              </div>

              <div className="history-card-body">
                <h3 className="history-card-title">{sess.title || (isKn ? 'ಕೃಷಿ ಸಲಹಾ ಸಂಭಾಷಣೆ' : 'Agricultural Advisory')}</h3>
              </div>

              <div className="history-card-footer">
                <button
                  type="button"
                  className="btn-continue"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenSession(sess.id);
                  }}
                >
                  <span>{isKn ? 'ಮುಂದುವರಿಸಿ' : 'Continue'}</span>
                  <ArrowRight size={14} />
                </button>

                <button
                  type="button"
                  className="btn-delete"
                  onClick={(e) => handleDeleteSession(e, sess.id)}
                  title={isKn ? 'ಸಂಭಾಷಣೆ ತೆಗೆದುಹಾಕಿ' : 'Delete session'}
                  aria-label={isKn ? 'ಸಂಭಾಷಣೆ ತೆಗೆದುಹಾಕಿ' : 'Delete session'}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
