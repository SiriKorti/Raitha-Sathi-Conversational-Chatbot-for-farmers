import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import './ErrorState.css';

export const ErrorState = ({ message, onRetry }) => {
  const { t } = useLanguage();

  return (
    <div className="error-state-card glass-panel animate-fade-in">
      <div className="error-icon-wrapper">
        <AlertTriangle size={32} className="error-icon" />
      </div>
      <h3>{t('status.offline')}</h3>
      <p>{message || 'Something went wrong while connecting to the backend.'}</p>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry}>
          <RefreshCw size={16} /> {t('btn.retry')}
        </button>
      )}
    </div>
  );
};
