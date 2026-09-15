'use client';

import { get, set, del, keys } from 'idb-keyval';
import type { Course } from './types';
import { parseCourse } from './parse';

const IDB_PREFIX = 'code-lab-course::';

export async function getCustomCourses(): Promise<Course[]> {
  const allKeys = await keys();
  const courseKeys = (allKeys as string[]).filter((k) => k.startsWith(IDB_PREFIX));
  const courses = await Promise.all(
    courseKeys.map(async (k) => {
      const md = await get(k);
      try {
        const c = parseCourse(md as string);
        return { ...c, isCustom: true };
      } catch {
        return null;
      }
    })
  );
  return courses.filter(Boolean) as Course[];
}

export async function saveCustomCourse(markdown: string, course: Course): Promise<void> {
  await set(`${IDB_PREFIX}${course.id}`, markdown);
}

export async function deleteCustomCourse(courseId: string): Promise<void> {
  await del(`${IDB_PREFIX}${courseId}`);
}
