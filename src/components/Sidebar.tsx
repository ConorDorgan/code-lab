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

function getActiveCourseId(pathname: string | null): string | null {
  if (!pathname) return null;
  const m = pathname.match(/^\/learn\/([^/]+)/);
  return m ? m[1] : null;
}

export default function Sidebar({ builtInCourses }: Props) {
  const pathname = usePathname();
  const activeCourseId = getActiveCourseId(pathname);

  const [customCourses, setCustomCourses] = useState<Course[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  // Track which courses are manually expanded; active course always expanded
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    getCustomCourses().then(setCustomCourses);
  }, []);

  const allCourses = [...builtInCourses, ...customCourses];

  function isExpanded(courseId: string): boolean {
    if (courseId === activeCourseId) return true;
    return expanded[courseId] ?? false;
  }

  function toggleExpanded(courseId: string) {
    if (courseId === activeCourseId) return; // active course is always open
    setExpanded((prev) => ({ ...prev, [courseId]: !prev[courseId] }));
  }

  function handleAdded(course: Course) {
    setCustomCourses((prev) => [...prev.filter((c) => c.id !== course.id), course]);
    setShowDialog(false);
    setMobileOpen(false);
  }

  async function handleDelete(courseId: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
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
        <Link
          href="/"
          onClick={() => setMobileOpen(false)}
          className="font-mono text-xs font-semibold tracking-widest uppercase transition-colors duration-100"
          style={{ color: 'var(--text-muted)' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          code-lab
        </Link>
        <ThemeToggle />
      </div>

      {/* Course list */}
      <nav className="flex-1 overflow-y-auto py-2" aria-label="Lessons">
        {/* Dashboard link */}
        <div className="px-4 pb-2 pt-1">
          <Link
            href="/"
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2 font-mono text-[11px] transition-colors duration-100"
            style={{ color: !activeCourseId ? 'var(--accent)' : 'var(--text-muted)' }}
            onMouseEnter={(e) => { if (activeCourseId) e.currentTarget.style.color = 'var(--text)'; }}
            onMouseLeave={(e) => { if (activeCourseId) e.currentTarget.style.color = 'var(--text-muted)'; }}
          >
            <span aria-hidden>⊞</span> all courses
          </Link>
        </div>

        <div className="border-t mb-1" style={{ borderColor: 'var(--border)' }} />

        {allCourses.map((course) => {
          const open = isExpanded(course.id);
          return (
            <div key={course.id} className="mb-0.5">
              {/* Course header — clickable to toggle */}
              <div
                className="flex items-center justify-between px-4 py-2 cursor-pointer select-none"
                onClick={() => toggleExpanded(course.id)}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <span
                    className="font-mono text-[9px] shrink-0"
                    style={{ color: 'var(--text-muted)' }}
                    aria-hidden
                  >
                    {open ? '▾' : '▸'}
                  </span>
                  <span
                    className="font-mono text-[10px] uppercase tracking-wider font-semibold truncate"
                    style={{ color: course.id === activeCourseId ? 'var(--text)' : 'var(--text-muted)' }}
                  >
                    {course.name}
                  </span>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <span
                    className="font-mono text-[9px] px-1"
                    style={{ background: 'var(--border)', color: 'var(--text-muted)' }}
                  >
                    {LANG_LABEL[course.language] ?? course.language}
                  </span>
                  {course.isCustom && (
                    <button
                      onClick={(e) => handleDelete(course.id, e)}
                      title={`Remove ${course.name}`}
                      aria-label={`Remove ${course.name}`}
                      className="font-mono text-xs w-5 h-5 flex items-center justify-center transition-colors duration-100"
                      style={{ color: 'var(--text-muted)' }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#e05252')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>

              {/* Lesson list (collapsed/expanded) */}
              {open && (
                <div>
                  {course.lessons.map((lesson, idx) => {
                    const href = `/learn/${course.id}/${lesson.id}`;
                    const active = pathname === href;
                    return (
                      <Link
                        key={lesson.id}
                        href={href}
                        onClick={() => setMobileOpen(false)}
                        className="flex items-center gap-2 px-4 py-1.5 transition-colors duration-100 min-h-[32px]"
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
              )}
            </div>
          );
        })}
      </nav>

      {/* Add course */}
      <div className="shrink-0 p-3 border-t" style={{ borderColor: 'var(--border)' }}>
        <button
          onClick={() => setShowDialog(true)}
          className="w-full flex items-center gap-2 px-3 py-2 font-mono text-xs border transition-colors duration-150 text-left"
          style={{ color: 'var(--text-muted)', borderColor: 'var(--border)', background: 'transparent' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
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
          <div className="flex-1 bg-black/50" onClick={() => setMobileOpen(false)} />
        </div>
      )}

      {showDialog && (
        <AddLessonDialog onAdded={handleAdded} onClose={() => setShowDialog(false)} />
      )}
    </>
  );
}
