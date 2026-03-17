'use client'

import { useState, useEffect, useRef } from 'react'
import { searchCards } from '@/lib/api'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSelectCard: (card: any) => void
  onSearch?: (query: string) => void
}

export default function SearchBar({ onSelectCard, onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking/tapping outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent | TouchEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchstart', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
    }
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
            <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          )}
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && query.length >= 2 && onSearch) {
              e.preventDefault()
              setIsOpen(false)
              setResults([])
              onSearch(query)
            }
          }}
          placeholder="Search for any Pokémon card..."
          className="w-full pl-12 pr-5 py-3 text-base border-2 border-gray-200 dark:border-white/10 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-gray-900 placeholder:text-gray-400 bg-white dark:bg-[#1a1a1a] dark:text-white dark:placeholder:text-gray-500 shadow-sm hover:shadow-md"
        />
      </div>

      {/* Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="absolute w-full mt-3 bg-white/95 dark:bg-[#0a0a0a]/95 backdrop-blur-md rounded-md shadow-2xl border border-gray-200 dark:border-white/10 max-h-[70vh] overflow-y-auto z-50">
          {results.map((card) => (
            <button
              key={card.id}
              onClick={() => handleSelectCard(card)}
              className="w-full px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-white/5 border-b border-gray-100 dark:border-white/5 last:border-b-0 transition-all group"
            >
              <div className="flex items-center space-x-4">
                {card.image_url && (
                  <img
                    src={card.image_url}
                    alt={card.name}
                    className="w-14 h-20 object-cover rounded shadow-sm group-hover:shadow-md transition-shadow"
                  />
                )}
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{card.name}</div>
                  <div className="text-sm text-gray-500 dark:text-white/60 mt-0.5">{card.set_name}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {isOpen && query.length >= 2 && !isLoading && results.length === 0 && (
        <div className="absolute w-full mt-3 bg-white/95 dark:bg-[#0a0a0a]/95 backdrop-blur-md rounded-md shadow-2xl border border-gray-200 dark:border-white/10 px-6 py-10 text-center z-50">
          <p className="text-gray-600 dark:text-white/70 font-medium">No cards found matching "{query}"</p>
          <p className="text-sm text-gray-500 dark:text-white/50 mt-2 font-light">Try a different search term</p>
        </div>
      )}
    </div>
  )
}
