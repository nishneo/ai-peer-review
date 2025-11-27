/**
 * API client for the AI Peer Review backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

/**
 * Custom API error class with detailed error information.
 */
export class ApiError extends Error {
  constructor(status, statusText, message, retryAfter = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.retryAfter = retryAfter;
  }

  /**
   * Get a user-friendly error message based on HTTP status code.
   */
  static getErrorMessage(status, responseData = null) {
    const errorMessages = {
      400: {
        title: 'Invalid Request',
        description: 'The request was malformed. Please check your input and try again.',
        icon: '⚠️',
      },
      401: {
        title: 'Authentication Error',
        description: 'API key is missing or invalid. Please check your configuration.',
        icon: '🔐',
      },
      402: {
        title: 'Payment Required',
        description: 'Insufficient credits in your OpenRouter account. Please add funds to continue.',
        icon: '💳',
      },
      403: {
        title: 'Access Denied',
        description: 'You don\'t have permission to access this resource.',
        icon: '🚫',
      },
      404: {
        title: 'Not Found',
        description: 'The requested resource was not found.',
        icon: '🔍',
      },
      408: {
        title: 'Request Timeout',
        description: 'The request took too long. Please try again.',
        icon: '⏱️',
      },
      429: {
        title: 'Rate Limit Exceeded',
        description: 'Too many requests. Please wait a moment before trying again.',
        icon: '🚦',
      },
      500: {
        title: 'Server Error',
        description: 'An internal server error occurred. Please try again later.',
        icon: '🔧',
      },
      502: {
        title: 'Bad Gateway',
        description: 'The AI service is temporarily unavailable. Please try again.',
        icon: '🌐',
      },
      503: {
        title: 'Service Unavailable',
        description: 'The service is temporarily overloaded or under maintenance. Please try again later.',
        icon: '🔄',
      },
      504: {
        title: 'Gateway Timeout',
        description: 'The AI model took too long to respond. Please try again.',
        icon: '⏳',
      },
    };

    // Check for specific error message from response
    if (responseData?.error?.message) {
      const defaultError = errorMessages[status] || errorMessages[500];
      return {
        ...defaultError,
        description: responseData.error.message,
      };
    }

    return errorMessages[status] || {
      title: 'Unknown Error',
      description: `An unexpected error occurred (${status}). Please try again.`,
      icon: '❌',
    };
  }
}

/**
 * Handle API response and throw appropriate errors.
 */
async function handleResponse(response, context = 'request') {
  if (response.ok) {
    return response;
  }

  let responseData = null;
  try {
    responseData = await response.json();
  } catch {
    // Response might not be JSON
  }

  const errorInfo = ApiError.getErrorMessage(response.status, responseData);
  const retryAfter = response.headers.get('Retry-After');
  
  const error = new ApiError(
    response.status,
    response.statusText,
    errorInfo.description,
    retryAfter ? parseInt(retryAfter, 10) : null
  );
  error.title = errorInfo.title;
  error.icon = errorInfo.icon;
  error.context = context;
  
  throw error;
}

export const api = {
  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    await handleResponse(response, 'listing conversations');
    return response.json();
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    await handleResponse(response, 'creating conversation');
    return response.json();
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
    );
    await handleResponse(response, 'loading conversation');
    return response.json();
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      }
    );
    await handleResponse(response, 'sending message');
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      }
    );

    await handleResponse(response, 'sending message');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  },
};
