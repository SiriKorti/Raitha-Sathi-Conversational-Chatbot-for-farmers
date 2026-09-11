import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

const normalizeUser = (u) => {
  if (!u) return null;
  if (u.id === 'farmer_001' || u.fullName === 'Ramesh Gowda' || u.name === 'Ramesh Gowda') {
    const updated = { ...u, fullName: 'farmer-01', name: 'farmer-01' };
    try {
      localStorage.setItem('raitha_user', JSON.stringify(updated));
    } catch {}
    return updated;
  }
  return u;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('raitha_user');
    try {
      return saved ? normalizeUser(JSON.parse(saved)) : null;
    } catch {
      return null;
    }
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return Boolean(localStorage.getItem('raitha_auth_token'));
  });

  const [isLoading, setIsLoading] = useState(false);

  // Sync state if localStorage changes or on init
  useEffect(() => {
    const token = localStorage.getItem('raitha_auth_token');
    const savedUser = localStorage.getItem('raitha_user');
    if (token && savedUser) {
      try {
        setUser(normalizeUser(JSON.parse(savedUser)));
        setIsAuthenticated(true);
      } catch {
        // ignore corrupted json
      }
    }
  }, []);

  const login = async (credentials) => {
    setIsLoading(true);
    try {
      const result = await authService.login(credentials);
      if (result && result.user) {
        setUser(result.user);
        setIsAuthenticated(true);
        localStorage.setItem('raitha_auth_token', result.token || 'rs_auth_token');
        localStorage.setItem('raitha_user', JSON.stringify(result.user));
        return result;
      }
      throw new Error('Invalid response from authentication server');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData) => {
    setIsLoading(true);
    try {
      const result = await authService.register(userData);
      if (result && result.user) {
        setUser(result.user);
        setIsAuthenticated(true);
        localStorage.setItem('raitha_auth_token', result.token || 'rs_auth_token');
        localStorage.setItem('raitha_user', JSON.stringify(result.user));
        return result;
      }
      throw new Error('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('raitha_auth_token');
      localStorage.removeItem('raitha_user');
      setIsLoading(false);
    }
  };

  const deleteAccount = async (identifier) => {
    setIsLoading(true);
    try {
      const targetId = identifier || user?.email || user?.mobile || user?.id;
      if (!targetId) throw new Error('No user account identifier found to delete.');
      const result = await authService.deleteAccount(targetId);
      
      // Clear session after successful backend deletion
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('raitha_auth_token');
      localStorage.removeItem('raitha_user');
      return result;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
