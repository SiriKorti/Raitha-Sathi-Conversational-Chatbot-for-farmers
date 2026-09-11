import { useNavigate } from 'react-router-dom';

/**
 * Shared Hook for triggering contextual queries into the Ask Sathi ChatPage
 * Passes prompt through React Router navigation state.
 */
export const usePromptTrigger = () => {
  const navigate = useNavigate();

  const askSathi = (promptText) => {
    if (!promptText) return;
    navigate('/chat', { state: { prompt: promptText } });
  };

  return { askSathi };
};
