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

export default function LessonPageClient({ course, lesson }: Props) {
  const starter = lesson.blocks.find((b) => b.role === 'starter')?.code ?? '';
  const solution = lesson.blocks.find((b) => b.role === 'solution')?.code ?? '';
  const expected = lesson.blocks.find((b) => b.role === 'expected')?.code ?? '';
  const setup = lesson.blocks.find((b) => b.role === 'setup')?.code;

  const [code, setCode] = useState(starter);
  const [showSolution, setShowSolution] = useState(false);
  const { run, status, result } = useRunner(course.language);

  async function handleRun() {
    await run(code, setup);
  }

  function handleReset() {
    setCode(starter);
    setShowSolution(false);
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-950 shrink-0">
        <div>
          <p className="text-xs text-zinc-500 mb-0.5">{course.name}</p>
          <h1 className="text-lg font-semibold text-white leading-tight">{lesson.title}</h1>
        </div>
        <div className="flex items-center gap-2">
          {solution && (
            <button
              onClick={() => setShowSolution((v) => !v)}
              className="px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-100 border border-zinc-700 hover:border-zinc-500 rounded transition-colors"
            >
              {showSolution ? 'Hide solution' : 'Show solution'}
            </button>
          )}
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-100 border border-zinc-700 hover:border-zinc-500 rounded transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleRun}
            disabled={status === 'running' || status === 'loading'}
            className="px-4 py-1.5 text-sm font-medium bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded transition-colors"
          >
            {status === 'running' ? 'Running...' : status === 'loading' ? 'Loading...' : 'Run'}
          </button>
        </div>
      </div>

      {/* Main content: lesson prose | editor + output */}
      <div className="flex flex-1 min-h-0">
        {/* Left: lesson content */}
        <div className="w-96 shrink-0 border-r border-zinc-800 overflow-y-auto p-5 bg-zinc-950">
          <LessonView lesson={lesson} />

          {expected && (
            <div className="mt-6">
              <p className="text-xs text-zinc-500 font-mono mb-1">Expected output</p>
              <pre className="bg-zinc-800 rounded p-3 text-xs text-zinc-300 font-mono">{expected}</pre>
            </div>
          )}
        </div>

        {/* Right: editor + output */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Editor */}
          <div className={`${showSolution ? 'h-1/3' : 'flex-1'} min-h-0 border-b border-zinc-800`}>
            <CodeEditor value={code} onChange={setCode} language={course.language} />
          </div>

          {/* Solution (when shown) */}
          {showSolution && solution && (
            <div className="h-1/3 border-b border-zinc-800 bg-zinc-900/60 relative min-h-0">
              <div className="absolute top-2 left-3 text-xs text-zinc-500 font-mono">solution</div>
              <div className="pt-6 h-full">
                <CodeEditor value={solution} onChange={() => {}} language={course.language} />
              </div>
            </div>
          )}

          {/* Output */}
          <div className="h-48 shrink-0 border-t border-zinc-800 bg-zinc-950">
            <div className="flex items-center px-3 py-1 border-b border-zinc-800 bg-zinc-900">
              <span className="text-xs text-zinc-500 font-mono">output</span>
              {result && (
                <span className={`ml-auto text-xs ${result.error ? 'text-red-400' : 'text-green-400'}`}>
                  {result.error ? 'error' : 'ok'}
                </span>
              )}
            </div>
            <div className="h-[calc(100%-2rem)] overflow-auto">
              <OutputPanel status={status} result={result} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
