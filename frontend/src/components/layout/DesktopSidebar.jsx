import React from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  MessageSquare,
  History,
  Sprout,
  ShieldCheck,
  Compass,
  CloudSun,
  Coins,
  Settings,
  HelpCircle,
  LogIn,
  Sparkles,
  TrendingUp,
  Camera,
  Bookmark,
} from 'lucide-react';
import './DesktopSidebar.css';

export const DesktopSidebar = () => {
  const { language } = useLanguage();
  const { isAuthenticated, user } = useAuth();
  const isLoggedIn = isAuthenticated || Boolean(user);

  const coreNavItems = [
    { to: '/chat', icon: MessageSquare, labelEn: 'Ask Sathi (Chat)', labelKn: 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' },
    { to: '/crops', icon: Sprout, labelEn: 'Crop Explorer', labelKn: 'ಬೆಳೆಗಳ ಮಾಹಿತಿ', badgeEn: '15 Crops', badgeKn: '15 ಬೆಳೆಗಳು' },
    { to: '/schemes', icon: ShieldCheck, labelEn: 'Govt Schemes', labelKn: 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು' },
    { to: '/weather', icon: CloudSun, labelEn: 'Weather Advisory', labelKn: 'ಹವಾಮಾನ ಸಲಹೆ' },
    { to: '/mandi', icon: Coins, labelEn: 'Mandi Prices', labelKn: 'ಮಾರುಕಟ್ಟೆ ದರ' },
  ];

  const toolsNavItems = [
    { to: '/history', icon: History, labelEn: 'Chat History', labelKn: 'ಹಿಂದಿನ ಚರ್ಚೆಗಳು' },
    { to: '/progress', icon: TrendingUp, labelEn: 'Crop Progress', labelKn: 'ಬೆಳೆ ಹಂತಗಳು' },
    { to: '/diagnosis', icon: Camera, labelEn: 'Visual Diagnosis', labelKn: 'ರೋಗ ನಿರ್ಣಯ', badgeEn: 'Vision', badgeKn: 'ಕ್ಯಾಮೆರಾ' },
    { to: '/saved', icon: Bookmark, labelEn: 'Saved Advice', labelKn: 'ಉಳಿಸಿದ ಸಲಹೆಗಳು' },
  ];

  const bottomNavItems = isLoggedIn
    ? [
        { to: '/settings', icon: Settings, labelEn: 'Settings', labelKn: 'ಸೆಟ್ಟಿಂಗ್ಸ್' },
        { to: '/help', icon: HelpCircle, labelEn: 'Help & Support', labelKn: 'ಸಹಾಯ' },
      ]
    : [
        { to: '/', icon: Sparkles, labelEn: 'Storytelling Landing', labelKn: 'ಮುಖಪುಟ' },
        { to: '/settings', icon: Settings, labelEn: 'Settings', labelKn: 'ಸೆಟ್ಟಿಂಗ್ಸ್' },
        { to: '/help', icon: HelpCircle, labelEn: 'Help & Support', labelKn: 'ಸಹಾಯ' },
        { to: '/login', icon: LogIn, labelEn: 'Login / Register', labelKn: 'ಲಾಗಿನ್' },
      ];

  const getBadge = (item) => {
    if (!item.badge && !item.badgeEn && !item.badgeKn) return null;
    return language === 'kn' ? (item.badgeKn || item.badge) : (item.badgeEn || item.badge);
  };

  return (
    <aside className="desktop-sidebar glass-panel">
      {/* Core Features */}
      <div className="sidebar-section">
        <span className="sidebar-section-title">
          {language === 'kn' ? 'ಪ್ರಮುಖ ಕೃಷಿ ವಿಭಾಗಗಳು' : 'Core Agricultural Hubs'}
        </span>
        <nav className="sidebar-nav">
          {coreNavItems.map((item) => {
            const Icon = item.icon;
            const badge = getBadge(item);
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} className="sidebar-icon" />
                <span className="sidebar-label">
                  {language === 'kn' ? item.labelKn : item.labelEn}
                </span>
                {badge && <span className="sidebar-badge">{badge}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Services & Tools */}
      <div className="sidebar-section">
        <span className="sidebar-section-title">
          {language === 'kn' ? 'ಉಪಕರಣಗಳು ಮತ್ತು ಸೇವೆಗಳು' : 'Tools & Features'}
        </span>
        <nav className="sidebar-nav">
          {toolsNavItems.map((item) => {
            const Icon = item.icon;
            const badge = getBadge(item);
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} className="sidebar-icon" />
                <span className="sidebar-label">
                  {language === 'kn' ? item.labelKn : item.labelEn}
                </span>
                {badge && <span className="sidebar-badge">{badge}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom Actions */}
      <div className="sidebar-section sidebar-bottom">
        <nav className="sidebar-nav">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} className="sidebar-icon" />
                <span className="sidebar-label">
                  {language === 'kn' ? item.labelKn : item.labelEn}
                </span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};
