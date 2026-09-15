'use client';

import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains('dark'));
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem('theme', next ? 'dark' : 'light');
  }

  return (
    <button
      onClick={toggle}
      title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="w-7 h-7 flex items-center justify-center rounded text-[color:var(--text-muted)] hover:text-[color:var(--text)] hover:bg-[color:var(--border)] transition-colors duration-150 font-mono text-xs"
    >
      {dark ? '◑' : '◐'}
    </button>
  );
}
