import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import './ThemeSelector.css';

/**
 * ThemeSelector — Simple Light / Dark toggle button.
 * Named ThemeSelector to preserve existing imports in TopBar, LoginPage, etc.
 */
export const ThemeSelector = () => {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      className="theme-toggle-btn"
      onClick={toggleTheme}
      title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      aria-label={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      {isDarkMode ? (
        <Sun size={17} className="theme-toggle-icon" />
      ) : (
        <Moon size={17} className="theme-toggle-icon" />
      )}
    </button>
  );
};
