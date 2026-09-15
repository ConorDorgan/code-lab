'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import type { Course } from '@/lib/lessons/types';
import { getCustomCourses, deleteCustomCourse } from '@/lib/lessons/store';
import AddLessonDialog from './AddLessonDialog';

interface Props {
  builtInCourses: Course[];
}

export default function Sidebar({ builtInCourses }: Props) {
  const pathname = usePathname();
  const [customCourses, setCustomCourses] = useState<Course[]>([]);
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    getCustomCourses().then(setCustomCourses);
  }, []);

  const allCourses = [...builtInCourses, ...customCourses];

  function handleAdded(course: Course) {
    setCustomCourses((prev) => {
      const next = prev.filter((c) => c.id !== course.id);
      return [...next, course];
    });
    setShowDialog(false);
  }

  async function handleDelete(courseId: string) {
    await deleteCustomCourse(courseId);
    setCustomCourses((prev) => prev.filter((c) => c.id !== courseId));
  }

  return (
    <>
      <aside className="w-64 shrink-0 bg-zinc-900 border-r border-zinc-800 flex flex-col h-screen sticky top-0 overflow-hidden">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-zinc-800">
          <span className="text-white font-bold tracking-tight">Code Lab</span>
        </div>

        {/* Course list */}
        <nav className="flex-1 overflow-y-auto py-3">
          {allCourses.map((course) => (
            <div key={course.id} className="mb-4">
              {/* Course header */}
              <div className="flex items-center justify-between px-4 mb-1">
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                  {course.name}
                </span>
                {course.isCustom && (
                  <button
                    onClick={() => handleDelete(course.id)}
                    title="Remove course"
                    className="text-zinc-600 hover:text-red-400 text-xs transition-colors"
                  >
                    &times;
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
                    className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                      active
                        ? 'bg-sky-900/40 text-sky-300 border-r-2 border-sky-400'
                        : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                    }`}
                  >
                    <span className="text-zinc-600 text-xs w-4 text-right shrink-0">{idx + 1}</span>
                    {lesson.title}
                  </Link>
                );
              })}

              {/* Custom badge */}
              {course.isCustom && (
                <div className="px-4 mt-1">
                  <span className="text-xs text-sky-600 italic">Custom</span>
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* Add new */}
        <div className="px-4 py-3 border-t border-zinc-800">
          <button
            onClick={() => setShowDialog(true)}
            className="w-full px-3 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-sky-600 text-zinc-300 hover:text-white text-sm rounded-lg transition-colors text-left"
          >
            + Add course
          </button>
        </div>
      </aside>

      {showDialog && (
        <AddLessonDialog onAdded={handleAdded} onClose={() => setShowDialog(false)} />
      )}
    </>
  );
}
