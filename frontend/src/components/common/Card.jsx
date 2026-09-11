import React from 'react';
import './Card.css';

export const Card = ({
  children,
  glass = false,
  hoverable = false,
  className = '',
  onClick,
  ...props
}) => {
  const baseClass = glass ? 'glass-panel' : 'surface-card';
  const hoverClass = hoverable ? 'glass-panel-hover' : '';

  return (
    <div
      className={`${baseClass} ${hoverClass} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};
