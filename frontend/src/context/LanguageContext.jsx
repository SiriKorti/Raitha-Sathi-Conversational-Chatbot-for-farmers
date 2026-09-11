import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations, t as translateHelper } from '../utils/translations';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    const saved = localStorage.getItem('raitha_lang');
    return (saved === 'en' || saved === 'kn') ? saved : 'kn';
  });

  useEffect(() => {
    const normalized = (language === 'en' || language === 'kn') ? language : 'kn';
    if (normalized !== language) {
      setLanguage(normalized);
      return;
    }
    localStorage.setItem('raitha_lang', normalized);
    document.documentElement.lang = normalized;
  }, [language]);

  const toggleLanguage = () => {
    setLanguage(prev => (prev === 'kn' ? 'en' : 'kn'));
  };


  const t = (key) => translateHelper(key, language);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t, translations }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within a LanguageProvider');
  return context;
};
