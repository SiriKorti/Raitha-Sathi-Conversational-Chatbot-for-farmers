import React, { useState, useEffect } from 'react';
import {
  Sprout,
  MapPin,
  Layers,
  Droplet,
  Save,
  Plus,
  X,
  Edit3,
  CheckCircle2,
  AlertCircle,
  User,
} from 'lucide-react';
import { useFarm } from '../../context/FarmContext';
import { useLanguage } from '../../context/LanguageContext';
import { PageHeader } from '../../components/common/PageHeader';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import './FarmPage.css';

export const FarmPage = () => {
  const { farmProfile, isSetup, updateFarmProfile, isLoading, error } = useFarm();
  const { t, language } = useLanguage();
  const isKn = language === 'kn';

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    farmerName: '',
    location: '',
    landArea: '',
    soilType: '',
    irrigationType: '',
    crops: [],
  });
  const [newCropInput, setNewCropInput] = useState('');

  // Populate form data whenever farmProfile changes
  useEffect(() => {
    if (farmProfile) {
      setFormData({
        farmerName: farmProfile.farmerName || '',
        location: farmProfile.location || '',
        landArea: farmProfile.landArea || '',
        soilType: farmProfile.soilType || '',
        irrigationType: farmProfile.irrigationType || '',
        crops: Array.isArray(farmProfile.crops) ? [...farmProfile.crops] : [],
      });
    }
  }, [farmProfile]);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddCrop = () => {
    const trimmed = newCropInput.trim();
    if (trimmed && !formData.crops.includes(trimmed)) {
      setFormData((prev) => ({
        ...prev,
        crops: [...prev.crops, trimmed],
      }));
      setNewCropInput('');
    }
  };

  const handleRemoveCrop = (cropToRemove) => {
    setFormData((prev) => ({
      ...prev,
      crops: prev.crops.filter((c) => c !== cropToRemove),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await updateFarmProfile(formData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (farmProfile) {
      setFormData({
        farmerName: farmProfile.farmerName || '',
        location: farmProfile.location || '',
        landArea: farmProfile.landArea || '',
        soilType: farmProfile.soilType || '',
        irrigationType: farmProfile.irrigationType || '',
        crops: Array.isArray(farmProfile.crops) ? [...farmProfile.crops] : [],
      });
    }
    setIsEditing(false);
  };

  return (
    <div className="farm-page-container">
      <PageHeader
        title={t('nav.farm') || (isKn ? 'ನನ್ನ ಜಮೀನು' : 'My Farm')}
        subtitle={
          isKn
            ? 'ನಿಮ್ಮ ಬೆಳೆಗಳು, ಮಣ್ಣು ಮತ್ತು ಜಮೀನಿನ ವಿವರಗಳನ್ನು ನಿರ್ವಹಿಸಿ.'
            : 'Manage your crops, soil types, and farm profile for contextual AI recommendations.'
        }
        icon={Sprout}
        action={
          !isEditing && isSetup && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setIsEditing(true)}
            >
              <Edit3 size={16} />
              <span>{isKn ? 'ವಿವರ ತಿದ್ದುಪಡಿ' : 'Edit Farm'}</span>
            </button>
          )
        }
      />

      {isLoading && !isEditing ? (
        <div className="farm-loading-state">
          <LoadingSpinner
            size="large"
            label={isKn ? 'ಜಮೀನಿನ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...' : 'Loading farm profile from server...'}
          />
        </div>
      ) : isEditing || !isSetup ? (
        /* Edit / Setup Form */
        <div className="farm-form-container glass-panel">
          <div className="farm-form-header">
            <div className="form-icon">
              <Sprout size={22} />
            </div>
            <div>
              <h3>
                {isSetup
                  ? isKn
                    ? 'ಜಮೀನಿನ ವಿವರ ನವೀಕರಿಸಿ'
                    : 'Update Farm Profile'
                  : isKn
                  ? 'ಜಮೀನಿನ ವಿವರ ಭರ್ತಿ ಮಾಡಿ'
                  : 'Set Up Your Farm'}
              </h3>
              <p>
                {isKn
                  ? 'ಈ ವಿವರಗಳು ರೈತ ಸಾಥಿ AI ನಿಮ್ಮ ಜಮೀನಿಗೆ ತಕ್ಕಂತೆ ನಿಖರ ಕೃಷಿ ಸಲಹೆ ನೀಡಲು ಸಹಾಯ ಮಾಡುತ್ತವೆ.'
                  : 'These details allow Raitha Sathi AI to customize agricultural advice specifically for your land.'}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="farm-edit-form">
            <div className="form-grid">
              {/* Farmer Name */}
              <div className="form-field">
                <label className="field-label">{isKn ? 'ರೈತರ ಹೆಸರು' : 'Farmer Name'}</label>
                <div className="field-input-wrap">
                  <User size={16} className="field-icon" />
                  <input
                    type="text"
                    className="field-input"
                    value={formData.farmerName}
                    onChange={(e) => handleInputChange('farmerName', e.target.value)}
                    placeholder={isKn ? 'ಉದಾ: farmer-01' : 'e.g. farmer-01'}
                    required
                  />
                </div>
              </div>

              {/* Location */}
              <div className="form-field">
                <label className="field-label">{isKn ? 'ಸ್ಥಳ (ಜಿಲ್ಲೆ / ತಾಲೂಕು)' : 'Location (District / Taluk)'}</label>
                <div className="field-input-wrap">
                  <MapPin size={16} className="field-icon" />
                  <input
                    type="text"
                    className="field-input"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    placeholder={isKn ? 'ಉದಾ: ಮಂಡ್ಯ, ಮದ್ದೂರು' : 'e.g. Mandya, Maddur'}
                    required
                  />
                </div>
              </div>

              {/* Land Area */}
              <div className="form-field">
                <label className="field-label">{isKn ? 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಎಕರೆ / ಗುಂಟೆ)' : 'Land Area (Acres / Guntas)'}</label>
                <div className="field-input-wrap">
                  <Layers size={16} className="field-icon" />
                  <input
                    type="text"
                    className="field-input"
                    value={formData.landArea}
                    onChange={(e) => handleInputChange('landArea', e.target.value)}
                    placeholder={isKn ? 'ಉದಾ: 4.5 ಎಕರೆ' : 'e.g. 4.5 Acres'}
                    required
                  />
                </div>
              </div>

              {/* Soil Type */}
              <div className="form-field">
                <label className="field-label">{isKn ? 'ಮಣ್ಣಿನ ವಿಧ' : 'Soil Type'}</label>
                <select
                  className="field-select"
                  value={formData.soilType}
                  onChange={(e) => handleInputChange('soilType', e.target.value)}
                >
                  <option value="">{isKn ? 'ಮಣ್ಣಿನ ವಿಧ ಆಯ್ಕೆಮಾಡಿ...' : 'Select Soil Type...'}</option>
                  <option value="Red Loam">{isKn ? 'ಕೆಂಪು ಗೋಡು ಮಣ್ಣು' : 'Red Loam'}</option>
                  <option value="Black Soil">{isKn ? 'ಕಪ್ಪು ಹತ್ತಿ ಮಣ್ಣು' : 'Black Soil'}</option>
                  <option value="Clay">{isKn ? 'ಜೇಡಿ ಮಣ್ಣು' : 'Clay Soil'}</option>
                  <option value="Sandy Loam">{isKn ? 'ಮರಳು ಮಿಶ್ರಿತ ಗೋಡು ಮಣ್ಣು' : 'Sandy Loam'}</option>
                  <option value="Alluvial">{isKn ? 'ಮೆಕ್ಕಲು ಮಣ್ಣು' : 'Alluvial Soil'}</option>
                </select>
              </div>

              {/* Irrigation Type */}
              <div className="form-field">
                <label className="field-label">{isKn ? 'ನೀರಾವರಿ ವಿಧಾನ' : 'Irrigation Method'}</label>
                <div className="field-input-wrap">
                  <Droplet size={16} className="field-icon" />
                  <input
                    type="text"
                    className="field-input"
                    value={formData.irrigationType}
                    onChange={(e) => handleInputChange('irrigationType', e.target.value)}
                    placeholder={isKn ? 'ಉದಾ: ಹನಿ ನೀರಾವರಿ / ಕೊಳವೆಬಾವಿ' : 'e.g. Drip Irrigation / Borewell'}
                  />
                </div>
              </div>
            </div>

            {/* Cultivated Crops Tag Editor */}
            <div className="form-field crops-section">
              <label className="field-label">{isKn ? 'ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆಗಳು' : 'Cultivated Crops'}</label>
              <div className="crop-input-row">
                <input
                  type="text"
                  className="field-input crop-input"
                  value={newCropInput}
                  onChange={(e) => setNewCropInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddCrop();
                    }
                  }}
                  placeholder={isKn ? 'ಬೆಳೆಯ ಹೆಸರು ನಮೂದಿಸಿ (ಉದಾ: ರಾಗಿ, ಭತ್ತ, ಟೊಮೆಟೊ)...' : 'Type crop name (e.g. Tomato, Ragi, Paddy)...'}
                />
                <button
                  type="button"
                  className="btn btn-secondary add-crop-btn"
                  onClick={handleAddCrop}
                >
                  <Plus size={16} />
                  <span>{isKn ? 'ಬೆಳೆ ಸೇರಿಸಿ' : 'Add Crop'}</span>
                </button>
              </div>

              <div className="crops-tags-list">
                {formData.crops.map((crop, idx) => (
                  <span key={idx} className="crop-tag">
                    <span>{crop}</span>
                    <button
                      type="button"
                      className="crop-tag-remove"
                      onClick={() => handleRemoveCrop(crop)}
                      title={isKn ? `${crop} ತೆಗೆದುಹಾಕಿ` : `Remove ${crop}`}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
                {formData.crops.length === 0 && (
                  <span className="no-crops-hint">
                    {isKn ? 'ಇನ್ನೂ ಯಾವುದೇ ಬೆಳೆ ಸೇರಿಸಿಲ್ಲ. ಮೇಲೆ ಬೆಳೆಯ ಹೆಸರು ನಮೂದಿಸಿ.' : 'No crops added yet. Enter a crop name above.'}
                  </span>
                )}
              </div>
            </div>

            {/* Form Action Buttons */}
            <div className="form-actions-bar">
              {isSetup && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleCancel}
                  disabled={isLoading}
                >
                  <X size={16} />
                  <span>{isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}</span>
                </button>
              )}
              <button
                type="submit"
                className="btn btn-primary save-farm-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="btn-spinner" />
                ) : (
                  <>
                    <Save size={16} />
                    <span>{isKn ? 'ಜಮೀನಿನ ವಿವರ ಉಳಿಸಿ' : 'Save Farm Profile'}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      ) : (
        /* Profile Display View */
        <div className="farm-view-container">
          {/* Profile Overview Card */}
          <div className="farm-hero-card glass-panel">
            <div className="farm-hero-header">
              <div className="farm-hero-icon">
                <Sprout size={32} />
              </div>
              <div className="farm-hero-info">
                <div className="farm-verified-badge">
                  <CheckCircle2 size={14} />
                  <span>{isKn ? 'ಸಕ್ರಿಯ ಪ್ರೊಫೈಲ್' : 'Configured & Active'}</span>
                </div>
                <h2 className="farm-farmer-title">{farmProfile.farmerName || (isKn ? 'ರೈತರು' : 'Farmer')}</h2>
                <div className="farm-location-tag">
                  <MapPin size={14} />
                  <span>{farmProfile.location || (isKn ? 'ಕರ್ನಾಟಕ' : 'Karnataka')}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="farm-details-grid">
            {/* Land Area */}
            <div className="farm-metric-card surface-card">
              <div className="metric-icon area-icon">
                <Layers size={20} />
              </div>
              <div className="metric-content">
                <span className="metric-label">{isKn ? 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ' : 'Land Area'}</span>
                <span className="metric-value">{farmProfile.landArea || (isKn ? 'ತಿಳಿಸಿಲ್ಲ' : 'Not specified')}</span>
              </div>
            </div>

            {/* Soil Type */}
            <div className="farm-metric-card surface-card">
              <div className="metric-icon soil-icon">
                <Sprout size={20} />
              </div>
              <div className="metric-content">
                <span className="metric-label">{isKn ? 'ಮಣ್ಣಿನ ವಿಧ' : 'Soil Type'}</span>
                <span className="metric-value">{farmProfile.soilType || (isKn ? 'ತಿಳಿಸಿಲ್ಲ' : 'Not specified')}</span>
              </div>
            </div>

            {/* Irrigation Type */}
            <div className="farm-metric-card surface-card">
              <div className="metric-icon water-icon">
                <Droplet size={20} />
              </div>
              <div className="metric-content">
                <span className="metric-label">{isKn ? 'ನೀರಾವರಿ ವಿಧಾನ' : 'Irrigation Method'}</span>
                <span className="metric-value">{farmProfile.irrigationType || (isKn ? 'ತಿಳಿಸಿಲ್ಲ' : 'Not specified')}</span>
              </div>
            </div>
          </div>

          {/* Crops Card */}
          <div className="farm-crops-card glass-panel">
            <div className="crops-card-header">
              <h3>{isKn ? 'ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆಗಳು' : 'Cultivated Crops'}</h3>
              <span className="crops-count-badge">
                {Array.isArray(farmProfile.crops) ? farmProfile.crops.length : 0} {isKn ? 'ಬೆಳೆಗಳು' : 'Crops'}
              </span>
            </div>

            <div className="crops-badges-wrap">
              {Array.isArray(farmProfile.crops) && farmProfile.crops.length > 0 ? (
                farmProfile.crops.map((crop, idx) => (
                  <div key={idx} className="farm-crop-badge">
                    <span className="crop-leaf-emoji">🌱</span>
                    <span className="crop-badge-name">{crop}</span>
                  </div>
                ))
              ) : (
                <p className="no-crops-text">
                  {isKn ? 'ನಿಮ್ಮ ಪ್ರೊಫೈಲ್‌ನಲ್ಲಿ ಇನ್ನೂ ಯಾವುದೇ ಬೆಳೆಗಳನ್ನು ದಾಖಲಿಸಿಲ್ಲ.' : 'No crops recorded in your profile yet.'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
