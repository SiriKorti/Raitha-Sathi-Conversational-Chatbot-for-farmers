import React, { useState, useEffect, useMemo } from 'react';
import { Search, Sprout, MessageSquare, AlertTriangle, ArrowRight, Bug } from 'lucide-react';
import { cropService } from '../../services/cropService';
import { CROPS_DATA } from '../../data/cropsData';
import { useLanguage } from '../../context/LanguageContext';
import { usePromptTrigger } from '../../utils/usePromptTrigger';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import './CropsPage.css';

const CATEGORY_LABELS = {
  All: { en: 'All Crops', kn: 'ಎಲ್ಲಾ ಬೆಳೆಗಳು' },
  'Millet & Cereal': { en: 'Millet & Cereal', kn: 'ಸಿರಿಧಾನ್ಯ & ಧಾನ್ಯ' },
  Cereal: { en: 'Cereals', kn: 'ಧಾನ್ಯಗಳು' },
  Commercial: { en: 'Commercial', kn: 'ವಾಣಿಜ್ಯ ಬೆಳೆ' },
  'Commercial & Fiber': { en: 'Fiber & Commercial', kn: 'ನಾರಿನ ಬೆಳೆ' },
  Plantation: { en: 'Plantation', kn: 'ತೋಟಗಾರಿಕೆ' },
  Oilseed: { en: 'Oilseeds', kn: 'ಎಣ್ಣೆಕಾಳು' },
  'Spice & Commercial': { en: 'Spices', kn: 'ಮಸಾಲೆ ಬೆಳೆ' },
  Pulse: { en: 'Pulses', kn: 'ದ್ವಿದಳ ಧಾನ್ಯ' },
};

