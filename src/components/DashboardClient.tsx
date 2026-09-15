'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getCustomCourses } from '@/lib/lessons/store';
import type { Course } from '@/lib/lessons/types';
import AddLessonDialog from './AddLessonDialog';

interface Props {
  builtInCourses: Course[];
}

const LANG_BADGE: Record<string, { label: string; color: string }> = {
  python: { label: 'python', color: '#3B82F6' },
  sql:    { label: 'sql',    color: '#F59E0B' },
};

function CourseCard({ course }: { course: Course }) {
  const badge = LANG_BADGE[course.language] ?? { label: course.language, color: 'var(--text-muted)' };
  const href = `/learn/${course.id}/${course.lessons[0]?.id ?? ''}`;

  return (
    <Link
      href={href}
      className="group flex flex-col gap-3 p-5 border transition-colors duration-150"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
    >
      {/* Language badge */}
      <span
        className="font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 self-start"
        style={{ background: `${badge.color}18`, color: badge.color, border: `1px solid ${badge.color}30` }}
      >
        {badge.label}
      </span>

      {/* Course name */}
      <div>
        <h2
          className="font-mono text-sm font-semibold leading-snug group-hover:text-[color:var(--accent)] transition-colors duration-150"
          style={{ color: 'var(--text)' }}
        >
          {course.name}
        </h2>
        {course.description && (
          <p className="font-sans text-xs mt-1 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            {course.description}
          </p>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          {course.lessons.length} lesson{course.lessons.length !== 1 ? 's' : ''}
        </span>
        {course.isCustom && (
          <span className="font-mono text-[10px]" style={{ color: 'var(--accent)' }}>custom</span>
        )}
        <span
          className="font-mono text-[10px] group-hover:text-[color:var(--accent)] transition-colors duration-150"
          style={{ color: 'var(--text-muted)' }}
        >
          start →
        </span>
      </div>
    </Link>
  );
}

function AddCourseCard({ onAdded }: { onAdded: (c: Course) => void }) {
  const [showDialog, setShowDialog] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowDialog(true)}
        className="flex flex-col items-center justify-center gap-2 p-5 border-2 border-dashed transition-colors duration-150 min-h-[140px]"
        style={{ borderColor: 'var(--border)', color: 'var(--text-muted)', background: 'transparent' }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'var(--accent)';
          e.currentTarget.style.color = 'var(--accent)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'var(--border)';
          e.currentTarget.style.color = 'var(--text-muted)';
        }}
      >
        <span className="font-mono text-xl leading-none">+</span>
        <span className="font-mono text-xs">add course</span>
      </button>

      {showDialog && (
        <AddLessonDialog
          onAdded={(c) => { onAdded(c); setShowDialog(false); }}
          onClose={() => setShowDialog(false)}
        />
      )}
    </>
  );
}

export default function DashboardClient({ builtInCourses }: Props) {
  const [customCourses, setCustomCourses] = useState<Course[]>([]);

  useEffect(() => {
    getCustomCourses().then(setCustomCourses);
  }, []);

  const allCourses = [...builtInCourses, ...customCourses];

  function handleAdded(course: Course) {
    setCustomCourses((prev) => [...prev.filter((c) => c.id !== course.id), course]);
  }

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <div
        className="px-8 py-10 border-b"
        style={{ background: 'var(--terminal-bg)', borderColor: 'rgba(255,255,255,0.08)' }}
      >
        <p
          className="font-mono text-[10px] uppercase tracking-widest mb-3"
          style={{ color: 'var(--terminal-dim)' }}
        >
          code-lab
        </p>
        <h1 className="font-mono text-2xl font-semibold" style={{ color: 'var(--terminal-txt)' }}>
          Courses
        </h1>
        <p className="font-sans text-sm mt-1.5" style={{ color: 'var(--terminal-dim)' }}>
          Select a course to start. Code runs entirely in your browser — no account needed.
        </p>
      </div>

      {/* Course grid */}
      <div className="px-8 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {allCourses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
          <AddCourseCard onAdded={handleAdded} />
        </div>
      </div>
    </div>
  );
}
