'use client';

import { useState } from 'react';
import type { Course, Lesson } from '@/lib/lessons/types';
import LessonView from '@/components/LessonView';
import CodeEditor from '@/components/CodeEditor';
import OutputPanel from '@/components/OutputPanel';
import { useRunner } from '@/lib/runners/useRunner';

interface Props {
  course: Course;
  lesson: Lesson;
}

const LANG_LABEL: Record<string, string> = { python: 'python', sql: 'sql' };

export default function LessonPageClient({ course, lesson }: Props) {
  const starter  = lesson.blocks.find((b) => b.role === 'starter')?.code ?? '';
  const solution = lesson.blocks.find((b) => b.role === 'solution')?.code ?? '';
  const expected = lesson.blocks.find((b) => b.role === 'expected')?.code ?? '';
  const setup    = lesson.blocks.find((b) => b.role === 'setup')?.code;

  const [code, setCode] = useState(starter);
  const [showSolution, setShowSolution] = useState(false);
  const [activeEditor, setActiveEditor] = useState<'code' | 'solution'>('code');
  const { run, status, result } = useRunner(course.language);

  async function handleRun() {
    await run(activeEditor === 'solution' ? solution : code, setup);
  }

  function handleReset() {
    setCode(starter);
    setShowSolution(false);
    setActiveEditor('code');
  }

  function toggleSolution() {
    const next = !showSolution;
    setShowSolution(next);
    if (next) setActiveEditor('solution');
    else setActiveEditor('code');
  }

  const isRunning = status === 'running' || status === 'loading';
  const editorValue = activeEditor === 'solution' ? solution : code;
  const editorOnChange = activeEditor === 'solution' ? () => {} : setCode;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Lesson prose panel ───────────────────── */}
      <section
        className="w-[380px] shrink-0 flex flex-col border-r overflow-hidden hidden md:flex"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        aria-label="Lesson content"
      >
        {/* Lesson header */}
        <div
          className="px-6 pt-5 pb-4 border-b shrink-0"
          style={{ borderColor: 'var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span
              className="font-mono text-[10px] uppercase tracking-widest"
              style={{ color: 'var(--text-muted)' }}
            >
              {course.name}
            </span>
            <span style={{ color: 'var(--border)' }}>/</span>
            <span
              className="font-mono text-[10px] uppercase tracking-widest"
              style={{ color: 'var(--text-muted)' }}
            >
              {LANG_LABEL[course.language]}
            </span>
          </div>
          <h1
            className="font-mono text-base font-semibold leading-snug"
            style={{ color: 'var(--text)' }}
          >
            {lesson.title}
          </h1>
        </div>

        {/* Prose content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <LessonView lesson={lesson} />

          {/* Expected output */}
          {expected && (
            <div className="mt-6">
              <p
                className="font-mono text-[10px] uppercase tracking-widest mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                expected output
              </p>
              <pre
                className="px-4 py-3 font-mono text-xs overflow-x-auto border-l-2 text-[color:var(--terminal-txt)]"
                style={{
                  background: 'var(--terminal-bg)',
                  borderLeftColor: 'var(--accent)',
                }}
              >
                {expected}
              </pre>
            </div>
          )}
        </div>
      </section>

      {/* ── Editor + Output zone (always dark) ───── */}
      <div
        className="flex-1 flex flex-col overflow-hidden"
        style={{ background: 'var(--terminal-bg)' }}
      >
        {/* Editor toolbar */}
        <div
          className="h-9 shrink-0 flex items-center gap-1 px-3 border-b"
          style={{ borderColor: 'rgba(255,255,255,0.08)' }}
        >
          {/* Tab: code / solution */}
          <div className="flex items-center gap-0 flex-1">
            <button
              onClick={() => setActiveEditor('code')}
              className="font-mono text-[11px] px-3 h-9 border-b-2 transition-colors duration-150"
              style={{
                color: activeEditor === 'code' ? 'var(--terminal-txt)' : 'var(--terminal-dim)',
                borderBottomColor: activeEditor === 'code' ? 'var(--accent)' : 'transparent',
              }}
            >
              {LANG_LABEL[course.language]}
            </button>
            {showSolution && solution && (
              <button
                onClick={() => setActiveEditor('solution')}
                className="font-mono text-[11px] px-3 h-9 border-b-2 transition-colors duration-150"
                style={{
                  color: activeEditor === 'solution' ? 'var(--terminal-txt)' : 'var(--terminal-dim)',
                  borderBottomColor: activeEditor === 'solution' ? 'var(--accent)' : 'transparent',
                }}
              >
                solution
              </button>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-1">
            {solution && (
              <button
                onClick={toggleSolution}
                className="font-mono text-[11px] px-3 py-1 border transition-colors duration-150"
                style={{
                  color: showSolution ? 'var(--accent)' : 'var(--terminal-dim)',
                  borderColor: showSolution ? 'var(--accent)' : 'rgba(255,255,255,0.12)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
                onMouseLeave={(e) => { if (!showSolution) e.currentTarget.style.color = 'var(--terminal-dim)'; }}
              >
                {showSolution ? 'hide solution' : 'solution'}
              </button>
            )}
            <button
              onClick={handleReset}
              className="font-mono text-[11px] px-3 py-1 border transition-colors duration-150"
              style={{ color: 'var(--terminal-dim)', borderColor: 'rgba(255,255,255,0.12)' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--terminal-txt)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--terminal-dim)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)'; }}
            >
              reset
            </button>
            <button
              onClick={handleRun}
              disabled={isRunning}
              className="font-mono text-[11px] px-4 py-1 font-semibold transition-colors duration-150 disabled:opacity-50"
              style={{ background: 'var(--accent)', color: 'var(--terminal-bg)' }}
              onMouseEnter={(e) => { if (!isRunning) e.currentTarget.style.opacity = '0.85'; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
            >
              {isRunning ? 'running…' : 'run'}
            </button>
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 min-h-0">
          <CodeEditor
            value={editorValue}
            onChange={editorOnChange}
            language={course.language}
          />
        </div>

        {/* Output panel */}
        <div
          className="shrink-0 border-t flex flex-col"
          style={{ height: '180px', borderColor: 'rgba(255,255,255,0.08)' }}
        >
          {/* Output header */}
          <div
            className="h-7 shrink-0 flex items-center px-3 border-b gap-3"
            style={{ borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: 'var(--terminal-dim)' }}>
              output
            </span>
            {result && (
              <span
                className="font-mono text-[10px]"
                style={{ color: result.error ? '#f87171' : '#4ade80' }}
              >
                {result.error ? '● error' : '● ok'}
              </span>
            )}
          </div>
          <div className="flex-1 min-h-0 overflow-hidden">
            <OutputPanel status={status} result={result} />
          </div>
        </div>
      </div>
    </div>
  );
}
