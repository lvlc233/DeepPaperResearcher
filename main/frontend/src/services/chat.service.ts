import request from '@/lib/request';

export interface ChatSession {
  session_id: string;
  title?: string;
  agent_type: string;
  created_at?: string;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export const chatService = {
  createSession: async (agentType: string, context?: any): Promise<ChatSession> => {
    return request.post('/chat/sessions', { agent_type: agentType, context });
  },

  getSessions: async (): Promise<ChatSession[]> => {
    return request.get('/chat/sessions');
  },

  getSession: async (sessionId: string): Promise<ChatSession> => {
    return request.get(`/chat/sessions/${sessionId}`);
  },

  getMessages: async (sessionId: string): Promise<ChatMessage[]> => {
    return request.get(`/chat/sessions/${sessionId}/messages`);
  },

  // Note: Send Message is via SSE (POST /chat/sessions/{id}/message)
  // This service function might not be used if we use `fetch` or `EventSource` directly for SSE.
  // But if we need a standard POST:
  sendMessage: async (sessionId: string, content: string): Promise<void> => {
    // This endpoint returns text/event-stream, so axios might not be the best way to consume it
    // if we want to stream. But for sending, it's a POST.
    return request.post(`/chat/sessions/${sessionId}/message`, { content });
  }
};
