import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  User,
  Phone,
  Globe,
  MapPin,
  Building,
  Home,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Info,
  ShieldCheck,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { ThemeSelector } from '../../components/common/ThemeSelector';
import { authService } from '../../services/authService';
import './RegistrationPage.css';

/* ── Field error component ─────────────────────────────── */
const FieldError = ({ message }) =>
  message ? (
    <span className="field-error" role="alert">
      <AlertCircle size={12} />
      {message}
    </span>
  ) : null;

export const RegistrationPage = () => {
  const navigate = useNavigate();
  const { language, setLanguage } = useLanguage();

  // Multi-step state: 1 | 2 | 3 | 'review' | 'submitted'
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Form State (kept purely in React memory, never persisted to localStorage)
  const [formData, setFormData] = useState({
    fullName: '',
    mobile: '',
    preferredLanguage: language || 'kn',
    state: 'Karnataka',
    district: '',
    taluk: '',
    village: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  /* ── Step 1 Validation ────────────────────────────────── */
  const validateStep1 = () => {
    const errs = {};
    if (!formData.fullName.trim()) {
      errs.fullName = 'Full name is required / ಪೂರ್ಣ ಹೆಸರು ಅಗತ್ಯವಿದೆ';
    }
    const cleanMobile = formData.mobile.replace(/\D/g, '');
    if (!cleanMobile) {
      errs.mobile = 'Mobile number is required / ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಗತ್ಯವಿದೆ';
    } else if (cleanMobile.length !== 10) {
      errs.mobile = 'Enter a valid 10-digit mobile number';
    }
    if (!formData.preferredLanguage) {
      errs.preferredLanguage = 'Please select a language';
    }
    return errs;
  };

  /* ── Step 2 Validation ────────────────────────────────── */
  const validateStep2 = () => {
    const errs = {};
    if (!formData.state.trim()) errs.state = 'State is required / ರಾಜ್ಯ ಅಗತ್ಯವಿದೆ';
    if (!formData.district.trim()) errs.district = 'District is required / ಜಿಲ್ಲೆ ಅಗತ್ಯವಿದೆ';
    if (!formData.taluk.trim()) errs.taluk = 'Taluk is required / ತಾಲೂಕು ಅಗತ್ಯವಿದೆ';
    if (!formData.village.trim()) errs.village = 'Village is required / ಗ್ರಾಮ ಅಗತ್ಯವಿದೆ';
    return errs;
  };

  /* ── Step 3 Validation ────────────────────────────────── */
  const validateStep3 = () => {
    const errs = {};
    if (!formData.email.trim()) {
      errs.email = 'Email address is required / ಇಮೇಲ್ ಅಗತ್ಯವಿದೆ';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errs.email = 'Enter a valid email address';
    }
    if (!formData.password) {
      errs.password = 'Password is required / ಪಾಸ್‌ವರ್ಡ್ ಅಗತ್ಯವಿದೆ';
    } else if (formData.password.length < 6) {
      errs.password = 'Password must be at least 6 characters';
    }
    if (!formData.confirmPassword) {
      errs.confirmPassword = 'Confirm your password / ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ';
    } else if (formData.password !== formData.confirmPassword) {
      errs.confirmPassword = 'Passwords do not match / ಪಾಸ್‌ವರ್ಡ್‌ಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ';
    }
    return errs;
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (step === 1) {
      const errs = validateStep1();
      if (Object.keys(errs).length > 0) {
        setErrors(errs);
        return;
      }
      setErrors({});
      setStep(2);
    } else if (step === 2) {
      const errs = validateStep2();
      if (Object.keys(errs).length > 0) {
        setErrors(errs);
        return;
      }
      setErrors({});
      setStep(3);
    } else if (step === 3) {
      const errs = validateStep3();
      if (Object.keys(errs).length > 0) {
        setErrors(errs);
        return;
      }
      setErrors({});
      setStep('review');
    }
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    setSubmitError('');
    setIsSubmitting(true);
    try {
      await authService.register({
        fullName: formData.fullName,
        mobile: formData.mobile,
        email: formData.email,
        password: formData.password,
        state: formData.state,
        district: formData.district,
        taluk: formData.taluk,
        village: formData.village,
        preferredLanguage: formData.preferredLanguage || language || 'kn',
      });
      setStep('submitted');
    } catch (err) {
      setSubmitError(err?.message || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const lang = language === 'kn' ? 'kn' : 'en';

  return (
    <div className="login-root">
      {/* ── LEFT PANEL ─────────────────────────────────── */}
      <div className="login-left" aria-hidden="true">
        <div className="login-left-inner">
          <div className="login-field-illustration">
            <div className="field-row field-row-1" />
            <div className="field-row field-row-2" />
            <div className="field-row field-row-3" />
            <div className="field-sun" />
          </div>
          <div className="login-left-text">
            <div className="login-left-leaf">🌾</div>
            <h2 className="login-left-brand">Raitha Sathi</h2>
            <p className="login-left-quote">
              "Join our network of farmers for smart, localized AI agricultural guidance."
            </p>
            <p className="login-left-quote-kn">
              "ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ನಮ್ಮ ರೈತರ ಸಮುದಾಯಕ್ಕೆ ಸೇರಿ."
            </p>
          </div>
        </div>
      </div>

      {/* ── RIGHT PANEL ────────────────────────────────── */}
      <div className="login-right">
        {/* Top Navigation */}
        <div className="login-top-bar">
          <button
            type="button"
            className="login-back-btn"
            onClick={() => {
              if (step === 'submitted' || step === 1) navigate('/login');
              else if (step === 'review') setStep(3);
              else setStep((s) => s - 1);
            }}
            aria-label="Go Back"
          >
            <ArrowLeft size={15} />
            <span>
              {step === 1 || step === 'submitted' ? 'Back to Login' : 'Previous Step'}
            </span>
          </button>

          <div className="login-top-actions">
            <div className="lang-toggle" role="group" aria-label="Language">
              <button
                type="button"
                className={`lang-btn ${lang === 'en' ? 'lang-active' : ''}`}
                onClick={() => {
                  setLanguage('en');
                  updateField('preferredLanguage', 'en');
                }}
              >
                EN
              </button>
              <button
                type="button"
                className={`lang-btn ${lang === 'kn' ? 'lang-active' : ''}`}
                onClick={() => {
                  setLanguage('kn');
                  updateField('preferredLanguage', 'kn');
                }}
              >
                ಕನ್ನಡ
              </button>
            </div>
            <ThemeSelector />
          </div>
        </div>

        {/* Content Container */}
        <div className="login-form-area reg-form-area">
          {step !== 'submitted' && (
            <>
              {/* Stepper Header */}
              <div className="reg-stepper-header">
                <div className="reg-step-indicator">
                  <div className={`step-dot ${step >= 1 ? 'active' : ''}`}>1</div>
                  <div className={`step-line ${step >= 2 ? 'active' : ''}`} />
                  <div className={`step-dot ${step >= 2 ? 'active' : ''}`}>2</div>
                  <div className={`step-line ${step >= 3 || step === 'review' ? 'active' : ''}`} />
                  <div className={`step-dot ${step >= 3 || step === 'review' ? 'active' : ''}`}>3</div>
                </div>
                <div className="reg-step-title">
                  {step === 1 && 'Step 1 of 3: About You'}
                  {step === 2 && 'Step 2 of 3: Farm Location'}
                  {step === 3 && 'Step 3 of 3: Account Security'}
                  {step === 'review' && 'Review Your Information'}
                </div>
              </div>

              <h1 className="login-headline">
                {step === 1 && 'Tell us about yourself'}
                {step === 2 && 'Where is your farm located?'}
                {step === 3 && 'Create your account'}
                {step === 'review' && 'Verify registration details'}
              </h1>
              <p className="login-tagline">
                {step === 1 && 'Provide your basic details to personalize your agricultural advice.'}
                {step === 2 && 'Location helps Sathi provide weather, soil, and crop-specific alerts.'}
                {step === 3 && 'Set your email and secure password for farmer access.'}
                {step === 'review' && 'Ensure your profile and farm location details are accurate.'}
              </p>
            </>
          )}

          {/* ── STEP 1: ABOUT YOU ──────────────────────────── */}
          {step === 1 && (
            <form onSubmit={handleNext} className="login-form" noValidate>
              <div className="form-field">
                <label htmlFor="reg-fullname" className="field-label">
                  <User size={14} aria-hidden="true" />
                  Full Name / ಪೂರ್ಣ ಹೆಸರು
                </label>
                <input
                  id="reg-fullname"
                  type="text"
                  className={`text-input ${errors.fullName ? 'input-error' : ''}`}
                  value={formData.fullName}
                  onChange={(e) => updateField('fullName', e.target.value)}
                  placeholder="Enter your full name (e.g., farmer-01)"
                  autoComplete="name"
                  autoFocus
                />
                <FieldError message={errors.fullName} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-mobile" className="field-label">
                  <Phone size={14} aria-hidden="true" />
                  Mobile Number / ಮೊಬೈಲ್ ಸಂಖ್ಯೆ
                </label>
                <div className="phone-input-combo">
                  <span className="phone-country-tag">+91</span>
                  <input
                    id="reg-mobile"
                    type="tel"
                    inputMode="numeric"
                    className={`text-input combo-input ${errors.mobile ? 'input-error' : ''}`}
                    value={formData.mobile}
                    onChange={(e) => updateField('mobile', e.target.value.replace(/\D/g, '').slice(0, 10))}
                    placeholder="98765 43210"
                    autoComplete="tel-national"
                  />
                </div>
                <FieldError message={errors.mobile} />
              </div>

              <div className="form-field">
                <label className="field-label">
                  <Globe size={14} aria-hidden="true" />
                  Preferred Language / ಆದ್ಯತೆಯ ಭಾಷೆ
                </label>
                <div className="lang-radio-group">
                  {[
                    { id: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
                    { id: 'en', label: 'English' },
                  ].map((l) => (
                    <label key={l.id} className={`lang-radio-card ${formData.preferredLanguage === l.id ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="preferredLanguage"
                        value={l.id}
                        checked={formData.preferredLanguage === l.id}
                        onChange={(e) => {
                          updateField('preferredLanguage', e.target.value);
                          setLanguage(e.target.value);
                        }}
                      />
                      <span>{l.label}</span>
                    </label>
                  ))}

                </div>
                <FieldError message={errors.preferredLanguage} />
              </div>

              <button type="submit" className="btn-auth btn-auth-dev" id="reg-next-1">
                Continue to Farm Location
                <ArrowRight size={15} aria-hidden="true" />
              </button>
            </form>
          )}

          {/* ── STEP 2: FARM LOCATION (FREE TEXT OPTION C) ── */}
          {step === 2 && (
            <form onSubmit={handleNext} className="login-form" noValidate>
              <div className="form-field">
                <label htmlFor="reg-state" className="field-label">
                  <MapPin size={14} aria-hidden="true" />
                  State / ರಾಜ್ಯ
                </label>
                <input
                  id="reg-state"
                  type="text"
                  className={`text-input ${errors.state ? 'input-error' : ''}`}
                  value={formData.state}
                  onChange={(e) => updateField('state', e.target.value)}
                  placeholder="Karnataka"
                  autoComplete="address-level1"
                />
                <FieldError message={errors.state} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-district" className="field-label">
                  <Building size={14} aria-hidden="true" />
                  District / ಜಿಲ್ಲೆ
                </label>
                <input
                  id="reg-district"
                  type="text"
                  className={`text-input ${errors.district ? 'input-error' : ''}`}
                  value={formData.district}
                  onChange={(e) => updateField('district', e.target.value)}
                  placeholder="e.g., Mandya, Mysuru, Belagavi"
                  autoComplete="address-level2"
                  autoFocus
                />
                <FieldError message={errors.district} />
              </div>

              <div className="form-grid-row">
                <div className="form-field">
                  <label htmlFor="reg-taluk" className="field-label">
                    Taluk / ತಾಲೂಕು
                  </label>
                  <input
                    id="reg-taluk"
                    type="text"
                    className={`text-input ${errors.taluk ? 'input-error' : ''}`}
                    value={formData.taluk}
                    onChange={(e) => updateField('taluk', e.target.value)}
                    placeholder="e.g., Maddur"
                  />
                  <FieldError message={errors.taluk} />
                </div>

                <div className="form-field">
                  <label htmlFor="reg-village" className="field-label">
                    <Home size={14} aria-hidden="true" />
                    Village / ಗ್ರಾಮ
                  </label>
                  <input
                    id="reg-village"
                    type="text"
                    className={`text-input ${errors.village ? 'input-error' : ''}`}
                    value={formData.village}
                    onChange={(e) => updateField('village', e.target.value)}
                    placeholder="e.g., Gejjalagere"
                  />
                  <FieldError message={errors.village} />
                </div>
              </div>

              <div className="reg-actions-row">
                <button
                  type="button"
                  className="btn-auth btn-auth-secondary"
                  onClick={() => setStep(1)}
                >
                  <ArrowLeft size={15} aria-hidden="true" />
                  Back
                </button>
                <button type="submit" className="btn-auth btn-auth-dev" id="reg-next-2">
                  Continue to Account
                  <ArrowRight size={15} aria-hidden="true" />
                </button>
              </div>
            </form>
          )}

          {/* ── STEP 3: ACCOUNT & PASSWORD ─────────────────── */}
          {step === 3 && (
            <form onSubmit={handleNext} className="login-form" noValidate>
              <div className="form-field">
                <label htmlFor="reg-email" className="field-label">
                  <Mail size={14} aria-hidden="true" />
                  Email Address / ಇಮೇಲ್ ವಿಳಾಸ
                </label>
                <input
                  id="reg-email"
                  type="email"
                  className={`text-input ${errors.email ? 'input-error' : ''}`}
                  value={formData.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  placeholder="farmer@example.com"
                  autoComplete="email"
                  autoFocus
                />
                <FieldError message={errors.email} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-password" className="field-label">
                  <Lock size={14} aria-hidden="true" />
                  Create Password / ಪಾಸ್‌ವರ್ಡ್ ರಚಿಸಿ
                </label>
                <div className="password-wrap">
                  <input
                    id="reg-password"
                    type={showPassword ? 'text' : 'password'}
                    className={`text-input password-input ${errors.password ? 'input-error' : ''}`}
                    value={formData.password}
                    onChange={(e) => updateField('password', e.target.value)}
                    placeholder="At least 6 characters"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="pw-toggle"
                    onClick={() => setShowPassword((s) => !s)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <FieldError message={errors.password} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-confirm-password" className="field-label">
                  <Lock size={14} aria-hidden="true" />
                  Confirm Password / ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ
                </label>
                <div className="password-wrap">
                  <input
                    id="reg-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    className={`text-input password-input ${errors.confirmPassword ? 'input-error' : ''}`}
                    value={formData.confirmPassword}
                    onChange={(e) => updateField('confirmPassword', e.target.value)}
                    placeholder="Re-enter your password"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="pw-toggle"
                    onClick={() => setShowConfirmPassword((s) => !s)}
                    aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <FieldError message={errors.confirmPassword} />
              </div>

              <div className="reg-actions-row">
                <button
                  type="button"
                  className="btn-auth btn-auth-secondary"
                  onClick={() => setStep(2)}
                >
                  <ArrowLeft size={15} aria-hidden="true" />
                  Back
                </button>
                <button type="submit" className="btn-auth btn-auth-dev" id="reg-next-3">
                  Review & Finalize
                  <ArrowRight size={15} aria-hidden="true" />
                </button>
              </div>
            </form>
          )}

          {/* ── REVIEW SCREEN ─────────────────────────────── */}
          {step === 'review' && (
            <div className="reg-review-wrap">
              <div className="review-card">
                <div className="review-section">
                  <div className="review-section-header">
                    <span className="review-title">About You</span>
                    <button type="button" className="review-edit-btn" onClick={() => setStep(1)}>
                      Edit
                    </button>
                  </div>
                  <div className="review-grid">
                    <div className="review-item">
                      <span className="review-label">Name:</span>
                      <span className="review-val">{formData.fullName}</span>
                    </div>
                    <div className="review-item">
                      <span className="review-label">Mobile:</span>
                      <span className="review-val">+91 {formData.mobile}</span>
                    </div>
                    <div className="review-item">
                      <span className="review-label">Language:</span>
                      <span className="review-val">{formData.preferredLanguage.toUpperCase()}</span>
                    </div>
                  </div>
                </div>

                <div className="review-section">
                  <div className="review-section-header">
                    <span className="review-title">Farm Location</span>
                    <button type="button" className="review-edit-btn" onClick={() => setStep(2)}>
                      Edit
                    </button>
                  </div>
                  <div className="review-grid">
                    <div className="review-item">
                      <span className="review-label">State:</span>
                      <span className="review-val">{formData.state}</span>
                    </div>
                    <div className="review-item">
                      <span className="review-label">District:</span>
                      <span className="review-val">{formData.district}</span>
                    </div>
                    <div className="review-item">
                      <span className="review-label">Taluk / Village:</span>
                      <span className="review-val">
                        {formData.taluk}, {formData.village}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="review-section">
                  <div className="review-section-header">
                    <span className="review-title">Account</span>
                    <button type="button" className="review-edit-btn" onClick={() => setStep(3)}>
                      Edit
                    </button>
                  </div>
                  <div className="review-grid">
                    <div className="review-item">
                      <span className="review-label">Email:</span>
                      <span className="review-val">{formData.email}</span>
                    </div>
                  </div>
                </div>
              </div>

              {submitError && (
                <div className="auth-error-banner" style={{ marginTop: '1rem' }} role="alert">
                  <AlertCircle size={16} />
                  <span>{submitError}</span>
                </div>
              )}

              <div className="reg-actions-row" style={{ marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn-auth btn-auth-secondary"
                  onClick={() => setStep(3)}
                  disabled={isSubmitting}
                >
                  <ArrowLeft size={15} aria-hidden="true" />
                  Back
                </button>
                <button
                  type="button"
                  className="btn-auth btn-auth-primary"
                  onClick={handleCreateAccount}
                  disabled={isSubmitting}
                  id="reg-submit-btn"
                >
                  {isSubmitting ? 'Creating Account…' : 'Create Account'}
                  <CheckCircle2 size={15} aria-hidden="true" />
                </button>
              </div>
            </div>
          )}

          {/* ── REAL ACCOUNT CREATED RESULT ────────────── */}
          {step === 'submitted' && (
            <div className="reg-submitted-wrap" role="status">
              <div className="auth-notice" style={{ borderLeftColor: 'var(--primary)', backgroundColor: 'var(--primary-light)' }}>
                <div className="notice-icon" style={{ color: 'var(--primary)' }}>
                  <CheckCircle2 size={20} />
                </div>
                <div className="notice-body">
                  <strong className="notice-title" style={{ color: 'var(--primary)' }}>Account Created Successfully!</strong>
                  <p className="notice-text" style={{ color: 'var(--text-main)' }}>
                    Your farmer profile for <strong>{formData.fullName}</strong> is now registered.
                    You can sign in with your email or mobile number anytime.
                  </p>
                </div>
              </div>

              <div className="submitted-actions" style={{ marginTop: '1.5rem' }}>
                <Link to="/login" className="btn-auth btn-auth-primary" id="submitted-back-login">
                  Sign In to Your Account
                  <ArrowRight size={15} aria-hidden="true" />
                </Link>
              </div>
            </div>
          )}

          {/* Footer Back link */}
          {step !== 'submitted' && (
            <div className="auth-footer-links">
              <span className="auth-footer-text">Already registered?</span>
              <Link to="/login" className="text-link" id="goto-login-link">
                Sign in to your account →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
