'use client'

import { useEffect, useState } from 'react'
import { getCardDetails, CardDetails } from '@/lib/api'
import { ExternalLink, Loader2, Star, Calendar, Palette, Hash } from 'lucide-react'

interface CardDisplayProps {
  card: any
  onDetailsLoaded?: (details: CardDetails) => void
}

export default function CardDisplay({ card, onDetailsLoaded }: CardDisplayProps) {
  const [details, setDetails] = useState<CardDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDetails = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getCardDetails(card.id)
        if (data) {
          setDetails(data)
          onDetailsLoaded?.(data)
        } else {
          setError('Failed to load card details')
        }
      } catch (err: any) {
        console.error('Error loading card details:', err)
        setError(err.response?.data?.detail || 'Failed to load card details. The API may be slow.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchDetails()
  }, [card.id, onDetailsLoaded])

  if (isLoading) {
    return (
      <div className="card flex flex-col items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600 dark:text-white/80">Loading card details...</p>
        <p className="text-sm text-gray-400 dark:text-white/60 mt-2">This may take a moment</p>
      </div>
    )
  }

  if (error || !details) {
    return (
      <div className="card">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 dark:bg-red-500/20 dark:border-red-500/40">
          <p className="text-red-700 font-semibold mb-2 dark:text-red-100">Error loading card details</p>
          <p className="text-sm text-red-600 dark:text-red-200">{error || 'Card details not available'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Card Image */}
      <div className="mb-6">
        {details.image_url ? (
          <img
            src={details.image_url}
            alt={details.name}
            className="w-full rounded-lg shadow-md"
          />
        ) : (
          <div className="w-full h-96 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center text-gray-400 text-xl font-semibold dark:from-white/10 dark:to-white/5 dark:text-white/60">
            {details.name}
          </div>
        )}
      </div>

      {/* Card Info */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{details.name}</h2>
          <p className="text-gray-600 dark:text-white/70">{details.set_name}</p>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-white/10">
          <div className="flex items-start space-x-3">
            <Star className="w-5 h-5 text-yellow-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-500 dark:text-white/60 mb-1">Rarity</div>
              <div className="font-semibold text-gray-900 dark:text-white">{details.rarity || 'Unknown'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <Palette className="w-5 h-5 text-purple-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-500 dark:text-white/60 mb-1">Artist</div>
              <div className="font-semibold text-gray-900 dark:text-white">{details.artist || 'Unknown'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <Calendar className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-500 dark:text-white/60 mb-1">Release Year</div>
              <div className="font-semibold text-gray-900 dark:text-white">{details.release_year || 'N/A'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <Hash className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-500 dark:text-white/60 mb-1">Card Number</div>
              <div className="font-semibold text-gray-900 dark:text-white">{details.card_number || 'N/A'}</div>
            </div>
          </div>
        </div>

        {/* External Links */}
        {(details.tcgplayer_url || details.ebay_url) && (
          <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-white/10">
            {details.tcgplayer_url && (
              <a
                href={details.tcgplayer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between w-full px-4 py-3 bg-blue-50 hover:bg-blue-100 border border-blue-100 rounded-lg transition-colors group dark:bg-[#050505] dark:hover:bg-[#0b0b0b] dark:border-white/15 dark:text-white"
              >
                <span className="text-sm font-medium text-blue-900 dark:text-white">View on TCGPlayer</span>
                <ExternalLink className="w-4 h-4 text-blue-600 dark:text-blue-300 group-hover:translate-x-1 transition-transform" />
              </a>
            )}
            {details.ebay_url && (
              <a
                href={details.ebay_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between w-full px-4 py-3 bg-yellow-50 hover:bg-yellow-100 border border-yellow-100 rounded-lg transition-colors group dark:bg-[#050505] dark:hover:bg-[#0b0b0b] dark:border-white/15 dark:text-white"
              >
                <span className="text-sm font-medium text-yellow-900 dark:text-white">View on eBay</span>
                <ExternalLink className="w-4 h-4 text-yellow-500 dark:text-yellow-200 group-hover:translate-x-1 transition-transform" />
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
