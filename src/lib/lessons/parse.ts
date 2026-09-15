import matter from 'gray-matter';
import type { Course, Lesson, CodeBlock, Language } from './types';

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function parseLessonBody(raw: string): { prose: string; blocks: CodeBlock[] } {
  const blocks: CodeBlock[] = [];
  // Extract fenced code blocks whose info string has a second token (the role)
  const fenceRe = /^```(\S+)\s+(\S+)\s*\n([\s\S]*?)^```/gm;
  const prose = raw.replace(fenceRe, (_, lang: string, role: string, code: string) => {
    const validRoles = ['starter', 'solution', 'expected', 'setup'];
    if (validRoles.includes(role)) {
      blocks.push({ lang: lang as CodeBlock['lang'], role: role as CodeBlock['role'], code: code.trimEnd() });
      return ''; // remove from prose
    }
    return _; // leave plain code blocks in prose
  }).trim();
  return { prose, blocks };
}

export function parseCourse(markdown: string): Course {
  const { data, content } = matter(markdown);

  if (!data.course) throw new Error('Missing frontmatter field: course');
  if (!data.language) throw new Error('Missing frontmatter field: language');
  if (data.language !== 'python' && data.language !== 'sql') {
    throw new Error(`Invalid language "${data.language}". Must be "python" or "sql".`);
  }

  // Split on top-level "# Lesson: <title>" headings
  const lessonSections = content.split(/^# Lesson:\s*/m).filter(Boolean);
  if (lessonSections.length === 0) {
    throw new Error('No lessons found. Add at least one "# Lesson: <title>" heading.');
  }

  const lessons: Lesson[] = lessonSections.map((section) => {
    const newlineIdx = section.indexOf('\n');
    const title = (newlineIdx === -1 ? section : section.slice(0, newlineIdx)).trim();
    const body = newlineIdx === -1 ? '' : section.slice(newlineIdx + 1);
    const { prose, blocks } = parseLessonBody(body);
    return { id: slugify(title), title, prose, blocks };
  });

  const courseId = slugify(data.course);
  return {
    id: courseId,
    name: data.course,
    language: data.language as Language,
    description: data.description ?? '',
    lessons,
  };
}

export function validateCourseMarkdown(markdown: string): { ok: true; course: Course } | { ok: false; error: string } {
  try {
    const course = parseCourse(markdown);
    return { ok: true, course };
  } catch (e) {
    return { ok: false, error: (e as Error).message };
  }
}
