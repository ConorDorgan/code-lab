'use client';

import { useRef, useState, useCallback } from 'react';
import { AUTHORING_SPEC } from '@/lib/lessons/authoringSpec';
import { validateCourseMarkdown } from '@/lib/lessons/parse';
import { saveCustomCourse } from '@/lib/lessons/store';
import type { Course } from '@/lib/lessons/types';

interface Props {
  onAdded: (course: Course) => void;
  onClose: () => void;
}

type Tab = 'format' | 'import';

export default function AddLessonDialog({ onAdded, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('format');
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleCopy() {
    navigator.clipboard.writeText(AUTHORING_SPEC).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleFile(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => setMarkdown((e.target?.result as string) ?? '');
    reader.readAsText(file);
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  async function handleImport() {
    setError('');
    const result = validateCourseMarkdown(markdown);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    await saveCustomCourse(markdown, result.course);
    onAdded({ ...result.course, isCustom: true });
    setMarkdown('');
  }

  const tabStyle = (t: Tab) => ({
    color: tab === t ? 'var(--text)' : 'var(--text-muted)',
    borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
    background: 'transparent',
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.6)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-w-2xl max-h-[88vh] flex flex-col border overflow-hidden"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        role="dialog"
        aria-modal="true"
        aria-label="Add a course"
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 h-11 border-b shrink-0"
          style={{ borderColor: 'var(--border)' }}
        >
          <span className="font-mono text-xs uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            add course
          </span>
          <button
            onClick={onClose}
            className="font-mono text-lg leading-none w-8 h-8 flex items-center justify-center transition-colors duration-100"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div
          className="flex border-b shrink-0"
          style={{ borderColor: 'var(--border)' }}
          role="tablist"
        >
          {(['format', 'import'] as Tab[]).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className="px-5 py-2.5 font-mono text-xs uppercase tracking-wider transition-colors duration-100"
              style={tabStyle(t)}
            >
              {t === 'format' ? '1. get format' : '2. import'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-5">
          {tab === 'format' && (
            <div className="space-y-4">
              <p className="font-sans text-sm" style={{ color: 'var(--text-muted)' }}>
                Copy these instructions into a{' '}
                <strong style={{ color: 'var(--text)' }}>Claude project</strong> and ask Claude to write you a course.
                Then paste the result in the Import tab.
              </p>

              <div className="relative">
                <pre
                  className="font-mono text-xs p-4 overflow-auto max-h-[52vh] border"
                  style={{
                    background: 'var(--terminal-bg)',
                    color: 'var(--terminal-txt)',
                    borderColor: 'var(--border)',
                    lineHeight: 1.6,
                  }}
                >
                  {AUTHORING_SPEC}
                </pre>
                <button
                  onClick={handleCopy}
                  className="absolute top-3 right-3 font-mono text-[11px] px-3 py-1.5 border transition-colors duration-150"
                  style={{
                    background: copied ? 'var(--accent)' : 'var(--terminal-bg)',
                    color: copied ? 'var(--terminal-bg)' : 'var(--accent)',
                    borderColor: 'var(--accent)',
                  }}
                >
                  {copied ? 'copied' : 'copy'}
                </button>
              </div>

              <button
                onClick={() => setTab('import')}
                className="font-mono text-xs px-4 py-2 border transition-colors duration-150"
                style={{
                  color: 'var(--accent)',
                  borderColor: 'var(--accent)',
                  background: 'transparent',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'color-mix(in srgb, var(--accent) 10%, transparent)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                next: import course →
              </button>
            </div>
          )}

          {tab === 'import' && (
            <div className="space-y-4">
              <p className="font-sans text-sm" style={{ color: 'var(--text-muted)' }}>
                Drop a <code className="font-mono text-xs" style={{ color: 'var(--accent)' }}>.md</code> file or paste
                the markdown Claude generated.
              </p>

              {/* Drop zone */}
              <button
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onClick={() => fileRef.current?.click()}
                className="w-full py-6 border-2 border-dashed font-mono text-xs transition-colors duration-150 text-center"
                style={{
                  borderColor: isDragOver ? 'var(--accent)' : 'var(--border)',
                  color: isDragOver ? 'var(--accent)' : 'var(--text-muted)',
                  background: isDragOver ? 'color-mix(in srgb, var(--accent) 5%, transparent)' : 'transparent',
                }}
                aria-label="Drop .md file or click to browse"
              >
                drop .md file or click to browse
                <input
                  ref={fileRef}
                  type="file"
                  accept=".md,text/markdown,text/plain"
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                />
              </button>

              <div className="flex items-center gap-3">
                <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
                <span className="font-mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>or paste</span>
                <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
              </div>

              <textarea
                value={markdown}
                onChange={(e) => setMarkdown(e.target.value)}
                className="w-full h-44 font-mono text-xs p-3 border resize-none focus:outline-none transition-colors duration-150"
                style={{
                  background: 'var(--surface-2)',
                  color: 'var(--text)',
                  borderColor: 'var(--border)',
                  caretColor: 'var(--accent)',
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
                onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
                placeholder="paste course markdown here…"
                aria-label="Course markdown content"
              />

              {error && (
                <div
                  className="font-mono text-xs px-4 py-3 border"
                  style={{ color: '#f87171', background: 'rgba(248,113,113,0.08)', borderColor: 'rgba(248,113,113,0.3)' }}
                  role="alert"
                >
                  {error}
                </div>
              )}

              <div className="flex items-center gap-3">
                <button
                  onClick={handleImport}
                  disabled={!markdown.trim()}
                  className="font-mono text-xs px-5 py-2 font-semibold transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ background: 'var(--accent)', color: 'var(--accent-fg)' }}
                  onMouseEnter={(e) => { if (markdown.trim()) e.currentTarget.style.opacity = '0.85'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
                >
                  import course
                </button>
                <button
                  onClick={() => { setMarkdown(''); setError(''); }}
                  className="font-mono text-xs px-3 py-2 transition-colors duration-150"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                >
                  clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
