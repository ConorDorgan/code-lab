'use client';

import { useRef, useState } from 'react';
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

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

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

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-700">
          <h2 className="text-white font-semibold">Add a course</h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-white text-xl leading-none">&times;</button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-700">
          {(['format', 'import'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-3 text-sm font-medium transition-colors ${
                tab === t ? 'text-white border-b-2 border-sky-500' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              {t === 'format' ? '1. Get the format' : '2. Import course'}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto p-5">
          {tab === 'format' && (
            <div>
              <p className="text-zinc-300 text-sm mb-3">
                Copy these instructions into a <strong>Claude project</strong> and ask Claude to write you a course. Then paste the result in the Import tab.
              </p>
              <div className="relative">
                <pre className="bg-zinc-800 rounded-lg p-4 text-xs text-zinc-300 overflow-auto max-h-[50vh] whitespace-pre-wrap">
                  {AUTHORING_SPEC}
                </pre>
                <button
                  onClick={handleCopy}
                  className="absolute top-3 right-3 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs rounded transition-colors"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <button
                onClick={() => setTab('import')}
                className="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-sm rounded-lg transition-colors"
              >
                Next: Import course &rarr;
              </button>
            </div>
          )}

          {tab === 'import' && (
            <div className="space-y-4">
              <p className="text-zinc-300 text-sm">
                Drop a <code className="text-sky-400">.md</code> file or paste the Markdown that Claude generated.
              </p>

              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-zinc-600 hover:border-sky-500 rounded-lg p-6 text-center cursor-pointer transition-colors"
              >
                <p className="text-zinc-400 text-sm">Drop .md file here or click to browse</p>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".md,text/markdown,text/plain"
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                />
              </div>

              <p className="text-zinc-500 text-xs text-center">or paste directly</p>

              <textarea
                value={markdown}
                onChange={(e) => setMarkdown(e.target.value)}
                className="w-full h-48 bg-zinc-800 border border-zinc-600 rounded-lg p-3 text-sm font-mono text-zinc-200 focus:outline-none focus:border-sky-500 resize-none"
                placeholder="Paste course markdown here..."
              />

              {error && (
                <p className="text-red-400 text-sm bg-red-950/40 border border-red-800 rounded px-3 py-2">{error}</p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={handleImport}
                  disabled={!markdown.trim()}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                >
                  Import course
                </button>
                <button
                  onClick={() => { setMarkdown(''); setError(''); }}
                  className="px-4 py-2 text-zinc-400 hover:text-white text-sm transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
