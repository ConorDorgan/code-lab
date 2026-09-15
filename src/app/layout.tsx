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
    <html lang="en">
      <head>
        {/* Prevent FOUC — read theme preference before first paint */}
        <script dangerouslySetInnerHTML={{ __html: `(function(){var t=localStorage.getItem('theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.classList.add('dark')})()` }} />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased flex h-screen overflow-hidden bg-[color:var(--bg)] text-[color:var(--text)]`}>
        <Sidebar builtInCourses={builtInCourses} />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
