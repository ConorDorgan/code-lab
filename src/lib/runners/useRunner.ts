'use client';

import { useRef, useState, useCallback } from 'react';
import type { Language } from '@/lib/lessons/types';

export type RunStatus = 'idle' | 'loading' | 'running' | 'done' | 'error';

export interface RunResult {
  output: string;
  error?: string;
  sqlResults?: Array<{ columns: string[]; values: unknown[][] }>;
}

export function useRunner(language: Language) {
  const workerRef = useRef<Worker | null>(null);
  const [status, setStatus] = useState<RunStatus>('idle');
  const [result, setResult] = useState<RunResult | null>(null);
  const pendingRef = useRef<Map<string, (r: RunResult) => void>>(new Map());

  const getWorker = useCallback((): Worker => {
    if (workerRef.current) return workerRef.current;
    const src = language === 'python' ? '/python-worker.js' : '/sql-worker.js';
    const w = new Worker(src);
    w.onmessage = (e) => {
      const { id, ok, output, error, results } = e.data;
      const resolve = pendingRef.current.get(id);
      if (!resolve) return;
      pendingRef.current.delete(id);
      resolve({
        output: output ?? '',
        error: ok ? undefined : (error ?? 'Unknown error'),
        sqlResults: results,
      });
    };
    workerRef.current = w;
    return w;
  }, [language]);

  const run = useCallback(
    async (code: string, setup?: string): Promise<void> => {
      setStatus('running');
      setResult(null);
      const worker = getWorker();
      const id = Math.random().toString(36).slice(2);

      const res = await new Promise<RunResult>((resolve) => {
        pendingRef.current.set(id, resolve);
        worker.postMessage({ id, code, setup });
      });

      setResult(res);
      setStatus(res.error ? 'error' : 'done');
    },
    [getWorker]
  );

  // Called when Pyodide first needs to load
  const markLoading = useCallback(() => setStatus('loading'), []);

  return { run, status, result, markLoading };
}
