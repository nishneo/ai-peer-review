import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api, ApiError } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      if (err instanceof ApiError) {
        setError(err);
      }
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (err) {
      console.error('Failed to load conversation:', err);
      if (err instanceof ApiError) {
        setError(err);
      }
    }
  };

  const handleNewConversation = async () => {
    try {
      setError(null);
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (err) {
      console.error('Failed to create conversation:', err);
      if (err instanceof ApiError) {
        setError(err);
      }
    }
  };

  const handleDismissError = () => {
    setError(null);
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    setError(null);
    
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'model_errors':
            // Handle individual model errors (e.g., 429 rate limits)
            if (event.errors && event.errors.length > 0) {
              const firstError = event.errors[0];
              const modelError = new ApiError(
                firstError.status_code || 500,
                'Model Error',
                `${firstError.model}: ${firstError.message}`
              );
              
              // Set appropriate title and icon based on status code
              if (firstError.status_code === 429) {
                modelError.title = 'Rate Limit Exceeded';
                modelError.icon = '🚦';
                modelError.message = `Some models hit rate limits (${event.errors.length} failed). Results may be incomplete.`;
              } else if (firstError.status_code === 402) {
                modelError.title = 'Payment Required';
                modelError.icon = '💳';
                modelError.message = 'Insufficient credits for some models. Check your OpenRouter balance.';
              } else {
                modelError.title = `Stage ${event.stage} Partial Failure`;
                modelError.icon = '⚠️';
                modelError.message = `${event.errors.length} model(s) failed. Results may be incomplete.`;
              }
              
              setError(modelError);
            }
            break;

          case 'error':
            console.error('Stream error:', event.message);
            // Create an error object for stream errors
            const streamError = new ApiError(
              event.status || 500,
              'Stream Error',
              event.message || 'An error occurred during processing'
            );
            streamError.title = event.title || 'Processing Error';
            streamError.icon = event.icon || '⚠️';
            setError(streamError);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (err) {
      console.error('Failed to send message:', err);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      
      // Set appropriate error
      if (err instanceof ApiError) {
        setError(err);
      } else if (err.name === 'TypeError' && err.message.includes('fetch')) {
        // Network error
        const networkError = new ApiError(0, 'Network Error', 'Unable to connect to the server. Please check your connection.');
        networkError.title = 'Connection Error';
        networkError.icon = '📡';
        setError(networkError);
      } else {
        // Generic error
        const genericError = new ApiError(500, 'Error', err.message || 'An unexpected error occurred');
        genericError.title = 'Error';
        genericError.icon = '❌';
        setError(genericError);
      }
      
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        error={error}
        onDismissError={handleDismissError}
      />
    </div>
  );
}

export default App;
