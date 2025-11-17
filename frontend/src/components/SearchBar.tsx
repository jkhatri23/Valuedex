'use client'

import { useState, useEffect, useRef } from 'react'
import { searchCards } from '@/lib/api'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSelectCard: (card: any) => void
}

export default function SearchBar({ onSelectCard }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced search
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length >= 2) {
        setIsLoading(true)
        const data = await searchCards(query)
        setResults(data)
        setIsLoading(false)
        setIsOpen(true)
      } else {
        setResults([])
        setIsOpen(false)
      }
    }, 300)

    return () => clearTimeout(delayDebounceFn)
  }, [query])

  const handleSelectCard = (card: any) => {
    onSelectCard(card)
    setQuery('')
    setResults([])
    setIsOpen(false)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-gray-400" />
          )}
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for Pokemon cards..."
          className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder:text-gray-400 bg-white dark:bg-[#1a1a1a] dark:border-white/10 dark:text-white dark:placeholder:text-gray-400"
        />
      </div>

      {/* Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="w-full mt-2 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto dark:bg-[#1a1a1a] dark:border-white/10 dark:shadow-black/40">
          {results.map((card) => (
            <button
              key={card.id}
              onClick={() => handleSelectCard(card)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors dark:hover:bg-white/10 dark:border-white/5"
            >
              <div className="flex items-center space-x-3">
                {card.image_url && (
                  <img
                    src={card.image_url}
                    alt={card.name}
                    className="w-12 h-16 object-cover rounded"
                  />
                )}
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white">{card.name}</div>
                  <div className="text-sm text-gray-500 dark:text-white/70">{card.set_name}</div>
                  {card.current_price > 0 && (
                    <div className="text-sm font-semibold text-blue-600 dark:text-blue-300 mt-1">
                      ${card.current_price.toFixed(2)}
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {isOpen && query.length >= 2 && !isLoading && results.length === 0 && (
        <div className="w-full mt-2 bg-white rounded-lg shadow-xl border border-gray-200 px-4 py-8 text-center dark:bg-[#1a1a1a] dark:border-white/10 dark:shadow-black/40">
          <p className="text-gray-500 dark:text-white/70">No cards found matching "{query}"</p>
          <p className="text-sm text-gray-400 dark:text-white/50 mt-2">Try a different search term</p>
        </div>
      )}
    </div>
  )
}
