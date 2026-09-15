'use client';

import dynamic from 'next/dynamic';
import type { Language } from '@/lib/lessons/types';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface Props {
  value: string;
  onChange: (v: string) => void;
  language: Language;
  readOnly?: boolean;
}

const monacoLang: Record<Language, string> = { python: 'python', sql: 'sql' };

export default function CodeEditor({ value, onChange, language, readOnly }: Props) {
  return (
    <MonacoEditor
      height="100%"
      language={monacoLang[language]}
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? '')}
      options={{
        fontSize: 13,
        fontFamily: 'var(--font-geist-mono), "JetBrains Mono", "Fira Code", monospace',
        fontLigatures: true,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        lineNumbers: 'on',
        lineNumbersMinChars: 3,
        wordWrap: 'on',
        padding: { top: 12, bottom: 12 },
        renderWhitespace: 'none',
        tabSize: 4,
        readOnly: readOnly ?? false,
        renderLineHighlight: readOnly ? 'none' : 'line',
        scrollbar: {
          verticalScrollbarSize: 6,
          horizontalScrollbarSize: 6,
        },
        overviewRulerLanes: 0,
        glyphMargin: false,
        folding: false,
        lineDecorationsWidth: 8,
      }}
    />
  );
}
