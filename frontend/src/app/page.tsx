'use client'

import { useState } from 'react'
import Image from 'next/image'
import SearchBar from '@/components/SearchBar'
import CardDisplay from '@/components/CardDisplay'
import PriceChart from '@/components/PriceChart'
import PredictionPanel from '@/components/PredictionPanel'
import InvestmentRating from '@/components/InvestmentRating'
import { TrendingUp, Search } from 'lucide-react'

export default function Home() {
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [cardDetails, setCardDetails] = useState<any>(null)

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#0d0d0d] to-[#121212]">
      {/* Header */}
      <header className="bg-gradient-to-b from-[#151515] via-[#121212] to-[#0f0f0f] shadow-sm border-b border-[#1f1f1f]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-black p-3 rounded-xl">
                <Image 
                  src="/logo.png" 
                  alt="Valuedex Logo" 
                  width={32} 
                  height={32}
                  className="w-8 h-8"
                />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">
                  Valuedex
                </h1>
                <p className="text-white text-sm">AI-Powered Card Value Predictions</p>
              </div>
            </div>
            
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {!selectedCard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12 animate-fade-in">
            <h2 className="text-5xl font-bold text-white mb-4">
              Predict Your Card's Future Value
            </h2>
            <p className="text-xl text-white mb-8 max-w-2xl mx-auto">
              Using machine learning and historical market data, discover what your trading cards could be worth in the future.
            </p>
          </div>

          {/* Search Section */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl p-8 animate-slide-up overflow-visible">
              <div className="flex items-center space-x-3 mb-6">
                <Search className="w-6 h-6 text-gray-400" />
                <h3 className="text-2xl font-semibold text-gray-900">Search for a Card</h3>
              </div>
              <div className="relative">
                <SearchBar onSelectCard={(card) => setSelectedCard(card)} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Card Details Section */}
      {selectedCard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={() => {
              setSelectedCard(null)
              setCardDetails(null)
            }}
            className="mb-6 text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-2"
          >
            <span>← Back to Search</span>
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Card Info */}
            <div className="lg:col-span-1 space-y-6">
              <CardDisplay 
                card={selectedCard} 
                onDetailsLoaded={setCardDetails}
              />
              {cardDetails && cardDetails.features && (
                <InvestmentRating 
                  cardId={selectedCard.id}
                  features={cardDetails.features}
                />
              )}
            </div>

            {/* Right Column - Charts and Predictions */}
            <div className="lg:col-span-2 space-y-6">
              {cardDetails && (
                <>
                  <PriceChart cardId={selectedCard.id} />
                  <PredictionPanel 
                    cardId={selectedCard.id}
                    cardName={selectedCard.name}
                    currentPrice={cardDetails.current_price}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-gradient-to-t from-[#151515] via-[#121212] to-[#0f0f0f] border-t border-[#1f1f1f] mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-white">
            <p className="mb-2">
              Data powered by PriceCharting API • Predictions by ML Models
            </p>
            <p className="text-sm text-white">
              For entertainment and educational purposes only. Not financial advice. This site is not affiliated with, endorsed, or sponsored by The Pokémon Company International, Nintendo, or Game Freak.
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}

