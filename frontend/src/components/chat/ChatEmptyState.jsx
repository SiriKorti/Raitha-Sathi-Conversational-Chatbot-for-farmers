import React, { useMemo } from 'react';
import { Sprout, Bug, Droplets, Sparkles, CloudSun, ShieldCheck, ArrowUpRight } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import './ChatEmptyState.css';

export const ChatEmptyState = ({ onSelectPrompt }) => {
  const { language } = useLanguage();
  const { user } = useAuth();

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    const rawName = user?.name || user?.fullName || '';
    const cleanName = (rawName === 'Ramesh Gowda' || user?.id === 'farmer_001') ? 'farmer-01' : rawName;
    const name = cleanName ? ` ${cleanName}` : '';
    if (language === 'kn') {
      if (hour < 12) return `ಶುಭೋದಯ${name}!`;
      if (hour < 17) return `ಶುಭ ಮಧ್ಯಾಹ್ನ${name}!`;
      return `ಶುಭ ಸಂಜೆ${name}!`;
    }
    if (hour < 12) return `Good morning${name}`;
    if (hour < 17) return `Good afternoon${name}`;
    return `Good evening${name}`;
  }, [language, user]);

  const promptSuggestions = [
    {
      icon: Bug,
      category: 'Pest & Disease',
      titleKn: 'ಟೊಮೆಟೊ ಎಲೆ ಮುದುರು ರೋಗಕ್ಕೆ ಪರಿಹಾರವೇನು?',
      titleEn: 'How to control leaf curl pest in tomato?',
    },
    {
      icon: Sprout,
      category: 'Fertilizer Guide',
      titleKn: 'ಭತ್ತದ ಬೆಳೆಗೆ ರಸಗೊಬ್ಬರ ಪ್ರಮಾಣ ಮತ್ತು ಸಮಯ ತಿಳಿಸಿ',
      titleEn: 'What is the fertilizer dosage and schedule for paddy?',
    },
    {
      icon: CloudSun,
      category: 'Weather Advisory',
      titleKn: 'ಇಂದಿನ ಹವಾಮಾನ ಹೇಗಿದೆ? ಔಷಧ ಸಿಂಪಡಿಸಬಹುದೇ?',
      titleEn: 'What is the weather today? Is it safe to spray?',
    },
    {
      icon: ShieldCheck,
      category: 'Government Schemes',
      titleKn: 'ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆಯ ಸಬ್ಸಿಡಿ ಮತ್ತು ಅರ್ಜಿ ವಿಧಾನ ತಿಳಿಸಿ',
      titleEn: 'Tell me about Krishi Bhagya scheme benefits & application',
    },
  ];

  const getPromptText = (item) => {
    if (language === 'en') return item.titleEn;
    return item.titleKn;
  };

  return (
    <div className="chat-empty-state-container">
      <div className="empty-state-hero">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          <span>{language === 'kn' ? 'ರೈತ ಸಾಥಿ AI' : 'Raitha Sathi AI'}</span>
        </div>
        <h1 className="hero-title">{greeting}</h1>
        <p className="hero-subtitle">
          {language === 'en'
            ? 'Your dedicated farming companion. Ask about crops, pest remedies, weather, market trends, farming decisions, or simply discuss how things are going on your farm.'
            : 'ನಿಮ್ಮ ಆತ್ಮೀಯ ಕೃಷಿ ಸಂಗಾತಿ. ಬೆಳೆ ರಕ್ಷಣೆ, ರೋಗ ಪರಿಹಾರ, ಹವಾಮಾನ, ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ, ಕೃಷಿ ನಿರ್ಧಾರಗಳ ಕುರಿತು ಮುಕ್ತವಾಗಿ ಮಾತನಾಡಿ.'}
        </p>
      </div>


      <div className="prompt-suggestions-grid">
        {promptSuggestions.map((item, index) => {
          const Icon = item.icon;
          const text = getPromptText(item);
          return (
            <button
              key={index}
              type="button"
              className="prompt-card"
              onClick={() => onSelectPrompt(text)}
            >
              <div className="prompt-card-top">
                <div className="prompt-icon">
                  <Icon size={16} />
                </div>
                <span className="prompt-category">{item.category}</span>
                <ArrowUpRight size={14} className="prompt-arrow-icon" />
              </div>
              <p className="prompt-text">{text}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
};
