import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot,
  Send,
  PlusCircle,
  Trash2,
  Copy,
  Check,
  AlertTriangle,
  Sparkles,
  Info,
  ShieldAlert,
  Code2,
  X,
} from 'lucide-react';
import {
  fetchAIStatus,
  fetchConversations,
  fetchConversationDetail,
  createConversation,
  deleteConversation,
  sendChatMessage,
  ApiError,
} from '../services/api';
import type {
  AIStatus,
  ChatMessage,
  ConversationSummary,
  FindingContext,
  User,
} from '../types';

interface AssistantViewProps {
  currentUser: User | null;
  onRequireAuth: () => void;
  pendingFindingContext?: FindingContext | null;
  onClearPendingFinding?: () => void;
}

export const AssistantView: React.FC<AssistantViewProps> = ({
  currentUser,
  onRequireAuth,
  pendingFindingContext,
  onClearPendingFinding,
}) => {
  // AI Status
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(true);

  // Conversations & Messages
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Input & Sending
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);

  // Active Finding Context Pill
  const [activeFinding, setActiveFinding] = useState<FindingContext | null>(
    pendingFindingContext || null
  );
  const [includeCodeSnippet, setIncludeCodeSnippet] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadStatus = useCallback(async () => {
    setLoadingStatus(true);
    try {
      const status = await fetchAIStatus();
      setAiStatus(status);
    } catch {
      setAiStatus({
        available: false,
        model: 'unavailable',
        message: 'Could not contact the CodeGuard backend service.',
      });
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const list = await fetchConversations();
      setConversations(list);
      if (list.length > 0 && !activeConversationId) {
        setActiveConversationId(list[0].id);
      }
    } catch {
      // Handled
    }
  }, [activeConversationId]);

  const loadMessages = useCallback(async (convId: string) => {
    setLoadingHistory(true);
    setErrorBanner(null);
    try {
      const detail = await fetchConversationDetail(convId);
      setMessages(detail.messages);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Could not load conversation.';
      setErrorBanner(msg);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // Sync incoming pending finding from "Ask AI about this finding"
  useEffect(() => {
    if (pendingFindingContext) {
      setActiveFinding(pendingFindingContext);
      setIncludeCodeSnippet(true);
      setInputPrompt(
        `Can you explain finding ${pendingFindingContext.rule_id} (${pendingFindingContext.message}) and show how to fix it securely?`
      );
      if (onClearPendingFinding) {
        onClearPendingFinding();
      }
    }
  }, [pendingFindingContext, onClearPendingFinding]);

  // Initial load
  useEffect(() => {
    loadStatus();
    if (currentUser) {
      loadConversations();
    }
  }, [currentUser, loadStatus, loadConversations]);

  // Load conversation messages when activeConversationId changes
  useEffect(() => {
    if (activeConversationId && currentUser) {
      loadMessages(activeConversationId);
    }
  }, [activeConversationId, currentUser, loadMessages]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleStartNewConversation = async () => {
    if (!currentUser) {
      onRequireAuth();
      return;
    }
    setErrorBanner(null);
    try {
      const newConv = await createConversation('New Conversation');
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      setActiveFinding(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create conversation.';
      setErrorBanner(msg);
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!currentUser) return;
    try {
      await deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        const remaining = conversations.filter((c) => c.id !== convId);
        if (remaining.length > 0) {
          setActiveConversationId(remaining[0].id);
        } else {
          setActiveConversationId(null);
          setMessages([]);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete conversation.';
      setErrorBanner(msg);
    }
  };

  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const prompt = (textToSend || inputPrompt).trim();
    if (!prompt) return;

    if (!currentUser) {
      onRequireAuth();
      return;
    }

    if (aiStatus && !aiStatus.available) {
      setErrorBanner(
        'OpenAI API is currently unavailable because OPENAI_API_KEY is not configured on the server. Please add your key to backend/.env.'
      );
      return;
    }

    setIsSending(true);
    setErrorBanner(null);
    setInputPrompt('');

    const nowIso = new Date().toISOString();
    const tempId = `local_${Math.random().toString(36).slice(2)}`;

    // Optimistic user message preview
    const tempUserMsg: ChatMessage = {
      id: tempId,
      conversation_id: activeConversationId || 'pending',
      sender: 'user',
      content: prompt,
      created_at: nowIso,
      finding_context: activeFinding,
      is_ai: false,
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const reply = await sendChatMessage({
        message: prompt,
        conversation_id: activeConversationId || undefined,
        finding_context: activeFinding || undefined,
        include_code: includeCodeSnippet,
      });

      // Update active conversation if it was newly created by the backend
      if (!activeConversationId || activeConversationId !== reply.conversation_id) {
        setActiveConversationId(reply.conversation_id);
        loadConversations();
      }

      setMessages((prev) => [...prev, reply]);
      setActiveFinding(null);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setErrorBanner('Session expired. Please sign in again.');
          onRequireAuth();
        } else if (err.status === 429) {
          setErrorBanner(
            'Rate limit exceeded. You can make up to 10 AI requests per minute. Please pause for a moment.'
          );
        } else if (err.status === 503) {
          setErrorBanner(err.message || 'OpenAI Assistant is currently unavailable on the server.');
        } else {
          setErrorBanner(err.message || 'AI Assistant request failed.');
        }
      } else if (err instanceof Error) {
        setErrorBanner(err.message);
      } else {
        setErrorBanner('An unexpected communication error occurred.');
      }
    } finally {
      setIsSending(false);
    }
  }, [
    inputPrompt,
    currentUser,
    onRequireAuth,
    aiStatus,
    activeConversationId,
    activeFinding,
    includeCodeSnippet,
    loadConversations,
  ]);

  const handleCopyCode = (snippet: string, snippetId: string) => {
    navigator.clipboard.writeText(snippet);
    setCopiedCodeId(snippetId);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  const starterPrompts = [
    {
      title: 'Remediate SQL Injection',
      prompt: 'Explain common causes of SQL injection (Bandit B608) and provide a parameterized query example.',
    },
    {
      title: 'Secure Credential Storage',
      prompt: 'How should API secrets and database passwords be securely handled in a production Python backend?',
    },
    {
      title: 'MD5 vs Argon2id / SHA-256',
      prompt: 'Why is MD5 considered dangerous for cryptographic tokens and passwords, and what are recommended alternatives?',
    },
    {
      title: 'Ruff vs Bandit Distinctions',
      prompt: 'Explain the difference between Ruff static code quality rules and Bandit security vulnerability findings.',
    },
  ];

  // Safe markdown-to-components parser
  const renderMessageContent = (content: string, msgId: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.slice(3, -3).split('\n');
        const lang = lines[0].trim() || 'python';
        const codeText = lines.slice(1).join('\n').trim();
        const snippetId = `${msgId}_code_${index}`;
        const isCopied = copiedCodeId === snippetId;

        return (
          <div key={snippetId} className="ai-code-block">
            <div className="ai-code-header">
              <span className="ai-code-lang">{lang.toUpperCase()}</span>
              <button
                type="button"
                className="ai-copy-btn"
                onClick={() => handleCopyCode(codeText, snippetId)}
                title="Copy code to clipboard"
              >
                {isCopied ? (
                  <>
                    <Check size={12} style={{ color: 'var(--color-success)' }} />
                    <span style={{ color: 'var(--color-success)' }}>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <pre className="ai-code-pre">
              <code>{codeText}</code>
            </pre>
          </div>
        );
      }

      // Format non-code paragraphs safely
      return (
        <div key={`${msgId}_p_${index}`} className="ai-text-block">
          {part.split('\n\n').map((para, pIdx) => {
            if (!para.trim()) return null;
            // Render headings if starting with #
            if (para.startsWith('### ')) {
              return <h3 key={pIdx} className="ai-h3">{para.replace('### ', '')}</h3>;
            }
            if (para.startsWith('## ')) {
              return <h2 key={pIdx} className="ai-h2">{para.replace('## ', '')}</h2>;
            }
            if (para.startsWith('# ')) {
              return <h1 key={pIdx} className="ai-h1">{para.replace('# ', '')}</h1>;
            }
            return (
              <p key={pIdx} className="ai-paragraph">
                {para}
              </p>
            );
          })}
        </div>
      );
    });
  };

  return (
    <div className="assistant-workspace-layout">
      {/* Left Sidebar: Conversation Threads */}
      <aside className="assistant-sidebar">
        <div className="assistant-sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={18} style={{ color: 'var(--color-amber)' }} />
            <span style={{ fontWeight: 700, fontSize: '0.88rem', letterSpacing: '0.04em' }}>
              CONVERSATIONS
            </span>
          </div>
          <button
            type="button"
            className="btn-icon"
            onClick={handleStartNewConversation}
            title="Start new conversation"
          >
            <PlusCircle size={16} />
          </button>
        </div>

        {/* Conversation List */}
        <div className="assistant-thread-list">
          {!currentUser ? (
            <div className="assistant-auth-gate-sidebar">
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Sign in to save and access your conversation history.
              </p>
              <button
                type="button"
                className="btn-primary auth-submit-btn"
                style={{ fontSize: '0.8rem', padding: '8px 12px' }}
                onClick={onRequireAuth}
              >
                Sign In
              </button>
            </div>
          ) : conversations.length === 0 ? (
            <div style={{ padding: '16px', fontSize: '0.8rem', color: 'var(--text-dim)', textAlign: 'center' }}>
              No saved conversations yet. Start a new thread below.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeConversationId;
              return (
                <div
                  key={conv.id}
                  className={`assistant-thread-item ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveConversationId(conv.id)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="thread-title" title={conv.title}>
                    {conv.title}
                  </div>
                  <button
                    type="button"
                    className="thread-delete-btn"
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    title="Delete conversation"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* AI Engine Status Banner */}
        <div className="assistant-status-footer">
          <div className="status-indicator-row">
            <div className={`status-dot ${aiStatus?.available ? '' : 'offline'}`} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>
              {loadingStatus
                ? 'Connecting to OpenAI...'
                : aiStatus?.available
                ? `OpenAI (${aiStatus.model})`
                : 'OpenAI Offline'}
            </span>
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Official OpenAI SDK · Responses API
          </div>
        </div>
      </aside>

      {/* Center / Right: Chat Conversation Stream */}
      <main className="assistant-main-stream">
        {/* Offline / Unavailable Warning Banner */}
        {aiStatus && !aiStatus.available && (
          <div className="alert-banner alert-warning" style={{ margin: '14px 16px 0 16px' }}>
            <AlertTriangle size={18} style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '0.82rem' }}>
              <strong>AI Assistant Unavailable: </strong>
              The backend server does not have an <code>OPENAI_API_KEY</code> configured. Configure it in{' '}
              <code>backend/.env</code> to unlock live AI explanations. Static Ruff and Bandit scans remain fully operational.
            </div>
          </div>
        )}

        {/* Error Notification */}
        {errorBanner && (
          <div className="alert-banner alert-error" style={{ margin: '14px 16px 0 16px' }} role="alert">
            <AlertTriangle size={18} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.82rem' }}>{errorBanner}</span>
          </div>
        )}

        {/* Chat Stream Area */}
        <div className="chat-messages-scroll">
          {messages.length === 0 && !isSending && (
            <div className="assistant-empty-state">
              <div className="assistant-icon-halo">
                <Bot size={40} style={{ color: 'var(--color-amber)' }} />
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '12px' }}>
                CodeGuard AI Assistant
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '440px', lineHeight: 1.5, marginTop: '6px' }}>
                Powered by official OpenAI API. Ask security questions, review Ruff & Bandit findings, or explore remediation guidance.
              </p>

              {/* Starter Prompts */}
              <div className="starter-prompts-grid">
                {starterPrompts.map((starter, i) => (
                  <button
                    key={i}
                    type="button"
                    className="starter-prompt-card"
                    onClick={() => handleSendMessage(starter.prompt)}
                    disabled={isSending}
                  >
                    <div className="starter-prompt-title">
                      <Sparkles size={13} style={{ color: 'var(--color-amber)', flexShrink: 0 }} />
                      <span>{starter.title}</span>
                    </div>
                    <p className="starter-prompt-body">{starter.prompt}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {loadingHistory && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              <div className="spinner" style={{ margin: '0 auto 8px auto' }} />
              Loading conversation history...
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-message-row ${msg.sender === 'user' ? 'msg-user' : 'msg-assistant'}`}
            >
              <div className="msg-avatar">
                {msg.sender === 'user' ? <Code2 size={16} /> : <Bot size={16} />}
              </div>
              <div className="msg-content-wrapper">
                <div className="msg-author-tag">
                  {msg.sender === 'user' ? (currentUser?.full_name || 'You') : 'CodeGuard AI'}
                  <span className="msg-timestamp">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Finding Context Pill if Attached */}
                {msg.finding_context && (
                  <div className="msg-finding-pill">
                    <ShieldAlert size={14} style={{ color: 'var(--color-amber)' }} />
                    <span style={{ fontWeight: 700 }}>{msg.finding_context.rule_id}</span>
                    <span className={`severity-badge sev-${msg.finding_context.severity}`}>
                      {msg.finding_context.severity}
                    </span>
                    <span style={{ color: 'var(--text-dim)' }}>
                      Line {msg.finding_context.line || 1}
                    </span>
                  </div>
                )}

                <div className="msg-body">
                  {renderMessageContent(msg.content, msg.id)}
                </div>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="chat-message-row msg-assistant">
              <div className="msg-avatar">
                <Bot size={16} />
              </div>
              <div className="msg-content-wrapper">
                <div className="msg-author-tag">CodeGuard AI</div>
                <div className="ai-typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginLeft: '6px' }}>
                    Consulting OpenAI Assistant...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar & Finding Context Pill */}
        <div className="assistant-input-tray">
          {activeFinding && (
            <div className="active-finding-context-bar">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                <ShieldAlert size={15} style={{ color: 'var(--color-amber)', flexShrink: 0 }} />
                <span style={{ fontWeight: 700, fontSize: '0.78rem' }}>{activeFinding.rule_id}</span>
                <span className={`severity-badge sev-${activeFinding.severity}`} style={{ fontSize: '0.68rem', padding: '2px 6px' }}>
                  {activeFinding.severity}
                </span>
                <span className="truncate" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {activeFinding.message}
                </span>
              </div>

              {/* Explicit Code Consent Checkbox */}
              {activeFinding.code_snippet && (
                <label className="checkbox-label" style={{ fontSize: '0.72rem', whiteSpace: 'nowrap' }}>
                  <input
                    type="checkbox"
                    checked={includeCodeSnippet}
                    onChange={(e) => setIncludeCodeSnippet(e.target.checked)}
                    className="custom-checkbox"
                  />
                  <span>Share excerpt ({activeFinding.code_snippet.length} chars)</span>
                </label>
              )}

              <button
                type="button"
                className="btn-icon"
                onClick={() => setActiveFinding(null)}
                title="Remove finding context"
              >
                <X size={14} />
              </button>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="assistant-input-form"
          >
            <input
              type="text"
              className="assistant-text-input"
              placeholder={
                currentUser
                  ? 'Ask about vulnerabilities, Python code explanation, or remediation...'
                  : 'Please sign in to send messages to the AI Assistant...'
              }
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              disabled={isSending || !currentUser}
            />

            <button
              type="submit"
              className="btn-primary assistant-send-btn"
              disabled={isSending || !inputPrompt.trim() || !currentUser}
              title="Send message"
            >
              <Send size={15} />
              <span>Send</span>
            </button>
          </form>

          <div className="assistant-privacy-disclaimer">
            <Info size={12} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <span>
              Advisory AI guidance is purely educational. Verified static AST scan results from Ruff and Bandit govern production security.
            </span>
          </div>
        </div>
      </main>
    </div>
  );
};
