import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import { getBuiltInCourses } from '@/lib/lessons/builtIn';

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] });
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Code Lab',
  description: 'Learn and run Python and SQL in your browser',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const builtInCourses = getBuiltInCourses();

  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-zinc-950 text-zinc-100 flex`}>
        <Sidebar builtInCourses={builtInCourses} />
        <main className="flex-1 min-h-screen overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
