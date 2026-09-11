import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { StatusBadge } from '../common/StatusBadge';
import { ThemeSelector } from '../common/ThemeSelector';
import { Sun, Moon, Globe, User, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';
import './TopBar.css';

export const TopBar = () => {
  const { language, toggleLanguage, t } = useLanguage();
  const { isDarkMode, toggleTheme } = useTheme();
  const { user, isAuthenticated } = useAuth();
  const isLoggedIn = isAuthenticated || Boolean(user);

  return (
    <header className="topbar-header glass-panel">
      <div className="topbar-left">
        <Link to={isLoggedIn ? "/chat" : "/"} className="brand-link">
          <div className="brand-icon-leaf">🌱</div>
          <div className="brand-text-col">
            <span className="brand-title">{t('app.name')}</span>
            <span className="brand-subtitle">{t('app.tagline')}</span>
          </div>
        </Link>
      </div>

      <div className="topbar-right">
        <StatusBadge />

        <button className="btn-icon" onClick={toggleLanguage} title={`Language: ${language.toUpperCase()}`}>
          <Globe size={18} />
          <span className="lang-code">{language.toUpperCase()}</span>
        </button>

        <ThemeSelector />

        <Link to="/notifications" className="btn-icon" title={t('nav.notifications')}>
          <Bell size={18} />
        </Link>

        <Link to="/profile" className="farmer-profile-pill glass-panel-hover" title={t('nav.profile')}>
          <div className="farmer-avatar">
            <User size={16} />
          </div>
          <span className="farmer-name">
            {(user?.name === 'Ramesh Gowda' || user?.fullName === 'Ramesh Gowda' || user?.id === 'farmer_001') ? 'farmer-01' : (user?.name || user?.fullName || 'Farmer')}
          </span>
        </Link>
      </div>
    </header>
  );
};
