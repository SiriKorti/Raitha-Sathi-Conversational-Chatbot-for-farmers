import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Sprout,
  History,
  ArrowRight,
  Sparkles,
  Plus,
  Clock,
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useFarm } from '../../context/FarmContext';
import { useLanguage } from '../../context/LanguageContext';
import './HomePage.css';

export const HomePage = () => {
  const navigate = useNavigate();
  const { sessions, selectSession, createNewChat } = useChat();
  const { farmProfile, isSetup } = useFarm();
  const { language } = useLanguage();
  const isKn = language === 'kn';
  const [quickQuery, setQuickQuery] = useState('');

  // Determine greeting based on current hour
  const hour = new Date().getHours();
  const greetingTime =
    hour < 12
      ? isKn
        ? 'ಶುಭೋದಯ'
        : 'Good morning'
      : hour < 17
      ? isKn
        ? 'ಶುಭ ಮಧ್ಯಾಹ್ನ'
        : 'Good afternoon'
      : isKn
      ? 'ಶುಭ ಸಂಜೆ'
      : 'Good evening';

  const farmerName = farmProfile?.farmerName
    ? `${farmProfile.farmerName}`
    : isKn
    ? 'ರೈತ ಮಿತ್ರರೇ'
    : 'Farmer';

  const handleAskQuick = (e) => {
    e.preventDefault();
    const trimmed = quickQuery.trim();
    if (!trimmed) return;
    setQuickQuery('');
    navigate('/chat', {
      state: {
        prompt: trimmed,
      },
    });
  };

  const handleOpenSession = async (sessionId) => {
    await selectSession(sessionId);
    navigate('/chat');
  };

  const handleStartNewChat = async () => {
    await createNewChat();
    navigate('/chat');
  };

  const recentSessions = (sessions || []).slice(0, 3);

  return (
    <div className="home-page-container">
      {/* Welcome Hero Banner */}
      <section className="home-hero-section glass-panel">
        <div className="hero-greeting-badge">
          <Sparkles size={14} className="sparkle-icon" />
          <span>
            {isKn
              ? 'ರೈತ ಸಾಥಿ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಕೃಷಿ ಸಹಾಯಕ'
              : 'Raitha Sathi AI Agricultural Intelligence'}
          </span>
        </div>

        <h1 className="hero-greeting-heading">
          {greetingTime}, {farmerName}! 🌾
        </h1>

        <p className="hero-greeting-description">
          {isKn
            ? 'ಕರ್ನಾಟಕದ ರೈತರಿಗಾಗಿ ವಿನ್ಯಾಸಗೊಳಿಸಲಾದ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಕೃಷಿ ಸಹಾಯಕ. ಬೆಳೆ ರಕ್ಷಣೆ, ರೋಗ ನಿಯಂತ್ರಣ ಮತ್ತು ಕೃಷಿ ಸಲಹೆಗಳಿಗಾಗಿ ಪ್ರಶ್ನೆ ಕೇಳಿ.'
            : 'Your dedicated AI agricultural assistant grounded in verified Karnataka crop knowledge. Ask any question about crop health, fertilizers, pests, or irrigation.'}
        </p>

        {/* Quick Question Input */}
        <form onSubmit={handleAskQuick} className="hero-query-form">
          <input
            type="text"
            className="hero-query-input"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder={
              isKn
                ? 'ಸಾಥಿ ಜೊತೆ ಮಾತನಾಡಿ: ಉದಾ. ಟೊಮೆಟೊ ಎಲೆ ಮುದುರು ರೋಗ ನಿಯಂತ್ರಣ ಹೇಗೆ?...'
                : 'Ask Sathi: e.g. How to prevent root rot in tomato?...'
            }
          />
          <button type="submit" className="btn btn-primary hero-query-submit">
            <span>{isKn ? 'ಸಾಥಿ ಕೇಳಿ' : 'Ask Sathi'}</span>
            <ArrowRight size={16} />
          </button>
        </form>
      </section>

      {/* Main 2-Column Dashboard Grid */}
      <div className="home-dashboard-grid">
        {/* Left Column: Recent Chats & Actions */}
        <div className="dashboard-col">
          {/* Quick Core Actions */}
          <div className="quick-actions-cards-row">
            <div
              className="quick-action-card surface-card glass-panel-hover"
              onClick={handleStartNewChat}
            >
              <div className="action-card-icon chat-icon">
                <MessageSquare size={22} />
              </div>
              <div className="action-card-info">
                <h4>{isKn ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Ask Sathi'}</h4>
                <p>{isKn ? 'ಹೊಸ ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ' : 'Start a new conversation'}</p>
              </div>
              <ChevronRight size={18} className="action-arrow" />
            </div>

            <div
              className="quick-action-card surface-card glass-panel-hover"
              onClick={() => navigate('/farm')}
            >
              <div className="action-card-icon farm-icon">
                <Sprout size={22} />
              </div>
              <div className="action-card-info">
                <h4>{isKn ? 'ನನ್ನ ಜಮೀನಿನ ವಿವರ' : 'My Farm Profile'}</h4>
                <p>
                  {isSetup
                    ? isKn
                      ? `${farmProfile?.crops?.length || 0} ಬೆಳೆಗಳನ್ನು ನಮೂದಿಸಲಾಗಿದೆ`
                      : `${farmProfile?.crops?.length || 0} Crops Configured`
                    : isKn
                    ? 'ಜಮೀನಿನ ವಿವರ ಭರ್ತಿ ಮಾಡಿ'
                    : 'Set up your farm profile'}
                </p>
              </div>
              <ChevronRight size={18} className="action-arrow" />
            </div>
          </div>

          {/* Recent Active Conversations */}
          <div className="recent-conversations-card surface-card">
            <div className="card-section-header">
              <div className="header-title-group">
                <History size={18} className="section-header-icon" />
                <h3>{isKn ? 'ಇತ್ತೀಚಿನ ಸಂಭಾಷಣೆಗಳು' : 'Recent Conversations'}</h3>
              </div>
              <button
                type="button"
                className="view-all-btn"
                onClick={() => navigate('/history')}
              >
                <span>{isKn ? 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ' : 'View All'}</span>
                <ChevronRight size={14} />
              </button>
            </div>

            <div className="recent-sessions-list">
              {recentSessions.length === 0 ? (
                <div className="no-recent-chats">
                  <p>{isKn ? 'ಯಾವುದೇ ಇತ್ತೀಚಿನ ಸಂಭಾಷಣೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ.' : 'No recent conversations found.'}</p>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleStartNewChat}
                  >
                    <Plus size={14} />
                    <span>{isKn ? 'ಮೊದಲ ಸಂಭಾಷಣೆ ಪ್ರಾರಂಭಿಸಿ' : 'Start First Chat'}</span>
                  </button>
                </div>
              ) : (
                recentSessions.map((sess) => (
                  <div
                    key={sess.id}
                    className="recent-session-item"
                    onClick={() => handleOpenSession(sess.id)}
                  >
                    <div className="session-item-left">
                      <div className="session-bullet" />
                      <div className="session-info">
                        <span className="session-title-text">{sess.title || (isKn ? 'ಕೃಷಿ ಸಮಾಲೋಚನೆ' : 'Agricultural Discussion')}</span>
                        <div className="session-time-text">
                          <Clock size={11} />
                          <span>
                            {sess.updated_at
                              ? new Date(sess.updated_at * 1000).toLocaleDateString([], {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : ''}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="resume-session-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenSession(sess.id);
                      }}
                      title={isKn ? 'ಚರ್ಚೆ ಮುಂದುವರಿಸಿ' : 'Continue this chat'}
                    >
                      <span>{isKn ? 'ಮುಂದುವರಿಸಿ' : 'Resume'}</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Farm Snapshot & Intelligence Overview */}
        <div className="dashboard-col">
          {/* Farm Profile Snapshot */}
          <div className="farm-snapshot-card glass-panel">
            <div className="card-section-header">
              <div className="header-title-group">
                <Sprout size={18} className="section-header-icon" />
                <h3>{isKn ? 'ಜಮೀನಿನ ಚಿತ್ರಣ' : 'Farm Snapshot'}</h3>
              </div>
              <button
                type="button"
                className="view-all-btn"
                onClick={() => navigate('/farm')}
              >
                <span>{isSetup ? (isKn ? 'ನಿರ್ವಹಿಸಿ' : 'Manage') : (isKn ? 'ಭರ್ತಿ ಮಾಡಿ' : 'Set Up')}</span>
                <ChevronRight size={14} />
              </button>
            </div>

            {isSetup && farmProfile ? (
              <div className="farm-snapshot-content">
                <div className="snapshot-header-row">
                  <div>
                    <span className="snapshot-location-label">{farmProfile.location || (isKn ? 'ಕರ್ನಾಟಕ' : 'Karnataka')}</span>
                    <h3 className="snapshot-area-val">{farmProfile.landArea || (isKn ? 'ಕೃಷಿ ಭೂಮಿ' : 'Active Land')}</h3>
                  </div>
                  <div className="snapshot-status-pill">
                    <CheckCircle2 size={12} />
                    <span>{isKn ? 'ಸಕ್ರಿಯವಾಗಿದೆ' : 'Configured'}</span>
                  </div>
                </div>

                <div className="snapshot-details-pills">
                  {farmProfile.soilType && (
                    <span className="snapshot-pill">
                      <strong>{isKn ? 'ಮಣ್ಣು:' : 'Soil:'}</strong> {farmProfile.soilType}
                    </span>
                  )}
                  {farmProfile.irrigationType && (
                    <span className="snapshot-pill">
                      <strong>{isKn ? 'ನೀರಾವರಿ:' : 'Water:'}</strong> {farmProfile.irrigationType}
                    </span>
                  )}
                </div>

                <div className="snapshot-crops-section">
                  <span className="snapshot-subhead">{isKn ? 'ಸಕ್ರಿಯ ಬೆಳೆಗಳು:' : 'Active Crops:'}</span>
                  <div className="snapshot-crops-tags">
                    {Array.isArray(farmProfile.crops) && farmProfile.crops.length > 0 ? (
                      farmProfile.crops.map((c, i) => (
                        <span key={i} className="snapshot-crop-tag">
                          🌱 {c}
                        </span>
                      ))
                    ) : (
                      <span className="no-crop-tag">{isKn ? 'ಯಾವುದೇ ಬೆಳೆಗಳನ್ನು ಸೇರಿಸಿಲ್ಲ' : 'No crops added'}</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="farm-not-setup-box">
                <p>
                  {isKn
                    ? 'ನಿಮ್ಮ ಬೆಳೆ ಮತ್ತು ಮಣ್ಣಿನ ವಿವರಗಳನ್ನು ಸೇರಿಸಿ ವೈಯಕ್ತಿಕ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಕೃಷಿ ಸಲಹೆ ಪಡೆಯಿರಿ.'
                    : 'Add your crops and soil details to get customized AI agricultural guidance.'}
                </p>
                <button
                  type="button"
                  className="btn btn-primary setup-farm-btn"
                  onClick={() => navigate('/farm')}
                >
                  <Plus size={14} />
                  <span>{isKn ? 'ಜಮೀನಿನ ವಿವರ ಸೇರಿಸಿ' : 'Set Up Farm Profile'}</span>
                </button>
              </div>
            )}
          </div>

          {/* AI Intelligence Architecture Card */}
          <div className="agri-intelligence-card surface-card">
            <div className="card-section-header">
              <div className="header-title-group">
                <ShieldCheck size={18} className="section-header-icon" />
                <h3>{isKn ? 'ಪರಿಶೀಲಿಸಿದ ಕೃಷಿ AI ವ್ಯವಸ್ಥೆ' : 'Verified Agricultural Pipeline'}</h3>
              </div>
            </div>

            <div className="intelligence-features-list">
              <div className="intelligence-item">
                <div className="item-icon-box">
                  <Zap size={16} />
                </div>
                <div>
                  <h5>{isKn ? 'ಅಧಿಕೃತ ಕೃಷಿ ಜ್ಞಾನ ಭಂಡಾರ' : 'Direct Database Grounding'}</h5>
                  <p>
                    {isKn
                      ? 'ಕರ್ನಾಟಕ ಕೃಷಿ ವಿಶ್ವವಿದ್ಯಾಲಯಗಳು ಮತ್ತು ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರಗಳ 1,500+ ಪರಿಶೀಲಿಸಿದ ಪರಿಹಾರಗಳು.'
                      : '1,500+ verified solutions from Karnataka Agricultural University & Krishi Kendra research.'}
                  </p>
                </div>
              </div>

              <div className="intelligence-item">
                <div className="item-icon-box">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h5>{isKn ? 'ದ್ವಿಭಾಷಾ RAG ಮತ್ತು ಧ್ವನಿ ಸಂಭಾಷಣೆ' : 'Hybrid Semantic RAG & Gemini'}</h5>
                  <p>
                    {isKn
                      ? 'ನೈಜ ಕನ್ನಡ ಧ್ವನಿ ಗುರುತಿಸುವಿಕೆ (STT), ಧ್ವನಿ ಉತ್ಪಾದನೆ (TTS) ಮತ್ತು ನಿಖರ ಕೃಷಿ ಸಂಭಾಷಣೆ.'
                      : 'Contextual Kannada language reasoning with voice synthesis and automatic speech recognition.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
