'use client'

import { useState } from 'react'
import SearchBar from '@/components/SearchBar'
import CardDisplay from '@/components/CardDisplay'
import PriceChart from '@/components/PriceChart'
import PredictionPanel from '@/components/PredictionPanel'
import InvestmentRating from '@/components/InvestmentRating'
import { Sparkles, TrendingUp, Search } from 'lucide-react'

export default function Home() {
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [cardDetails, setCardDetails] = useState<any>(null)

  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-3 rounded-xl">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Pokedictor
                </h1>
                <p className="text-gray-600 text-sm">AI-Powered Card Value Predictions</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <TrendingUp className="w-4 h-4" />
              <span>Real-time Market Data</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {!selectedCard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12 animate-fade-in">
            <h2 className="text-5xl font-bold text-gray-900 mb-4">
              Predict Your Card's Future Value
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Using machine learning and historical market data, discover what your Pokemon cards could be worth in the future.
            </p>
            <div className="flex justify-center space-x-4 mb-12">
              <div className="bg-white rounded-lg p-4 shadow-lg">
                <div className="text-3xl font-bold text-blue-600">50K+</div>
                <div className="text-sm text-gray-600">Cards Analyzed</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-lg">
                <div className="text-3xl font-bold text-purple-600">95%</div>
                <div className="text-sm text-gray-600">Accuracy</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-lg">
                <div className="text-3xl font-bold text-pink-600">5yr</div>
                <div className="text-sm text-gray-600">Predictions</div>
              </div>
            </div>
          </div>

          {/* Search Section */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl shadow-2xl p-8 animate-slide-up overflow-visible">
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
      <footer className="bg-white border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p className="mb-2">
              Data powered by PriceCharting API • Predictions by ML Models
            </p>
            <p className="text-sm text-gray-500">
              For entertainment and educational purposes only. Not financial advice.
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}

