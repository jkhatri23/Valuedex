'use client'

import { useState, useEffect } from 'react'
import { searchCards, Card } from '@/lib/api'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSelectCard: (card: Card) => void
}

export default function SearchBar({ onSelectCard }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Card[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)

  useEffect(() => {
    const searchTimeout = setTimeout(async () => {
      if (query.length > 1) {
        setIsLoading(true)
        try {
          const cards = await searchCards(query)
          console.log('Search results:', cards)
          setResults(cards || [])
          setShowResults(true)
        } catch (error) {
          console.error('Error in search:', error)
          setResults([])
          setShowResults(false)
        } finally {
          setIsLoading(false)
        }
      } else {
        setResults([])
        setShowResults(false)
      }
    }, 300)

    return () => clearTimeout(searchTimeout)
  }, [query])

  const handleSelectCard = (card: Card) => {
    onSelectCard(card)
    setQuery('')
    setShowResults(false)
  }

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for Pokemon cards (e.g., Charizard, Pikachu)..."
          className="w-full px-5 py-4 pl-12 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors text-gray-900 placeholder:text-gray-400 bg-white"
        />
        <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
          {isLoading ? (
            <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Search Results Dropdown */}
      {showResults && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-xl max-h-96 overflow-y-auto">
          {results.map((card, index) => (
            <button
              key={card.id || `card-${index}`}
              onClick={() => handleSelectCard(card)}
              className="w-full px-4 py-3 flex items-center space-x-4 hover:bg-gray-50 transition-colors text-left border-b border-gray-100 last:border-b-0"
            >
              {card.image_url && (
                <img
                  src={card.image_url}
                  alt={card.name || 'Card'}
                  className="w-12 h-16 object-cover rounded"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              )}
              <div className="flex-1">
                <div className="font-semibold text-gray-900">{card.name || 'Unknown Card'}</div>
                <div className="text-sm text-gray-600">{card.set_name || 'Unknown Set'}</div>
              </div>
              <div className="text-right">
                <div className="font-bold text-blue-600">${(card.current_price || 0).toFixed(2)}</div>
                <div className="text-xs text-gray-500">Current</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {showResults && query.length > 1 && results.length === 0 && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-xl p-4 text-center text-gray-600">
          No cards found. Try a different search term.
        </div>
      )}
    </div>
  )
}

