import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Plus } from 'lucide-react';
import { apiClient } from '../../api/client';
import type { ErrorEnvelope } from '../../types/api';

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

interface ToolCall {
  tool: string;
  args?: Record<string, unknown>;
}

interface ApiChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: ToolCall[] | null;
  created_at: string;
}

interface ChatSendResponse {
  session_id: string;
  reply: string;
  tool_calls: ToolCall[];
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
}

const GREETING_MESSAGE: ChatMessage = {
  id: 'greeting',
  role: 'assistant',
  content: 'Hi, I am TransitOps AI. How can I help you today?',
};

const EMPTY_SESSIONS: ChatSession[] = [];
const AI_DISABLED_TEXT = 'Assistant is turned off. Fleet Managers can enable it in AI Settings.';

function isAiDisabledError(error: unknown): boolean {
  return axios.isAxiosError<ErrorEnvelope>(error) && error.response?.status === 503;
}

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING_MESSAGE]);
  const [inputText, setInputText] = useState('');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [aiDisabled, setAiDisabled] = useState(false);
  const autoSelected = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const sessionsQuery = useQuery({
    queryKey: ['ai', 'sessions'],
    queryFn: async () => {
      const res = await apiClient.get<ChatSession[]>('/ai/sessions');
      return res.data;
    },
    enabled: isOpen,
    retry: 1,
    staleTime: 30_000,
  });

  const sessions = sessionsQuery.data ?? EMPTY_SESSIONS;
  const sortedSessions = useMemo(
    () => [...sessions].sort((a, b) => b.created_at.localeCompare(a.created_at)),
    [sessions]
  );

  // Auto-select the most recent session once, so a returning user sees their history.
  useEffect(() => {
    if (!autoSelected.current && activeSessionId === null && sortedSessions.length > 0) {
      autoSelected.current = true;
      setActiveSessionId(sortedSessions[0].id);
    }
  }, [sortedSessions, activeSessionId]);

  const messagesQuery = useQuery({
    queryKey: ['ai', 'sessions', activeSessionId, 'messages'],
    queryFn: async () => {
      const res = await apiClient.get<ApiChatMessage[]>(`/ai/sessions/${activeSessionId}/messages`);
      return res.data;
    },
    enabled: isOpen && !!activeSessionId,
    retry: 1,
  });

  useEffect(() => {
    if (activeSessionId && messagesQuery.data) {
      const mapped: ChatMessage[] = messagesQuery.data
        .filter((m): m is ApiChatMessage & { role: 'user' | 'assistant' } => m.role !== 'tool')
        .map((m) => ({ id: m.id, role: m.role, content: m.content, toolCalls: m.tool_calls ?? undefined }));
      setMessages(mapped.length > 0 ? mapped : [GREETING_MESSAGE]);
    }
  }, [activeSessionId, messagesQuery.data]);

  useEffect(() => {
    if (messagesQuery.isError) {
      setMessages([GREETING_MESSAGE]);
      setActiveSessionId(null);
    }
  }, [messagesQuery.isError]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const createSessionMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post<ChatSession>('/ai/sessions', {});
      return res.data;
    },
    onSuccess: (session) => {
      queryClient.setQueryData<ChatSession[]>(['ai', 'sessions'], (old) => [session, ...(old ?? [])]);
      autoSelected.current = true;
      setActiveSessionId(session.id);
      setMessages([GREETING_MESSAGE]);
      setAiDisabled(false);
    },
  });

  const sendMutation = useMutation({
    mutationFn: async (message: string) => {
      const res = await apiClient.post<ChatSendResponse>('/ai/chat', {
        session_id: activeSessionId ?? undefined,
        message,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: data.reply, toolCalls: data.tool_calls },
      ]);
      if (data.session_id !== activeSessionId) {
        autoSelected.current = true;
        setActiveSessionId(data.session_id);
        queryClient.invalidateQueries({ queryKey: ['ai', 'sessions'] });
      }
    },
    onError: (err: unknown) => {
      if (isAiDisabledError(err)) {
        setAiDisabled(true);
      }
    },
  });

  const handleSelectSession = (id: string) => {
    if (!id) {
      createSessionMutation.mutate();
      return;
    }
    autoSelected.current = true;
    setActiveSessionId(id);
    setAiDisabled(false);
  };

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text || sendMutation.isPending || aiDisabled) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: text }]);
    setInputText('');
    sendMutation.mutate(text);
  };

  const inputDisabled = sendMutation.isPending || aiDisabled;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="w-80 h-96 bg-surface-0 border border-line rounded-xl shadow-xl flex flex-col overflow-hidden mb-4 transition-all origin-bottom-right">
          {/* Header */}
          <div className="bg-surface-2 border-b border-line px-4 py-3 flex justify-between items-center gap-2">
            <div className="flex items-center space-x-2 min-w-0">
              <div className={`w-2 h-2 rounded-full ${aiDisabled ? 'bg-neutral' : 'bg-ok'}`}></div>
              <h3 className="font-semibold text-sm text-ink truncate">TransitOps AI</h3>
            </div>
            <div className="flex items-center space-x-1 shrink-0">
              {sortedSessions.length > 0 && (
                <select
                  aria-label="Chat history"
                  value={activeSessionId ?? ''}
                  onChange={(e) => handleSelectSession(e.target.value)}
                  className="h-7 rounded border border-line bg-surface-1 text-ink text-[11px] px-1 max-w-[90px] focus:outline-none focus:border-signal"
                >
                  <option value="">New chat</option>
                  {sortedSessions.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title || 'Untitled'}
                    </option>
                  ))}
                </select>
              )}
              <button
                type="button"
                onClick={() => createSessionMutation.mutate()}
                disabled={createSessionMutation.isPending}
                title="New chat"
                aria-label="Start a new chat"
                className="text-ink-mute hover:text-ink transition-colors p-1 disabled:opacity-50"
              >
                <Plus size={14} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close"
                aria-label="Close chat"
                className="text-ink-mute hover:text-ink transition-colors p-1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface-1/50">
            {aiDisabled ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-3 px-2">
                <p className="text-sm text-ink-mute">{AI_DISABLED_TEXT}</p>
                <button
                  type="button"
                  onClick={() => setAiDisabled(false)}
                  className="text-xs text-signal hover:underline"
                >
                  Try again
                </button>
              </div>
            ) : messagesQuery.isFetching && messages.length === 0 ? (
              <p className="text-xs text-ink-mute text-center">Loading conversation…</p>
            ) : (
              <>
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === 'user'
                          ? 'bg-signal text-white rounded-br-none'
                          : 'bg-surface-2 border border-line text-ink rounded-bl-none'
                      }`}
                    >
                      {msg.content}
                    </div>
                    {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5 max-w-[80%]">
                        {msg.toolCalls.map((tc, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center text-[10px] px-1.5 py-0.5 rounded bg-surface-2 border border-line text-ink-mute"
                          >
                            🔧 {tc.tool}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {sendMutation.isPending && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm bg-surface-2 border border-line text-ink-mute italic rounded-bl-none">
                      Thinking…
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Input */}
          <div className="p-3 border-t border-line bg-surface-0">
            {sendMutation.isError && !aiDisabled && (
              <p className="text-xs text-danger pb-2">Message failed to send. Please try again.</p>
            )}
            <form onSubmit={handleSend} className="flex items-center space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={sendMutation.isPending ? 'Thinking…' : 'Type a message...'}
                disabled={inputDisabled}
                className="flex-1 h-9 rounded-md border border-line bg-surface-1 px-3 text-sm focus:border-signal focus:outline-none text-ink disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputText.trim() || inputDisabled}
                className="h-9 w-9 rounded-md bg-signal text-white flex items-center justify-center disabled:opacity-50 hover:bg-signal/90 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 bg-signal rounded-full shadow-lg flex items-center justify-center text-white hover:bg-signal/90 hover:scale-105 transition-all focus:outline-none focus:ring-4 focus:ring-signal/30"
      >
        {isOpen ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        )}
      </button>
    </div>
  );
}
