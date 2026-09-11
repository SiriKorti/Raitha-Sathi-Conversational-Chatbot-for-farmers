import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useTheme } from '../../context/ThemeContext';
import { useToast } from '../../context/ToastContext';
import { useFarm } from '../../context/FarmContext';
import { useChat } from '../../context/ChatContext';
import { useDiary } from '../../context/DiaryContext';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Sparkles, ShieldAlert, Cpu, Layers } from 'lucide-react';
import './FoundationPlaceholder.css';

/**
 * FoundationPlaceholder Component
 * Renders an honest, clearly marked placeholder for all future routes during Phase 1.
 * Shows active session telemetry, language/theme states, and backend dependency notices.
 */
export const FoundationPlaceholder = ({
  pageTitle,
  pageKey,
  icon: Icon,
  phaseTarget = 'Phase 2',
  isBackendDependent = false,
  backendRequirement = ''
}) => {
  const { language, t } = useLanguage();
  const { isDarkMode } = useTheme();
  const { showToast } = useToast();
  const { farmProfile } = useFarm();
  const { sessionId } = useChat();

  const handleTestToast = () => {
    showToast(`Phase 1 Foundation active! [${pageTitle}] — Language: ${language.toUpperCase()} | Theme: ${isDarkMode ? 'Dark' : 'Light'}`, 'success');
  };

  return (
    <div className="foundation-placeholder-container animate-fade-in">
      <Card glass={true} className="placeholder-hero-card">
        <div className="placeholder-header-row">
          {Icon && (
            <div className="placeholder-icon-box">
              <Icon size={32} />
            </div>
          )}
          <div className="placeholder-header-text">
            <div className="placeholder-title-line">
              <h1>{t(pageKey) || pageTitle}</h1>
              <span className="phase-pill">{phaseTarget} Feature</span>
              <StatusBadge />
            </div>
            <p className="placeholder-subtitle">
              Foundation & Routing Layer active. Full feature integration scheduled for {phaseTarget}.
            </p>
          </div>
        </div>

        {isBackendDependent && (
          <div className="backend-dependent-banner">
            <ShieldAlert size={20} className="text-warning flex-shrink-0" />
            <div>
              <strong>Backend Dependent Feature:</strong>
              <p>{backendRequirement}</p>
            </div>
          </div>
        )}

        <div className="telemetry-grid">
          <Card className="telemetry-card">
            <span className="telemetry-title">Session State</span>
            <span className="telemetry-val font-mono">{sessionId ? sessionId.slice(0, 14) + '...' : 'Init / Ready'}</span>
          </Card>

          <Card className="telemetry-card">
            <span className="telemetry-title">Farm Profile Bound</span>
            <span className="telemetry-val">{farmProfile?.farmName || 'farmer-01 Farm (user_123)'}</span>
          </Card>

          <Card className="telemetry-card">
            <span className="telemetry-title">Language Engine</span>
            <span className="telemetry-val">{language.toUpperCase()} ({language === 'kn' ? 'ಕನ್ನಡ' : 'English'})</span>
          </Card>


          <Card className="telemetry-card">
            <span className="telemetry-title">Theme Environment</span>
            <span className="telemetry-val">{isDarkMode ? '🌙 Dark Botanical' : '☀️ Light Botanical'}</span>
          </Card>
        </div>

        <div className="placeholder-actions">
          <Button variant="primary" icon={Sparkles} onClick={handleTestToast}>
            Test Live State & Toast
          </Button>
        </div>
      </Card>
    </div>
  );
};
