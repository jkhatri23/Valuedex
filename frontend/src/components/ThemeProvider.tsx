'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('dark')
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    const storedTheme = localStorage.getItem('valuedex-theme') as Theme | null
    const nextTheme = storedTheme ?? 'dark'
    setThemeState(nextTheme)
    document.documentElement.classList.toggle('dark', nextTheme === 'dark')
    setInitialized(true)
  }, [])

  useEffect(() => {
    if (!initialized) return
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('valuedex-theme', theme)
  }, [theme, initialized])

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const setTheme = (nextTheme: Theme) => {
    setThemeState(nextTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}

