'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from "@/components/layout/Navbar";
import { chatService, ChatSession, ChatMessage } from '@/services/chat.service';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { Plus, MessageSquare, Bot, User, Send, Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { createParser } from 'eventsource-parser';
import { useAuthStore } from '@/store/use-auth-store';
import { logger } from '@/lib/logger';

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const { token } = useAuthStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadSessions = React.useCallback(async () => {
    try {
      const data = await chatService.getSessions();
      setSessions(data);
      setActiveSessionId((prev) => prev ?? (data[0]?.id ?? null));
    } catch (error) {
      logger.error("Failed to load sessions", error, 'ChatPage');
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = async (sessionId: string) => {
    setIsLoadingMessages(true);
    try {
      const data = await chatService.getMessages(sessionId);
      setMessages(data);
    } catch (error) {
      logger.error("Failed to load messages", error, 'ChatPage');
      toast.error("加载消息失败");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const handleCreateSession = async () => {
    try {
      const newSession = await chatService.createSession('research_assistant');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.session_id);
    } catch (error) {
      toast.error("创建会话失败");
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeSessionId || isSending) return;
    
    const content = inputValue.trim();
    setInputValue('');
    setIsSending(true);

    // Optimistic update
    const userMsg: ChatMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMsg]);

    const aiMsgPlaceholder: ChatMessage = { role: 'ai', content: '' };
    setMessages(prev => [...prev, aiMsgPlaceholder]);
    
    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/chat/sessions/${activeSessionId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) throw new Error(response.statusText);
        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        const parser = createParser({
          onEvent: (event: any) => {
            if (event.type === 'event') {
                try {
                    if (event.data === '[DONE]') return;
                    const data = JSON.parse(event.data);
                    const delta = data.content || "";
                    
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        const lastMsg = newMsgs[newMsgs.length - 1];
                        if (lastMsg.role === 'ai') {
                            lastMsg.content += delta;
                        }
                        return newMsgs;
                    });
                } catch (e) {
                    // ignore
                }
            }
          }
        });

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            parser.feed(chunk);
        }
    } catch (error) {
        toast.error("发送失败");
        setMessages(prev => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            if (lastMsg.role === 'ai' && lastMsg.content === '') {
                 lastMsg.content = "发送失败，请重试。";
            }
            return newMsgs;
        });
    } finally {
        setIsSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-100">
            <Button onClick={handleCreateSession} className="w-full gap-2" variant="outline">
              <Plus className="w-4 h-4" />
              新建对话
            </Button>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {isLoadingSessions ? (
                 <div className="p-4 text-center text-gray-400 text-sm">加载中...</div>
              ) : sessions.map(session => (
                <button
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={cn(
                    "w-full text-left px-3 py-3 rounded-lg text-sm flex items-center gap-3 transition-colors",
                    activeSessionId === session.id 
                      ? "bg-indigo-50 text-indigo-700" 
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <MessageSquare className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate flex-1">{session.title || session.id.substring(0, 8)}</span>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-white">
          {activeSessionId ? (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {isLoadingMessages ? (
                    <div className="h-full flex items-center justify-center">
                        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                ) : messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                        <Bot className="w-12 h-12 text-gray-200" />
                        <p>开始一个新的对话吧</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={cn("flex gap-4 max-w-3xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "")}>
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                msg.role === 'ai' ? "bg-indigo-100 text-indigo-600" : "bg-gray-900 text-white"
                            )}>
                                {msg.role === 'ai' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                            </div>
                            <div className={cn(
                                "px-4 py-3 rounded-2xl text-sm leading-relaxed max-w-[80%]",
                                msg.role === 'ai' 
                                    ? "bg-gray-50 text-gray-800 rounded-tl-none" 
                                    : "bg-gray-900 text-white rounded-tr-none"
                            )}>
                                {msg.content}
                                {msg.role === 'ai' && msg.content === '' && isSending && idx === messages.length - 1 && (
                                    <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-1 align-middle" />
                                )}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-gray-100">
                <div className="max-w-3xl mx-auto relative">
                    <Input 
                        value={inputValue}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                        placeholder="输入您的问题..." 
                        className="flex-1"
                        disabled={isSending}
                    />
                    <Button 
                        size="icon" 
                        className="absolute right-1 top-1 h-10 w-10" 
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isSending}
                    >
                        {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
                请选择或创建一个会话
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
