import { getBuiltInCourses } from '@/lib/lessons/builtIn';
import DashboardClient from '@/components/DashboardClient';

export default function Home() {
  const builtInCourses = getBuiltInCourses();
  return <DashboardClient builtInCourses={builtInCourses} />;
}
