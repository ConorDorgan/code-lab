'use client';

import dynamic from 'next/dynamic';
import type { Language } from '@/lib/lessons/types';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface Props {
  value: string;
  onChange: (v: string) => void;
  language: Language;
}

const monacoLang: Record<Language, string> = { python: 'python', sql: 'sql' };

export default function CodeEditor({ value, onChange, language }: Props) {
  return (
    <MonacoEditor
      height="100%"
      language={monacoLang[language]}
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? '')}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        lineNumbers: 'on',
        wordWrap: 'on',
        padding: { top: 12, bottom: 12 },
        renderWhitespace: 'none',
        tabSize: 4,
      }}
    />
  );
}
