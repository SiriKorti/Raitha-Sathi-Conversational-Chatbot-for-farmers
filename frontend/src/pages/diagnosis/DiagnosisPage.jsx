import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Camera,
  UploadCloud,
  Image as ImageIcon,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  MessageSquare,
  Trash2,
  HelpCircle,
  ShieldAlert,
  Search,
  Sparkles,
  Info
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { PageHeader } from '../../components/common/PageHeader';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';
import { diagnosisService } from '../../services/diagnosisService';
import './DiagnosisPage.css';

const COMMON_CROPS = [
  { id: 'Tomato', en: 'Tomato', kn: 'ಟೊಮೆಟೊ' },
  { id: 'Ragi', en: 'Ragi', kn: 'ರಾಗಿ' },
  { id: 'Paddy', en: 'Paddy / Rice', kn: 'ಭತ್ತ' },
  { id: 'Cotton', en: 'Cotton', kn: 'ಹತ್ತಿ' },
  { id: 'Maize', en: 'Maize / Corn', kn: 'ಮೆಕ್ಕೆಜೋಳ' },
  { id: 'Sugarcane', en: 'Sugarcane', kn: 'ಕಬ್ಬು' },
  { id: 'Chilli', en: 'Chilli', kn: 'ಮೆಣಸಿನಕಾಯಿ' },
  { id: 'Onion', en: 'Onion', kn: 'ಈರುಳ್ಳಿ' },
  { id: 'Potato', en: 'Potato', kn: 'ಆಲೂಗಡ್ಡೆ' },
  { id: 'Groundnut', en: 'Groundnut', kn: 'ಕಡಲೆಕಾಯಿ' },
  { id: 'Turmeric', en: 'Turmeric', kn: 'ಅರಿಶಿನ' },
  { id: 'Arecanut', en: 'Arecanut', kn: 'ಅಡಿಕೆ' },
  { id: 'Banana', en: 'Banana', kn: 'ಬಾಳೆ' },
  { id: 'Coconut', en: 'Coconut', kn: 'ತೆಂಗು' },
];

