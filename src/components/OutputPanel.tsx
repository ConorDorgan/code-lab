'use client';

import type { RunResult, RunStatus } from '@/lib/runners/useRunner';

interface Props {
  status: RunStatus;
  result: RunResult | null;
}

export default function OutputPanel({ status, result }: Props) {
  const baseClass = 'h-full overflow-auto p-3 font-mono text-xs';

  if (status === 'idle') {
    return (
      <div className={baseClass} style={{ color: 'var(--terminal-dim)' }}>
        <span className="select-none">─ press run to execute</span>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className={baseClass} style={{ color: 'var(--terminal-dim)' }}>
        <span className="animate-pulse">loading python runtime…</span>
      </div>
    );
  }

  if (status === 'running') {
    return (
      <div className={baseClass} style={{ color: 'var(--terminal-dim)' }}>
        <span className="animate-pulse">running…</span>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className={baseClass}>
      {/* SQL table results */}
      {result.sqlResults && result.sqlResults.length > 0 && (
        <div className="space-y-4">
          {result.sqlResults.map((res, i) => (
            <div key={i} className="overflow-x-auto">
              <table className="text-xs border-collapse w-full">
                <thead>
                  <tr>
                    {res.columns.map((col) => (
                      <th
                        key={col}
                        className="border px-3 py-1 text-left font-mono text-[10px] uppercase tracking-wider"
                        style={{ borderColor: '#2A3441', background: '#161C24', color: 'var(--terminal-dim)' }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {res.values.map((row, ri) => (
                    <tr key={ri} style={{ background: ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
                      {row.map((cell, ci) => (
                        <td
                          key={ci}
                          className="border px-3 py-1"
                          style={{ borderColor: '#2A3441', color: 'var(--terminal-txt)' }}
                        >
                          {cell === null
                            ? <span style={{ color: 'var(--terminal-dim)' }}>null</span>
                            : String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-1" style={{ color: 'var(--terminal-dim)' }}>
                {res.values.length} row{res.values.length !== 1 ? 's' : ''}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Text output lines — prefix each line with > */}
      {result.output && (
        <pre className="whitespace-pre-wrap" style={{ color: 'var(--terminal-txt)' }}>
          {result.output.split('\n').filter(Boolean).map((line, i) => (
            <div key={i} className="flex gap-2">
              <span className="select-none shrink-0" style={{ color: 'var(--terminal-dim)' }}>&gt;</span>
              <span>{line}</span>
            </div>
          ))}
        </pre>
      )}

      {/* Error */}
      {result.error && (
        <pre className="whitespace-pre-wrap mt-2" style={{ color: '#f87171' }}>
          {result.error.split('\n').map((line, i) => (
            <div key={i} className="flex gap-2">
              <span className="select-none shrink-0" style={{ color: '#7f1d1d' }}>&gt;</span>
              <span>{line}</span>
            </div>
          ))}
        </pre>
      )}

      {/* SQL no rows */}
      {result.sqlResults && result.sqlResults.length === 0 && !result.error && (
        <span style={{ color: 'var(--terminal-dim)' }}>query ok — no rows returned</span>
      )}
    </div>
  );
}
