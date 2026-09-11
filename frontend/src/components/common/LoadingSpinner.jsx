import React from 'react';
import { Loader2 } from 'lucide-react';
import './LoadingSpinner.css';

export const LoadingSpinner = ({ text, size = 28 }) => {
  return (
    <div className="loading-spinner-wrapper animate-fade-in">
      <Loader2 size={size} className="animate-spin spinner-icon" />
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );
};