export const CropsPage = () => {
  const { language } = useLanguage();
  const { askSathi } = usePromptTrigger();
  const isKn = language === 'kn';

  const [backendCrops, setBackendCrops] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [expandedCropId, setExpandedCropId] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchCrops = async () => {
      setIsLoading(true);
      try {
        const res = await cropService.getCrops();
        if (isMounted) {
          setBackendCrops(res?.crops || []);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          console.warn('[CropsPage] Could not load crop list from backend:', err);
          setError(
            isKn
              ? 'ಸರ್ವರ್‌ನಿಂದ ಬೆಳೆಗಳ ಪಟ್ಟಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಪರಿಶೀಲಿಸಿದ ಸ್ಥಳೀಯ ಕೃಷಿ ಮಾಹಿತಿ ಪ್ರದರ್ಶಿಸಲಾಗುತ್ತಿದೆ.'
              : 'Failed to sync with backend crops catalog. Showing verified local knowledgebase.'
          );
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchCrops();
    return () => {
      isMounted = false;
    };
  }, [isKn]);

  const categories = useMemo(() => {
    const rawCats = Array.from(new Set(CROPS_DATA.map((c) => c.categoryEn || c.category)));
    return ['All', ...rawCats];
  }, []);

  const filteredCrops = useMemo(() => {
    return CROPS_DATA.filter((crop) => {
      const cropCategory = crop.categoryEn || crop.category;
      const matchesCategory = selectedCategory === 'All' || cropCategory === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        crop.nameEn.toLowerCase().includes(q) ||
        crop.nameKn.includes(q) ||
        (crop.soilEn && crop.soilEn.toLowerCase().includes(q)) ||
        (crop.soilKn && crop.soilKn.includes(q)) ||
        (crop.seasonEn && crop.seasonEn.toLowerCase().includes(q)) ||
        (crop.seasonKn && crop.seasonKn.includes(q));
      return matchesCategory && matchesSearch;
    });
  }, [searchQuery, selectedCategory]);

  return (
    <div className="crops-page-container">
      {/* Hero Header */}
      <header className="crops-hero-header">
        <div className="hero-badge">
          <Sprout size={14} />
          <span>
            {isKn ? '15 ಅಧಿಕೃತ ಕರ್ನಾಟಕ ಕೃಷಿ ಬೆಳೆಗಳ ಮಾರ್ಗದರ್ಶಿ' : '15 Verified Karnataka Crop Guides'}
          </span>
        </div>
        <h1 className="crops-hero-title">
          {isKn
            ? 'ಕರ್ನಾಟಕದ ಪ್ರಮುಖ ಬೆಳೆಗಳ ಸಮಗ್ರ ಮಾಹಿತಿ'
            : 'Karnataka Crop Knowledge & Advisory Hub'}
        </h1>
        <p className="crops-hero-subtitle">
          {isKn
            ? 'ಬಿತ್ತನೆ ಸಮಯ, ಮಣ್ಣಿನ ಅಗತ್ಯತೆ, ಗೊಬ್ಬರ ಪ್ರಮಾಣ ಮತ್ತು ಕೀಟ-ರೋಗಗಳ ನಿರ್ವಹಣೆಯ ಅಧಿಕೃತ ಕೃಷಿ ಮಾಹಿತಿ.'
            : 'Explore verified agronomic guides, season timelines, fertilizer schedules, and disease remedies.'}
        </p>

        {/* Search & Filter Toolbar */}
        <div className="crops-toolbar">
          <div className="crops-search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                isKn
                  ? 'ಬೆಳೆ ಅಥವಾ ರೋಗದ ಹೆಸರು ಹುಡುಕಿ (ಉದಾ: ರಾಗಿ, ಭತ್ತ, ಕಬ್ಬು)...'
                  : 'Search by crop name, season, or soil type...'
              }
              className="crops-search-input"
            />
          </div>

          <div className="crops-category-chips" role="group" aria-label="Crop Categories">
            {categories.map((cat) => {
              const label = CATEGORY_LABELS[cat] ? (isKn ? CATEGORY_LABELS[cat].kn : CATEGORY_LABELS[cat].en) : cat;
              return (
                <button
                  key={cat}
                  type="button"
                  className={`category-chip ${selectedCategory === cat ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <main className="crops-content-body">
        {isLoading ? (
          <div className="crops-loading-state">
            <LoadingSpinner
              size="large"
              label={isKn ? 'ಬೆಳೆಗಳ ಮಾಹಿತಿ ಪಡೆಯಲಾಗುತ್ತಿದೆ...' : 'Loading verified crop database...'}
            />
          </div>
        ) : error ? (
          <div className="crops-error-banner" role="alert">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        ) : filteredCrops.length === 0 ? (
          <div className="crops-empty-state">
            <Sprout size={36} className="empty-icon" />
            <h3>{isKn ? 'ಯಾವುದೇ ಬೆಳೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No crops found'}</h3>
            <p>{isKn ? 'ಬೇರೆ ಹುಡುಕಾಟ ಅಥವಾ ವರ್ಗವನ್ನು ಆಯ್ಕೆಮಾಡಿ.' : 'Try adjusting your search query or category filter.'}</p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('All');
              }}
            >
              {isKn ? 'ಫಿಲ್ಟರ್ ಮರುಹೊಂದಿಸಿ' : 'Reset Filters'}
            </button>
          </div>
        ) : (
          <div className="crops-cards-grid">
            {filteredCrops.map((crop) => {
              const isExpanded = expandedCropId === crop.id;
              const primaryName = isKn ? crop.nameKn : crop.nameEn;
              const secondaryName = isKn ? crop.nameEn : crop.nameKn;
              const categoryBadge = isKn ? (crop.categoryKn || crop.category) : (crop.categoryEn || crop.category);
              const seasonValue = isKn ? (crop.seasonKn || crop.season) : (crop.seasonEn || crop.season);
              const soilValue = isKn ? (crop.soilKn || crop.soil) : (crop.soilEn || crop.soil);
              const durationValue = isKn ? (crop.durationKn || crop.duration) : (crop.durationEn || crop.duration);
              const pestsList = isKn ? (crop.commonPestsKn || crop.commonPests) : (crop.commonPestsEn || crop.commonPests);

              return (
                <article key={crop.id} className={`crop-card ${isExpanded ? 'expanded' : ''}`}>
                  <div className="crop-card-top">
                    <div className="crop-icon-box">{crop.icon}</div>
                    <div className="crop-title-meta">
                      <h2 className="crop-name-kn">{primaryName}</h2>
                      <span className="crop-name-en">{secondaryName}</span>
                    </div>
                    <span className="crop-category-badge">{categoryBadge}</span>
                  </div>

                  <div className="crop-quick-details">
                    <div className="detail-item">
                      <span className="detail-label">{isKn ? 'ಕಾಲ:' : 'Season:'}</span>
                      <span className="detail-value">{seasonValue}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">{isKn ? 'ಮಣ್ಣು:' : 'Soil:'}</span>
                      <span className="detail-value">{soilValue}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">{isKn ? 'ಅವಧಿ:' : 'Duration:'}</span>
                      <span className="detail-value">{durationValue}</span>
                    </div>
                  </div>

                  {/* Major Pests Badge List */}
                  <div className="crop-pests-section">
                    <span className="pests-title">
                      <Bug size={13} />
                      <span>{isKn ? 'ಪ್ರಮುಖ ಕೀಟ-ರೋಗಗಳು:' : 'Major Pests & Diseases:'}</span>
                    </span>
                    <div className="pests-tags-list">
                      {pestsList.map((pest, idx) => (
                        <span key={idx} className="pest-tag">
                          {pest}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Sample Questions with Ask Sathi Triggers */}
                  <div className="crop-prompts-section">
                    <span className="prompts-title">
                      <MessageSquare size={13} />
                      <span>{isKn ? 'ಸಾಥಿ ಜೊತೆ ಈ ಬೆಳೆಯ ಬಗ್ಗೆ ಕೇಳಿ:' : 'Ask Sathi about this crop:'}</span>
                    </span>
                    <div className="crop-prompts-list">
                      {crop.sampleQuestions.map((sample, sIdx) => {
                        const promptText = isKn ? sample.qKn : sample.qEn;
                        return (
                          <button
                            key={sIdx}
                            type="button"
                            className="crop-prompt-btn"
                            onClick={() => askSathi(promptText)}
                            title={isKn ? 'ಈ ಪ್ರಶ್ನೆಯನ್ನು ಚಾಟ್‌ನಲ್ಲಿ ಕೇಳಲು ಕ್ಲಿಕ್ ಮಾಡಿ' : 'Click to ask Sathi this question in chat'}
                          >
                            <span>{promptText}</span>
                            <ArrowRight size={13} className="arrow-icon" />
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Footer Action */}
                  <div className="crop-card-footer">
                    <button
                      type="button"
                      className="btn-ask-custom"
                      onClick={() =>
                        askSathi(
                          isKn
                            ? `${crop.nameKn} ಬೆಳೆಯ ಸಂಪೂರ್ಣ ಬೇಸಾಯ ಕ್ರಮಗಳು, ಗೊಬ್ಬರ ಪ್ರಮಾಣ ಮತ್ತು ರೋಗ ನಿರ್ವಹಣೆ ತಿಳಿಸಿ.`
                            : `Explain complete cultivation practices, fertilizer dosage, and pest management for ${crop.nameEn}.`
                        )
                      }
                    >
                      <span>{isKn ? 'ಸಾಥಿ ಸಮಗ್ರ ಮಾಹಿತಿ ಪಡೆಯಿರಿ' : 'Ask Sathi Full Advisory'}</span>
                      <ArrowRight size={14} />
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
