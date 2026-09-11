import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Bookmark,
  Trash2,
  Copy,
  Check,
  Calendar,
  Sprout,
  Tag,
  MessageSquare,
  Database,
  Sparkles,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';

import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { adviceService } from '../../services/adviceService';
import { PageHeader } from '../../components/common/PageHeader';
import { Card } from '../../components/common/Card';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { ErrorState } from '../../components/common/ErrorState';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import './SavedAdvicePage.css';

export const SavedAdvicePage = () => {
  const { user } = useAuth();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const userId = user?.id || 'user_123';

  const [adviceList, setAdviceList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch saved advice from backend
  const fetchAdvice = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await adviceService.getSavedAdvice(userId);
      if (response && response.status === 'success') {
        setAdviceList(response.advice || []);
      } else {
        throw new Error(response?.message || 'Failed to fetch saved advice');
      }
    } catch (err) {
      console.error('Failed to load saved advice:', err);
      setError(err.message || 'Unable to load saved advice. Please check backend connection.');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchAdvice();
  }, [fetchAdvice]);

  // Copy advice content to clipboard
  const handleCopy = async (adviceId, content) => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(adviceId);
      showToast(language === 'kn' ? 'ಸಲಹೆಯನ್ನು ನಕಲಿಸಲಾಗಿದೆ!' : 'Advice copied to clipboard!', 'info');
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  // Open confirmation modal for deletion
  const handleOpenDelete = (item) => {
    setItemToDelete(item);
    setDeleteModalOpen(true);
  };

  // Confirm and execute deletion
  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;
    setIsDeleting(true);
    try {
      const targetUserId = itemToDelete.user_id || userId;
      const response = await adviceService.deleteSavedAdvice(targetUserId, itemToDelete.advice_id);
      if (response && response.status === 'success') {
        setAdviceList((prev) => prev.filter((a) => a.advice_id !== itemToDelete.advice_id));
        showToast(t('saved.delete_success') || (language === 'kn' ? 'ಸಲಹೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ತೆಗೆದುಹಾಕಲಾಗಿದೆ.' : 'Advice removed from saved list.'), 'success');
        setDeleteModalOpen(false);
        setItemToDelete(null);
      } else {
        throw new Error(response?.message || 'Failed to delete advice');
      }
    } catch (err) {
      console.error('Delete advice error:', err);
      showToast(err.message || (language === 'kn' ? 'ಸಲಹೆಯನ್ನು ತೆಗೆದುಹಾಕಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.' : 'Failed to delete advice. Please try again.'), 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  // Format date safely
  const formatSavedDate = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(language === 'kn' ? 'kn-IN' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="saved-advice-page">
      <PageHeader
        title={t('saved.title') || (language === 'kn' ? 'ಉಳಿಸಿದ ಸಲಹೆಗಳು' : 'Saved Advice')}
        subtitle={t('saved.subtitle') || (language === 'kn' ? 'ಉಳಿಸಿದ ಕೃಷಿ ಸಲಹೆಗಳನ್ನು ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.' : 'Review and manage your bookmarked agricultural advisories anytime.')}
        icon={Bookmark}
      >
        <div className="saved-header-badge">
          <span className="saved-count-pill">
            {adviceList.length} {language === 'kn' ? 'ಸಲಹೆಗಳು' : adviceList.length === 1 ? 'Advisory' : 'Advisories'}
          </span>
        </div>
      </PageHeader>

      <div className="saved-advice-content">
        {/* Loading State */}
        {isLoading && (
          <div className="saved-loading-state">
            <LoadingSpinner size="large" label={language === 'kn' ? 'ಉಳಿಸಿದ ಸಲಹೆಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...' : 'Loading saved advisories...'} />
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <ErrorState
            title={language === 'kn' ? 'ಸಲಹೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ' : 'Failed to Load Saved Advice'}
            message={error}
            onRetry={fetchAdvice}
          />
        )}

        {/* Empty State */}
        {!isLoading && !error && adviceList.length === 0 && (
          <EmptyState
            icon={Bookmark}
            title={t('saved.empty_title') || (language === 'kn' ? 'ಇನ್ನೂ ಯಾವುದೇ ಸಲಹೆ ಉಳಿಸಿಲ್ಲ' : 'No Saved Advice Yet')}
            description={t('saved.empty_desc') || (language === 'kn' ? 'ರೈತ ಸಾಥಿ ಚಾಟ್‌ನಲ್ಲಿ ದೊರೆತ ಉಪಯುಕ್ತ ಸಲಹೆಗಳನ್ನು ಉಳಿಸಿ, ಅವು ಇಲ್ಲಿ ಸುಲಭವಾಗಿ ಸಿಗುತ್ತವೆ.' : 'Save useful answers from Ask Sathi and they will appear here for easy reference.')}
            actionLabel={language === 'kn' ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Ask Sathi'}
            onAction={() => navigate('/chat')}
          />
        )}

        {/* Saved Advice Cards Grid */}
        {!isLoading && !error && adviceList.length > 0 && (
          <div className="saved-advice-grid">
            {adviceList.map((item) => (
              <Card key={item.advice_id} className="saved-advice-card" variant="default">
                {/* Card Meta Header */}
                <div className="saved-card-header">
                  <div className="saved-tags-cluster">
                    {item.crop && (
                      <span className="saved-tag crop-tag">
                        <Sprout size={13} />
                        <span>{item.crop}</span>
                      </span>
                    )}
                    {item.topic && (
                      <span className="saved-tag topic-tag">
                        <Tag size={12} />
                        <span>{item.topic}</span>
                      </span>
                    )}
                    {item.source === 'database' && (
                      <span className="saved-tag db-tag" title="Grounded in verified agricultural database">
                        <Database size={12} />
                        <span>Verified</span>
                      </span>
                    )}
                    {item.source === 'rag' && (
                      <span className="saved-tag rag-tag" title="Derived from agricultural research knowledge base">
                        <Sparkles size={12} />
                        <span>RAG</span>
                      </span>
                    )}
                  </div>

                  <div className="saved-date-label">
                    <Calendar size={13} />
                    <span>{formatSavedDate(item.saved_at)}</span>
                  </div>
                </div>

                {/* Farmer Question */}
                {item.user_query && (
                  <div className="saved-question-box">
                    <MessageSquare size={16} className="question-icon" />
                    <span className="question-text">{item.user_query}</span>
                  </div>
                )}

                {/* Advice Content with Markdown Support */}
                <div className="saved-answer-box">
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {item.content}
                    </ReactMarkdown>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="saved-card-footer">
                  <div className="footer-left-actions">
                    <button
                      type="button"
                      className="card-action-btn copy-action-btn"
                      onClick={() => handleCopy(item.advice_id, item.content)}
                      title={language === 'kn' ? 'ಸಲಹೆಯನ್ನು ನಕಲಿಸಿ' : 'Copy advice'}
                      aria-label="Copy advice content"
                    >
                      {copiedId === item.advice_id ? (
                        <>
                          <Check size={14} className="copied-icon" />
                          <span>{language === 'kn' ? 'ನಕಲಿಸಲಾಗಿದೆ ✓' : 'Copied ✓'}</span>
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          <span>{language === 'kn' ? 'ನಕಲಿಸಿ' : 'Copy'}</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      className="card-action-btn ask-followup-btn"
                      onClick={() =>
                        navigate('/chat', {
                          state: {
                            prompt: item.user_query
                              ? `Regarding "${item.user_query}": `
                              : 'Regarding my saved advice: ',
                          },
                        })
                      }
                      title={language === 'kn' ? 'ಚಾಟ್‌ನಲ್ಲಿ ಈ ಸಲಹೆಯ ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ಕೇಳಿ' : 'Ask more about this advice in Chat'}
                      aria-label="Ask follow up question in chat"
                    >
                      <ArrowRight size={14} />
                      <span>{language === 'kn' ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Ask Sathi'}</span>
                    </button>
                  </div>

                  <button
                    type="button"
                    className="card-action-btn delete-action-btn"
                    onClick={() => handleOpenDelete(item)}
                    title={language === 'kn' ? 'ಉಳಿಸಿದ ಸಲಹೆ ತೆಗೆದುಹಾಕಿ' : 'Delete saved advice'}
                    aria-label="Delete this saved advice"
                  >
                    <Trash2 size={14} />
                    <span>{language === 'kn' ? 'ತೆಗೆದುಹಾಕಿ' : 'Delete'}</span>
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => {
          if (!isDeleting) {
            setDeleteModalOpen(false);
            setItemToDelete(null);
          }
        }}
        title={language === 'kn' ? 'ಸಲಹೆಯನ್ನು ಪಟ್ಟಿಯಿಂದ ತೆಗೆದುಹಾಕಿ' : 'Delete Saved Advice'}
      >
        <div className="delete-modal-body">
          <div className="delete-modal-warning">
            <AlertTriangle size={24} className="warning-icon" />
            <p>
              {t('saved.delete_confirm') ||
                'Are you sure you want to remove this advice from your saved list?'}
            </p>
          </div>

          {itemToDelete?.user_query && (
            <div className="delete-item-preview">
              <strong>Question: </strong>
              <span>{itemToDelete.user_query}</span>
            </div>
          )}

          <div className="modal-actions-row">
            <Button
              variant="danger"
              icon={Trash2}
              onClick={handleConfirmDelete}
              disabled={isDeleting}
            >
              {isDeleting
                ? (language === 'kn' ? 'ತೆಗೆದುಹಾಕಲಾಗುತ್ತಿದೆ...' : 'Deleting...')
                : (language === 'kn' ? 'ಹೌದು, ತೆಗೆದುಹಾಕಿ' : 'Yes, Delete')}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setDeleteModalOpen(false);
                setItemToDelete(null);
              }}
              disabled={isDeleting}
            >
              {language === 'kn' ? 'ರದ್ದುಮಾಡಿ' : 'Cancel & Keep'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
