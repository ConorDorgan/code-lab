'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import type { Course } from '@/lib/lessons/types';
import { getCustomCourses, deleteCustomCourse } from '@/lib/lessons/store';
import AddLessonDialog from './AddLessonDialog';
import ThemeToggle from './ThemeToggle';

interface Props {
  builtInCourses: Course[];
}

const LANG_LABEL: Record<string, string> = { python: 'py', sql: 'sql' };

export default function Sidebar({ builtInCourses }: Props) {
  const pathname = usePathname();
  const [customCourses, setCustomCourses] = useState<Course[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    getCustomCourses().then(setCustomCourses);
  }, []);

  const allCourses = [...builtInCourses, ...customCourses];

  function handleAdded(course: Course) {
    setCustomCourses((prev) => [...prev.filter((c) => c.id !== course.id), course]);
    setShowDialog(false);
    setMobileOpen(false);
  }

  async function handleDelete(courseId: string, e: React.MouseEvent) {
    e.preventDefault();
    await deleteCustomCourse(courseId);
    setCustomCourses((prev) => prev.filter((c) => c.id !== courseId));
  }

  const sidebarContent = (
    <aside
      className="flex flex-col h-full w-[220px] shrink-0 border-r"
      style={{ background: 'var(--surface-2)', borderColor: 'var(--border)' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 h-11 border-b shrink-0"
        style={{ borderColor: 'var(--border)' }}
      >
        <span
          className="font-mono text-xs font-semibold tracking-widest uppercase"
          style={{ color: 'var(--text-muted)' }}
        >
          code-lab
        </span>
        <ThemeToggle />
      </div>

      {/* Course list */}
      <nav className="flex-1 overflow-y-auto py-2" aria-label="Lessons">
        {allCourses.map((course) => (
          <div key={course.id} className="mb-1">
            {/* Course label */}
            <div
              className="flex items-center justify-between px-4 pt-3 pb-1"
            >
              <span
                className="font-mono text-[10px] uppercase tracking-widest font-semibold flex items-center gap-1.5"
                style={{ color: 'var(--text-muted)' }}
              >
                <span
                  className="inline-block px-1 text-[9px] rounded-sm font-mono"
                  style={{ background: 'var(--border)', color: 'var(--text-muted)' }}
                >
                  {LANG_LABEL[course.language] ?? course.language}
                </span>
                {course.name}
              </span>
              {course.isCustom && (
                <button
                  onClick={(e) => handleDelete(course.id, e)}
                  title="Remove course"
                  aria-label={`Remove ${course.name}`}
                  className="font-mono text-xs transition-colors duration-150 min-w-[44px] min-h-[44px] flex items-center justify-center"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#e05252')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                >
                  ×
                </button>
              )}
            </div>

            {/* Lessons */}
            {course.lessons.map((lesson, idx) => {
              const href = `/learn/${course.id}/${lesson.id}`;
              const active = pathname === href;
              return (
                <Link
                  key={lesson.id}
                  href={href}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2 px-4 py-1.5 transition-colors duration-100 group relative min-h-[36px]"
                  style={active ? {
                    background: 'color-mix(in srgb, var(--accent) 12%, transparent)',
                    color: 'var(--accent)',
                    borderLeft: '2px solid var(--accent)',
                    paddingLeft: 'calc(1rem - 2px)',
                  } : { color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => { if (!active) { e.currentTarget.style.color = 'var(--text)'; e.currentTarget.style.background = 'color-mix(in srgb, var(--border) 60%, transparent)'; } }}
                  onMouseLeave={(e) => { if (!active) { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = ''; } }}
                  aria-current={active ? 'page' : undefined}
                >
                  <span
                    className="font-mono text-[10px] w-4 text-right shrink-0 tabular-nums"
                    style={{ color: active ? 'var(--accent)' : 'var(--border)' }}
                  >
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="font-mono text-xs truncate leading-snug">{lesson.title}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Add course */}
      <div className="shrink-0 p-3 border-t" style={{ borderColor: 'var(--border)' }}>
        <button
          onClick={() => setShowDialog(true)}
          className="w-full flex items-center gap-2 px-3 py-2 font-mono text-xs border transition-colors duration-150 text-left"
          style={{ color: 'var(--text-muted)', borderColor: 'var(--border)', background: 'transparent' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--accent)';
            e.currentTarget.style.borderColor = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.borderColor = 'var(--border)';
          }}
        >
          <span aria-hidden>+</span> add course
        </button>
      </div>
    </aside>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="md:hidden fixed top-3 left-3 z-50 w-8 h-8 flex items-center justify-center border font-mono text-sm transition-colors duration-150"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text-muted)' }}
        onClick={() => setMobileOpen((v) => !v)}
        aria-label="Toggle navigation"
        aria-expanded={mobileOpen}
      >
        {mobileOpen ? '×' : '☰'}
      </button>

      {/* Desktop sidebar */}
      <div className="hidden md:flex h-screen sticky top-0 shrink-0">
        {sidebarContent}
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div className="flex h-full">{sidebarContent}</div>
          <div
            className="flex-1 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      {showDialog && (
        <AddLessonDialog onAdded={handleAdded} onClose={() => setShowDialog(false)} />
      )}
    </>
  );
}
