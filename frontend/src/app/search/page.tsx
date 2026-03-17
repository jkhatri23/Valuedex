'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import { searchCards, Card } from '@/lib/api'
import { Search, Loader2, ArrowLeft } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

function SearchResults() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const q = searchParams.get('q') || ''

  const [query, setQuery] = useState(q)
  const [results, setResults] = useState<Card[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    setQuery(q)
  }, [q])

  useEffect(() => {
    if (!q) return
    setIsLoading(true)
    setHasSearched(true)
    searchCards(q).then((data) => {
      setResults(data)
      setIsLoading(false)
    })
  }, [q])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.length >= 2) {
      router.push(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  const handleCardClick = (card: Card) => {
    router.push(`/?cardId=${card.id}`)
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-[#0a0a0a] dark:via-[#0d0d0d] dark:to-[#0a0a0a]">
      <header className="bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-gray-200 dark:border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.push('/')}
              className="flex items-center space-x-2"
            >
              <div className="bg-black p-2 rounded-lg hover:scale-110 transition-transform duration-300">
                <Image
                  src="/logo.png"
                  alt="Valuedex Logo"
                  width={24}
                  height={24}
                  className="w-6 h-6"
                />
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
                Valuedex
              </h1>
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => router.push('/')}
          className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 dark:text-white/70 dark:hover:text-white font-medium transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>

        <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-10">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for any Pokémon card..."
              className="w-full pl-12 pr-5 py-3 text-base border-2 border-gray-200 dark:border-white/10 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-gray-900 placeholder:text-gray-400 bg-white dark:bg-[#1a1a1a] dark:text-white dark:placeholder:text-gray-500 shadow-sm hover:shadow-md"
            />
          </div>
        </form>

        {q && (
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Search results for &ldquo;{q}&rdquo;
          </h2>
        )}

        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-3" />
            <p className="text-gray-500 dark:text-white/60">Searching cards...</p>
          </div>
        )}

        {!isLoading && hasSearched && results.length === 0 && (
          <div className="text-center py-20">
            <p className="text-gray-600 dark:text-white/70 font-medium text-lg">
              No cards found matching &ldquo;{q}&rdquo;
            </p>
            <p className="text-sm text-gray-500 dark:text-white/50 mt-2">
              Try a different search term
            </p>
          </div>
        )}

        {!isLoading && results.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
            {results.map((card) => (
              <button
                key={card.id}
                onClick={() => handleCardClick(card)}
                className="group bg-white/60 dark:bg-white/5 backdrop-blur-sm border border-gray-200 dark:border-white/10 rounded-lg p-5 hover:scale-105 hover:border-gray-300 dark:hover:border-white/20 hover:shadow-xl transition-all duration-300 text-left"
              >
                {card.image_url && (
                  <div className="mb-4 rounded-lg overflow-hidden bg-gray-100 dark:bg-white/5 aspect-[2.5/3.5]">
                    <img
                      src={card.image_url}
                      alt={card.name}
                      className="w-full h-full object-contain"
                    />
                  </div>
                )}
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors min-h-[2.5rem]">
                  {card.name}
                </h4>
                <p className="text-xs text-gray-500 dark:text-white/60 mb-3">
                  {card.set_name}
                </p>
                {card.current_price > 0 ? (
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    ${card.current_price.toFixed(2)}
                  </div>
                ) : (
                  <div className="text-sm font-semibold text-gray-400 dark:text-white/40 italic">
                    Price Coming Soon
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}

export default function SearchPage() {
  return (
    <Suspense>
      <SearchResults />
    </Suspense>
  )
}
