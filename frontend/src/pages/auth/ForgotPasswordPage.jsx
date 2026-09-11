import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Mail,
  ArrowRight,
  ArrowLeft,
  Info,
  AlertCircle,
  KeyRound,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { ThemeSelector } from '../../components/common/ThemeSelector';
import './ForgotPasswordPage.css';

/* ── Field error component ─────────────────────────────── */
const FieldError = ({ message }) =>
  message ? (
    <span className="field-error" role="alert">
      <AlertCircle size={12} />
      {message}
    </span>
  ) : null;

export const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const { language, setLanguage } = useLanguage();

  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email address is required / ಇಮೇಲ್ ವಿಳಾಸ ಅಗತ್ಯವಿದೆ');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address / ಮಾನ್ಯವಾದ ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ನಮೂದಿಸಿ');
      return;
    }

    setError('');
    // Honest backend-dependent state: do NOT fake email dispatch or reset tokens
    setSubmitted(true);
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
              "Recover your farmer account credentials securely."
            </p>
            <p className="login-left-quote-kn">
              "ನಿಮ್ಮ ರೈತ ಖಾತೆಯ ವಿವರಗಳನ್ನು ಸುರಕ್ಷಿತವಾಗಿ ಮರುಪಡೆಯಿರಿ."
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
            onClick={() => navigate('/login')}
            aria-label="Back to login"
          >
            <ArrowLeft size={15} />
            <span>Back to login</span>
          </button>

          <div className="login-top-actions">
            <div className="lang-toggle" role="group" aria-label="Language">
              <button
                type="button"
                className={`lang-btn ${lang === 'en' ? 'lang-active' : ''}`}
                onClick={() => setLanguage('en')}
              >
                EN
              </button>
              <button
                type="button"
                className={`lang-btn ${lang === 'kn' ? 'lang-active' : ''}`}
                onClick={() => setLanguage('kn')}
              >
                ಕನ್ನಡ
              </button>
            </div>
            <ThemeSelector />
          </div>
        </div>

        {/* Content Area */}
        <div className="login-form-area">
          <div className="login-logo">
            <span className="login-logo-leaf">
              <KeyRound size={22} color="var(--primary)" />
            </span>
          </div>

          <h1 className="login-headline">Reset Password</h1>
          <p className="login-tagline">
            Enter your registered email address to receive password reset instructions.
          </p>

          {!submitted ? (
            <form onSubmit={handleSubmit} className="login-form" noValidate>
              <div className="form-field">
                <label htmlFor="reset-email" className="field-label">
                  <Mail size={14} aria-hidden="true" />
                  Registered Email / ನೋಂದಾಯಿತ ಇಮೇಲ್
                </label>
                <input
                  id="reset-email"
                  type="email"
                  className={`text-input ${error ? 'input-error' : ''}`}
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setError('');
                  }}
                  placeholder="farmer@example.com"
                  autoComplete="email"
                  autoFocus
                />
                <FieldError message={error} />
              </div>

              <button type="submit" className="btn-auth btn-auth-dev" id="forgot-submit-btn">
                Send Recovery Instructions
                <ArrowRight size={15} aria-hidden="true" />
              </button>
            </form>
          ) : (
            <div className="reg-submitted-wrap" role="status">
              <div className="auth-notice status-notice">
                <div className="notice-icon">
                  <Info size={18} />
                </div>
                <div className="notice-body">
                  <strong className="notice-title">Backend Authentication Not Connected</strong>
                  <p className="notice-text">
                    Password recovery will be available once backend authentication is connected.
                    No reset link has been dispatched.
                  </p>
                </div>
              </div>

              <p className="submitted-guidance">
                You can return to the login screen and enter using <strong>Development Mode</strong> to access your workspace.
              </p>

              <div className="submitted-actions">
                <Link to="/login" className="btn-auth btn-auth-dev" id="forgot-back-login">
                  Back to Login
                  <ArrowRight size={15} aria-hidden="true" />
                </Link>
              </div>
            </div>
          )}

          <div className="auth-footer-links">
            <span className="auth-footer-text">Remember your password?</span>
            <Link to="/login" className="text-link">
              Sign in to your account →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
