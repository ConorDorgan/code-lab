'use client';

import { useState, useRef, useEffect } from 'react';
import type { Course, Lesson } from '@/lib/lessons/types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  course: Course;
  lesson: Lesson;
}

const LS_KEY = 'code-lab-api-key';

export default function AIChat({ course, lesson }: Props) {
  const [apiKey, setApiKey] = useState<string>(() => {
    if (typeof window === 'undefined') return '';
    return localStorage.getItem(LS_KEY) ?? '';
  });
  const [keyInput, setKeyInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function saveKey() {
    const k = keyInput.trim();
    if (!k) return;
    localStorage.setItem(LS_KEY, k);
    setApiKey(k);
    setKeyInput('');
  }

  function clearKey() {
    localStorage.removeItem(LS_KEY);
    setApiKey('');
    setMessages([]);
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    const next: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setLoading(true);
    try {
      const system = `You are a concise coding tutor helping a learner with the following lesson.

Course: ${course.name} (${course.language})
Lesson: ${lesson.title}

Lesson content:
${lesson.prose}

Answer questions about this lesson. Keep responses short and practical. Use code examples when helpful. If asked something unrelated to coding or this lesson, gently redirect.`;

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-api-key': apiKey },
        body: JSON.stringify({
          system,
          messages: next.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Error: ${data.error ?? res.statusText}` },
        ]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.text }]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Network error: ${(e as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (!apiKey) {
    return (
      <div className="flex flex-col items-start justify-center h-full px-4 py-3 gap-3">
        <p className="font-mono text-xs" style={{ color: 'var(--terminal-dim)' }}>
          Enter a free Google Gemini API key to ask questions about this lesson.
        </p>
        <p className="font-mono text-[10px]" style={{ color: 'var(--terminal-dim)', opacity: 0.6 }}>
          Get one free at aistudio.google.com — stored in localStorage, only sent to Google.
        </p>
        <div className="flex gap-2 w-full max-w-sm">
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && saveKey()}
            placeholder="AIza..."
            className="flex-1 font-mono text-xs px-2 py-1 border bg-transparent outline-none focus:border-[color:var(--accent)]"
            style={{ color: 'var(--terminal-txt)', borderColor: 'rgba(255,255,255,0.15)' }}
          />
          <button
            onClick={saveKey}
            className="font-mono text-[11px] px-3 py-1 transition-colors duration-150"
            style={{ background: 'var(--accent)', color: 'var(--terminal-bg)' }}
          >
            save
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {messages.length === 0 && (
          <p className="font-mono text-xs pt-1" style={{ color: 'var(--terminal-dim)' }}>
            Ask anything about this lesson…
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="font-mono text-xs px-2 py-1.5 max-w-[85%] whitespace-pre-wrap break-words"
              style={
                m.role === 'user'
                  ? { background: 'color-mix(in srgb, var(--accent) 18%, transparent)', color: 'var(--terminal-txt)', border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)' }
                  : { color: 'var(--terminal-dim)', borderLeft: '2px solid rgba(255,255,255,0.12)', paddingLeft: '8px' }
              }
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <span className="font-mono text-xs" style={{ color: 'var(--terminal-dim)' }}>thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 flex gap-1 px-2 py-1.5 border-t" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          placeholder="Ask a question…"
          disabled={loading}
          className="flex-1 font-mono text-xs px-2 py-1 bg-transparent border outline-none focus:border-[color:var(--accent)] disabled:opacity-50"
          style={{ color: 'var(--terminal-txt)', borderColor: 'rgba(255,255,255,0.12)' }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="font-mono text-[11px] px-3 py-1 transition-colors duration-150 disabled:opacity-40"
          style={{ background: 'var(--accent)', color: 'var(--terminal-bg)' }}
        >
          ask
        </button>
        <button
          onClick={clearKey}
          title="Clear API key"
          className="font-mono text-[10px] px-2 py-1 border transition-colors duration-150"
          style={{ color: 'var(--terminal-dim)', borderColor: 'rgba(255,255,255,0.12)' }}
        >
          ×key
        </button>
      </div>
    </div>
  );
}
