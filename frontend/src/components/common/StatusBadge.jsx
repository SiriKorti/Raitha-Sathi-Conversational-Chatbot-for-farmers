import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient';
import { useLanguage } from '../../context/LanguageContext';
import { RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import './StatusBadge.css';

/**
 * StatusBadge Component
 * Performs an INITIAL health check on mount and MANUAL refresh when clicked.
 * Strictly NO periodic interval or background polling per project specification.
 */
export const StatusBadge = () => {
  const { t } = useLanguage();
  const [isOnline, setIsOnline] = useState(null); // null = checking, true = healthy, false = offline
  const [isChecking, setIsChecking] = useState(false);
  const [healthData, setHealthData] = useState(null);

  const checkStatus = async () => {
    setIsChecking(true);
    try {
      const res = await apiClient.checkHealth();
      if (res && res.status === 'healthy') {
        setIsOnline(true);
        setHealthData(res);
      } else {
        setIsOnline(false);
        setHealthData(res);
      }
    } catch {
      setIsOnline(false);
      setHealthData(null);
    } finally {
      setIsChecking(false);
    }
  };

  // Initial check on mount ONLY (No setInterval / No polling)
  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className={`status-badge ${isOnline === true ? 'status-online' : isOnline === false ? 'status-offline' : 'status-checking'}`}>
      <span className="status-dot"></span>
      <span className="status-label">
        {isChecking 
          ? 'Checking...' 
          : isOnline === true 
            ? t('status.online') 
            : t('status.offline')}
      </span>
      <button 
        className={`status-refresh-btn ${isChecking ? 'animate-spin' : ''}`}
        onClick={checkStatus} 
        title="Manual Health Refresh (No Polling)"
        disabled={isChecking}
        aria-label="Refresh backend status"
      >
        <RefreshCw size={12} />
      </button>
    </div>
  );
};
