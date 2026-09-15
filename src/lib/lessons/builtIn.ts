import fs from 'fs';
import path from 'path';
import { parseCourse } from './parse';
import type { Course } from './types';

const CONTENT_DIR = path.join(process.cwd(), 'src', 'content');

let cached: Course[] | null = null;

export function getBuiltInCourses(): Course[] {
  if (cached) return cached;
  const files = ['python-basics.md', 'sql-basics.md'];
  cached = files.map((f) => {
    const raw = fs.readFileSync(path.join(CONTENT_DIR, f), 'utf-8');
    return parseCourse(raw); // parseCourse normalises CRLF internally
  });
  return cached;
}
