'use client'

import { useState, useEffect, useMemo, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import { searchCards, getCardDetails, Card } from '@/lib/api'
import { Search, Loader2, ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const CARDS_PER_PAGE = 20

function SearchResults() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const q = searchParams.get('q') || ''

  const [query, setQuery] = useState(q)
  const [results, setResults] = useState<Card[]>([])
  const [prices, setPrices] = useState<Record<string, number>>({})
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  const totalPages = Math.max(1, Math.ceil(results.length / CARDS_PER_PAGE))

  const paginatedResults = useMemo(
    () => results.slice((currentPage - 1) * CARDS_PER_PAGE, currentPage * CARDS_PER_PAGE),
    [results, currentPage]
  )

  useEffect(() => {
    setQuery(q)
  }, [q])

  useEffect(() => {
    if (!q) return
    let cancelled = false
    setIsLoading(true)
    setHasSearched(true)
    setPrices({})
    setCheckedIds(new Set())
    setCurrentPage(1)

    searchCards(q).then((data) => {
      if (cancelled) return
      setResults(data)
      setIsLoading(false)
    })

    return () => { cancelled = true }
  }, [q])

  useEffect(() => {
    if (paginatedResults.length === 0) return
    let cancelled = false

    const missing = paginatedResults.filter(
      (c) => !(c.current_price > 0) && !checkedIds.has(c.id)
    )
    for (const card of missing) {
      getCardDetails(card.id).then((details) => {
        if (cancelled) return
        setCheckedIds((prev) => new Set(prev).add(card.id))
        if (details && details.current_price > 0) {
          setPrices((prev) => ({ ...prev, [card.id]: details.current_price }))
        }
      })
    }

    return () => { cancelled = true }
  }, [paginatedResults, checkedIds])

  const getPrice = (card: Card) => prices[card.id] ?? card.current_price
  const isPriceLoading = (card: Card) => !(card.current_price > 0) && !checkedIds.has(card.id)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.length >= 2) {
      router.push(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  const handleCardClick = (card: Card) => {
    router.push(`/card/${card.id}`)
  }

  const goToPage = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const pageNumbers = useMemo(() => {
    const pages: (number | 'ellipsis')[] = []
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push('ellipsis')
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      for (let i = start; i <= end; i++) pages.push(i)
      if (currentPage < totalPages - 2) pages.push('ellipsis')
      pages.push(totalPages)
    }
    return pages
  }, [currentPage, totalPages])

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
          <div className="flex items-baseline justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Search results for &ldquo;{q}&rdquo;
            </h2>
            {!isLoading && results.length > 0 && (
              <span className="text-sm text-gray-500 dark:text-white/50">
                {results.length} card{results.length !== 1 && 's'} found
              </span>
            )}
          </div>
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
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
              {paginatedResults.map((card) => (
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
                  {getPrice(card) > 0 ? (
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      ${getPrice(card).toFixed(2)}
                    </div>
                  ) : isPriceLoading(card) ? (
                    <div className="text-xs text-gray-400 dark:text-white/40">
                      <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
                      Loading price...
                    </div>
                  ) : (
                    <div className="text-sm font-semibold text-gray-400 dark:text-white/40 italic">
                      Price Unavailable
                    </div>
                  )}
                </button>
              ))}
            </div>

            {totalPages > 1 && (
              <nav className="flex items-center justify-center gap-2 mt-10">
                <button
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  aria-label="Previous page"
                  className="p-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-white/70 hover:bg-gray-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>

                {pageNumbers.map((p, i) =>
                  p === 'ellipsis' ? (
                    <span
                      key={`e-${i}`}
                      className="px-2 text-gray-400 dark:text-white/30 select-none"
                    >
                      &hellip;
                    </span>
                  ) : (
                    <button
                      key={p}
                      onClick={() => goToPage(p)}
                      className={`min-w-[2.5rem] h-10 rounded-lg text-sm font-medium transition-colors ${
                        p === currentPage
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'border border-gray-200 dark:border-white/10 text-gray-700 dark:text-white/70 hover:bg-gray-100 dark:hover:bg-white/10'
                      }`}
                    >
                      {p}
                    </button>
                  )
                )}

                <button
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  aria-label="Next page"
                  className="p-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-white/70 hover:bg-gray-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </nav>
            )}
          </>
        )}
      </div>

      <footer className="bg-white/50 dark:bg-[#0a0a0a]/50 backdrop-blur-sm border-t border-gray-200 dark:border-white/10 mt-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <p className="text-gray-600 dark:text-white/70 mb-3 font-light">
              Data powered by eBay API &amp; Pokemon TCG API &bull; Predictions by Advanced ML Models
            </p>
            <p className="text-sm text-gray-500 dark:text-white/50 font-light max-w-3xl mx-auto">
              For entertainment and educational purposes only. Not financial advice.
              This site is not affiliated with, endorsed, or sponsored by The Pok&eacute;mon Company International, Nintendo, or Game Freak.
            </p>
          </div>
        </div>
      </footer>
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