export const DiagnosisPage = () => {
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [cropName, setCropName] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileChange = (file) => {
    if (!file) return;

    // Validate MIME type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      showToast(t('diagnosis.err_invalid_type'), 'error');
      return;
    }

    // Validate size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      showToast(t('diagnosis.err_too_large'), 'error');
      return;
    }

    setError(null);
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleRemoveImage = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      showToast(t('diagnosis.err_select_image'), 'warning');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await diagnosisService.diagnoseImage(selectedFile, cropName, symptoms, language);
      if (response && response.success && response.diagnosis) {
        setDiagnosisResult(response);
      } else {
        throw new Error('Diagnosis response was incomplete. Please try again.');
      }
    } catch (err) {
      console.error('Diagnosis error:', err);
      setError(err.message || 'Failed to complete visual diagnosis. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDiscussInChat = () => {
    if (!diagnosisResult || !diagnosisResult.diagnosis) return;

    const diag = diagnosisResult.diagnosis;
    const cropText = cropName ? cropName : (diagnosisResult.crop || 'crop');

    let promptText = '';
    if (language === 'kn') {
      promptText = `ನನ್ನ ${cropText} ಬೆಳೆಗೆ ಎಲೆ ರೋಗ ಪರೀಕ್ಷೆ ಮಾಡಿದ್ದೇನೆ. ಗುರುತಿಸಲಾದ ಸಮಸ್ಯೆ: "${diag.problem}" (ವರ್ಗ: ${diag.category}). ಕಂಡುಬಂದ ಲಕ್ಷಣಗಳು: ${diag.observations.join(', ')}. ಈ ಸಮಸ್ಯೆಗೆ ವಿವರವಾದ ನಿರ್ವಹಣೆ ಮತ್ತು ಪರಿಹಾರ ಕ್ರಮಗಳನ್ನು ತಿಳಿಸಿ.`;
    } else {
      promptText = `I ran a visual diagnosis on my ${cropText} crop. Identified issue: "${diag.problem}" (Category: ${diag.category}, Confidence: ${diag.confidence}). Observed symptoms: ${diag.observations.join(', ')}. Please provide detailed management and recovery steps.`;
    }

    navigate('/chat', { state: { prompt: promptText } });
  };

  const getConfidenceBadgeClass = (confidence) => {
    switch (confidence) {
      case 'HIGH':
        return 'badge-conf-high';
      case 'MEDIUM':
        return 'badge-conf-medium';
      case 'LOW':
        return 'badge-conf-low';
      default:
        return 'badge-conf-uncertain';
    }
  };

  const getConfidenceLabel = (confidence) => {
    switch (confidence) {
      case 'HIGH':
        return t('diagnosis.conf_high');
      case 'MEDIUM':
        return t('diagnosis.conf_medium');
      case 'LOW':
        return t('diagnosis.conf_low');
      default:
        return t('diagnosis.conf_uncertain');
    }
  };

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'disease':
        return t('diagnosis.cat_disease');
      case 'pest':
        return t('diagnosis.cat_pest');
      case 'nutrient':
        return t('diagnosis.cat_nutrient');
      case 'environmental':
        return t('diagnosis.cat_environmental');
      case 'uncertain':
        return t('diagnosis.cat_uncertain');
      default:
        return t('diagnosis.cat_other');
    }
  };

  return (
    <div className="diagnosis-container">
      <PageHeader
        title={t('diagnosis.title')}
        subtitle={t('diagnosis.subtitle')}
        icon={Camera}
      />

      <div className="diagnosis-grid">
        {/* Left Column: Image Upload & Context Form */}
        <Card className="diagnosis-card">
          <form onSubmit={handleAnalyze}>
            {!previewUrl ? (
              <div
                className={`upload-dropzone ${isDragOver ? 'drag-active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="upload-icon-circle">
                  <UploadCloud size={28} />
                </div>
                <h3 className="upload-title">{t('diagnosis.upload_title')}</h3>
                <p className="upload-hint">{t('diagnosis.upload_hint')}</p>

                <div className="upload-actions" onClick={(e) => e.stopPropagation()}>
                  <Button
                    type="button"
                    variant="outline"
                    icon={ImageIcon}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {t('diagnosis.browse_files')}
                  </Button>
                  <Button
                    type="button"
                    variant="primary"
                    icon={Camera}
                    onClick={() => cameraInputRef.current?.click()}
                  >
                    {t('diagnosis.take_photo')}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="preview-container">
                <div className="preview-image-wrapper">
                  <img src={previewUrl} alt="Crop preview" className="preview-image" />
                </div>
                <div className="preview-meta">
                  <span>{selectedFile?.name} ({(selectedFile?.size / 1024).toFixed(0)} KB)</span>
                  <div className="preview-buttons">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      icon={ImageIcon}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      {t('diagnosis.change_image')}
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      icon={Trash2}
                      onClick={handleRemoveImage}
                    >
                      {t('diagnosis.remove_image')}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Hidden native file inputs */}
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => handleFileChange(e.target.files?.[0])}
            />
            <input
              type="file"
              ref={cameraInputRef}
              style={{ display: 'none' }}
              accept="image/jpeg,image/png,image/webp"
              capture="environment"
              onChange={(e) => handleFileChange(e.target.files?.[0])}
            />

            {/* Crop & Symptoms Context */}
            <div className="diagnosis-form">
              <div className="form-group">
                <label className="form-label">{t('diagnosis.crop_label')}</label>
                <select
                  className="form-select"
                  value={cropName}
                  onChange={(e) => setCropName(e.target.value)}
                >
                  <option value="">{t('diagnosis.crop_placeholder')}</option>
                  {COMMON_CROPS.map((crop) => (
                    <option key={crop.id} value={crop.id}>
                      {language === 'kn' ? crop.kn : crop.en}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">{t('diagnosis.symptoms_label')}</label>
                <textarea
                  className="form-textarea"
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder={t('diagnosis.symptoms_placeholder')}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                icon={isLoading ? RefreshCw : Sparkles}
                disabled={!selectedFile || isLoading}
                className="w-full"
              >
                {isLoading ? t('diagnosis.analyzing') : t('diagnosis.analyze_btn')}
              </Button>
            </div>
          </form>
        </Card>

        {/* Right Column: Diagnostic Result / Placeholder */}
        <div className="diagnosis-result-area">
          {isLoading ? (
            <Card className="result-card text-center p-8">
              <LoadingSpinner message={t('diagnosis.analyzing')} />
            </Card>
          ) : error ? (
            <ErrorState
              title="Diagnosis Error"
              message={error}
              onRetry={handleAnalyze}
            />
          ) : diagnosisResult?.diagnosis ? (
            <Card className="result-card">
              <div className="result-header">
                <div className="result-problem-box">
                  {diagnosisResult.crop && (
                    <span className="result-crop-tag">{diagnosisResult.crop}</span>
                  )}
                  <h2 className="result-problem-title">
                    {diagnosisResult.diagnosis.problem}
                  </h2>
                </div>
                <div className="result-badges">
                  <span className="badge-category">
                    {getCategoryLabel(diagnosisResult.diagnosis.category)}
                  </span>
                  <span className={`badge-category ${getConfidenceBadgeClass(diagnosisResult.diagnosis.confidence)}`}>
                    {getConfidenceLabel(diagnosisResult.diagnosis.confidence)}
                  </span>
                </div>
              </div>

              {/* Observed Symptoms */}
              {diagnosisResult.diagnosis.observations?.length > 0 && (
                <div className="result-section">
                  <h3 className="result-section-title">
                    <Search size={16} />
                    {t('diagnosis.observations')}
                  </h3>
                  <ul className="result-list">
                    {diagnosisResult.diagnosis.observations.map((obs, idx) => (
                      <li key={idx}>{obs}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Possible Causes */}
              {diagnosisResult.diagnosis.possible_causes?.length > 0 && (
                <div className="result-section">
                  <h3 className="result-section-title">
                    <Info size={16} />
                    {t('diagnosis.causes')}
                  </h3>
                  <ul className="result-list">
                    {diagnosisResult.diagnosis.possible_causes.map((cause, idx) => (
                      <li key={idx}>{cause}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Management Recommendations */}
              {diagnosisResult.diagnosis.management?.length > 0 && (
                <div className="result-section">
                  <h3 className="result-section-title">
                    <CheckCircle2 size={16} />
                    {t('diagnosis.management')}
                  </h3>
                  <ul className="result-list">
                    {diagnosisResult.diagnosis.management.map((mgmt, idx) => (
                      <li key={idx}>{mgmt}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warning & Disclaimers */}
              <div className="warning-box">
                <ShieldAlert size={20} className="warning-icon" />
                <div>
                  <strong>{t('diagnosis.warning_title')}: </strong>
                  {diagnosisResult.diagnosis.warning ? diagnosisResult.diagnosis.warning.replace(/^(ಮುನ್ನೆಚ್ಚರಿಕೆ\s*&\s*ಸಲಹೆ|Warning\s*&\s*Advisory|Advisory\s*Disclaimer|ಮುನ್ನೆಚ್ಚರಿಕೆ)\s*:\s*/i, '') : ''}
                </div>
              </div>

              {/* Discuss in Ask Sathi CTA */}
              <div className="discuss-card">
                <div className="discuss-text">
                  <h4 className="discuss-title">{t('diagnosis.discuss_chat')}</h4>
                  <p className="discuss-desc">{t('diagnosis.discuss_chat_desc')}</p>
                </div>
                <Button
                  variant="primary"
                  icon={MessageSquare}
                  onClick={handleDiscussInChat}
                >
                  {t('diagnosis.discuss_chat')}
                </Button>
              </div>
            </Card>
          ) : (
            <Card>
              <EmptyState
                icon={Camera}
                title={t('diagnosis.upload_title')}
                description={t('diagnosis.subtitle')}
              />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
