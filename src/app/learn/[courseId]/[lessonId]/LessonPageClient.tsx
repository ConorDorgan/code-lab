'use client';

import dynamic from 'next/dynamic';
import { useState, useRef, useCallback } from 'react';
import type { Course, Lesson } from '@/lib/lessons/types';
import LessonView from '@/components/LessonView';
import CodeEditor from '@/components/CodeEditor';
import OutputPanel from '@/components/OutputPanel';
import { useRunner } from '@/lib/runners/useRunner';

const AIChat = dynamic(() => import('@/components/AIChat'), { ssr: false });

interface Props {
  course: Course;
  lesson: Lesson;
}

const LANG_LABEL: Record<string, string> = { python: 'python', sql: 'sql' };
const MIN_PROSE = 220;
const MAX_PROSE = 640;
const DEFAULT_PROSE = 380;

export default function LessonPageClient({ course, lesson }: Props) {
  const starter     = lesson.blocks.find((b) => b.role === 'starter')?.code ?? '';
  const solution    = lesson.blocks.find((b) => b.role === 'solution')?.code ?? '';
  const expected    = lesson.blocks.find((b) => b.role === 'expected')?.code ?? '';
  const setup       = lesson.blocks.find((b) => b.role === 'setup')?.code;
  const explanation = lesson.blocks.find((b) => b.role === 'explanation')?.code ?? '';

  const [code, setCode] = useState(starter);
  const [showSolution, setShowSolution] = useState(false);
  const [activeEditor, setActiveEditor] = useState<'code' | 'solution'>('code');
  const [outputTab, setOutputTab] = useState<'output' | 'ai'>('output');
  const [mobilePane, setMobilePane] = useState<'lesson' | 'code'>('lesson');
  const [proseWidth, setProseWidth] = useState(DEFAULT_PROSE);
  const [proseCollapsed, setProseCollapsed] = useState(false);
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, width: DEFAULT_PROSE });
  const { run, status, result } = useRunner(course.language);

  async function handleRun() {
    setOutputTab('output');
    setMobilePane('code');
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

  const onDragStart = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    dragging.current = true;
    dragStart.current = { x: e.clientX, width: proseWidth };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [proseWidth]);

  const onDragMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    const delta = e.clientX - dragStart.current.x;
    setProseWidth(Math.min(MAX_PROSE, Math.max(MIN_PROSE, dragStart.current.width + delta)));
  }, []);

  const onDragEnd = useCallback(() => {
    dragging.current = false;
  }, []);

  const isRunning = status === 'running' || status === 'loading';
  const editorValue = activeEditor === 'solution' ? solution : code;
  const editorOnChange = activeEditor === 'solution' ? () => {} : setCode;

  return (
    <div className="flex h-screen overflow-hidden flex-col md:flex-row">
      {/* ── Lesson prose panel ───────────────────── */}
      <section
        className={`shrink-0 flex flex-col overflow-hidden md:flex ${mobilePane === 'lesson' ? 'flex flex-1 w-full' : 'hidden'}`}
        style={{
          background: 'var(--surface)',
          borderRight: '1px solid var(--border)',
          width: proseCollapsed ? '0px' : undefined,
          minWidth: proseCollapsed ? '0px' : undefined,
          // On desktop, use the draggable width unless collapsed
          ...(typeof window !== 'undefined' && window.innerWidth >= 768 && !proseCollapsed
            ? { width: `${proseWidth}px` }
            : {}),
        }}
        aria-label="Lesson content"
      >
        {/* Lesson header */}
        <div
          className="px-6 pt-5 pb-4 border-b shrink-0"
          style={{ borderColor: 'var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              {course.name}
            </span>
            <span style={{ color: 'var(--border)' }}>/</span>
            <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              {LANG_LABEL[course.language]}
            </span>
          </div>
          <h1 className="font-mono text-base font-semibold leading-snug" style={{ color: 'var(--text)' }}>
            {lesson.title}
          </h1>
        </div>

        {/* Prose content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <LessonView lesson={lesson} />

          {expected && (
            <div className="mt-6">
              <p className="font-mono text-[10px] uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted)' }}>
                expected output
              </p>
              <pre
                className="px-4 py-3 font-mono text-xs overflow-x-auto border-l-2 text-[color:var(--terminal-txt)]"
                style={{ background: 'var(--terminal-bg)', borderLeftColor: 'var(--accent)' }}
              >
                {expected}
              </pre>
            </div>
          )}

          {showSolution && explanation && (
            <div className="mt-6 pt-5 border-t" style={{ borderColor: 'var(--border)' }}>
              <p className="font-mono text-[10px] uppercase tracking-widest mb-3" style={{ color: 'var(--accent)' }}>
                why this works
              </p>
              <p className="font-mono text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                {explanation}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ── Resize handle (desktop only) ─────────── */}
      <div
        className="hidden md:flex shrink-0 w-[5px] cursor-col-resize items-center justify-center group select-none"
        style={{ background: 'var(--border)' }}
        onPointerDown={onDragStart}
        onPointerMove={onDragMove}
        onPointerUp={onDragEnd}
        title="Drag to resize"
      >
        {/* Collapse/expand toggle on the handle */}
        <button
          onClick={() => setProseCollapsed((v) => !v)}
          className="hidden group-hover:flex w-5 h-8 items-center justify-center rounded transition-colors duration-100 z-10"
          style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', fontSize: '10px' }}
          title={proseCollapsed ? 'Expand lesson' : 'Collapse lesson'}
        >
          {proseCollapsed ? '›' : '‹'}
        </button>
      </div>

      {/* ── Editor + Output zone (always dark) ───── */}
      <div
        className={`flex flex-col overflow-hidden md:flex-1 ${mobilePane === 'code' ? 'flex-1 w-full' : 'hidden md:flex'}`}
        style={{ background: 'var(--terminal-bg)' }}
      >
        {/* Editor toolbar */}
        <div
          className="h-9 shrink-0 flex items-center gap-1 px-3 border-b"
          style={{ borderColor: 'rgba(255,255,255,0.08)' }}
        >
          {/* Expand lesson button (shown when collapsed, desktop only) */}
          {proseCollapsed && (
            <button
              onClick={() => setProseCollapsed(false)}
              className="hidden md:flex font-mono text-[11px] px-2 py-1 border mr-1 transition-colors duration-150"
              style={{ color: 'var(--terminal-dim)', borderColor: 'rgba(255,255,255,0.12)' }}
              title="Expand lesson"
            >
              ›
            </button>
          )}

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

        {/* Output + AI panel */}
        <div
          className="shrink-0 border-t flex flex-col"
          style={{ height: '220px', borderColor: 'rgba(255,255,255,0.08)' }}
        >
          <div
            className="h-7 shrink-0 flex items-center border-b"
            style={{ borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <button
              onClick={() => setOutputTab('output')}
              className="font-mono text-[10px] uppercase tracking-widest px-3 h-7 border-b-2 transition-colors duration-150"
              style={{
                color: outputTab === 'output' ? 'var(--terminal-txt)' : 'var(--terminal-dim)',
                borderBottomColor: outputTab === 'output' ? 'var(--accent)' : 'transparent',
              }}
            >
              output
              {result && (
                <span className="ml-1.5 text-[9px]" style={{ color: result.error ? '#f87171' : '#4ade80' }}>●</span>
              )}
            </button>
            <button
              onClick={() => setOutputTab('ai')}
              className="font-mono text-[10px] uppercase tracking-widest px-3 h-7 border-b-2 transition-colors duration-150"
              style={{
                color: outputTab === 'ai' ? 'var(--terminal-txt)' : 'var(--terminal-dim)',
                borderBottomColor: outputTab === 'ai' ? 'var(--accent)' : 'transparent',
              }}
            >
              ai chat
            </button>
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            {outputTab === 'output' ? (
              <OutputPanel status={status} result={result} />
            ) : (
              <AIChat course={course} lesson={lesson} />
            )}
          </div>
        </div>
      </div>

      {/* ── Mobile pill nav ───────────────────────── */}
      <div
        className="md:hidden shrink-0 flex justify-center items-center py-2"
        style={{ background: 'var(--terminal-bg)', borderTop: '1px solid rgba(255,255,255,0.08)' }}
      >
        <div
          className="flex items-center gap-1 px-1.5 py-1.5 rounded-full"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.10)' }}
          role="tablist"
          aria-label="Toggle lesson pane"
        >
          <button
            role="tab"
            aria-selected={mobilePane === 'lesson'}
            onClick={() => setMobilePane('lesson')}
            className="font-mono text-xs px-5 py-2 rounded-full transition-colors duration-150"
            style={mobilePane === 'lesson'
              ? { background: 'var(--accent)', color: 'var(--terminal-bg)' }
              : { color: 'var(--terminal-dim)' }}
          >
            lesson
          </button>
          <button
            role="tab"
            aria-selected={mobilePane === 'code'}
            onClick={() => setMobilePane('code')}
            className="font-mono text-xs px-5 py-2 rounded-full transition-colors duration-150"
            style={mobilePane === 'code'
              ? { background: 'var(--accent)', color: 'var(--terminal-bg)' }
              : { color: 'var(--terminal-dim)' }}
          >
            code
          </button>
        </div>
      </div>
    </div>
  );
}
