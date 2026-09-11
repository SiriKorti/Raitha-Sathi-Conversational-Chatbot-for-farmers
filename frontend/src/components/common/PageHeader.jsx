import React from 'react';
import './PageHeader.css';

export const PageHeader = ({
  title,
  subtitle,
  icon: Icon,
  action,
  className = ''
}) => {
  return (
    <div className={`page-header-container ${className}`}>
      <div className="page-header-left">
        {Icon && (
          <div className="page-header-icon-box">
            <Icon size={24} />
          </div>
        )}
        <div className="page-header-text">
          <h1 className="page-header-title">{title}</h1>
          {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="page-header-action">{action}</div>}
    </div>
  );
};
