import React from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  Sprout,
  Bug,
  CloudSun,
  Coins,
  ShieldCheck,
  Droplets,
  FlaskConical,
  MessageSquare,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { usePromptTrigger } from '../../utils/usePromptTrigger';
import './ExplorePage.css';

export const ExplorePage = () => {
  const { language } = useLanguage();
  const { askSathi } = usePromptTrigger();

  const exploreCategories = [
    {
      id: 'crops',
      titleKn: 'ಬೆಳೆಗಳ ಸಮಗ್ರ ಮಾರ್ಗದರ್ಶಿ',
      titleEn: '15 Karnataka Crop Guides',
      descKn: 'ರಾಗಿ, ಭತ್ತ, ಕಬ್ಬು, ಹತ್ತಿ, ಅಡಿಕೆ ಮುಂತಾದ 15 ಪ್ರಮುಖ ಬೆಳೆಗಳ ಬಿತ್ತನೆ, ಮಣ್ಣು ಮತ್ತು ಇಳುವರಿ ಮಾಹಿತಿ.',
      descEn: 'Explore agronomic guides, optimal sowing calendars, and crop management for 15 verified crops.',
      icon: Sprout,
      link: '/crops',
      badge: '15 Crops',
    },
    {
      id: 'schemes',
      titleKn: 'ಸರ್ಕಾರಿ ಕೃಷಿ ಯೋಜನೆಗಳು & ಸಬ್ಸಿಡಿ',
      titleEn: 'Government Schemes & Subsidies',
      descKn: 'ಕೃಷಿ ಭಾಗ್ಯ, PM-KISAN, ಬೆಳೆ ವಿಮೆ ಮತ್ತು ಭೂಮಿ ಪೋರ್ಟಲ್ ಸೌಲಭ್ಯಗಳ ಅಧಿಕೃತ ಮಾರ್ಗದರ್ಶಿ.',
      descEn: 'Verified state & central subsidies, eligibility checklists, and RSK application procedures.',
      icon: ShieldCheck,
      link: '/schemes',
      badge: 'Verified Subsidies',
    },
    {
      id: 'weather',
      titleKn: 'ಹವಾಮಾನ ಮತ್ತು ಸಿಂಪಡಣೆ ಸಲಹೆ',
      titleEn: 'Weather & Spray Advisories',
      descKn: 'ನೈಜ ಸಮಯದ ಮಳೆ ಮುನ್ಸೂಚನೆ, ತಾಪಮಾನ ಮತ್ತು ಕೀಟನಾಶಕ ಸಿಂಪಡಣೆಗೆ ಸೂಕ್ತ ಸಮಯದ ಮಾಹಿತಿ.',
      descEn: 'Real-time weather assessments, precipitation forecasts, and agricultural spray recommendations.',
      icon: CloudSun,
      link: '/weather',
      badge: 'Live Forecast',
    },
    {
      id: 'mandi',
      titleKn: 'ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ',
      titleEn: 'Mandi Market Prices',
      descKn: 'ಕರ್ನಾಟಕದ ಪ್ರಮುಖ ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ಧಾನ್ಯ, ತರಕಾರಿ ಮತ್ತು ವಾಣಿಜ್ಯ ಬೆಳೆಗಳ ಪ್ರಸ್ತುತ ದರಗಳು.',
      descEn: 'APMC market rate assessments for Ragi, Rice, Maize, Tomato, and Sugarcane.',
      icon: Coins,
      link: '/mandi',
      badge: 'APMC Rates',
    },
  ];

  const popularTopics = [
    {
      titleKn: 'ಕೀಟ ಮತ್ತು ರೋಗ ನಿಯಂತ್ರಣ',
      titleEn: 'Pest & Disease Control',
      icon: Bug,
      promptKn: 'ಟೊಮೆಟೊ, ಮೆಣಸಿನಕಾಯಿ ಮತ್ತು ಭತ್ತದ ಬೆಳೆಯ ಪ್ರಮುಖ ಕೀಟ-ರೋಗಗಳ ಲಕ್ಷಣ ಮತ್ತು ಸಾವಯವ ಪರಿಹಾರಗಳನ್ನು ತಿಳಿಸಿ.',
      promptEn: 'Explain organic and chemical control methods for major pests in tomato, chilli, and paddy.',
    },
    {
      titleKn: 'ರಸಗೊಬ್ಬರ ಮತ್ತು ಪೋಷಕಾಂಶ ನಿರ್ವಹಣೆ',
      titleEn: 'Fertilizer & Nutrition Schedule',
      icon: FlaskConical,
      promptKn: 'ರಾಗಿ ಮತ್ತು ಭತ್ತ ಬೆಳೆಗೆ ಹಂತವಾರು ಯೂರಿಯಾ, ಡಿಎಪಿ ಮತ್ತು ಪೊಟ್ಯಾಷ್ ಗೊಬ್ಬರ ಕೊಡುವ ವೇಳಾಪಟ್ಟಿ ತಿಳಿಸಿ.',
      promptEn: 'Give the step-by-step NPK fertilizer application schedule for Ragi and Paddy crops.',
    },
    {
      titleKn: 'ಹನಿ ನೀರಾವರಿ ಮತ್ತು ಮಣ್ಣಿನ ತೇವಾಂಶ',
      titleEn: 'Drip Irrigation & Soil Health',
      icon: Droplets,
      promptKn: 'ಬೇಸಿಗೆಯಲ್ಲಿ ತೋಟಗಾರಿಕಾ ಬೆಳೆಗಳಿಗೆ ಹನಿ ನೀರಾವರಿ ನಿರ್ವಹಣೆ ಮತ್ತು ಮಣ್ಣಿನ ತೇವಾಂಶ ಕಾಪಾಡುವ ವಿಧಾನಗಳು ಯಾವುವು?',
      promptEn: 'Best practices for drip irrigation and soil moisture conservation during hot summer months.',
    },
  ];

  return (
    <div className="explore-page-container">
      {/* Hero Header */}
      <header className="explore-hero-header">
        <div className="hero-badge">
          <Compass size={14} />
          <span>Knowledge Discovery / ಜ್ಞಾನ ಕೇಂದ್ರ</span>
        </div>
        <h1 className="explore-hero-title">
          {language === 'kn'
            ? 'ಕೃಷಿ ಜ್ಞಾನ ಮತ್ತು ಸೇವೆಗಳ ಅನ್ವೇಷಣೆ'
            : 'Explore Agricultural Knowledge & Tools'}
        </h1>
        <p className="explore-hero-subtitle">
          {language === 'kn'
            ? 'ರೈತ ಸಾಥಿಯ ಅಧಿಕೃತ ಕೃಷಿ ಮಾರ್ಗದರ್ಶಿಗಳು, ಬೆಳೆಗಳ ಮಾಹಿತಿ, ಮಾರುಕಟ್ಟೆ ದರಗಳು ಮತ್ತು ಹವಾಮಾನ ಸಲಹೆಗಳು ಒಂದೇ ವೇದಿಕೆಯಲ್ಲಿ.'
            : 'Your curated agricultural gateway to verified crop knowledge, government welfare schemes, weather advisories, and market pricing.'}
        </p>
      </header>

      {/* Core Services Grid */}
      <section className="explore-section">
        <div className="section-header-row">
          <h2 className="section-title">Core Agricultural Hubs / ಪ್ರಮುಖ ವಿಭಾಗಗಳು</h2>
        </div>

        <div className="explore-hubs-grid">
          {exploreCategories.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.id} to={item.link} className="explore-hub-card">
                <div className="hub-card-top">
                  <div className="hub-icon-box">
                    <Icon size={22} />
                  </div>
                  <span className="hub-badge">{item.badge}</span>
                </div>
                <h3 className="hub-title">{language === 'kn' ? item.titleKn : item.titleEn}</h3>
                <p className="hub-desc">{language === 'kn' ? item.descKn : item.descEn}</p>
                <div className="hub-action-link">
                  <span>Open Hub / ತೆರೆಯಿರಿ</span>
                  <ArrowRight size={14} className="arrow-icon" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Popular Agricultural Topics */}
      <section className="explore-section" style={{ marginTop: '2.5rem' }}>
        <div className="section-header-row">
          <h2 className="section-title">Common Farming Topics / ಜನಪ್ರಿಯ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳು</h2>
        </div>

        <div className="explore-topics-grid">
          {popularTopics.map((topic, idx) => {
            const Icon = topic.icon;
            const title = language === 'kn' ? topic.titleKn : topic.titleEn;
            const prompt = language === 'kn' ? topic.promptKn : topic.promptEn;

            return (
              <div key={idx} className="explore-topic-card">
                <div className="topic-card-header">
                  <div className="topic-icon-box">
                    <Icon size={18} />
                  </div>
                  <h3 className="topic-title">{title}</h3>
                </div>
                <p className="topic-prompt-preview">"{prompt}"</p>
                <button
                  type="button"
                  className="btn-topic-ask"
                  onClick={() => askSathi(prompt)}
                >
                  <MessageSquare size={13} />
                  <span>Ask Sathi / ಸಾಥಿ ಜೊತೆ ಮಾತನಾಡಿ</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
