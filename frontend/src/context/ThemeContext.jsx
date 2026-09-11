import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

/**
 * Theme system: EXACTLY TWO themes — light and dark.
 * Default: light.
 * Persisted in localStorage under 'raitha_theme'.
 * Applied as data-theme="light"|"dark" on <html>.
 *
 * NOTE: palette/setPalette/palettes are NOT part of this system.
 * They are exposed as no-ops for any legacy code that may still
 * destructure them (backward compat — Phase 2 protection).
 */
export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('raitha_theme');
    if (saved !== null) return saved === 'dark';
    return false; // Default: LIGHT theme
  });

  useEffect(() => {
    const theme = isDarkMode ? 'dark' : 'light';
    localStorage.setItem('raitha_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleTheme = () => setIsDarkMode(prev => !prev);

  return (
    <ThemeContext.Provider value={{
      isDarkMode,
      setIsDarkMode,
      toggleTheme,
      // Legacy no-ops — kept so any destructured {palette, setPalette, palettes}
      // in existing components does not throw a runtime error
      palette: 'default',
      setPalette: () => {},
      palettes: [],
    }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within a ThemeProvider');
  return context;
};
