'use client';

import type { RunResult, RunStatus } from '@/lib/runners/useRunner';

interface Props {
  status: RunStatus;
  result: RunResult | null;
}

export default function OutputPanel({ status, result }: Props) {
  if (status === 'idle') {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
        Press Run to execute your code
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-full text-zinc-400 text-sm">
        <span className="animate-pulse">Loading Python runtime (first run only)...</span>
      </div>
    );
  }

  if (status === 'running') {
    return (
      <div className="flex items-center justify-center h-full text-zinc-400 text-sm">
        <span className="animate-pulse">Running...</span>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="h-full overflow-auto p-3 font-mono text-sm">
      {/* SQL table results */}
      {result.sqlResults && result.sqlResults.length > 0 && (
        <div className="space-y-4">
          {result.sqlResults.map((res, i) => (
            <div key={i} className="overflow-x-auto">
              <table className="text-xs border-collapse w-full">
                <thead>
                  <tr>
                    {res.columns.map((col) => (
                      <th key={col} className="border border-zinc-600 bg-zinc-800 px-3 py-1 text-left text-zinc-300">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {res.values.map((row, ri) => (
                    <tr key={ri} className="even:bg-zinc-800/40">
                      {row.map((cell, ci) => (
                        <td key={ci} className="border border-zinc-700 px-3 py-1 text-zinc-300">
                          {cell === null ? <span className="text-zinc-600 italic">NULL</span> : String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-zinc-500 text-xs mt-1">{res.values.length} row{res.values.length !== 1 ? 's' : ''}</p>
            </div>
          ))}
        </div>
      )}

      {/* Python / text output */}
      {result.output && (
        <pre className="text-zinc-200 whitespace-pre-wrap">{result.output}</pre>
      )}

      {/* Error */}
      {result.error && (
        <pre className="text-red-400 whitespace-pre-wrap mt-2">{result.error}</pre>
      )}

      {/* SQL with no rows */}
      {result.sqlResults && result.sqlResults.length === 0 && !result.error && (
        <p className="text-zinc-500 text-xs">Query executed successfully (no rows returned)</p>
      )}
    </div>
  );
}
