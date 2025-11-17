import type { Metadata } from 'next'
import { Inconsolata } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'

const inconsolata = Inconsolata({
  subsets: ['latin'],
  weight: ['400', '700'],
  style: ['normal'],
  display: 'swap',
  variable: '--font-inconsolata',
})

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
    <html lang="en" className={inconsolata.variable}>
      <body className={inconsolata.className}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}

