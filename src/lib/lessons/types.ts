export type Language = 'python' | 'sql';

export interface CodeBlock {
  lang: Language | 'text';
  role: 'starter' | 'solution' | 'expected' | 'setup' | 'explanation';
  code: string;
}

export interface Lesson {
  id: string;
  title: string;
  prose: string;
  blocks: CodeBlock[];
}

export interface Course {
  id: string;
  name: string;
  language: Language;
  description: string;
  lessons: Lesson[];
  isCustom?: boolean;
}
