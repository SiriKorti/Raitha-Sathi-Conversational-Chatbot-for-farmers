import React from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { LanguageProvider } from '../context/LanguageContext';
import { ToastProvider } from '../context/ToastContext';
import { AuthProvider } from '../context/AuthContext';
import { FarmProvider } from '../context/FarmContext';
import { ChatProvider } from '../context/ChatContext';
import { DiaryProvider } from '../context/DiaryContext';

export const AppProviders = ({ children }) => {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <ToastProvider>
          <AuthProvider>
            <FarmProvider>
              <ChatProvider>
                <DiaryProvider>
                  {children}
                </DiaryProvider>
              </ChatProvider>
            </FarmProvider>
          </AuthProvider>
        </ToastProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
};
