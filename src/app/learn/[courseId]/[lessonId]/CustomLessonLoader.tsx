'use client';

import { useEffect, useState } from 'react';
import { getCustomCourses } from '@/lib/lessons/store';
import type { Course, Lesson } from '@/lib/lessons/types';
import LessonPageClient from './LessonPageClient';

interface Props {
  courseId: string;
  lessonId: string;
}

export default function CustomLessonLoader({ courseId, lessonId }: Props) {
  const [state, setState] = useState<'loading' | 'found' | 'missing'>('loading');
  const [course, setCourse] = useState<Course | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);

  useEffect(() => {
    getCustomCourses().then((courses) => {
      const c = courses.find((x) => x.id === courseId);
      const l = c?.lessons.find((x) => x.id === lessonId);
      if (c && l) {
        setCourse(c);
        setLesson(l);
        setState('found');
      } else {
        setState('missing');
      }
    });
  }, [courseId, lessonId]);

  if (state === 'loading') {
    return (
      <div className="flex items-center justify-center h-screen text-zinc-500 text-sm">
        Loading...
      </div>
    );
  }

  if (state === 'missing') {
    return (
      <div className="flex items-center justify-center h-screen text-zinc-500 text-sm">
        Lesson not found.
      </div>
    );
  }

  return <LessonPageClient course={course!} lesson={lesson!} />;
}
