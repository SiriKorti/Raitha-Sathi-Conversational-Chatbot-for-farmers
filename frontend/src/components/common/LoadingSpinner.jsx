import React from 'react';
import { Loader2 } from 'lucide-react';
import './LoadingSpinner.css';

export const LoadingSpinner = ({ text, label, size = 28 }) => {
  const numericSize = typeof size === 'number' 
    ? size 
    : size === 'large' ? 36 : size === 'small' ? 18 : 28;
  const displayText = text || label;
  return (
    <div className="loading-spinner-wrapper animate-fade-in">
      <Loader2 size={numericSize} className="animate-spin spinner-icon" />
      {displayText && <span className="spinner-text">{displayText}</span>}
    </div>
  );
};
