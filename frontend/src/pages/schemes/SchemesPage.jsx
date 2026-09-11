import React, { useState, useMemo } from 'react';
import { ShieldCheck, Search, FileText, CheckCircle2, Gift, MessageSquare, ArrowRight } from 'lucide-react';
import { SCHEMES_DATA } from '../../data/schemesData';
import { useLanguage } from '../../context/LanguageContext';
import { usePromptTrigger } from '../../utils/usePromptTrigger';
import './SchemesPage.css';

export const SchemesPage = () => {
  const { language } = useLanguage();
  const { askSathi } = usePromptTrigger();
  const isKn = language === 'kn';

  const [searchQuery, setSearchQuery] = useState('');

  const filteredSchemes = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return SCHEMES_DATA;
    return SCHEMES_DATA.filter((scheme) => {
      return (
        (scheme.nameEn && scheme.nameEn.toLowerCase().includes(q)) ||
        (scheme.nameKn && scheme.nameKn.toLowerCase().includes(q)) ||
        (scheme.descriptionEn && scheme.descriptionEn.toLowerCase().includes(q)) ||
        (scheme.descriptionKn && scheme.descriptionKn.toLowerCase().includes(q)) ||
        (scheme.categoryEn && scheme.categoryEn.toLowerCase().includes(q)) ||
        (scheme.categoryKn && scheme.categoryKn.toLowerCase().includes(q)) ||
        (scheme.eligibilityEn && scheme.eligibilityEn.toLowerCase().includes(q)) ||
        (scheme.eligibilityKn && scheme.eligibilityKn.toLowerCase().includes(q))
      );
    });
  }, [searchQuery]);

  return (
    <div className="schemes-page-container">
      {/* Hero Header */}
      <header className="schemes-hero-header">
        <div className="hero-badge">
          <ShieldCheck size={14} />
          <span>
            {isKn ? 'ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿಗಳು ಮತ್ತು ಕೃಷಿ ಯೋಜನೆಗಳು' : 'Verified Government Subsidies & Welfare'}
          </span>
        </div>
        <h1 className="schemes-hero-title">
          {isKn
            ? 'ಸರ್ಕಾರಿ ಕೃಷಿ ಯೋಜನೆಗಳು ಮತ್ತು ಸಬ್ಸಿಡಿ ಮಾಹಿತಿ'
            : 'Government Schemes & Farmer Subsidies Guide'}
        </h1>
        <p className="schemes-hero-subtitle">
          {isKn
            ? 'ಕರ್ನಾಟಕ ಮತ್ತು ಕೇಂದ್ರ ಸರ್ಕಾರದ ಅಧಿಕೃತ ಕೃಷಿ ಯೋಜನೆಗಳು, ಅರ್ಹತಾ ಮಾನದಂಡಗಳು ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಕೆಯ ಮಾಹಿತಿ.'
            : 'Official verified state and central agricultural schemes, subsidy rates, eligibility criteria, and application steps.'}
        </p>

        {/* Search Input */}
        <div className="schemes-search-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={
              isKn
                ? 'ಯೋಜನೆಯ ಹೆಸರು ಅಥವಾ ಸಬ್ಸಿಡಿ ಹುಡುಕಿ (ಉದಾ: ಕೃಷಿ ಭಾಗ್ಯ, PM-KISAN, ವಿಮೆ)...'
                : 'Search schemes by name, subsidy benefit, or eligibility...'
            }
            className="schemes-search-input"
          />
        </div>
      </header>

      {/* Schemes Grid */}
      <main className="schemes-content-body">
        {filteredSchemes.length === 0 ? (
          <div className="schemes-empty-state">
            <ShieldCheck size={36} className="empty-icon" />
            <h3>{isKn ? 'ಯಾವುದೇ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No schemes matched your search'}</h3>
            <p>
              {isKn
                ? 'ಕೃಷಿ ಭಾಗ್ಯ, PM-KISAN, ಭೂಮಿ ಅಥವಾ ಬೆಳೆ ವಿಮೆ ಎಂದು ಹುಡುಕಿ ನೋಡಿ.'
                : 'Try searching for Krishi Bhagya, PM-KISAN, Bhoomi, or PMFBY.'}
            </p>
          </div>
        ) : (
          <div className="schemes-cards-list">
            {filteredSchemes.map((scheme) => {
              const title = isKn ? scheme.nameKn : scheme.nameEn;
              const category = isKn ? scheme.categoryKn : scheme.categoryEn;
              const description = isKn ? scheme.descriptionKn : scheme.descriptionEn;
              const eligibility = isKn ? scheme.eligibilityKn : scheme.eligibilityEn;
              const benefits = isKn ? scheme.benefitsKn : scheme.benefitsEn;
              const applicationProcess = isKn ? scheme.applicationProcessKn : scheme.applicationProcessEn;

              return (
                <article key={scheme.id} className="scheme-card">
                  <div className="scheme-card-header">
                    <div className="scheme-badge-row">
                      <span className="scheme-category-tag">{category}</span>
                      <span className="scheme-verified-pill">
                        <CheckCircle2 size={12} />
                        <span>{isKn ? 'ಅಧಿಕೃತ ಯೋಜನೆ' : 'Verified Scheme'}</span>
                      </span>
                    </div>
                    <h2 className="scheme-title">{title}</h2>
                    <p className="scheme-description">{description}</p>
                  </div>

                  <div className="scheme-details-grid">
                    {/* Eligibility */}
                    <div className="scheme-detail-block">
                      <div className="detail-header">
                        <FileText size={14} className="detail-icon" />
                        <span>{isKn ? 'ಅರ್ಹತೆ:' : 'Eligibility:'}</span>
                      </div>
                      <p className="detail-text">{eligibility}</p>
                    </div>

                    {/* Benefits */}
                    <div className="scheme-detail-block benefit-block">
                      <div className="detail-header">
                        <Gift size={14} className="detail-icon" />
                        <span>{isKn ? 'ಸೌಲಭ್ಯಗಳು ಮತ್ತು ಸಬ್ಸಿಡಿ:' : 'Subsidies & Benefits:'}</span>
                      </div>
                      <p className="detail-text">{benefits}</p>
                    </div>
                  </div>

                  {/* Application Process */}
                  <div className="scheme-apply-box">
                    <span className="apply-title">
                      {isKn ? 'ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ:' : 'How to Apply:'}
                    </span>
                    <p className="apply-text">{applicationProcess}</p>
                  </div>

                  {/* Action Row */}
                  <div className="scheme-card-actions">
                    <button
                      type="button"
                      className="btn-scheme-ask"
                      onClick={() =>
                        askSathi(
                          isKn
                            ? `${title} ಯೋಜನೆಯ ಅರ್ಹತೆ, ಸಬ್ಸಿಡಿ ವಿವರ ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಸಂಪೂರ್ಣ ವಿಧಾನ ತಿಳಿಸಿ.`
                            : `Explain detailed eligibility, subsidy calculation, and application steps for ${title}.`
                        )
                      }
                    >
                      <MessageSquare size={14} />
                      <span>{isKn ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Ask Sathi About This Scheme'}</span>
                      <ArrowRight size={14} className="arrow-icon" />
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};
