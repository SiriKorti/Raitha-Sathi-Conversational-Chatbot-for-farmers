import React, { useState } from 'react';
import { Coins, MapPin, ArrowRight, MessageSquare, Info, TrendingUp } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { usePromptTrigger } from '../../utils/usePromptTrigger';
import './MandiPage.css';

const APMC_MARKETS = [
  { id: 'Mandya', nameEn: 'Mandya', nameKn: 'ಮಂಡ್ಯ' },
  { id: 'Mysuru (Bandipalya)', nameEn: 'Mysuru (Bandipalya)', nameKn: 'ಮೈಸೂರು (ಬಂಡಿಪಾಳ್ಯ)' },
  { id: 'Bengaluru (Yeshwanthpur)', nameEn: 'Bengaluru (Yeshwanthpur)', nameKn: 'ಬೆಂಗಳೂರು (ಯಶವಂತಪುರ)' },
  { id: 'Belagavi', nameEn: 'Belagavi', nameKn: 'ಬೆಳಗಾವಿ' },
  { id: 'Davangere', nameEn: 'Davangere', nameKn: 'ದಾವಣಗೆರೆ' },
  { id: 'Hassan', nameEn: 'Hassan', nameKn: 'ಹಾಸನ' },
  { id: 'Shivamogga', nameEn: 'Shivamogga', nameKn: 'ಶಿವಮೊಗ್ಗ' },
  { id: 'Ballari', nameEn: 'Ballari', nameKn: 'ಬಳ್ಳಾರಿ' },
];

const COMMODITIES = [
  { id: 'ragi', nameKn: 'ರಾಗಿ', nameEn: 'Finger Millet (Ragi)', key: 'ರಾಗಿ' },
  { id: 'rice', nameKn: 'ಭತ್ತ', nameEn: 'Paddy / Rice', key: 'ಭತ್ತ' },
  { id: 'maize', nameKn: 'ಮೆಕ್ಕೆಜೋಳ', nameEn: 'Maize / Corn', key: 'ಮೆಕ್ಕೆಜೋಳ' },
  { id: 'tomato', nameKn: 'ಟೊಮೆಟೊ', nameEn: 'Tomato', key: 'ಟೊಮೆಟೊ' },
  { id: 'sugarcane', nameKn: 'ಕಬ್ಬು', nameEn: 'Sugarcane', key: 'ಕಬ್ಬು' },
];

