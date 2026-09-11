import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { farmService } from '../services/farmService';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';

const FarmContext = createContext();

export const FarmProvider = ({ children }) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const userId = user?.id || 'user_123';

  const [farmProfile, setFarmProfile] = useState(null);
  const [isSetup, setIsSetup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFarmProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await farmService.getProfile(userId);
      if (response && response.status === 'success' && response.data) {
        setFarmProfile(response.data);
        setIsSetup(true);
      } else {
        setFarmProfile(null);
        setIsSetup(false);
      }
    } catch (err) {
      console.error('Failed to fetch farm profile from backend:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const saveFarmProfile = useCallback(
    async (newProfileData) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await farmService.saveProfile(userId, newProfileData);
        if (response && response.status === 'success') {
          const savedData = response.data || newProfileData;
          setFarmProfile(savedData);
          setIsSetup(true);
          showToast('Farm profile saved successfully!', 'success');
          return savedData;
        }
        throw new Error(response?.message || 'Failed to save farm profile');
      } catch (err) {
        console.error('Failed to save farm profile:', err);
        setError(err.message);
        showToast(err.message || 'Failed to save farm profile.', 'error');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [userId, showToast]
  );

  useEffect(() => {
    fetchFarmProfile();
  }, [fetchFarmProfile]);

  return (
    <FarmContext.Provider
      value={{
        farmProfile,
        isSetup,
        isLoading,
        error,
        fetchFarmProfile,
        saveFarmProfile,
      }}
    >
      {children}
    </FarmContext.Provider>
  );
};

export const useFarm = () => {
  const context = useContext(FarmContext);
  if (!context) throw new Error('useFarm must be used within a FarmProvider');
  return context;
};
