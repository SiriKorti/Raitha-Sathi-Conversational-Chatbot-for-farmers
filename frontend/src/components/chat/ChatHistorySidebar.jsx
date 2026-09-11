import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, MessageSquare, Trash2, Search, X, Calendar } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import './ChatHistorySidebar.css';

export const ChatHistorySidebar = ({ onCloseMobile, isMobile = false }) => {
  const { sessionId, sessions, createNewChat, selectSession, closeSession } = useChat();
  const { t, language } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState(null);

  // Group sessions by date
  const groupedSessions = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 24 * 60 * 60 * 1000;
    const past7DaysStart = todayStart - 7 * 24 * 60 * 60 * 1000;

    const filtered = (sessions || []).filter((s) => {
      if (!searchQuery.trim()) return true;
      return (s.title || '').toLowerCase().includes(searchQuery.toLowerCase());
    });

    const groups = {
      today: [],
      yesterday: [],
      previous7Days: [],
      older: [],
    };

    filtered.forEach((sess) => {
      // Backend provides updated_at as float timestamp in seconds
      const ts = (sess.updated_at ? sess.updated_at * 1000 : Date.now());
      if (ts >= todayStart) {
        groups.today.push(sess);
      } else if (ts >= yesterdayStart) {
        groups.yesterday.push(sess);
      } else if (ts >= past7DaysStart) {
        groups.previous7Days.push(sess);
      } else {
        groups.older.push(sess);
      }
    });

    return groups;
  }, [sessions, searchQuery]);

  const navigate = useNavigate();

  const handleNewChat = async () => {
    const newId = await createNewChat();
    if (onCloseMobile) onCloseMobile();
    if (newId) {
      navigate(`/chat/${newId}`);
    } else {
      navigate('/chat');
    }
  };

  const handleSelectSession = (id) => {
    selectSession(id);
    navigate(`/chat/${id}`);
    if (onCloseMobile) onCloseMobile();
  };

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation();
    const confirmMsg = language === 'kn'
      ? 'ಈ ಸಂಭಾಷಣೆಯನ್ನು ಅಳಿಸಲು ನೀವು ಖಚಿತವಾಗಿ ಬಯಸುವಿರಾ?'
      : 'Are you sure you want to delete this conversation?';
    if (window.confirm(confirmMsg)) {
      await closeSession(id);
      if (id === sessionId) {
        navigate('/chat', { replace: true });
      }
    }
  };

  const renderGroup = (title, items) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="history-group">
        <span className="history-group-title">{title}</span>
        <div className="history-items-list">
          {items.map((sess) => {
            const isActive = sess.id === sessionId;
            return (
              <div
                key={sess.id}
                className={`history-session-item ${isActive ? 'active' : ''}`}
                onClick={() => handleSelectSession(sess.id)}
              >
                <MessageSquare size={16} className="session-icon" />
                <span className="session-title" title={sess.title}>
                  {sess.title || 'Conversation'}
                </span>
                <button
                  type="button"
                  className="session-delete-btn"
                  onClick={(e) => handleDeleteSession(e, sess.id)}
                  title="Close session / ಸಂಭಾಷಣೆ ತೆಗೆದುಹಾಕಿ"
                  aria-label="Close session"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const hasAnySessions = sessions && sessions.length > 0;

  return (
    <aside className={`chat-history-sidebar glass-panel ${isMobile ? 'mobile-drawer' : ''}`}>
      {/* Header Actions */}
      <div className="sidebar-header">
        <button
          type="button"
          className="btn btn-primary new-chat-btn"
          onClick={handleNewChat}
        >
          <Plus size={18} />
          <span>{language === 'kn' ? 'ಹೊಸ ಸಂಭಾಷಣೆ' : 'New Conversation'}</span>
        </button>

        {isMobile && (
          <button
            type="button"
            className="mobile-close-btn"
            onClick={onCloseMobile}
            title={language === 'kn' ? 'ಮುಚ್ಚಿ' : 'Close sidebar'}
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Search Input */}
      {hasAnySessions && (
        <div className="history-search-box">
          <Search size={15} className="search-icon" />
          <input
            type="text"
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={language === 'kn' ? 'ಸಂಭಾಷಣೆಗಳನ್ನು ಹುಡುಕಿ...' : 'Search conversations...'}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearchQuery('')}
            >
              <X size={12} />
            </button>
          )}
        </div>
      )}

      {/* Sessions List */}
      <div className="history-scroll-area">
        {!hasAnySessions ? (
          <div className="empty-history-notice">
            <Calendar size={28} className="empty-icon" />
            <p>{language === 'kn' ? 'ಹಿಂದಿನ ಯಾವುದೇ ಸಂಭಾಷಣೆಗಳಿಲ್ಲ' : 'No previous conversations'}</p>
            <span className="empty-sub">
              {language === 'kn' ? 'ಸಾಥಿ ಜೊತೆ ಪ್ರಶ್ನೆ ಕೇಳಲು ಪ್ರಾರಂಭಿಸಿ!' : 'Start asking questions with Sathi!'}
            </span>
          </div>
        ) : (
          <>
            {renderGroup(language === 'kn' ? 'ಇಂದು' : 'Today', groupedSessions.today)}
            {renderGroup(language === 'kn' ? 'ನಿನ್ನೆ' : 'Yesterday', groupedSessions.yesterday)}
            {renderGroup(language === 'kn' ? 'ಹಿಂದಿನ 7 ದಿನಗಳು' : 'Previous 7 Days', groupedSessions.previous7Days)}
            {renderGroup(language === 'kn' ? 'ಹಳೆಯ ಸಂಭಾಷಣೆಗಳು' : 'Older', groupedSessions.older)}
          </>
        )}
      </div>
    </aside>
  );
};
