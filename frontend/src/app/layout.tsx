import type { Metadata } from 'next'
import { Inter, Space_Grotesk } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800'],
  style: ['normal'],
  display: 'swap',
  variable: '--font-inter',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  style: ['normal'],
  display: 'swap',
  variable: '--font-space-grotesk',
})

const themeInitScript = `
(function() {
  try {
    const storedTheme = localStorage.getItem('valuedex-theme')
    const nextTheme = storedTheme === 'light' || storedTheme === 'dark' ? storedTheme : 'dark'
    document.documentElement.classList.toggle('dark', nextTheme === 'dark')
  } catch (error) {
    document.documentElement.classList.add('dark')
  }
})();
`

export const metadata: Metadata = {
  title: 'Pokedictor - Pokemon Card Value Predictor',
  description: 'Predict Pokemon card values using machine learning and historical market data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable} dark`} suppressHydrationWarning>
      <body className={inter.className}>
        <Script
          id="valuedex-theme-init"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{ __html: themeInitScript }}
        />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}

