import React from 'react';
import './Input.css';

export const Input = ({
  label,
  error,
  hint,
  icon: Icon,
  className = '',
  id,
  type = 'text',
  ...props
}) => {
  const inputId = id || `input_${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`input-field-group ${className}`}>
      {label && <label htmlFor={inputId} className="input-label">{label}</label>}
      <div className={`input-wrapper ${error ? 'input-error-state' : ''}`}>
        {Icon && <Icon size={18} className="input-icon" />}
        <input id={inputId} type={type} className="input-control" {...props} />
      </div>
      {error && <span className="input-error-text">{error}</span>}
      {!error && hint && <span className="input-hint-text">{hint}</span>}
    </div>
  );
};
