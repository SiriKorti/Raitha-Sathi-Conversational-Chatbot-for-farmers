import React from 'react';
import './EmptyState.css';

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div className={`empty-state-card glass-panel animate-fade-in ${className}`}>
      {Icon && (
        <div className="empty-state-icon-box">
          <Icon size={36} className="empty-state-icon" />
        </div>
      )}
      {title && <h3 className="empty-state-title">{title}</h3>}
      {description && <p className="empty-state-desc">{description}</p>}
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
};