export const MandiPage = () => {
  const { language } = useLanguage();
  const { askSathi } = usePromptTrigger();
  const isKn = language === 'kn';

  const [selectedMarketId, setSelectedMarketId] = useState('Mandya');
  const [customQuery, setCustomQuery] = useState('');

  const currentMarket = APMC_MARKETS.find((m) => m.id === selectedMarketId) || APMC_MARKETS[0];
  const marketDisplayName = isKn ? currentMarket.nameKn : currentMarket.nameEn;

  const handlePriceCheck = (cropKey, marketName) => {
    const prompt = isKn
      ? `${marketName} ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಇಂದಿನ ${cropKey} ಕ್ವಿಂಟಾಲ್ ಬೆಲೆ ಮತ್ತು ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ ಎಷ್ಟು?`
      : `What is the current APMC Mandi market price per quintal for ${cropKey} in ${marketName}?`;
    askSathi(prompt);
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    const prompt = customQuery.trim()
      ? `${marketDisplayName}: ${customQuery}`
      : (isKn
          ? `${marketDisplayName} ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಇಂದಿನ ಬೆಲೆ ಧಾರಣೆ ಮಾಹಿತಿ ತಿಳಿಸಿ.`
          : `Provide latest APMC mandi price insights for ${marketDisplayName}.`);
    askSathi(prompt);
  };

  return (
    <div className="mandi-page-container">
      {/* Hero Header */}
      <header className="mandi-hero-header">
        <div className="hero-badge">
          <Coins size={14} />
          <span>{isKn ? 'ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ದರಗಳು & ಮಾರಾಟ ಸಲಹೆ' : 'APMC Market Rates & Advisory'}</span>
        </div>
        <h1 className="mandi-hero-title">
          {isKn
            ? 'ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ ಮತ್ತು ಮಾರಾಟ ಸಲಹೆ'
            : 'APMC Mandi Market Prices & Commodity Insights'}
        </h1>
        <p className="mandi-hero-subtitle">
          {isKn
            ? 'ಕರ್ನಾಟಕದ ಪ್ರಮುಖ ಕೃಷಿ ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ರಾಗಿ, ಭತ್ತ, ಮೆಕ್ಕೆಜೋಳ, ಟೊಮೆಟೊ ಹಾಗೂ ಕಬ್ಬಿನ ದರಗಳನ್ನು ಸಾಥಿ ಮೂಲಕ ಪರಿಶೀಲಿಸಿ.'
            : 'Get daily APMC market rates per quintal across Karnataka — sourced from Government of India market data.'}
        </p>

        {/* Backend Transparency Banner */}
        <div className="mandi-notice-box" role="status">
          <Info size={16} className="notice-icon" />
          <div className="notice-content">
            <span className="notice-headline">
              {isKn ? 'ಭಾರತ ಸರ್ಕಾರದ ಅಧಿಕೃತ APMC (data.gov.in) ಡೇಟಾ ಆಧಾರಿತ' : 'Powered by Government of India APMC Data'}
            </span>
            <p className="notice-body">
              {isKn
                ? 'ದೈನಂದಿನ ಸಗಟು ಮಾರುಕಟ್ಟೆ ಧಾರಣೆಗಳನ್ನು ಭಾರತ ಸರ್ಕಾರದ ಕೃಷಿ ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಜಾಲದಿಂದ (AGMARKNET) ಪಡೆಯಲಾಗುತ್ತದೆ. ಬೆಲೆಗಳು ಪ್ರತಿ ಕ್ವಿಂಟಾಲ್‌ಗೆ ರೂಪಾಯಿಗಳಲ್ಲಿವೆ.'
                : 'Daily wholesale prices are fetched from the official Government of India Open Data API (data.gov.in), sourced from AGMARKNET — the national agricultural market information network. Prices are in rupees per quintal.'}
            </p>
          </div>
        </div>
      </header>

      {/* Market Selector Bar */}
      <section className="mandi-selector-section">
        <span className="section-label">
          <MapPin size={14} />
          <span>{isKn ? 'ಮಾರುಕಟ್ಟೆ ಆಯ್ಕೆಮಾಡಿ:' : 'Select APMC Market Yard:'}</span>
        </span>
        <div className="market-pills-row">
          {APMC_MARKETS.map((market) => (
            <button
              key={market.id}
              type="button"
              className={`market-pill ${selectedMarketId === market.id ? 'active' : ''}`}
              onClick={() => setSelectedMarketId(market.id)}
            >
              {isKn ? market.nameKn : market.nameEn}
            </button>
          ))}
        </div>
      </section>

      {/* Supported Commodities Quick Cards */}
      <section className="mandi-commodities-grid">
        {COMMODITIES.map((item) => (
          <article key={item.id} className="mandi-commodity-card">
            <div className="card-top-row">
              <div className="commodity-icon-box">
                <Coins size={20} />
              </div>
              <span className="market-tag">{marketDisplayName}</span>
            </div>

            <h3 className="commodity-name">{isKn ? item.nameKn : item.nameEn}</h3>
            <span className="commodity-sub">{isKn ? item.nameEn : item.nameKn}</span>

            <div className="commodity-price-prompt">
              <span>{isKn ? 'ಪ್ರಸ್ತುತ ಪ್ರತಿ ಕ್ವಿಂಟಾಲ್ ಮಾರುಕಟ್ಟೆ ಬೆಲೆ' : 'Current price per quintal'}</span>
            </div>

            <button
              type="button"
              className="btn-check-price"
              onClick={() => handlePriceCheck(item.key, marketDisplayName)}
            >
              <TrendingUp size={14} />
              <span>{isKn ? `${item.nameKn} ದರ ಪರಿಶೀಲಿಸಿ` : `Check ${item.nameEn} Price`}</span>
              <ArrowRight size={14} />
            </button>
          </article>
        ))}
      </section>

      {/* Custom Mandi Question */}
      <section className="mandi-custom-card">
        <div className="custom-card-header">
          <MessageSquare size={16} className="header-icon" />
          <h3>
            {isKn
              ? `${marketDisplayName} ಮಾರುಕಟ್ಟೆಯ ಮಾರಾಟ ಸಲಹೆ ಅಥವಾ ಬೆಂಬಲ ಬೆಲೆ (MSP) ಕುರಿತು ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ`
              : `Ask Sathi about commodity selling advice or MSP in ${marketDisplayName}`}
          </h3>
        </div>
        <form onSubmit={handleCustomSubmit} className="custom-mandi-form">
          <input
            type="text"
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder={
              isKn
                ? `ಉದಾ: ${marketDisplayName} ನಲ್ಲಿ ಉತ್ತಮ ಬೆಲೆಗೆ ಧಾನ್ಯ ಮಾರಾಟ ಮಾಡಲು ಸೂಕ್ತ ಸಮಯ ಯಾವುದು?`
                : `e.g., When is the best time to sell in ${marketDisplayName} for maximum returns?`
            }
            className="text-input"
          />
          <button type="submit" className="btn-mandi-submit">
            <span>{isKn ? 'ಸಾಥಿ ಮಾರುಕಟ್ಟೆ ಸಲಹೆ ಪಡೆಯಿರಿ' : 'Ask Sathi Market Advice'}</span>
            <ArrowRight size={14} />
          </button>
        </form>
      </section>
    </div>
  );
};
