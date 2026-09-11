import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  User,
  Mail,
  Phone,
  MapPin,
  LogOut,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Globe,
  SunMoon,
  Server,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { useTheme } from '../../context/ThemeContext';
import { Modal } from '../../components/common/Modal';
import { StatusBadge } from '../../components/common/StatusBadge';
import './SettingsPage.css';

export const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, logout, deleteAccount, isLoading } = useAuth();
  const { language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const { showToast } = useToast();

  const isKn = language === 'kn';

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [deleteConfirmationInput, setDeleteConfirmationInput] = useState('');

  /* ── Handle Logout ────────────────────────────────────────── */
  const handleConfirmLogout = async () => {
    setIsProcessing(true);
    try {
      await logout();
      showToast(isKn ? 'ಯಶಸ್ವಿಯಾಗಿ ಲಾಗ್ ಔಟ್ ಆಗಿದೆ.' : 'Logged out successfully.', 'success');
      navigate('/login');
    } catch {
      navigate('/login');
    } finally {
      setIsProcessing(false);
      setShowLogoutModal(false);
    }
  };

  /* ── Handle Delete Account ────────────────────────────────── */
  const handleConfirmDelete = async () => {
    const targetIdentifier = user?.email || user?.mobile || user?.id;
    if (!targetIdentifier) {
      showToast(isKn ? 'ಬಳಕೆದಾರರ ಖಾತೆ ಪತ್ತೆಯಾಗಿಲ್ಲ.' : 'No active user found to delete.', 'error');
      return;
    }

    setIsProcessing(true);
    try {
      await deleteAccount(targetIdentifier);
      showToast(
        isKn
          ? 'ನಿಮ್ಮ ಖಾತೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಅಳಿಸಲಾಗಿದೆ.'
          : 'Your account has been permanently deleted from the database.',
        'success'
      );
      navigate('/login');
    } catch (err) {
      showToast(
        err?.message || (isKn ? 'ಖಾತೆ ಅಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.' : 'Failed to delete account. Please try again.'),
        'error'
      );
    } finally {
      setIsProcessing(false);
      setShowDeleteModal(false);
    }
  };

  const rawDisplayName = user?.fullName || user?.name || (isKn ? 'ರೈತರು' : 'Farmer');
  const displayName = (rawDisplayName === 'Ramesh Gowda' || user?.id === 'farmer_001') ? 'farmer-01' : rawDisplayName;
  const displayEmail = user?.email || (isKn ? 'ಇಮೇಲ್ ನಮೂದಿಸಿಲ್ಲ' : 'No email linked');
  const displayPhone = user?.mobile || user?.phone || (isKn ? 'ಮೊಬೈಲ್ ನಮೂದಿಸಿಲ್ಲ' : 'No phone linked');
  const displayLocation = [user?.village, user?.taluk, user?.district, user?.state]
    .filter(Boolean)
    .join(', ') || 'Karnataka, India';

  return (
    <div className="settings-page">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="settings-header">
        <div className="settings-header-icon">
          <SettingsIcon size={24} />
        </div>
        <div className="settings-header-content">
          <div className="settings-header-title-row">
            <h1 className="settings-title">{isKn ? 'ಸೆಟ್ಟಿಂಗ್ಸ್ & ಖಾತೆ' : 'Account & Settings'}</h1>
            <StatusBadge status="ready" label={isKn ? 'ಸರ್ವರ್ ಸಂಪರ್ಕಿತವಾಗಿದೆ' : 'Backend Connected'} />
          </div>
          <p className="settings-subtitle">
            {isKn
              ? 'ನಿಮ್ಮ ಪ್ರೊಫೈಲ್, ಅಪ್ಲಿಕೇಶನ್ ಆದ್ಯತೆಗಳು ಮತ್ತು ಭದ್ರತಾ ಸೆಟ್ಟಿಂಗ್‌ಗಳನ್ನು ನಿರ್ವಹಿಸಿ.'
              : 'Manage your farmer profile, app preferences, and authentication session.'}
          </p>
        </div>
      </div>

      <div className="settings-grid">
        {/* ── 1. Profile Overview Card ──────────────────────── */}
        <section className="settings-card profile-card" aria-label="Profile Information">
          <div className="card-header">
            <div className="card-title-wrap">
              <User size={18} className="card-icon" />
              <h2>{isKn ? 'ರೈತರ ಪ್ರೊಫೈಲ್ ಮಾಹಿತಿ' : 'Farmer Profile Details'}</h2>
            </div>
            <span className="role-pill">
              <ShieldCheck size={13} />
              {user?.role === 'admin' ? 'Admin' : user?.role === 'developer' ? 'Developer' : 'Verified Farmer'}
            </span>
          </div>

          <div className="profile-details-grid">
            <div className="profile-detail-item">
              <span className="detail-label">{isKn ? 'ಪೂರ್ಣ ಹೆಸರು' : 'Full Name'}</span>
              <span className="detail-value">{displayName}</span>
            </div>

            <div className="profile-detail-item">
              <span className="detail-label">{isKn ? 'ಇಮೇಲ್ ವಿಳಾಸ' : 'Email Address'}</span>
              <span className="detail-value">{displayEmail}</span>
            </div>

            <div className="profile-detail-item">
              <span className="detail-label">{isKn ? 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : 'Mobile Number'}</span>
              <span className="detail-value">{displayPhone}</span>
            </div>

            <div className="profile-detail-item">
              <span className="detail-label">{isKn ? 'ಸ್ಥಳ / ಗ್ರಾಮ / ಜಿಲ್ಲೆ' : 'Farm Location'}</span>
              <span className="detail-value">{displayLocation}</span>
            </div>
          </div>
        </section>

        {/* ── 2. Preferences & Environment Card ────────────── */}
        <section className="settings-card" aria-label="Preferences">
          <div className="card-header">
            <div className="card-title-wrap">
              <Globe size={18} className="card-icon" />
              <h2>{isKn ? 'ಆದ್ಯತೆಗಳು & ಪರಿಸರ' : 'Preferences & Environment'}</h2>
            </div>
          </div>

          <div className="settings-options-list">
            {/* Language Selection */}
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-name">{isKn ? 'ಆದ್ಯತೆಯ ಭಾಷೆ' : 'Preferred Language'}</span>
                <span className="setting-desc">
                  {isKn ? 'ಧ್ವನಿ ಮತ್ತು ಪಠ್ಯ ಸಂವಹನಕ್ಕಾಗಿ ಭಾಷೆ' : 'Language used for voice and text advisory'}
                </span>
              </div>
              <div className="setting-control">
                <div className="lang-toggle">
                  <button
                    type="button"
                    className={`lang-btn ${language === 'en' ? 'lang-active' : ''}`}
                    onClick={() => setLanguage('en')}
                  >
                    English
                  </button>
                  <button
                    type="button"
                    className={`lang-btn ${language === 'kn' ? 'lang-active' : ''}`}
                    onClick={() => setLanguage('kn')}
                  >
                    ಕನ್ನಡ
                  </button>
                </div>
              </div>
            </div>

            {/* Theme Toggle */}
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-name">{isKn ? 'ಥೀಮ್ ಮೋಡ್' : 'Interface Theme'}</span>
                <span className="setting-desc">
                  {theme === 'dark' ? (isKn ? 'ಡಾರ್ಕ್ ಮೋಡ್ ಸಕ್ರಿಯವಾಗಿದೆ' : 'Dark Botanical mode') : (isKn ? 'ಲೈಟ್ ಮೋಡ್ ಸಕ್ರಿಯವಾಗಿದೆ' : 'Light Parchment mode')}
                </span>
              </div>
              <div className="setting-control">
                <button type="button" className="btn-theme-toggle" onClick={toggleTheme}>
                  <SunMoon size={16} />
                  <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
                </button>
              </div>
            </div>

            {/* Server Connection Info */}
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-name">{isKn ? 'ಸರ್ವರ್ ಸ್ಥಿತಿ' : 'Backend Engine'}</span>
                <span className="setting-desc">FastAPI RAG Backend (:8000)</span>
              </div>
              <div className="setting-control">
                <span className="server-status-tag">
                  <span className="status-indicator-dot" />
                  Online
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* ── 3. Session & Account Actions Card ────────────── */}
        <section className="settings-card danger-zone-card" aria-label="Account Actions">
          <div className="card-header">
            <div className="card-title-wrap">
              <AlertTriangle size={18} className="card-icon text-danger" />
              <h2>{isKn ? 'ಖಾತೆ ನಿರ್ವಹಣೆ & ಸುರಕ್ಷತೆ' : 'Account Management & Security'}</h2>
            </div>
          </div>

          <div className="account-actions-list">
            {/* Logout Action */}
            <div className="account-action-item">
              <div className="action-info">
                <h4>{isKn ? 'ಲಾಗಿನ್ ಅವಧಿ ಮುಕ್ತಾಯ (ಲಾಗ್ ಔಟ್)' : 'Sign Out of Session'}</h4>
                <p>
                  {isKn
                    ? 'ಪ್ರಸ್ತುತ ಸಾಧನದಿಂದ ನಿಮ್ಮ ರೈತ ಖಾತೆಯಿಂದ ಸುರಕ್ಷಿತವಾಗಿ ಹೊರಬನ್ನಿ.'
                    : 'Safely sign out from your current session on this device.'}
                </p>
              </div>
              <button
                type="button"
                className="btn-settings btn-logout"
                onClick={() => setShowLogoutModal(true)}
                disabled={isLoading || isProcessing}
                id="settings-logout-btn"
              >
                <LogOut size={16} />
                <span>{isKn ? 'ಲಾಗ್ ಔಟ್' : 'Log Out'}</span>
              </button>
            </div>

            {/* Delete Account Action */}
            <div className="account-action-item danger-item">
              <div className="action-info">
                <h4 className="text-danger">{isKn ? 'ಖಾತೆಯನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸಿ' : 'Delete Account Permanently'}</h4>
                <p>
                  {isKn
                    ? 'ನಿಮ್ಮ ಖಾತೆ, ಪ್ರೊಫೈಲ್ ಮತ್ತು ಡೇಟಾವನ್ನು ಡೇಟಾಬೇಸ್‌ನಿಂದ ಶಾಶ್ವತವಾಗಿ ತೆಗೆದುಹಾಕಲಾಗುತ್ತದೆ. ಈ ಕ್ರಿಯೆಯನ್ನು ಹಿಂಪಡೆಯಲಾಗುವುದಿಲ್ಲ.'
                    : 'Permanently remove your farmer profile and credentials from the backend database. This action cannot be undone.'}
                </p>
              </div>
              <button
                type="button"
                className="btn-settings btn-delete-account"
                onClick={() => setShowDeleteModal(true)}
                disabled={isLoading || isProcessing}
                id="settings-delete-btn"
              >
                <Trash2 size={16} />
                <span>{isKn ? 'ಖಾತೆ ಅಳಿಸಿ' : 'Delete Account'}</span>
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* ── Logout Confirmation Modal ──────────────────────── */}
      <Modal
        isOpen={showLogoutModal}
        onClose={() => setShowLogoutModal(false)}
        title={isKn ? 'ಲಾಗ್ ಔಟ್ ದೃಢೀಕರಿಸಿ' : 'Confirm Sign Out'}
        maxWidth="440px"
      >
        <div className="modal-inner-content">
          <p className="modal-text">
            {isKn
              ? 'ನೀವು ರೈತ ಸಾಥಿ ಅಪ್ಲಿಕೇಶನ್‌ನಿಂದ ಲಾಗ್ ಔಟ್ ಮಾಡಲು ಖಚಿತವಾಗಿದ್ದೀರಾ?'
              : 'Are you sure you want to sign out of Raitha Sathi?'}
          </p>
          <div className="modal-actions-row">
            <button
              type="button"
              className="btn-modal-secondary"
              onClick={() => setShowLogoutModal(false)}
              disabled={isProcessing}
            >
              {isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}
            </button>
            <button
              type="button"
              className="btn-modal-primary"
              onClick={handleConfirmLogout}
              disabled={isProcessing}
              id="confirm-logout-btn"
            >
              <LogOut size={15} />
              <span>{isProcessing ? (isKn ? 'ಲಾಗ್ ಔಟ್ ಆಗುತ್ತಿದೆ…' : 'Logging out…') : (isKn ? 'ಹೌದು, ಲಾಗ್ ಔಟ್ ಮಾಡಿ' : 'Yes, Sign Out')}</span>
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Delete Account Confirmation Modal ──────────────── */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title={isKn ? 'ಖಾತೆ ಅಳಿಸುವಿಕೆಯನ್ನು ದೃಢೀಕರಿಸಿ' : 'Confirm Account Deletion'}
        maxWidth="480px"
      >
        <div className="modal-inner-content">
          <div className="modal-danger-banner">
            <AlertTriangle size={22} className="text-danger" />
            <div>
              <strong>{isKn ? 'ಎಚ್ಚರಿಕೆ: ಈ ಕ್ರಿಯೆಯನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗುವುದಿಲ್ಲ!' : 'Warning: This action is permanent!'}</strong>
              <p>
                {isKn
                  ? `ಬಳಕೆದಾರ "${displayName}" ಅವರ ಖಾತೆಯನ್ನು ಬ್ಯಾಕೆಂಡ್ ಡೇಟಾಬೇಸ್‌ನಿಂದ ಶಾಶ್ವತವಾಗಿ ಅಳಿಸಲಾಗುತ್ತದೆ.`
                  : `Your farmer account (${user?.email || user?.mobile || displayName}) will be permanently deleted from the database.`}
              </p>
            </div>
          </div>

          <p className="modal-subtext">
            {isKn
              ? 'ದೃಢೀಕರಿಸಲು, ಕೆಳಗಿನ ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ:'
              : 'To confirm permanent deletion from backend, click the button below:'}
          </p>

          <div className="modal-actions-row">
            <button
              type="button"
              className="btn-modal-secondary"
              onClick={() => setShowDeleteModal(false)}
              disabled={isProcessing}
            >
              {isKn ? 'ರದ್ದುಮಾಡಿ (ಖಾತೆ ಉಳಿಸಿ)' : 'Cancel & Keep Account'}
            </button>
            <button
              type="button"
              className="btn-modal-danger"
              onClick={handleConfirmDelete}
              disabled={isProcessing}
              id="confirm-delete-account-btn"
            >
              <Trash2 size={15} />
              <span>{isProcessing ? (isKn ? 'ಅಳಿಸಲಾಗುತ್ತಿದೆ…' : 'Deleting…') : (isKn ? 'ಹೌದು, ಖಾತೆ ಅಳಿಸಿ' : 'Permanently Delete Account')}</span>
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
