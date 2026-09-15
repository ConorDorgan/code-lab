import { getBuiltInCourses } from '@/lib/lessons/builtIn';
import LessonPageClient from './LessonPageClient';
import CustomLessonLoader from './CustomLessonLoader';

interface Props {
  params: Promise<{ courseId: string; lessonId: string }>;
}

export default async function LessonPage({ params }: Props) {
  const { courseId, lessonId } = await params;
  const courses = getBuiltInCourses();
  const course = courses.find((c) => c.id === courseId);
  const lesson = course?.lessons.find((l) => l.id === lessonId);

  if (course && lesson) {
    return <LessonPageClient course={course} lesson={lesson} />;
  }

  // Could be a custom course in IndexedDB — let the client try
  return <CustomLessonLoader courseId={courseId} lessonId={lessonId} />;
}

export function generateStaticParams() {
  const courses = getBuiltInCourses();
  return courses.flatMap((course) =>
    course.lessons.map((lesson) => ({ courseId: course.id, lessonId: lesson.id }))
  );
}
