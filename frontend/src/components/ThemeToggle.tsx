'use client'

import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-white shadow-sm dark:border-white/10 dark:bg-white/5">
      <button
        type="button"
        aria-label="Switch to light mode"
        onClick={() => setTheme('light')}
        className={`px-3 py-2 transition-colors ${
          theme === 'light'
            ? 'bg-gray-100 text-amber-500 dark:bg-white/20'
            : 'text-gray-500 dark:text-white/60'
        } rounded-l-lg`}
      >
        <Sun className="w-4 h-4" />
      </button>
      <button
        type="button"
        aria-label="Switch to dark mode"
        onClick={() => setTheme('dark')}
        className={`px-3 py-2 transition-colors ${
          theme === 'dark'
            ? 'bg-gray-900 text-yellow-300 dark:bg-white/20 dark:text-white'
            : 'text-gray-500 dark:text-white/60'
        } rounded-r-lg`}
      >
        <Moon className="w-4 h-4" />
      </button>
    </div>
  )
}

