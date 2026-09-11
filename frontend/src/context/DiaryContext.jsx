import React, { createContext, useContext, useState, useEffect } from 'react';
import { diaryService } from '../services/diaryService';
import { useAuth } from './AuthContext';

const DiaryContext = createContext();

export const DiaryProvider = ({ children }) => {
  const { user } = useAuth();
  const userId = user?.id || 'user_123';

  const [entries, setEntries] = useState([]);
  const [isBackendSupported, setIsBackendSupported] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchEntries = async () => {
    setIsLoading(true);
    try {
      const result = await diaryService.getEntries(userId);
      if (result) {
        setEntries(result);
        setIsBackendSupported(true);
      } else {
        setIsBackendSupported(false);
      }
    } catch {
      setIsBackendSupported(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [userId]);

  const addEntry = async (entryData) => {
    try {
      return await diaryService.addEntry(userId, entryData);
    } catch (err) {
      console.warn('Backend Diary REST API not mounted. Preserving state in memory.', err);
      const newEntry = { id: `${Date.now()}`, ...entryData, date: new Date().toISOString().split('T')[0] };
      setEntries(prev => [newEntry, ...prev]);
      return newEntry;
    }
  };

  return (
    <DiaryContext.Provider value={{ entries, isBackendSupported, isLoading, fetchEntries, addEntry }}>
      {children}
    </DiaryContext.Provider>
  );
};

export const useDiary = () => {
  const context = useContext(DiaryContext);
  if (!context) throw new Error('useDiary must be used within a DiaryProvider');
  return context;
};
