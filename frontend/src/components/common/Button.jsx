import React from 'react';
import { Loader2 } from 'lucide-react';
import './Button.css';

export const Button = ({
  children,
  variant = 'primary', // primary | secondary | glow | icon | text
  size = 'md',        // sm | md | lg
  isLoading = false,
  disabled = false,
  icon: Icon,
  className = '',
  onClick,
  type = 'button',
  ...props
}) => {
  return (
    <button
      type={type}
      className={`btn btn-${variant} btn-${size} ${className}`}
      disabled={disabled || isLoading}
      onClick={onClick}
      {...props}
    >
      {isLoading ? (
        <Loader2 size={16} className="animate-spin" />
      ) : Icon ? (
        <Icon size={16} className="btn-prefix-icon" />
      ) : null}
      <span>{children}</span>
    </button>
  );
};
