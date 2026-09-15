'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Lesson } from '@/lib/lessons/types';

interface Props {
  lesson: Lesson;
}

export default function LessonView({ lesson }: Props) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson.prose}</ReactMarkdown>
    </div>
  );
}
