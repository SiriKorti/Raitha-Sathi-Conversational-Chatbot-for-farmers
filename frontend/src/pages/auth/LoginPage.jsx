import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  UserPlus,
  Sparkles,
  Bot,
  Activity,
  TrendingUp,
  CloudSun,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { ThemeSelector } from '../../components/common/ThemeSelector';
import './LoginPage.css';

/* ── Field error component ─────────────────────────────── */
const FieldError = ({ message }) =>
  message ? (
    <span className="field-error" role="alert">
      <AlertCircle size={13} />
      {message}
    </span>
  ) : null;

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const { language, setLanguage } = useLanguage();
  const { showToast } = useToast();

  const isKn = language === 'kn';

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [authError, setAuthError] = useState('');

  /* ── Validation ─────────────────────────────────────── */
  const validate = () => {
    const e = {};
    if (!identifier.trim()) {
      e.identifier = isKn ? 'ಇಮೇಲ್ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಗತ್ಯವಿದೆ.' : 'Email or mobile number is required.';
    }
    if (!password) {
      e.password = isKn ? 'ಪಾಸ್‌ವರ್ಡ್ ಅಗತ್ಯವಿದೆ.' : 'Password is required.';
    }
    return e;
  };

  /* ── Backend Login submit ─────────────────────────────── */
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setAuthError('');
    const v = validate();
    if (Object.keys(v).length) {
      setErrors(v);
      return;
    }
    setErrors({});

    try {
      const cleanIdent = identifier.trim();
      const res = await login({
        identifier: cleanIdent,
        email: cleanIdent.includes('@') ? cleanIdent : undefined,
        mobile: !cleanIdent.includes('@') ? cleanIdent : undefined,
        password,
      });

      showToast(isKn ? `ಸುಸ್ವಾಗತ, ${res.user?.fullName || res.user?.name || 'ರೈತರು'}!` : `Welcome back, ${res.user?.fullName || res.user?.name || 'Farmer'}!`, 'success');
      navigate('/chat');
    } catch (err) {
      const msg = err?.message || (isKn ? 'ಲಾಗಿನ್ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.' : 'Login failed. Please check your credentials.');
      setAuthError(msg);
      showToast(msg, 'error');
    }
  };

  /* ── Quick Demo Login ───────────────────────────────── */
  const handleQuickDemo = async () => {
    setAuthError('');
    setErrors({});
    setIdentifier('farmer@raitha.app');
    setPassword('farmer123');

    try {
      const res = await login({
        email: 'farmer@raitha.app',
        password: 'farmer123',
      });
      showToast(isKn ? 'ಡೆಮೊ ರೈತ ಖಾತೆಗೆ ಯಶಸ್ವಿಯಾಗಿ ಲಾಗಿನ್ ಆಗಿದೆ!' : 'Signed in as Demo Farmer (farmer-01)!', 'success');
      navigate('/chat');
    } catch (err) {
      // Fallback
      setIdentifier('farmer@raitha.app');
      setPassword('farmer123');
      setAuthError(err?.message || 'Demo login failed');
    }
  };

  return (
    <div className="login-root">

      {/* ── LEFT PANEL: Informative Agricultural Showcase ──────── */}
      <div className="login-left" aria-hidden="true">
        <div className="login-left-inner">
          
          {/* Header Brand */}
          <div className="login-brand-header">
            <div className="login-brand-badge">
              <span className="brand-leaf-icon">🌾</span>
              <span className="brand-tag">{isKn ? 'ಕರ್ನಾಟಕ ಕೃಷಿ AI' : 'AI Agri-Intelligence'}</span>
            </div>
            <h2 className="login-left-brand">
              Raitha Sathi
              <span className="login-left-brand-sub"> | ರೈತ ಸಾರಥಿ</span>
            </h2>
            <p className="login-left-lead">
              {isKn
                ? 'ಕರ್ನಾಟಕದ ರೈತರಿಗಾಗಿ ವಿನ್ಯಾಸಗೊಳಿಸಲಾದ ಧ್ವನಿ ಮತ್ತು ದೃಷ್ಟಿ ಆಧಾರಿತ AI ಕೃಷಿ ಸಲಹೆಗಾರ.'
                : 'Empowering farmers with real-time AI advisory, voice assistance, and mandi insights.'}
            </p>
          </div>

          {/* Feature Highlight Cards */}
          <div className="login-feature-grid">
            <div className="login-feature-card">
              <div className="feature-icon-box icon-rag">
                <Bot size={20} />
              </div>
              <div className="feature-info">
                <h4>{isKn ? 'ಕನ್ನಡ & ಇಂಗ್ಲಿಷ್ AI ಸಮಾಲೋಚನೆ' : 'Multilingual Agro-AI Advisory'}</h4>
                <p>{isKn ? 'ಧ್ವನಿ & ಪಠ್ಯದ ಮೂಲಕ 30+ ಬೆಳೆಗಳಿಗೆ ತಜ್ಞರ ಮಾರ್ಗದರ್ಶನ.' : 'Real-time Kannada & English RAG guidance tailored to local soils.'}</p>
              </div>
            </div>

            <div className="login-feature-card">
              <div className="feature-icon-box icon-vision">
                <Activity size={20} />
              </div>
              <div className="feature-info">
                <h4>{isKn ? 'ಬೆಳೆ ರೋಗ ತಪಾಸಣೆ' : 'Visual Crop Disease Diagnosis'}</h4>
                <p>{isKn ? 'ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ಕ್ಷಣಾರ್ಧದಲ್ಲಿ ರೋಗ ಪರಿಹಾರ ಪಡೆಯಿರಿ.' : 'Upload leaf photos for instant disease detection & organic remedies.'}</p>
              </div>
            </div>

            <div className="login-feature-card">
              <div className="feature-icon-box icon-mandi">
                <TrendingUp size={20} />
              </div>
              <div className="feature-info">
                <h4>{isKn ? 'ನೇರ ಮಂಡಿ & APMC ದರಗಳು' : 'Live Mandi & Market Rates'}</h4>
                <p>{isKn ? 'ಕರ್ನಾಟಕದ ಎಲ್ಲಾ ಪ್ರಮುಖ ಮಾರುಕಟ್ಟೆಗಳ ಬೆಲೆ ಮಾಹಿತಿ.' : 'Direct daily APMC market price trends and selling advice.'}</p>
              </div>
            </div>

            <div className="login-feature-card">
              <div className="feature-icon-box icon-weather">
                <CloudSun size={20} />
              </div>
              <div className="feature-info">
                <h4>{isKn ? 'ಹವಾಮಾನ & ಯೋಜನೆಗಳು' : 'Weather Alerts & Schemes'}</h4>
                <p>{isKn ? 'ಮಳೆ ಮುನ್ಸೂಚನೆ ಮತ್ತು ಕಿಸಾನ್ ಯೋಜನೆಗಳ ನೆರವು.' : 'Hyperlocal forecasts and subsidy alerts (PM-Kisan, PMFBY).'}</p>
              </div>
            </div>
          </div>

          {/* Trust Highlights */}
          <div className="login-trust-row">
            <div className="trust-pill">
              <CheckCircle2 size={13} />
              <span>30+ Crops Covered</span>
            </div>
            <div className="trust-pill">
              <ShieldCheck size={13} />
              <span>Verified Agronomy</span>
            </div>
            <div className="trust-pill">
              <Sparkles size={13} />
              <span>100% Free for Farmers</span>
            </div>
          </div>

          {/* Quote */}
          <div className="login-quote-card">
            <p className="login-left-quote">
              {isKn
                ? '"ಉತ್ತಮ ಕೃಷಿ ಉತ್ತಮ ಜ್ಞಾನದಿಂದ ಪ್ರಾರಂಭವಾಗುತ್ತದೆ."'
                : '"Good farming begins with good knowledge — Empowering farmers from seed to harvest."'}
            </p>
          </div>

        </div>
      </div>

      {/* ── RIGHT PANEL: Real Backend Authentication ────────────── */}
      <div className="login-right">
        {/* Top bar */}
        <div className="login-top-bar">
          <button
            type="button"
            className="login-back-btn"
            onClick={() => navigate('/')}
            aria-label="Back to home"
          >
            <ArrowLeft size={15} />
            <span>{isKn ? 'ಮುಖಪುಟಕ್ಕೆ ಮರಳಿ' : 'Back to home'}</span>
          </button>
          
          <div className="login-top-actions">
            <div className="lang-toggle" role="group" aria-label="Language">
              <button
                type="button"
                className={`lang-btn ${!isKn ? 'lang-active' : ''}`}
                onClick={() => setLanguage('en')}
              >
                EN
              </button>
              <button
                type="button"
                className={`lang-btn ${isKn ? 'lang-active' : ''}`}
                onClick={() => setLanguage('kn')}
              >
                ಕನ್ನಡ
              </button>
            </div>
            <ThemeSelector />
          </div>
        </div>

        {/* Form area */}
        <div className="login-form-area">
          <div className="login-logo">
            <span className="login-logo-leaf">🌱</span>
          </div>

          <h1 className="login-headline">
            {isKn ? 'ರೈತ ಸಾರಥಿಗೆ ಸುಸ್ವಾಗತ' : 'Welcome back to Raitha Sathi'}
          </h1>
          <p className="login-tagline">
            {isKn
              ? 'ನಿಮ್ಮ ಕೃಷಿ ಖಾತೆಗೆ ಲಾಗಿನ್ ಆಗಿ ಮುಂದುವರಿಯಿರಿ.'
              : 'Sign in to access your farm advisory, mandi rates & AI diagnosis.'}
          </p>

          {/* Auth Error Banner if login fails */}
          {authError && (
            <div className="auth-error-banner" role="alert">
              <AlertCircle size={16} />
              <span>{authError}</span>
            </div>
          )}

          {/* Login form */}
          <form onSubmit={handleLogin} className="login-form" noValidate>
            
            {/* Email or Mobile or Name identifier */}
            <div className="form-field">
              <label htmlFor="login-identifier" className="field-label">
                <Mail size={14} aria-hidden="true" />
                {isKn ? 'ಇಮೇಲ್, ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಹೆಸರು' : 'Email, Mobile Number, or Username'}
              </label>
              <input
                id="login-identifier"
                type="text"
                className={`text-input ${errors.identifier ? 'input-error' : ''}`}
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  setErrors((p) => ({ ...p, identifier: '' }));
                  setAuthError('');
                }}
                placeholder={isKn ? 'ಉದಾ: xyz, xyz@gmail.com ಅಥವಾ 9876543210' : 'e.g. xyz, xyz@gmail.com, or 9876543210'}
                autoComplete="username"
                aria-describedby={errors.identifier ? 'identifier-err' : undefined}
                aria-invalid={!!errors.identifier}
              />
              <FieldError message={errors.identifier} />
            </div>

            {/* Password */}
            <div className="form-field">
              <label htmlFor="login-password" className="field-label">
                <Lock size={14} aria-hidden="true" />
                {isKn ? 'ಪಾಸ್‌ವರ್ಡ್' : 'Password'}
              </label>
              <div className="password-wrap">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`text-input password-input ${errors.password ? 'input-error' : ''}`}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setErrors((p) => ({ ...p, password: '' }));
                    setAuthError('');
                  }}
                  placeholder={isKn ? 'ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ' : 'Enter your password'}
                  autoComplete="current-password"
                  aria-describedby={errors.password ? 'pw-err' : undefined}
                  aria-invalid={!!errors.password}
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

            {/* Forgot password */}
            <div className="form-links-row">
              <Link to="/forgot-password" className="text-link">
                {isKn ? 'ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿರಾ?' : 'Forgot Password?'}
              </Link>
            </div>

            {/* Login button — Active Backend Authentication */}
            <button
              type="submit"
              className="btn-auth btn-auth-primary"
              disabled={isLoading}
              id="login-submit-btn"
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  {isKn ? 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ…' : 'Authenticating…'}
                </>
              ) : (
                <>
                  {isKn ? 'ಲಾಗಿನ್ ಆಗಿ' : 'Login to Sathi'}
                  <ArrowRight size={15} aria-hidden="true" />
                </>
              )}
            </button>
          </form>

          {/* Separator */}
          <div className="auth-separator" aria-hidden="true">
            <span>{isKn ? 'ಅಥವಾ ತ್ವರಿತ ಪರೀಕ್ಷೆ' : 'or quick test'}</span>
          </div>

          {/* Quick 1-Click Demo Login */}
          <button
            type="button"
            className="btn-auth btn-auth-demo"
            onClick={handleQuickDemo}
            disabled={isLoading}
            id="demo-login-btn"
            title="Instant sign-in with pre-seeded demo farmer account"
          >
            <Sparkles size={15} aria-hidden="true" />
            {isKn ? 'ಡೆಮೊ ರೈತ ಖಾತೆಯಿಂದ ಪ್ರವೇಶಿಸಿ' : 'Try Demo Farmer Account (farmer-01)'}
          </button>

          {/* Register link */}
          <div className="auth-footer-links">
            <span className="auth-footer-text">
              {isKn ? 'ಹೊಸ ರೈತರಾಗಿದ್ದೀರಾ?' : 'New to Raitha Sathi?'}
            </span>
            <Link to="/register" className="btn-auth-outline" id="goto-register-btn">
              <UserPlus size={15} aria-hidden="true" />
              {isKn ? 'ಹೊಸ ರೈತ ಖಾತೆ ತೆರೆಯಿರಿ' : 'Create Farmer Account'}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
