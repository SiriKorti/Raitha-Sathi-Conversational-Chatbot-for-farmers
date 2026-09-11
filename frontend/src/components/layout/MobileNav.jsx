import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  MessageSquare,
  Sprout,
  ShieldCheck,
  Compass,
  Menu,
  X,
  History,
  TrendingUp,
  CloudSun,
  Coins,
  Camera,
  Bookmark,
  Settings,
  HelpCircle,
  LogIn,
} from 'lucide-react';
import './MobileNav.css';

export const MobileNav = () => {
  const { language } = useLanguage();
  const { isAuthenticated, user } = useAuth();
  const isLoggedIn = isAuthenticated || Boolean(user);
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  const moreItems = [
    { to: '/mandi', icon: Coins, labelEn: 'Mandi Prices', labelKn: 'ಮಾರುಕಟ್ಟೆ ದರ' },
    { to: '/history', icon: History, labelEn: 'Chat History', labelKn: 'ಹಿಂದಿನ ಚರ್ಚೆಗಳು' },
    { to: '/progress', icon: TrendingUp, labelEn: 'Crop Progress', labelKn: 'ಬೆಳೆ ಹಂತಗಳು' },
    { to: '/diagnosis', icon: Camera, labelEn: 'Visual Diagnosis', labelKn: 'ರೋಗ ನಿರ್ಣಯ' },
    { to: '/saved', icon: Bookmark, labelEn: 'Saved Advice', labelKn: 'ಉಳಿಸಿದ ಸಲಹೆಗಳು' },
    { to: '/settings', icon: Settings, labelEn: 'Settings', labelKn: 'ಸೆಟ್ಟಿಂಗ್ಸ್' },
    { to: '/help', icon: HelpCircle, labelEn: 'Help & Support', labelKn: 'ಸಹಾಯ' },
    ...(!isLoggedIn ? [{ to: '/login', icon: LogIn, labelEn: 'Login / Register', labelKn: 'ಲಾಗಿನ್' }] : []),
  ];

  return (
    <>
      {/* More Sheet Modal for Mobile */}
      {isMoreOpen && (
        <div className="mobile-more-backdrop" onClick={() => setIsMoreOpen(false)}>
          <div className="mobile-more-sheet glass-panel animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="mobile-more-header">
              <h3>{language === 'kn' ? 'ಹೆಚ್ಚಿನ ಸೇವೆಗಳು' : 'More Services'}</h3>
              <button className="btn-icon" onClick={() => setIsMoreOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="mobile-more-grid">
              {moreItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className="mobile-more-item glass-panel-hover"
                    onClick={() => setIsMoreOpen(false)}
                  >
                    <div className="mobile-more-icon-box">
                      <Icon size={20} />
                    </div>
                    <span>{language === 'kn' ? item.labelKn : item.labelEn}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Fixed Mobile Bottom Bar */}
      <nav className="mobile-bottom-nav glass-panel">
        <NavLink to="/crops" className={({ isActive }) => `mobile-nav-tab ${isActive ? 'active' : ''}`}>
          <Sprout size={20} />
          <span>{language === 'kn' ? 'ಬೆಳೆಗಳು' : 'Crops'}</span>
        </NavLink>

        <NavLink to="/chat" className={({ isActive }) => `mobile-nav-tab chat-glow-tab ${isActive ? 'active' : ''}`}>
          <div className="chat-glow-icon">
            <MessageSquare size={22} />
          </div>
          <span>{language === 'kn' ? 'ಸಾಥಿ' : 'Ask Sathi'}</span>
        </NavLink>

        <NavLink to="/schemes" className={({ isActive }) => `mobile-nav-tab ${isActive ? 'active' : ''}`}>
          <ShieldCheck size={20} />
          <span>{language === 'kn' ? 'ಯೋಜನೆಗಳು' : 'Schemes'}</span>
        </NavLink>

        <NavLink to="/weather" className={({ isActive }) => `mobile-nav-tab ${isActive ? 'active' : ''}`}>
          <CloudSun size={20} />
          <span>{language === 'kn' ? 'ಹವಾಮಾನ' : 'Weather'}</span>
        </NavLink>

        <button
          type="button"
          className={`mobile-nav-tab ${isMoreOpen ? 'active' : ''}`}
          onClick={() => setIsMoreOpen((prev) => !prev)}
        >
          <Menu size={20} />
          <span>{language === 'kn' ? 'ಇನ್ನಷ್ಟು' : 'More'}</span>
        </button>
      </nav>
    </>
  );
};
