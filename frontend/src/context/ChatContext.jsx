import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { chatService } from '../services/chatService';
import { useAuth } from './AuthContext';
import { useLanguage } from './LanguageContext';
import { useToast } from './ToastContext';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const { language } = useLanguage();
  const { showToast } = useToast();

  const [sessionId, setSessionId] = useState(() => {
    return sessionStorage.getItem('raitha_active_session') || null;
  });
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState(null);
  const [activeCount, setActiveCount] = useState(0);

  // Load all active sessions from backend
  const loadSessions = useCallback(async () => {
    try {
      const result = await chatService.getSessions();
      if (result && Array.isArray(result.sessions)) {
        setSessions(result.sessions);
      }
    } catch (err) {
      console.error('Failed to load sessions from backend:', err);
    }
  }, []);

  // Fetch active sessions count
  const loadActiveCount = useCallback(async () => {
    try {
      const result = await chatService.getActiveCount();
      if (result && typeof result.active_sessions === 'number') {
        setActiveCount(result.active_sessions);
      }
    } catch (err) {
      console.error('Failed to fetch active session count:', err);
    }
  }, []);

  // Initialize a brand new session using the backend endpoint
  const createNewChat = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const newId = await chatService.createNewSession();
      setSessionId(newId);
      sessionStorage.setItem('raitha_active_session', newId);
      setMessages([]);
      await loadSessions();
      return newId;
    } catch (err) {
      console.error('Failed to create new session:', err);
      const errMsg = err.message || 'Failed to create new conversation session.';
      setError(errMsg);
      showToast(errMsg, 'error');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [loadSessions, showToast]);

  // Load and select an existing session by ID
  const selectSession = useCallback(
    async (targetSessionId) => {
      if (!targetSessionId) return;
      if (targetSessionId === sessionId && messages.length > 0) return;

      setIsLoadingHistory(true);
      setError(null);
      try {
        const historyData = await chatService.getHistory(targetSessionId);
        setSessionId(targetSessionId);
        sessionStorage.setItem('raitha_active_session', targetSessionId);

        if (historyData && Array.isArray(historyData.history)) {
          const formattedMessages = historyData.history.map((turn, index) => ({
            id: `${targetSessionId}_${index}`,
            role: turn.role === 'farmer' ? 'user' : 'assistant',
            content: turn.content,
            timestamp: turn.timestamp ? turn.timestamp * 1000 : Date.now(),
          }));
          setMessages(formattedMessages);
        } else {
          setMessages([]);
        }
      } catch (err) {
        console.error(`Failed to load history for session ${targetSessionId}:`, err);
        const errMsg = err.status === 404 
          ? 'Conversation session expired or not found. Starting a new session.'
          : (err.message || 'Failed to load conversation history.');
        setError(errMsg);
        showToast(errMsg, 'warning');
        // If session not found, start a fresh session
        await createNewChat();
        throw err;
      } finally {
        setIsLoadingHistory(false);
      }
    },
    [sessionId, messages.length, showToast, createNewChat]
  );

  // Send message to real backend
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = (text || '').trim();
      if (!trimmed) return;
      if (trimmed.length > 2000) {
        showToast('Message exceeds maximum limit of 2000 characters.', 'warning');
        return;
      }

      let activeSession = sessionId;
      if (!activeSession) {
        activeSession = await createNewChat();
        if (!activeSession) return;
      }

      const tempUserMessageId = `user_${Date.now()}`;
      const userMessage = {
        id: tempUserMessageId,
        role: 'user',
        content: trimmed,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const responseData = await chatService.sendMessage({
          sessionId: activeSession,
          message: trimmed,
          language: language || 'kn',
          isVoiceMode: false,
        });

        const assistantMessage = {
          id: `asst_${Date.now()}`,
          role: 'assistant',
          content: responseData.response,
          timestamp: Date.now(),
          source: responseData.source,
          provider: responseData.provider,
          contextUsed: responseData.context_used,
          metadata: responseData.metadata,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Keep active session ID in sync if backend returned one
        if (responseData.session_id && responseData.session_id !== activeSession) {
          setSessionId(responseData.session_id);
          sessionStorage.setItem('raitha_active_session', responseData.session_id);
        }

        // Refresh sessions list to display updated first-turn titles
        await loadSessions();
      } catch (err) {
        console.error('Failed to send chat message:', err);
        const errMsg = err.message || 'Failed to get answer from Raitha Sathi server.';
        setError(errMsg);
        showToast(errMsg, 'error');
        // Remove optimistic user turn on error so retry works cleanly without duplicates
        setMessages((prev) => prev.filter((m) => m.id !== tempUserMessageId));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, createNewChat, language, loadSessions, showToast]
  );

  // Close and delete an active session
  const closeSession = useCallback(
    async (targetSessionId) => {
      if (!targetSessionId) return;
      try {
        await chatService.closeSession(targetSessionId);
        showToast('Conversation deleted successfully.', 'info');
        
        // Instantly remove from local sessions state
        setSessions((prev) => prev.filter((s) => s.id !== targetSessionId));

        // If closed session was the active one, clear active view
        if (targetSessionId === sessionId) {
          sessionStorage.removeItem('raitha_active_session');
          setSessionId(null);
          setMessages([]);
        }
      } catch (err) {
        console.error(`Failed to close session ${targetSessionId}:`, err);
        showToast(err.message || 'Failed to close conversation session.', 'error');
      }
    },
    [sessionId, showToast]
  );

  // Synchronize conversations with authenticated user
  useEffect(() => {
    if (!isAuthenticated || !user) {
      setSessionId(null);
      setSessions([]);
      setMessages([]);
      sessionStorage.removeItem('raitha_active_session');
      return;
    }

    const initUserConversations = async () => {
      await loadSessions();
      await loadActiveCount();

      const savedSession = sessionStorage.getItem('raitha_active_session');
      if (savedSession) {
        await selectSession(savedSession);
      }
    };
    initUserConversations();
  }, [user?.id, isAuthenticated, loadSessions, loadActiveCount, selectSession]);

  return (
    <ChatContext.Provider
      value={{
        sessionId,
        sessions,
        messages,
        isLoading,
        isLoadingHistory,
        error,
        activeCount,
        createNewChat,
        selectSession,
        sendMessage,
        closeSession,
        loadSessions,
        loadActiveCount,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within a ChatProvider');
  return context;
};
