import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useToast } from '../context/ToastContext';
import { useFarm } from '../context/FarmContext';
import { useChat } from '../context/ChatContext';
import { useDiary } from '../context/DiaryContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { Sparkles, ArrowRight, Activity, Terminal, ShieldAlert } from 'lucide-react';
import './Phase1Placeholder.css';

export const Phase1Placeholder = ({ pageTitle, pageKey, icon: Icon, isBackendDependent, backendRequirement }) => {
  const { language, t } = useLanguage();
  const { isDarkMode } = useTheme();
  const { showToast } = useToast();
  const { farmProfile } = useFarm();
  const { sessionId } = useChat();
  const { isBackendSupported } = useDiary();

  const handleTestToast = () => {
    showToast(`Phase 1 Foundation active! Language: ${language.toUpperCase()} | Theme: ${isDarkMode ? 'Dark' : 'Light'}`, 'success');
  };

  return (
    <div className="phase1-container animate-fade-in">
      <div className="phase1-hero glass-panel">
        <div className="phase1-icon-header">
          {Icon && (
            <div className="phase1-main-icon">
              <Icon size={36} />
            </div>
          )}
          <div>
            <div className="phase1-title-row">
              <h1>{t(pageKey) || pageTitle}</h1>
              <StatusBadge />
            </div>
            <p className="phase1-desc">
              Raitha Sathi Bio-Agritech Core — Phase 1 Foundation & Connected Shell
            </p>
          </div>
        </div>

        {isBackendDependent && (
          <div className="backend-dependent-banner">
            <ShieldAlert size={20} className="text-warning" />
            <div>
              <strong>Backend Dependent Feature:</strong>
              <p>{backendRequirement}</p>
            </div>
          </div>
        )}

        <div className="phase1-telemetry-grid">
          <div className="telemetry-box surface-card">
            <span className="telemetry-label">Active Session ID</span>
            <span className="telemetry-value font-mono">{sessionId ? sessionId.slice(0, 13) + '...' : 'Connecting...'}</span>
          </div>

          <div className="telemetry-box surface-card">
            <span className="telemetry-label">Farm Identity</span>
            <span className="telemetry-value">{farmProfile?.farmName || 'farmer-01 Farm (user_123)'}</span>
          </div>

          <div className="telemetry-box surface-card">
            <span className="telemetry-label">Language Engine</span>
            <span className="telemetry-value">{language.toUpperCase()} ({language === 'kn' ? 'ಕನ್ನಡ' : 'English'})</span>
          </div>


          <div className="telemetry-box surface-card">
            <span className="telemetry-label">Theme Mode</span>
            <span className="telemetry-value">{isDarkMode ? '🌙 Dark Botanical' : '☀️ Light Botanical'}</span>
          </div>
        </div>

        <div className="phase1-actions">
          <button className="btn btn-primary" onClick={handleTestToast}>
            <Sparkles size={16} /> Test Live Context & Toast
          </button>
        </div>
      </div>
    </div>
  );
};
