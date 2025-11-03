'use client'

import { useEffect, useState } from 'react'
import { getCardDetails, CardDetails } from '@/lib/api'
import { ExternalLink, Loader2, Star, Calendar, Palette } from 'lucide-react'

interface CardDisplayProps {
  card: any
  onDetailsLoaded?: (details: CardDetails) => void
}

export default function CardDisplay({ card, onDetailsLoaded }: CardDisplayProps) {
  const [details, setDetails] = useState<CardDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDetails = async () => {
      setIsLoading(true)
      const data = await getCardDetails(card.id)
      if (data) {
        setDetails(data)
        onDetailsLoaded?.(data)
      }
      setIsLoading(false)
    }

    fetchDetails()
  }, [card.id])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!details) {
    return <div className="card">Failed to load card details</div>
  }

  return (
    <div className="card animate-fade-in">
      {/* Card Image */}
      <div className="mb-6">
        {details.image_url ? (
          <img
            src={details.image_url}
            alt={details.name}
            className="w-full rounded-lg shadow-lg"
          />
        ) : (
          <div className="w-full h-96 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg flex items-center justify-center text-white text-xl font-bold">
            {details.name}
          </div>
        )}
      </div>

      {/* Card Info */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">{details.name}</h2>
          <p className="text-gray-600">{details.set_name}</p>
        </div>

        {/* Price */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Current Market Price</div>
          <div className="text-3xl font-bold text-blue-600">
            ${details.current_price.toFixed(2)}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div className="flex items-start space-x-2">
            <Star className="w-5 h-5 text-yellow-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-600">Rarity</div>
              <div className="font-semibold text-gray-900">{details.rarity || 'Unknown'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-2">
            <Palette className="w-5 h-5 text-purple-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-600">Artist</div>
              <div className="font-semibold text-gray-900">{details.artist || 'Unknown'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-2">
            <Calendar className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-600">Release Year</div>
              <div className="font-semibold text-gray-900">{details.release_year || 'N/A'}</div>
            </div>
          </div>

          <div className="flex items-start space-x-2">
            <Star className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <div className="text-xs text-gray-600">Card #</div>
              <div className="font-semibold text-gray-900">{details.card_number || 'N/A'}</div>
            </div>
          </div>
        </div>

        {/* External Links */}
        <div className="space-y-2 pt-4 border-t border-gray-200">
          {details.tcgplayer_url && (
            <a
              href={details.tcgplayer_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between w-full px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <span className="text-sm font-medium text-blue-900">View on TCGPlayer</span>
              <ExternalLink className="w-4 h-4 text-blue-600" />
            </a>
          )}
          {details.ebay_url && (
            <a
              href={details.ebay_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between w-full px-4 py-2 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors"
            >
              <span className="text-sm font-medium text-yellow-900">View on eBay</span>
              <ExternalLink className="w-4 h-4 text-yellow-600" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

