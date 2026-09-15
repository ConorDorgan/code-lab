import { redirect } from 'next/navigation';
import { getBuiltInCourses } from '@/lib/lessons/builtIn';

export default function Home() {
  const courses = getBuiltInCourses();
  const first = courses[0];
  if (first && first.lessons[0]) {
    redirect(`/learn/${first.id}/${first.lessons[0].id}`);
  }
  return null;
}
