'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Image from 'next/image'
import { getCardDetails, CardDetails } from '@/lib/api'
import { ArrowLeft, Loader2 } from 'lucide-react'
import CardDisplay from '@/components/CardDisplay'
import PriceChart from '@/components/PriceChart'
import PredictionPanel from '@/components/PredictionPanel'
import InvestmentRating from '@/components/InvestmentRating'
import ComparePanel from '@/components/ComparePanel'
import ThemeToggle from '@/components/ThemeToggle'

export default function CardPage() {
  const params = useParams()
  const router = useRouter()
  const cardId = params.id as string

  const [card, setCard] = useState<any>(null)
  const [cardDetails, setCardDetails] = useState<CardDetails | null>(null)
  const [latestPrediction, setLatestPrediction] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!cardId) return
    setIsLoading(true)
    setError(null)
    getCardDetails(cardId).then((details) => {
      if (details) {
        setCard({
          id: details.external_id || String(details.id) || cardId,
          name: details.name,
          set_name: details.set_name,
          current_price: details.current_price,
          image_url: details.image_url,
        })
      } else {
        setError('Card not found')
      }
      setIsLoading(false)
    })
  }, [cardId])

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
          onClick={() => router.back()}
          className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 dark:text-white/70 dark:hover:text-white font-medium transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {isLoading && (
          <div className="flex flex-col items-center justify-center py-32">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-3" />
            <p className="text-gray-500 dark:text-white/60">Loading card details...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-32">
            <p className="text-gray-600 dark:text-white/70 font-medium text-lg">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 text-blue-500 hover:text-blue-600 font-medium"
            >
              Return to Home
            </button>
          </div>
        )}

        {!isLoading && card && (
          <div className="bg-black/[0.02] dark:bg-white/[0.02] rounded-2xl p-8 border border-black/[0.03] dark:border-white/[0.03]">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
              <div className="lg:col-span-1 flex">
                <div className="w-full">
                  <CardDisplay
                    card={card}
                    onDetailsLoaded={setCardDetails}
                  />
                </div>
              </div>

              <div className="lg:col-span-2 flex">
                {cardDetails && (
                  <div className="w-full [&>.card]:h-full">
                    <PriceChart
                      cardId={card.id}
                      cardName={card.name}
                      setName={card.set_name}
                    />
                  </div>
                )}
              </div>
            </div>

            {cardDetails && cardDetails.features && (
              <div className="mt-8">
                <InvestmentRating
                  features={cardDetails.features}
                />
              </div>
            )}

            {cardDetails && (
              <div className="mt-8">
                <PredictionPanel
                  cardId={card.id}
                  cardName={card.name}
                  currentPrice={cardDetails.current_price}
                  onPredictionGenerated={setLatestPrediction}
                />
              </div>
            )}

            {cardDetails && (
              <div className="mt-8">
                <ComparePanel
                  primaryCard={{
                    id: card.id,
                    name: cardDetails.name || card.name,
                    set_name: cardDetails.set_name || card.set_name,
                    image_url: cardDetails.image_url || card.image_url,
                    current_price: cardDetails.current_price,
                    features: cardDetails.features,
                  }}
                  primaryPrediction={latestPrediction}
                />
              </div>
            )}
          </div>
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
