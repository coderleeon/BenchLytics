import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Benchlytics - LLM Benchmarking System',
  description: 'Production-grade LLM benchmarking and evaluation platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground`}>
        <nav className="glass sticky top-0 z-50 w-full px-6 py-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-xl font-bold tracking-tight text-white">
              Benchlytics
            </Link>
            <div className="hidden md:flex items-center gap-4 text-sm text-muted-foreground">
              <Link href="/" className="hover:text-white transition-colors">Leaderboard</Link>
              <Link href="/run" className="hover:text-white transition-colors">Run Benchmark</Link>
            </div>
          </div>
        </nav>
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
